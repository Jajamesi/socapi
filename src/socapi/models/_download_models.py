from typing import List, Literal, Union, get_args, Iterable, Dict, Optional, Any
from pydantic import BaseModel, field_validator, Field, ConfigDict, model_validator, computed_field
from datetime import datetime, timezone

from .. import endpoints
#
# class SearchPayload(BaseModel):
#     name: Optional[str]
#     poll_id: Optional[int]
#     is_in_track: bool = False
#     limit: Optional[int] = 51
#     offset: Optional[int] = 0
#
#     @model_validator(mode='before')
#     @classmethod
#     def check_search_params(cls, data: Any) -> Any:
#         if data.get("name") is None and data.get("poll_id") is None:
#             raise ValueError("name or poll_id are required")
#         return data

ExportFormat = Literal["sav", "xlsx"]
EXPORT_FORMATS = {
    "xlsx": 1,
    "sav":  2,
}

class DownloadPayload(BaseModel):
    poll_id: Union[int, List[int]]
    export_dir: Optional[str]=None
    export_format: Optional[ExportFormat]="sav"
    is_completes: bool=True
    is_in_progress: bool=True
    time_from: Optional[str]=None
    time_to: Optional[str]=None
    filenames: Optional[List[str]]=None

    @field_validator("poll_id", mode="before")
    def convert_to_list(cls, v):
        if isinstance(v, int):
            return [v]
        return v

    @field_validator("export_dir", mode="before")
    def convert_to_dot(cls, v):
        return '.' if v is None else v

    @field_validator("time_from", "time_to", mode="before")
    def parse_time(cls, v):
        dt = datetime.strptime(v, "%Y-%m-%d_%H:%M:%S")
        dt = dt.replace(microsecond=0, tzinfo=timezone.utc)
        formatted = dt.isoformat().replace("+00:00", "Z")
        return formatted

    @model_validator(mode="after")
    def make_filenames(self) -> 'DownloadPayload':
        if self.filenames is not None:
            if len(self.filenames) != len(self.poll_id):
                raise ValueError("length of filenames and poll_ids must be the same")
        return self

    @computed_field
    @property
    def export_format_num(self) -> int:
        return EXPORT_FORMATS.get(self.export_format)


    @computed_field
    @property
    def formatted_filenames(self) -> Dict[int: str]:
        if self.filenames is None:
            return {id_: f"poll_{id_}.{self.export_format}" for id_ in self.poll_id}
        return {id_: f"{name}.{self.export_format}" for id_, name in zip(self.poll_id, self.filenames)}


class FilterPayload(BaseModel):
    domain_ids: List[int] = [1]
    is_completes: bool = True
    is_in_progress: bool = True
    time_from: Optional[str] = None
    time_to: Optional[str] = None

