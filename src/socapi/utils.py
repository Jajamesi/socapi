import asyncio
from datetime import datetime, timezone, timedelta

from . import constants as const

def validate_file_format(export_format_input):
    if isinstance(export_format_input, str):
        if export_format_input not in const.EXPORT_FORMATS:
            raise ValueError(f"Invalid export format: {export_format_input}")
        return const.EXPORT_FORMATS[export_format_input]
    elif isinstance(export_format_input, int):
        if export_format_input not in set(const.EXPORT_FORMATS.values()):
            raise ValueError(f"Invalid export format: {export_format_input}")
        return export_format_input


def split_into_chunks(iterable, chunk_size):
    for i in range(0, len(iterable), chunk_size):
        yield set(iterable[i:i + chunk_size])


def validate_file_names_ids(poll_ids, filenames, export_format):
    """
    Validate and prepare filenames for export based on poll IDs and export format.

    This function checks if all poll IDs are integers, generates default filenames if none are provided,
    and ensures that the filenames list matches the poll IDs length.

    Parameters:
    poll_ids (List[int]): A list of poll IDs.
    filenames (List[str], optional): A list of filenames corresponding to the poll IDs. Defaults to None.
    export_format (str): The export format for the files.

    Returns:
    Dict[int, str]: A dictionary where keys are poll IDs and values are corresponding filenames.

    Raises:
    ValueError: If any poll ID is not an integer, or if the filenames list length does not match poll IDs length.
    """
    # if not all([isinstance(x, int) for x in poll_ids]):
    #     raise ValueError("All poll_ids must be integers")

    if filenames is None:
        filenames = [f"poll_{poll_id}.{export_format}" for poll_id in poll_ids]

    if len(poll_ids) != len(filenames):
        raise ValueError("Filenames list must be the same length as poll_ids")

    filenames = dict(zip(poll_ids, filenames))

    return filenames


def retry_decor(exception_message: str, attempts=const.RETRIES_NUM, sleep=1):
    async def decorator(func):
        async def wrapper(*args, **kwargs):
            for attempt in range(attempts):
                print(f"Attempting {func.__name__} {attempt}")
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    if attempt == attempts - 1:
                        raise Exception(f"{exception_message}: '{func.__name__}' retries amount exceeded:", e)
                    await asyncio.sleep(sleep)
        return wrapper
    return decorator


def convert_to_iso8601(date_str):
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


class EmptyPollError(Exception):
    """Custom exception for poll not having any completes."""
    pass


class EmptyPollWarning(Warning):
    """Custom warning for poll not having any completes."""
    pass