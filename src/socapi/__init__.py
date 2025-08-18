import asyncio
from http import HTTPMethod

from pydantic import validate_call

from . import utils

from ._downloader import Downloader
from ._statistic import Statistic
from ._searcher import Searcher
from ._links import Links
from ._meta_parser import MetaParser

from .models import _client_model as cm
from . import expeptions

import sys
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class SocAPIClient(cm.ClientModel, Downloader, Statistic, Searcher, Links, MetaParser):

    @validate_call
    @cm.validate_login
    async def has_completes(self, poll_id:int) -> bool:

        payload = {
            "is_poll_complete": True,
            "is_poll_in_progress": True,
            "domain_ids": [1],
            "id": poll_id
        }
        r = await self._request(
            method=HTTPMethod.POST,
            endpoint=cm.Endpoints.STATISTIC,
            payload=payload,
            request_name=cm.RequestNames.EMPTY_POLL,
            headers=self.headers,
            extract_result=True
        )

        return r["ended_count"] > 0