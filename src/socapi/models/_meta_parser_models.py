
from typing import List, Literal, Union, get_args, Iterable, Dict
from pydantic import BaseModel, field_validator, Field, ConfigDict

from .. import endpoints

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