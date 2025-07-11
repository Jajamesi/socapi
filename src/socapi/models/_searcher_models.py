from typing import List, Literal, Union, get_args, Iterable, Dict, Optional, Any
from pydantic import BaseModel, field_validator, Field, ConfigDict, model_validator

from .. import endpoints

STATUS_MAPPER = {
    "active": 1,
    "deleted": 2,
    "published": 3,
    "closed": 4,
}

class SearchPayload(BaseModel):
    name: Optional[str]
    num: Optional[int]
    status_id: Optional[int]
    is_in_track: bool = False
    limit: Optional[int] = 51
    offset: Optional[int] = 0

    @model_validator(mode='before')
    @classmethod
    def check_search_params(cls, data: Any) -> Any:
        if all([data.get("name") is None, data.get("num") is None, data.get("status_id") is None]):
            raise ValueError("name or poll_id are required")
        return data


    @field_validator("status_id", mode="before")
    def check_status_id(cls, v):
        return STATUS_MAPPER[v]



