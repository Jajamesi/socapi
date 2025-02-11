import asyncio
import aiohttp

from . import constants as const
from . import utils

from ._downloader import Downloader
from ._statistic import Statistic
from ._searcher import Searcher


class SocAPIClient(Downloader, Statistic, Searcher):
    def __init__(self, base_url, username, password):
        self.base_url = str(base_url)

        self.username = str(username)
        self.password = str(password)

        self._session = None
        self.token = str()
        self.headers = dict()
        self.progress_status = list()
        self.semaphore = asyncio.Semaphore(const.MAX_CONCURRENT_REQUESTS)

    async def _ensure_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()

    async def close(self):
        if self._session is not None:
            await self._session.close()

    # def close(self):
    #     asyncio.run(self._close())

    async def _request(
            self,
            endpoint,
            method="post",
            headers=None,
            payload=None,
            ssl=False,
            request_name="Request",
            attempts=const.RETRIES_NUM,
            sleep=1
    ):

        await self._ensure_session()

        # Validate the method and resolve aiohttp method
        if method.lower() not in const.VALID_REQUEST_METHODS:
            raise ValueError(f"Invalid method: {method}. Use one of {const.VALID_REQUEST_METHODS}.")
        aiohttp_method = getattr(self._session, method.lower())

        request_url = f"{self.base_url}/{endpoint}"

        for attempt in range(attempts):
            try:
                async with self.semaphore:
                    response = await aiohttp_method(request_url, headers=headers, json=payload, ssl=ssl)
                return response

            except Exception as e:
                error = e
                await asyncio.sleep(sleep)
            finally:
                if attempt == attempts - 1:
                    raise Exception(f"{request_name} failed - retries amount exceeded:", error)

    async def _login(self):

        login_payload = {
            "login": self.username,
            "password": self.password
        }

        result = await self._request(endpoint=const.LOGIN_ENDPOINT, request_name="Login", payload=login_payload)

        result_json = await result.json()

        request_result = result_json.get("result")

        if request_result is None:
            raise ValueError(f"Login failed: {result_json.get("error", "unknown error")}")

        token = request_result.get("session_token")
        if token is None:
            raise ValueError("Login failed: No session token received")

        self.token = token
        self.headers = {
            "Authorization": self.token
        }


    async def has_completes(self, poll_id:int) -> bool:

        payload = {
            "is_poll_complete": True,
            "is_poll_in_progress": True,
            "domain_ids": [1],
            "id": poll_id
        }

        result = await self._request(
            endpoint=const.STATISTIC_ENDPOINT,
            payload=payload,
            request_name="stat any exist",
            headers=self.headers
        )

        result_json = await result.json()

        if result_json.get("error")!= "":
            raise ValueError(f"Error in getting poll statistic: {result_json.get('error')}")

        return result_json["result"]["ended_count"] > 0


    # def has_completes(self, poll_id: int) -> bool:
    #     return asyncio.run(self._any_completes(poll_id))
