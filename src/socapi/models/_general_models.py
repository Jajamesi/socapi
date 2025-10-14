from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator, Field, field_serializer
from uuid import UUID
from datetime import datetime
from enum import Enum
from colour import Color
from typing import List, Optional


class PollType(Enum):
    by_all=1
    by_block=2
    by_question=3

class PollStatus(Enum):
    active=1
    deleted=2
    published=3
    closed=4

class LogicJoinCondition(Enum):
    OR = "OR"
    AND = "AND"

class PageType(Enum):
    greeting = 1
    finish=2
    disqualification=3



class AnswerTypes(Enum):
    singlepunch = 1
    droplist = 2
    one_in_row = 3
    multipunch = 4
    oe = 7
    ordered = 8
    slider = 9
    mult_in_row = 10
    info_screen = 11


class Measures(Enum):
    nominal="nominal"
    scale="scale"
    ordered="ordered"

class InputValidations(Enum):
    text="text"
    email="email"
    number="number"
    date_time="mask|99.99.99 99:99"
    date = "mask|99.99.99"
    time="mask|99:99"
    date_time_from_to="mask|99.99.99 99:99 до 99.99.99 99:99"
    date_from_to = "mask|99.99.99 до 99.99.99"
    time_from_to = "mask|99:99 до 99:99"
    phone="mask|8 (999) 999-99-99"
    none=""




class Predicate(BaseModel):
    counter_id: int
    counter_condition_id: int
    predicate_id: int
    poll_id: int
    condition: LogicJoinCondition
    deleted_at: Optional[datetime]


class Condition(BaseModel):
    id: int
    counter_id: int
    question_id: int
    answer_ids: List[int]
    logic_join_condition: LogicJoinCondition = LogicJoinCondition.OR
    created_at: datetime
    deleted_at: Optional[datetime]
    predicate: Predicate

class Counter(BaseModel):
    id: int
    poll_id: int
    name: str
    description: str
    hits: int
    order: int
    quota: int
    is_disabled: bool
    created_at: datetime
    deleted_at: Optional[datetime]
    conditions: Optional[List[Condition]] = Field(default_factory=list)
    source_ids: Optional[List[int]] = Field(default_factory=list)
    sources: Optional[List[Source]] = Field(default_factory=list)

class Answer(BaseModel):
    id: Optional[int]=None
    order: int
    title: str
    has_input: bool
    skip_randomize: bool
    exclude_answer: bool
    optional: bool
    question_id: int
    input_validation: InputValidations
    is_panel: bool


class Question(BaseModel):
    created_at: Optional[datetime] = None
    title: str
    answer_type: str = ""
    condition_type: str = ""
    id: Optional[int] = None
    parent_id: Optional[int] = 0
    updated_at: Optional[datetime] = None
    measure: Measures
    type_id: AnswerTypes
    max_answer: int
    min_answer: int
    order: int
    status_id: int = 1
    block_id: int
    optional: bool
    has_input: bool
    input_validation: Optional[str] = ""
    randomized: bool
    transpose: bool
    display_labels: bool
    children_randomized: bool
    is_panel: bool
    answers: Optional[List[Answer]] = None
    children: Optional[List[Question]] = None



class Block(BaseModel):
    id: int
    order: int
    name: str
    title: str
    description: str
    created_at: datetime
    questions: List[Question]


class DisplayLogic(BaseModel):
    """
    Logic unit how to display things
    """
    id: int
    poll_id: int
    reference_question_id: int
    comparator_id: int
    join_condition_id: int
    disabled: bool
    internal_condition: LogicJoinCondition
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    reference_answer_id: List[int] = Field(default_factory=list)
    reference_answer_value: List[int] = Field(default_factory=list)
    
    
class AnswerDisplayLogic(DisplayLogic):
    """
    Logic unit how to display answers
    """
    answer_id: int



class QuestionDisplayLogic(DisplayLogic):
    """
    Logic unit how to display questions
    """
    block_id: Optional[int]
    question_id: int


class Jump(DisplayLogic):
    """
    Logic unit how jumps work - Either to page or to question. block id seems to be empty all the time
    """
    target_block_id: Optional[int]
    target_question_id: Optional[int]
    target_page_id: Optional[int]


class PageData(BaseModel):
    description: str
    title: str


class Page(BaseModel):
    id: int
    name: str
    data: PageData
    type_id: PageType
    poll_id: int


class Source(BaseModel):
    id: int
    name: str
    utm: str
    created_at: datetime
    updated_at: Optional[datetime]
    name_sort_weight: int = 10 # who knows
    visible: bool
    is_active: bool
    activate: bool


class Poll(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id:int
    uuid: UUID
    name: str
    title: str
    description: str
    created_at: datetime
    user_id: int
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    updated_user_id: int
    status_id: PollStatus
    status_updated_at: Optional[datetime]
    type_id: PollType
    is_multiple: bool
    can_cameback: bool
    field_date: Optional[datetime]
    banner: str = "DEFAULT"
    background: Color = Color("#bdcff6")
    poll_responsible: None=None
    meta: Optional[List[int]] = Field(default_factory=list)
    counters: List[Counter] = Field(default_factory=list)
    notify_flag: bool
    blocks: List[Block] = Field(default_factory=list)
    jumps: List[Jump] = Field(default_factory=list)
    displays: List[QuestionDisplayLogic] = Field(default_factory=list)
    display_answers: List[AnswerDisplayLogic] = Field(default_factory=list)
    pages: List[Page] = Field(default_factory=list)
    sources: List[Source] = Field(default_factory=list)
    source_id: None=None
    state_id: int=0

    @field_validator("background", mode="before")
    @classmethod
    def parse_color(cls, v):
        if isinstance(v, Color):
            return v
        return Color(v)


    @field_serializer("background")
    def serialize_color(self, color: Color, _info):
        return color.hex_l
