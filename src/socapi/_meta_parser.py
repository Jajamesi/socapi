from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from __init__ import SocAPIClient

import asyncio
from typing import List, Literal, Union, get_args, Iterable, Dict, Optional, Set

from . import constants as const
from . import endpoints
from . import utils
from .models import _meta_parser_models as mpm
from .models import _client_model as cm

from pydantic import validate_call

class MetaParser:

    @cm.validate_login
    async def get_blocks(
        self: "SocAPIClient",
        poll_id: int,
        includes: Union[Literal["all"], List[mpm.BlockIncludeField]] = "all"
    ):
        p = mpm.BlockPayload(poll_id=poll_id, includes=includes)

        # await self._login()

        result = await self._request(
            method=cm.ValidRequestsMethods.post,
            endpoint=cm.Endpoints.BLOCKS,
            payload=p.model_dump(),
            headers=self.headers,
            request_name="Get blocks"
        )

        # print(result)
        result_json = await self._parse_json_result(result, "Get blocks")

        return result_json


    @cm.validate_login
    async def get_questions(
        self: "SocAPIClient",
        parent_id: int,
        how: str | mpm.QuestionExportHow,
        includes: Union[Literal["all"], List[mpm.QuestionIncludeField]] = "all",
    ):
        p = mpm.QuestionsPayload(parent_id=parent_id, how=how, includes=includes)
        endpoint = mpm.QuestionEndpoints.get(p.how).value

        # await self._login()

        # print(p.model_dump(exclude={"how"}, exclude_none=True))
        # print(endpoint)

        result = await self._request(
            method=cm.ValidRequestsMethods.post,
            endpoint=endpoint,
            payload=p.model_dump(exclude={"how"}, exclude_none=True),
            headers=self.headers,
            request_name="Get questions"
        )

        result_json = await self._parse_json_result(result, "Get questions")

        return result_json


    @staticmethod
    @validate_call
    async def find_last_item(
        items: List[mpm.IdOrderItem],
        question_types: Optional[Iterable[str]] = None
    ) -> mpm.IdOrderItem:
        max_i = mpm.IdOrderItem(id=-1, order=-1, title="")

        question_types_ids = mpm.QuestionTypes.get_ids_by_name(question_types) \
            if question_types is not None else None

        for item in items:
            if item.order > max_i.order:
                if question_types is None or item.type_id in question_types_ids:
                    max_i = item

        return max_i