from typing import List, Literal, Union, get_args, Iterable, Dict, Optional, Any
from typing import Callable, Awaitable, Optional, Dict, Any, Union, ClassVar

from pydantic import BaseModel, field_validator, Field, ConfigDict, model_validator, computed_field
from enum import Enum
import aiohttp
from http import HTTPStatus, HTTPMethod
import asyncio
from pydantic import validate_call, ValidationError
import inspect
from pathlib import Path

from .. import expeptions
from .. import utils

RETRIES_NUM = 3
REQUEST_RETRIE_INTERVAL = 1
MAX_CONCURRENT_DOWNLOAD_REQUESTS = 5
DOWNLOAD_CHUNK_SIZE = 1024
DEFAULT_DOMAIN_IDS = [1]


class FileInput(BaseModel):
    name: str

    VALID_EXTENSIONS: ClassVar[set[str]] = {'.sav', '.zsav', '.xls', '.xlsx'}

    @field_validator('name')
    def validate_filename(cls, v: str) -> str:
        ext = Path(v).suffix.lower()
        if not ext or ext not in cls.VALID_EXTENSIONS:
            raise ValueError(f"Filename must end with one of: {', '.join(cls.VALID_EXTENSIONS)}")
        return v


class PlatformsShort(str, Enum):
    online_sociology="online-sociology"
    world_survey = "world-survey"

class PlatformsAdmin(str, Enum):
    online_sociology = f"https://admin.online-sociology.ru"
    world_survey = f"https://admin.world-survey.com"


class PlatformsRoot(str, Enum):
    online_sociology = "https://online-sociology.ru"
    world_survey = "https://world-survey.com"


class Endpoints(str, Enum):
    LOGIN= "api/login"
    EXPORT_START = "api/poll/stat/export"
    EXPORT_PROGRESS = f"api/poll/stat/export/progress"
    DOWNLOAD_POLL = f"statistics"
    DOWNLOAD_START = f"api/poll/stat/export/progress/download"
    EXPORT_DONE = f"api/poll/stat/export/progress/done"
    QUOTAS = "api/counter/list"
    POLL_DESCRIPTION_SOURCES = "api/poll/get"
    SEARCH_POLS = "api/poll/list"
    STATISTIC = "api/poll/stat"
    CONVERSION = f"api/poll/stat/conversion"
    PERSONAL_LINKS = f"api/poll/source/links"
    QUESTIONS_BY_POLL = "api/question/getbypoll"
    QUESTIONS_BY_BLOCK = "api/question/getbyblock"
    BLOCKS_IN_POLL = "api/block/getbypoll"
    USER_PROFILE = "api/profile"

class RequestNames(str, Enum):
    GENERIC = "Request"
    LOGIN = "Login"
    PROFILE = "Profile"
    BLOCKS_IN_POLL = "Get blocks in poll"
    GET_QUESTIONS = "Get questions"
    EMPTY_POLL = "Empty poll"
    EXPORT_START = "Export"
    PROGRESS = "Progress"
    DOWNLOAD_START = "Download"
    DOWNLOAD_POLL = "Direct download"
    SEARCH_POLS="Searching polls"
    QUOTAS="Getting quotas"
    GET_METADATA="Getting metadata"
    CONVERSION="Getting conversions"
    EXPORT_DONE = "Done"
    STATISTIC = "Statistics"
    PERSONAL_LINKS = "Links"


class InitSource(Enum):
    from_credentials = 1
    from_token = 2


def validate_login(func):
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except expeptions.TokenError as e:
            await self._login()
            return await func(self, *args, **kwargs)
    return wrapper


