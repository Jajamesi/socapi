from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from __init__ import SocAPIClient

import asyncio

from . import utils
from .models import _client_model as cm
from .models import _general_models as gm

from pydantic import validate_call
from http import HTTPMethod

class Constructor:
    """
    A class to handle creating and modifying poll questions from a socpanel API.

    Expects the main class to define:
    - self._headers: headers for requests.
    - self._login(): method to login in panel.
    - self._request(): method to send generic requests.

    Attributes:
    -----------
    headers : dict
        Headers for the API requests.

    Methods:
    --------

    """


    @cm.validate_login
    async def duplicate_poll(
            self: "SocAPIClient",
            id: int,
            with_counters: bool
    ) -> gm.Poll:
        result = await self._request(
            method=HTTPMethod.POST,
            endpoint=cm.Endpoints.DUPLICATE_POLL,
            payload={
                "id": id,
                "with_counters": with_counters,
            },
            headers=self.headers,
            request_name=cm.RequestNames.DUPLICATE_POLL,
            extract_result=True,
        )

        return gm.Poll(**result)


    @cm.validate_login
    async def update_meta(
            self: "SocAPIClient",
            id: int,
            meta: List[int]
    ) -> None:
        await self._request(
            method=HTTPMethod.POST,
            endpoint=cm.Endpoints.UPDATE_META,
            payload={
                "id": id,
                "meta": meta,
            },
            headers=self.headers,
            request_name=cm.RequestNames.UPDATE_META,
        )




