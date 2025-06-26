
import asyncio

from . import constants as const
from . import endpoints
from . import utils

from typing import List, Literal, Union, get_args, Iterable, Dict
from pydantic import BaseModel, field_validator, Field, ConfigDict


BlockIncludeField = Literal["id", "name", "title", "description", "poll_id", "order"]
BLOCK_INCLUDES = list(get_args(BlockIncludeField))

class BlockPayload(BaseModel):
    poll_id: int
    includes: Union[Literal["all"], List[BlockIncludeField]] = Field(default="all", validate_default=True)

    @field_validator("includes", mode="before")
    @classmethod
    def expand_all(cls, v):
        if v == "all":
            return BLOCK_INCLUDES.copy()
        if not isinstance(v, list):
            raise ValueError("includes must be 'all' or a list of fields")
        return v


QUESTION_EXPORT_HOW = Literal["block", "poll"]
QUESTION_ENDPOINTS: Dict[QUESTION_EXPORT_HOW, str] = {
    "block": endpoints.QUESTIONS_BLOCK,
    "poll": endpoints.QUESTIONS_ALL,
}
QuestionIncludeField = Literal[
    "type_id",
    "answers",
    "id",
    "title",
    "block_id",
    "order",
    "optional",
    "max_answer",
    "min_answer",
    "has_input",
    "children",
    "children.type_id",
    "children.answers"
]
QUESTION_INCLUDES = list(get_args(QuestionIncludeField))

class QuestionsPayload(BaseModel):
    parent_id: int
    how: QUESTION_EXPORT_HOW
    includes: Union[Literal["all"], List[QuestionIncludeField]] = Field(default="all", validate_default=True)

    @field_validator("includes", mode="before")
    @classmethod
    def expand_all(cls, v):
        if v == "all":
            return QUESTION_INCLUDES.copy()
        if not isinstance(v, list):
            raise ValueError("includes must be 'all' or a list of fields")
        return v


class IdOrderItem(BaseModel):
    id: int
    order: int
    title: str

    model_config = ConfigDict(extra="allow")

class IdOrderItems(BaseModel):
    items: List[IdOrderItem]





class MetaParser:

    async def get_blocks(
        self,
        poll_id: int,
        includes: Union[Literal["all"], List[BlockIncludeField]] = "all"
    ):
        p = BlockPayload(poll_id=poll_id, includes=includes)

        result = await self._request(
            endpoint=endpoints.EXPORT_START_ENDPOINT,
            payload=p.model_dump(),
            headers=self.headers,
            request_name="Get blocks"
        )

        result_json = await self._parse_json_result(result, "Get blocks")

        return result_json["result"]


    async def get_questions(
        self,
        parent_id: int,
        how: QUESTION_EXPORT_HOW,
        includes: Union[Literal["all"], List[QuestionIncludeField]] = "all",
    ):
        p = QuestionsPayload(parent_id=parent_id, how=how, includes=includes)
        endpoint = QUESTION_ENDPOINTS.get(p.how)

        result = await self._request(
            endpoint=endpoint,
            payload=p.model_dump(exclude="how"),
            headers=self.headers,
            request_name="Get blocks"
        )

        try:
            result_json = await result.json()
        except Exception as e:
            raise ValueError(f"Failed to parse JSON: {e}")

        if result_json.get("error"):
            raise ValueError(f"Error in get_questions: {result_json.get('error')}")

        return result_json["result"]


    @staticmethod
    async def find_last_item(items: IdOrderItems):
        max_i = IdOrderItem(id=-1, order=-1, title="")
        for i in items.items:
            if i.order > max_i.order:
                max_i = i
        return max_i