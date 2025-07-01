from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from __init__ import SocAPIClient

import asyncio
from typing import List, Literal, Union, get_args, Iterable, Dict

from . import constants as const
from . import endpoints
from . import utils
from .models import _meta_parser_models as mpm



class MetaParser:

    async def get_blocks(
        self: "SocAPIClient",
        poll_id: int,
        includes: Union[Literal["all"], List[mpm.BlockIncludeField]] = "all"
    ):
        p = mpm.BlockPayload(poll_id=poll_id, includes=includes)

        result = await self._request(
            endpoint=endpoints.EXPORT_START_ENDPOINT,
            payload=p.model_dump(),
            headers=self.headers,
            request_name="Get blocks"
        )

        result_json = await self._parse_json_result(result, "Get blocks")

        return result_json


    async def get_questions(
        self: "SocAPIClient",
        parent_id: int,
        how: mpm.QUESTION_EXPORT_HOW,
        includes: Union[Literal["all"], List[mpm.QuestionIncludeField]] = "all",
    ):
        p = mpm.QuestionsPayload(parent_id=parent_id, how=how, includes=includes)
        endpoint = mpm.QUESTION_ENDPOINTS.get(p.how)

        result = await self._request(
            endpoint=endpoint,
            payload=p.model_dump(exclude="how"),
            headers=self.headers,
            request_name="Get questions"
        )

        result_json = await self._parse_json_result(result, "Get questions")

        return result_json


    @staticmethod
    async def find_last_item(items: mpm.IdOrderItems):
        max_i = mpm.IdOrderItem(id=-1, order=-1, title="")
        for i in items.items:
            if i.order > max_i.order:
                max_i = i
        return max_i