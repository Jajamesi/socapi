from __future__ import annotations

from typing import TYPE_CHECKING, List
if TYPE_CHECKING:
    from __init__ import SocAPIClient

from pydantic import BaseModel, validate_call
import asyncio

from .models import _general_models as gm
from .models import _client_model as cm

from http import HTTPMethod


class SourcePayload(BaseModel):
    name: str
    utm: str


class Collector:

    @cm.validate_login
    async def get_collectors(
            self: "SocAPIClient",
    ) -> List[gm.Source]:
        result = await self._request(
            method=HTTPMethod.POST,
            endpoint=cm.Endpoints.COLLECTORS_LIST,
            headers=self.headers,
            request_name=cm.RequestNames.COLLECTORS_LIST,
            extract_result=True,
        )

        return [gm.Source(**i) for i in result]


    @cm.validate_login
    @validate_call
    async def create_collector(
            self,
            inputs: List[SourcePayload],
    ) -> List[gm.Source]:
        if TYPE_CHECKING:
            self: SocAPIClient

        tasks = [
            self._request(
                method=HTTPMethod.POST,
                endpoint=cm.Endpoints.COLLECTOR_CREATE,
                headers=self.headers,
                payload=i.model_dump(),
                request_name=cm.RequestNames.COLLECTOR_CREATE,
                extract_result=True,
            )
            for i in inputs
        ]

        result = await asyncio.gather(*tasks)

        return [gm.Source(**i) for i in result]