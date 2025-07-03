from typing import List, Literal, Union, get_args, Iterable, Dict, Optional, Any
from pydantic import BaseModel, field_validator, Field, ConfigDict, model_validator

from .. import endpoints

class SearchPayload(BaseModel):
    name: Optional[str]
    num: Optional[int]
    is_in_track: bool = False
    limit: Optional[int] = 51
    offset: Optional[int] = 0

    @model_validator(mode='before')
    @classmethod
    def check_search_params(cls, data: Any) -> Any:
        if data.get("name") is None and data.get("num") is None:
            raise ValueError("name or poll_id are required")
        return data



