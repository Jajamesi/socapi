from typing import List, Literal, Union, get_args, Iterable, Dict, Optional, Any, Set
from pydantic import BaseModel, field_validator, Field, ConfigDict, model_validator, computed_field
from datetime import datetime, timezone
from enum import Enum
import pytz

from . import _client_model as cm


def parse_datetime(value: str) -> datetime:
    for fmt in ("%Y-%m-%d_%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"time data {value!r} does not match expected formats")


def format_datetime_to_z(dt: datetime) -> str:
    # Format with milliseconds and 'Z'
    return dt.astimezone(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


class ExportFileFormat(Enum):
    xlsx = 1
    sav = 2


class QuestionFilter(BaseModel):
    question_id: int
    answer_ids: List[int]


class ExportFilter(BaseModel):
    is_poll_complete: Optional[bool] = True
    is_poll_in_progress: Optional[bool] = True
    questions: Optional[List[QuestionFilter]] = None
    utm_source: Optional[List[int]] = None
    counters_ids: Optional[List[int]] = None
    from_: Optional[datetime] = Field(default=None, alias="from")
    to: Optional[datetime] = None
    is_disqualified: Optional[bool] = None
    domain_ids: Optional[List[int]] = None

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("from_", "to", mode="before")
    @classmethod
    def parse_custom_dates(cls, v):
        if isinstance(v, str):
            return parse_datetime(v)
        return v


    @field_validator("domain_ids", mode="before")
    @classmethod
    def validate_domain_ids(cls, v):
        if v is None:
            return cm.DEFAULT_DOMAIN_IDS
        return v


    def model_dump(self, *args, **kwargs):
        # Force timezone-aware ISO format
        original = super().model_dump(*args, **kwargs, by_alias=True, exclude_none=True)
        for key in ['from', 'to']:
            val = original.get(key)
            if isinstance(val, datetime):
                original[key] = format_datetime_to_z(val)
        return original


class ExportPayload(BaseModel):
    poll_id: int
    export_format: ExportFileFormat
    filter_: Optional[ExportFilter] = Field(default=ExportFilter(), alias="filter")

    model_config = ConfigDict(use_enum_values=True, populate_by_name=True)

    @field_validator("export_format", mode="before")
    @classmethod
    def file_format_from_str(cls, v):
        if isinstance(v, str):
            v = v.strip().lower()

        return ExportFileFormat[v] if v in ExportFileFormat._member_names_ else v


    def model_dump(self, *args, **kwargs):
        # Force filter to dump
        return {
            "poll_id": self.poll_id,
            "format_id": self.export_format,
            "filter": self.filter_.model_dump()
        }




class DownloadPayload(BaseModel):
    poll_id: Union[int, Set[int], List[int]]
    export_dir: Optional[str]=None
    export_format: Optional[ExportFileFormat]="sav"
    is_poll_complete: bool=True
    is_poll_in_progress: bool=True
    time_from: Optional[str]=None
    time_to: Optional[str]=None
    filenames: Optional[List[str]]=None
    domain_ids: Optional[List[int]] = [1]

    @field_validator("export_format", mode="before")
    def validate_export_format(cls, v):
        return 'sav' if v is None else v

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
        if v is None:
            return None
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

    # @computed_field
    # @property
    # def export_format_num(self) -> int:
    #     return EXPORT_FORMATS.get(self.export_format, 1)


    @computed_field
    @property
    def formatted_filenames(self) -> Dict[int, str]:
        if self.filenames is None:
            return {id_: f"poll_{id_}.{self.export_format}" for id_ in self.poll_id}
        return {id_: f"{name}.{self.export_format}" for id_, name in zip(self.poll_id, self.filenames)}


    @field_validator("domain_ids", mode="before")
    def validate_domain_ids(cls, v):
        if v is None:
            return [1]
        return v


class FilterPayload(BaseModel):
    domain_ids: List[int] = [1]
    is_completes: bool = True
    is_in_progress: bool = True
    time_from: Optional[str] = None
    time_to: Optional[str] = None


class ExportStatuses(str, Enum):
    in_progress="in_progress"
    done="done"
    error="error"
