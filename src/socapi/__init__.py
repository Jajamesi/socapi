import asyncio
import aiohttp
from pydantic import validate_call
from typing import List, Literal, Union, get_args, Iterable, Dict, Optional, Any, Coroutine

from . import constants as const
from . import endpoints
from . import utils

from ._downloader import Downloader
from ._statistic import Statistic
from ._searcher import Searcher
from ._links import Links
from ._meta_parser import MetaParser

from .models import _client_model as cm


class SocAPIClient(cm.ClientModel, Downloader, Statistic, Searcher, Links, MetaParser):

    async def _ensure_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()


    async def close(self):
        if self._session is not None:
            await self._session.close()


    async def _parse_json_result(self, result, context: str) -> dict:
        try:
            result_json = await result.json()
        except Exception as e:
            raise ValueError(f"Failed to parse JSON in {context}: {e}")
        if result_json.get("error"):
            raise ValueError(f"Error in {context}: {result_json.get('error')}")
        return result_json["result"]


    @validate_call
    async def _request(
            self,
            endpoint: cm.Endpoints,
            method: cm.ValidRequestsMethods,
            headers: Optional[dict[str, str]]=None,
            payload: Optional[dict]=None,
            ssl: Optional[bool] = False,
            request_name: Optional[str]="Request",
            attempts: Optional[int]=const.RETRIES_NUM,
            sleep: Optional[int]=cm.SLEEP_TIME
    ) -> Any | None:
        """
        Perform an HTTP request with automatic retry logic.

        Sends an asynchronous HTTP request to the specified endpoint using the configured session.
        If the request fails due to an exception, it will retry up to a specified number of attempts,
        waiting a given number of seconds between attempts.

        Args:
            endpoint (cm.Endpoints): The API endpoint to send the request to.
            method (cm.ValidRequestsMethods): The HTTP method to use (e.g., GET, POST).
            headers (Optional[dict[str, str]]): Optional HTTP headers to include in the request.
            payload (Optional[dict]): Optional JSON payload to send with the request.
            ssl (Optional[bool]): Whether to use SSL for the request. Defaults to False.
            request_name (Optional[str]): Name of the request for logging/debugging purposes.
            attempts (Optional[int]): Number of retry attempts in case of failure.
            sleep (Optional[int]): Number of seconds to wait between retry attempts.

        Returns:
            Any | None: The HTTP response object if the request is successful; otherwise, raises an exception.

        Raises:
            Exception: If all retry attempts fail, an exception is raised with the last encountered error.
        """

        await self._ensure_session()
        aiohttp_method = getattr(self._session, method.value.lower())

        request_url = f"{self.base_url}/{endpoint.value}"

        for attempt in range(attempts):
            try:
                async with self.semaphore:
                    response = await aiohttp_method(request_url, headers=headers, json=payload, ssl=ssl)
                return response

            except Exception as e:
                if attempt == attempts - 1:
                    raise Exception(f"{request_name} failed - retries amount exceeded:", e)
                await asyncio.sleep(sleep)


    async def _login(self) -> None:
        """
        Authenticate the client and store the session token.

        This method sends a login request using the client's credentials. If successful,
        it retrieves a session token from the response and stores it in the `self.token` attribute.
        The session token is also added to the `Authorization` header for subsequent requests.

        Raises:
            ValueError: If the login response does not contain a session token.
            SomeException: If the request or response parsing fails. (Replace with actual exceptions.)
        """

        # if session is created from existing token, no need to login
        if self.is_from_token:
            return None

        req_name = "Login"

        login_payload = cm.LoginPayload(login=self.login, password=self.password)

        result = await self._request(
            method=cm.ValidRequestsMethods.post,
            endpoint=endpoints.LOGIN_ENDPOINT,
            request_name=req_name,
            payload=login_payload.model_dump()
        )

        result_json = await self._parse_json_result(result, req_name)
        token = result_json.get("session_token")

        if token is None:
            raise ValueError("Login failed: No session token received")

        self.token = token
        self.headers = {
            "Authorization": self.token
        }


    async def profile_user(self) -> None:
        req_name = "Profile"
        result = await self._request(
            method=cm.ValidRequestsMethods.post,
            endpoint=cm.Endpoints.PROFILE,
            request_name=req_name,
            headers=self.headers
        )
        result_json = await self._parse_json_result(result, req_name)

        if result_json.get("login") is not None:
            self.login = result_json.get("login")
            return


    # @staticmethod
    # def validate_login(func):
    #     async def wrapFunc(self, *args, **kwargs):
    #         await self._login()
    #         return await func(self, *args, **kwargs)
    #     return wrapFunc

    @validate_call
    @cm.validate_login
    async def has_completes(self, poll_id:int) -> bool:
        """
        Check whether a poll has any completed responses.

        This method sends a request to the statistics endpoint to check if a poll,
        identified by its ID, has at least one completed response (`ended_count > 0`).

        Args:
            poll_id (int): The unique identifier of the poll to check.

        Returns:
            bool: True if the poll has at least one completed response; False otherwise.

        Raises:
            SomeException: If the request or JSON parsing fails. (Replace with actual exceptions if known.)
        """

        # await self._login()

        payload = {
            "is_poll_complete": True,
            "is_poll_in_progress": True,
            "domain_ids": [1],
            "id": poll_id
        }

        # print(payload)

        req_name="stat any exist"
        result = await self._request(
            method=cm.ValidRequestsMethods.post,
            endpoint=endpoints.STATISTIC_ENDPOINT,
            payload=payload,
            request_name=req_name,
            headers=self.headers
        )

        result_json = await self._parse_json_result(result, req_name)

        return result_json["ended_count"] > 0