class ClientModel(BaseModel):
    platform: Union[PlatformsShort | str]
    login: str | None
    password: str | None
    init_source: InitSource
    
    meta: list[int] | None  = None
    token: Optional[str] = None
    headers: Optional[dict[str, str]] = None
    progress_status: Optional[list[str]] = None
    semaphore: asyncio.Semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOAD_REQUESTS)

    model_config = ConfigDict(arbitrary_types_allowed=True)


    @classmethod
    async def from_credentials(cls, platform: str, login: str, password: str) -> "ClientModel":
        inst = cls(platform=platform, login=login, password=password, init_source=InitSource.from_credentials)
        await inst._login()
        return inst


    @classmethod
    async def from_token(cls, platform: str, token: str) -> "ClientModel":
        inst = cls(platform=platform, login=None, password=None, init_source=InitSource.from_token)
        inst.set_auth(token)
        await inst.profile_user()
        return inst


    @field_validator("platform", mode="before")
    @classmethod
    def validate_platform(cls, v: str) -> PlatformsShort:
        if isinstance(v, PlatformsShort): return v
        try: return PlatformsShort(v.lower().strip())
        except ValueError: raise ValueError(f"Invalid platform: {v!r}")


    @computed_field
    @property
    def admin_url(self) -> str:
        return PlatformsAdmin[self.platform.name].value

    @computed_field
    @property
    def base_url(self) -> str:
        return PlatformsRoot[self.platform.name].value





    async def _make_request_with_retries(
            self,
            request_func: Callable[[], Awaitable[Any]],
            request_name: RequestNames,
            attempts: int,
            sleep: int
    ) -> Any:
        for attempt in range(attempts):
            try:
                async with self.semaphore:
                    return await request_func()
            except Exception as e:
                if isinstance(e, expeptions.PlatformError):
                    if attempt < attempts - 1:
                        await asyncio.sleep(sleep)
                        continue
                raise
        raise expeptions.MaxRetriesExceededError(request_name)


    @validate_call
    async def _download_request(
            self,
            endpoint: Endpoints,
            server_filename: FileInput,
            dest_path: Path,
            host: Literal["admin_url", "base_url"] = "base_url",
            ssl: Optional[bool] = False,
            request_name: RequestNames = RequestNames.GENERIC,
            attempts: Optional[int] = RETRIES_NUM,
            sleep: Optional[int] = REQUEST_RETRIE_INTERVAL,
    ):
        request_url = f"{getattr(self, host)}/{endpoint.value}/{server_filename.name}"

        async def request_func():
            async with aiohttp.request(method=HTTPMethod.GET, url=request_url, ssl=ssl) as response:
                response.raise_for_status()
                utils.create_sub_dirs(dest_path)
                with open(dest_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(DOWNLOAD_CHUNK_SIZE):
                        f.write(chunk)
                return None

        return await self._make_request_with_retries(request_func, request_name, attempts, sleep)


    @validate_call
    async def _request(
            self,
            endpoint: Endpoints,
            method: HTTPMethod,
            host: Literal["admin_url", "base_url"] = "admin_url",
            headers: Optional[dict[str, str]] = None,
            payload: Optional[dict] = None,
            ssl: Optional[bool] = False,
            request_name: RequestNames = RequestNames.GENERIC,
            attempts: Optional[int] = RETRIES_NUM,
            sleep: Optional[int] = REQUEST_RETRIE_INTERVAL,
            extract_result: bool = False,
    ) -> Union[Dict[Any, Any], bytes, None, List[Any]]:
        request_url = f"{getattr(self, host)}/{endpoint.value}"

        async def request_func():
            async with aiohttp.request(
                    method=method,
                    url=request_url,
                    headers=headers,
                    json=payload,
                    ssl=ssl
            ) as response:
                match response.status:
                    case HTTPStatus.LOCKED:
                        raise expeptions.AuthError
                    case HTTPStatus.UNAUTHORIZED:
                        raise expeptions.TokenError
                    case HTTPStatus.OK:
                        if "application/json" in response.headers.get("Content-Type", ""):
                            resp_json = await response.json()
                            return resp_json.get("result") if extract_result else resp_json
                        else:
                            # Handle non-JSON response
                            return None

                        # # TBD
                        # match response.headers.get("Content-Type", ""):
                        #     case "application/json":
                        #         resp_json = await response.json()
                        #         return resp_json.get("result") if extract_result else resp_json
                        #     case _:
                        #         return None
                    case HTTPStatus.INTERNAL_SERVER_ERROR:
                        raise expeptions.PlatformError(request_name)
                    case _:
                        raise ValueError("UNCACHED STATUS", response.status)

        return await self._make_request_with_retries(request_func, request_name, attempts, sleep)

    def set_auth(self, t: str) -> None:
        if t is None: raise ValueError("Auth token is missing")
        self.token = t
        self.headers = {"Authorization": self.token}

    async def _login(self) -> None:
        class LoginPayload(BaseModel):
            login: str
            password: str

            @field_validator("login", "password")
            @classmethod
            def not_none(cls, v):
                if v is None: raise expeptions.MissingCredentialsError
                return v


        try: login_payload = LoginPayload(login=self.login, password=self.password)
        except ValidationError: raise expeptions.MissingCredentialsError

        r = await self._request(
            method=HTTPMethod.POST,
            endpoint=Endpoints.LOGIN,
            request_name=RequestNames.LOGIN,
            payload=login_payload.model_dump(),
            extract_result=True,
        )

        self.set_auth(r.get("session_token"))

        await self.profile_user()

    @validate_login
    async def profile_user(self) -> None:
        r = await self._request(
            method=HTTPMethod.POST,
            endpoint=Endpoints.USER_PROFILE,
            request_name=RequestNames.PROFILE,
            headers=self.headers,
            extract_result=True
        )

        self.login = r.get("login")
        self.meta = r.get("meta")