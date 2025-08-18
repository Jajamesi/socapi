from datetime import datetime, timezone, timedelta
import aiohttp
from typing import List, Literal, Union, get_args, Iterable, Dict, Optional, Set
import inspect
from pathlib import Path

from typing import ClassVar

from pydantic import validate_call, BaseModel, ConfigDict, field_validator
from .models import _client_model as cm
from .models import _meta_parser_models as mpm
from .models._download_models import ExportFileFormat


async def _parse_json_result(result: aiohttp.ClientResponse, context: cm.RequestNames) -> dict:
    try:
        result_json = await result.json()
    except Exception as e:
        raise ValueError(f"Failed to parse JSON in {context.value}: {e}")

    if result_json.get("error"):
        raise ValueError(f"Error in {context.value}: {result_json.get('error')}")

    if result_json.get("result"):
        return result_json.get("result")
    else:
        raise ValueError(f"No result in response {context.value}")


@validate_call
def convert_to_iso8601(date_str: str) -> str:
    """
    Convert a date string in various formats to ISO 8601 format.

    :param date_str: Input string in "dd:mm:yyyy hh:mm:ss", "dd:mm:yyyy", or "dd:mm" format
    :return: ISO 8601 formatted string
    """

    if date_str is None:
        return None

    # Set the timezone offset (+3:00)
    tz = timezone(timedelta(hours=3))
    current_year = datetime.now().year

    # Parse the input date string based on its export_format
    if len(date_str) == 16:  # "dd:mm:yyyy hh:mm:ss"
        dt = datetime.strptime(date_str, "%d:%m:%Y %H:%M:%S")
    if len(date_str) == 14:  # "dd:mm:yyyy hh:mm"
        dt = datetime.strptime(date_str, "%d:%m:%Y %H:%M")
    elif len(date_str) == 10:  # "dd:mm:yyyy"
        dt = datetime.strptime(date_str, "%d:%m:%Y")
        dt = dt.replace(hour=0, minute=0, second=0)
    elif len(date_str) == 5:  # "dd:mm"
        dt = datetime.strptime(date_str, "%d:%m")
        dt = dt.replace(year=current_year, hour=0, minute=0, second=0)
    else:
        raise ValueError("Invalid date format. Expected formats: 'dd:mm:yyyy hh:mm:ss', 'dd:mm:yyyy', or 'dd:mm'.")

    # Add the timezone info
    dt = dt.replace(tzinfo=tz)

    # Convert to ISO 8601 format
    return dt.isoformat()


class IdOrderItem(BaseModel):
    id: int
    order: int
    title: str

    model_config = ConfigDict(extra="allow")

class IdOrderItems(BaseModel):
    items: List[IdOrderItem]


@validate_call
async def find_last_item(
    items: List[IdOrderItem],
    question_types: Optional[Iterable[str]] = None
) -> IdOrderItem:
    max_i = IdOrderItem(id=-1, order=-1, title="")

    question_types_ids = mpm.QuestionTypes.get_ids_by_name(question_types) \
        if question_types is not None else None

    for item in items:
        if item.order > max_i.order:
            if question_types is None or item.type_id in question_types_ids:
                max_i = item

    return max_i





# def get_path_caller(input_file_name: FileInput) -> Path:
#     caller_file = Path(inspect.stack()[1].filename).resolve()
#     caller_dir = caller_file.parent
#     return caller_dir / input_file_name.name





def create_sub_dirs(path: Path) -> None:
    if path.suffix:  # it's a file path, so make parent dirs
        path.parent.mkdir(parents=True, exist_ok=True)
    else:  # it's a directory path
        path.mkdir(parents=True, exist_ok=True)


