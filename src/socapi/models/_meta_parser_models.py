
from typing import List, Literal, Union, get_args, Iterable, Dict
from pydantic import BaseModel, field_validator, Field, ConfigDict, computed_field
from enum import Enum
from dataclasses import dataclass

from . import _client_model as cm

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

class QuestionExportHow(str, Enum):
    poll="poll"
    block="block"


QuestionEndpoints = {
    QuestionExportHow.poll: cm.Endpoints.QUESTIONS_BY_POLL,
    QuestionExportHow.block: cm.Endpoints.QUESTIONS_BY_BLOCK,
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
    how: str | QuestionExportHow
    includes: Union[Literal["all"], List[QuestionIncludeField]] = Field(default="all", validate_default=True)


    @field_validator("how", mode="before")
    @classmethod
    def validate_how(cls, v: str) -> QuestionExportHow:
        if isinstance(v, QuestionExportHow):
            return v
        try:
            return QuestionExportHow(v)
        except ValueError:
            raise ValueError(f"Invalid how: {v!r}")


    @field_validator("includes", mode="before")
    @classmethod
    def expand_all(cls, v):
        if v == "all":
            return QUESTION_INCLUDES.copy()
        if not isinstance(v, list):
            raise ValueError("includes must be 'all' or a list of fields")
        return v


    @computed_field
    @property
    def poll_id(self) -> Union[int, None]:
        if self.how == QuestionExportHow.poll:
            return self.parent_id
        return None


    @computed_field
    @property
    def block_id(self) -> Union[int, None]:
        if self.how == QuestionExportHow.block:
            return self.parent_id
        return None





class QuestionTypes(Enum):
    singlepunch = (1, "singlepunch")
    droplist = (2, "droplist")
    one_in_row = (3, "one_in_row")
    multipunch = (4, "multipunch")
    oe = (7, "oe")
    ordered = (8, "ordered")
    slider = (9, "slider")
    mult_in_row = (10, "mult_in_row")
    info_screen = (11, "info_screen")

    def __init__(self, type_id: int, name: str):
        self.type_id = type_id
        self.display_name = name

    @classmethod
    def get_ids_by_name(cls, names: Union[str, Iterable[str], None]) -> set[int]:
        if isinstance(names, str): names = [names]
        lookup = set(names)
        return set([member.type_id for member in cls if member.name in lookup]) if names else None


class AnswerTypes(Enum):
    data = 0
    input = 1
    tech = 2



