
import constants as const

def validate_file_format(export_format_input):
    if isinstance(export_format_input, str):
        if export_format_input not in const.EXPORT_FORMATS:
            raise ValueError(f"Invalid export format: {export_format_input}")
        return const.EXPORT_FORMATS[export_format_input]
    elif isinstance(export_format_input, int):
        if export_format_input not in set(const.EXPORT_FORMATS.values()):
            raise ValueError(f"Invalid export format: {export_format_input}")
        return export_format_input


def split_into_chunks(iterbl, chunk_size):
    for i in range(0, len(iterbl), chunk_size):
        yield set(iterbl[i:i + chunk_size])


def validate_file_names_ids(poll_ids, filenames, export_format):
    if not all([isinstance(x, int) for x in poll_ids]):
        raise ValueError("All poll_ids must be integers")

    if filenames is None:
        filenames = [f"poll_{poll_id}.{export_format}" for poll_id in poll_ids]

    if (len(poll_ids) != len(filenames)):
        raise ValueError("Filenames list must be the same length as poll_ids")

    filenames = dict(zip(poll_ids, filenames))

    return filenames