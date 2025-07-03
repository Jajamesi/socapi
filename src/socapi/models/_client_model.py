from typing import List, Literal, Union, get_args, Iterable, Dict, Optional, Any
from pydantic import BaseModel, field_validator, Field, ConfigDict, model_validator, computed_field
from enum import Enum
import aiohttp
import asyncio

from .. import constants
from .. import endpoints

SLEEP_TIME=1 #sec

class PlatformsShort(str, Enum):
    online_sociology="online-sociology"
    world_survey = "world-survey"

class PlatformsFull(str, Enum):
    online_sociology = "https://admin.online-sociology.ru"
    world_survey = "https://admin.world_survey.com"


class ClientModel(BaseModel):
    platform: Union[PlatformsShort | str]
    login: str
    password: str

    _session: Optional[aiohttp.ClientSession | None] = None
    token: Optional[str] = None
    headers: Optional[dict[str, str]] = None
    progress_status: Optional[list[str]] = None
    semaphore: asyncio.Semaphore = asyncio.Semaphore(constants.MAX_CONCURRENT_REQUESTS)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_raw(cls, platform: str, login: str, password: str) -> "ClientModel":
        return cls(platform=PlatformsShort(platform), login=login, password=password)


    @field_validator("platform", mode="before")
    @classmethod
    def validate_platform(cls, v: str) -> PlatformsShort:
        if isinstance(v, PlatformsShort):
            return v
        try:
            return PlatformsShort(v)
        except ValueError:
            raise ValueError(f"Invalid platform: {v!r}")


    @computed_field
    @property
    def base_url(self) -> PlatformsFull:
        return PlatformsFull[self.platform.name].value


class ValidRequestsMethods(str, Enum):
    post = "post"
    get = "get"


class Endpoints(str, Enum):
    LOGIN_ENDPOINT="api/login"
    EXPORT_START_ENDPOINT = "api/poll/stat/export"
    EXPORT_PROGRESS_ENDPOINT = f"api/poll/stat/export/progress"
    DOWNLOAD_START_ENDPOINT = f"api/poll/stat/export/progress/download"
    DOWNLOAD_DONE_ENDPOINT = f"api/poll/stat/export/progress/done"
    QUOTA_LIST_ENDPOINT = "api/counter/list"
    POLL_GET_ENDPOINT = "api/poll/get"
    SEARCH_LIST_ENDPOINT = "api/poll/list"
    STATISTIC_ENDPOINT = "api/poll/stat"
    CONVERSION = f"api/poll/stat/conversion"
    LINKS_ENDPOINT = f"api/poll/source/links"
    QUESTIONS_ALL = "api/question/getbypoll"
    QUESTIONS_BLOCK = "api/question/getbyblock"
    BLOCKS = "api/block/getbypoll"


class LoginPayload(BaseModel):
    login: str
    password: str


def validate_login(func):
    async def wrapFunc(self, *args, **kwargs):
        await self._login()
        return await func(self, *args, **kwargs)
    return wrapFunc