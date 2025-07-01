from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from __init__ import SocAPIClient

from typing import List, Literal, Union, get_args, Iterable, Dict, Optional, Any
import asyncio
import warnings
from pathlib import Path

from . import constants as const
from . import endpoints
from . import utils
from .models import _download_models as dm


class Downloader:
    """
    A class to handle downloading poll data from a socpanel API.

    Expects the main class to define:
    - self._headers: headers for requests.
    - self._login(): method to login in panel.
    - self._request(): method to send generic requests.

    Attributes:
    -----------
    headers : dict
        Headers for the API requests.

    Methods:
    --------
    _export_poll_data(poll_id, export_format, is_completes, is_in_progress, export_interval)
        Exports poll data based on the provided parameters.

    _check_export_progress()
        Checks the progress of the export process.

    _download_poll(uuid, export_path)
        Downloads the exported poll data and saves it to the specified path.

    _done_export(uuid)
        Marks the export process as done.

    download_poll(poll_id, export_path, is_completes, is_in_progress, time_from, time_to)
        Downloads a single poll's data based on the provided parameters.

    download_polls(poll_ids, export_dir, export_format, filenames, is_completes, is_in_progress, time_from, time_to)
        Downloads multiple poll's data based on the provided parameters.
    """

    async def _export_poll_data(
            self: "SocAPIClient",
            poll_id: int,
            export_format: int,
            filter: dict,


    ):

        export_payload = {
            "poll_id": poll_id,
            "format_id": export_format,
            "filter": filter
        }

        await self._request(
            endpoint=endpoints.EXPORT_START_ENDPOINT,
            payload=export_payload,
            headers=self.headers,
            request_name="Export"
        )


    async def _check_export_progress(self: "SocAPIClient"):

        result = await self._request(endpoint=endpoints.EXPORT_PROGRESS_ENDPOINT, request_name="Progress", headers=self.headers)

        try:
            result_json = await result.json()
        except:
            raise ValueError("Failed to json progress")

        if result_json.get("error") != "":
            raise ValueError(f"Error in progress check: {result_json.get("error")}")

        return result_json["result"]


    async def _download_poll(
            self: "SocAPIClient",
            uuid: str,
            export_path: str
    ):

        # Download and write data
        download_payload = {"uuid": uuid}

        result = await self._request(
            endpoint=endpoints.DOWNLOAD_START_ENDPOINT,
            request_name="Download",
            headers=self.headers,
            payload=download_payload,
        )

        if result.status == const.SUCCESS_STATUS:
            content = await result.read()

            with open(export_path, 'wb') as f:
                f.write(content)

            await self._done_export(uuid=uuid)


    async def _done_export(self: "SocAPIClient", uuid: str):
        done_payload = {"uuid": uuid}

        await self._request(
            endpoint=endpoints.DOWNLOAD_DONE_ENDPOINT,
            request_name="Done",
            headers=self.headers,
            payload=done_payload,
        )


    # async def download_one_poll(
    #         self: "SocAPIClient",
    #         poll_id,
    #         export_path = None,
    #         is_completes=True,
    #         is_in_progress=True,
    #         time_from=None,
    #         time_to=None
    # ):
    #
    #     export_interval = (utils.convert_to_iso8601(time_from), utils.convert_to_iso8601(time_to))
    #
    #     if export_path is None:
    #         default_format = "sav"
    #         export_format = const.EXPORT_FORMATS.get(default_format, 2)
    #         export_path = Path(f"poll_{poll_id}.{default_format}")
    #     else:
    #         export_path = Path(export_path)
    #
    #         # Create directory if it doesn't exist'
    #         path_to_save = export_path.parent
    #         path_to_save.mkdir(parents=True, exist_ok=True)
    #
    #         export_format_str = export_path.suffix.strip('.')
    #         export_format = utils.validate_file_format(export_format_str)
    #
    #
    #     await self._login()
    #
    #     await self._export_poll_data(
    #         poll_id=poll_id,
    #         export_format=export_format,
    #         is_completes=is_completes,
    #         is_in_progress=is_in_progress,
    #         export_interval=export_interval,
    #     )
    #
    #     while True:
    #         result = await self._check_export_progress()
    #         for inst in result:
    #             if inst.get("params").get("poll_id") == poll_id:
    #                 inst_status = inst.get("status")
    #                 inst_uuid = inst.get("uuid")
    #                 break
    #         else:
    #             raise ValueError(f"Error in export check - could not find poll id: {poll_id}")
    #
    #         if inst_status == "in_progress":
    #             await asyncio.sleep(1)
    #             continue
    #         break
    #
    #     if inst_status=="done":
    #         await self._download_poll(
    #             uuid=inst_uuid,
    #             export_path=export_path
    #         )
    #     elif inst_status=="error":
    #         await self._done_export(uuid=inst_uuid)
    #         raise ValueError(f"Error in export check: {poll_id}")
    #
    #
    # # def download_poll(self, poll_id: int, *args, **kwargs):
    # #     asyncio.run(self._download_one_poll(poll_id, *args, **kwargs))
    #
    #
    # async def download_polls(
    #         self: "SocAPIClient",
    #         poll_ids: list[int],
    #         export_dir=None,
    #         export_format = "sav",
    #         filenames=None,
    #         is_completes=True,
    #         is_in_progress=True,
    #         time_from=None,
    #         time_to=None
    # ):
    #     empty_polls = []
    #
    #     # Validations
    #     export_interval = (utils.convert_to_iso8601(time_from), utils.convert_to_iso8601(time_to))
    #
    #     export_dir = Path() if export_dir is None else Path(export_dir)
    #
    #     filenames = utils.validate_file_names_ids(poll_ids, filenames, export_format)
    #
    #     export_format = utils.validate_file_format(export_format)
    #
    #     # Execution
    #     await self._login()
    #
    #     download_tasks = []
    #
    #     # Split polls into separate chunks to avoid db closing :(
    #     dwnld_chunks = utils.split_into_chunks(poll_ids, const.MAX_CONCURRENT_REQUESTS)
    #
    #     for init_chunk in dwnld_chunks:
    #
    #         # Filter out polls that has not any completes
    #         has_any_completes = await asyncio.gather(*(self.has_completes(poll_id) for poll_id in init_chunk))
    #         chunk = {poll_id for poll_id, has_any in zip(init_chunk, has_any_completes) if has_any}
    #         empty_polls.extend(poll_id for poll_id, has_any in zip(init_chunk, has_any_completes) if not has_any)
    #
    #         await asyncio.gather(*[self._export_poll_data(
    #             poll_id=poll_id,
    #             export_format=export_format,
    #             is_completes=is_completes,
    #             is_in_progress=is_in_progress,
    #             export_interval=export_interval,
    #             check_empty=False
    #         ) for poll_id in chunk])
    #
    #         started = set()
    #
    #         while chunk.difference(started):
    #             result = await self._check_export_progress()
    #             for inst in result:
    #                 inst_id = int(inst.get("params").get("poll_id"))
    #                 inst_status = inst.get("status")
    #                 if (inst_id in chunk) and (inst_status == "done") and (inst_id not in started):
    #                     started.add(inst_id)
    #                     inst_uuid = inst.get("uuid")
    #                     download_task = asyncio.create_task(self._download_poll(
    #                         uuid=inst_uuid,
    #                         export_path=export_dir / filenames[inst_id]
    #                     ))
    #                     download_tasks.append(download_task)
    #
    #             await asyncio.sleep(1)
    #
    #     # Ensure all tasks complete
    #     await asyncio.gather(*download_tasks)
    #
    #     if empty_polls:
    #         warnings.warn(f"No completes in poll(s) {', '.join(map(str, empty_polls))}", utils.EmptyPollWarning)



    async def download(
            self: "SocAPIClient",
            poll_id: Union[int, List[int]],
            export_dir: Optional[str] = None,
            export_format: Optional[Union[dm.ExportFormat | None]] = None,
            is_completes: bool = True,
            is_in_progress: bool = True,
            time_from: Optional[str] = None,
            time_to: Optional[str] = None,
            filenames: Optional[Iterable[str]] = None,
    ):
        p = dm.DownloadPayload(
            poll_id=poll_id,
            export_dir=export_dir,
            export_format=export_format,
            is_completes=is_completes,
            is_in_progress=is_in_progress,
            time_from=time_from,
            time_to=time_to,
            filenames=filenames
        )

        filter_payload = p.model_dump(include={
            "is_completes",
            "is_in_progress",
            "time_from",
            "time_to"
        }, exclude_none=True)

        await self._login()

        empty_polls = []
        download_tasks = []

        # Split polls into separate chunks to avoid db closing :(
        dwnld_chunks = utils.split_into_chunks(poll_id, const.MAX_CONCURRENT_REQUESTS)

        for init_chunk in dwnld_chunks:

            # Filter out polls that has not any completes
            has_any_completes = await asyncio.gather(*(self.has_completes(poll_id) for poll_id in init_chunk))
            chunk = {p_id for p_id, has_any in zip(init_chunk, has_any_completes) if has_any}
            empty_polls.extend(p_id for p_id, has_any in zip(init_chunk, has_any_completes) if not has_any)

            await asyncio.gather(*[self._export_poll_data(
                poll_id=p_id,
                export_format=p.export_format_num,
                filter=filter_payload
            ) for p_id in chunk])

            started = set()

            while chunk.difference(started):
                result = await self._check_export_progress()
                for inst in result:
                    inst_id = int(inst.get("params").get("poll_id"))
                    inst_status = inst.get("status")
                    if (inst_id in chunk) and (inst_status == "done") and (inst_id not in started):
                        started.add(inst_id)
                        inst_uuid = inst.get("uuid")
                        download_task = asyncio.create_task(self._download_poll(
                            uuid=inst_uuid,
                            export_path=f"{p.export_dir}/{p.formatted_filenames[inst_id]}"
                        ))
                        download_tasks.append(download_task)

                await asyncio.sleep(1)

        # Ensure all tasks complete
        await asyncio.gather(*download_tasks)

        if empty_polls:
            warnings.warn(f"No completes in poll(s) {', '.join(map(str, empty_polls))}", utils.EmptyPollWarning)

