from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from __init__ import SocAPIClient

from typing import List, Literal, Union, get_args, Iterable, Dict, Optional, Any
import asyncio
import warnings

from . import constants as const
from . import endpoints
from . import utils
from .models import _download_models as dm
from .models import _client_model as cm


class Downloader:

    async def _export_poll_data(
            self: "SocAPIClient",
            poll_id: int,
            export_format: int,
            filter_: dict,


    ):

        export_payload = {
            "poll_id": poll_id,
            "format_id": export_format,
            "filter": filter_
        }

        # print("export ", poll_id)
        # print("export ", export_payload)


        await self._request(
            method=cm.ValidRequestsMethods.post,
            endpoint=cm.Endpoints.EXPORT_START_ENDPOINT,
            payload=export_payload,
            headers=self.headers,
            request_name="Export"
        )


    async def _check_export_progress(self: "SocAPIClient"):
        req_name="Progress"
        result = await self._request(
            method=cm.ValidRequestsMethods.post,
            endpoint=cm.Endpoints.EXPORT_PROGRESS_ENDPOINT,
            request_name=req_name,
            headers=self.headers
        )

        try:
            result_json = await result.json()
            # print("progress ", result_json)
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

        # print("download ", uuid)

        result = await self._request(
            method=cm.ValidRequestsMethods.post,
            endpoint=cm.Endpoints.DOWNLOAD_START_ENDPOINT,
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
            method=cm.ValidRequestsMethods.post,
            endpoint=cm.Endpoints.DOWNLOAD_DONE_ENDPOINT,
            request_name="Done",
            headers=self.headers,
            payload=done_payload,
        )

    @cm.validate_login
    async def download(
            self: "SocAPIClient",
            poll_id: Union[int, List[int]],
            export_dir: Optional[str] = None,
            export_format: Optional[Union[dm.ExportFormat | None]] = None,
            is_poll_complete: bool = True,
            is_poll_in_progress: bool = True,
            time_from: Optional[str] = None,
            time_to: Optional[str] = None,
            filenames: Optional[Iterable[str]] = None,
            domain_ids: Optional[List[int]] = None,
    ):
        """
        Download poll data for one or multiple polls, filtering by completion status and optional date range.

        This method performs the following:
        1. Logs in the client if necessary.
        2. Filters out polls with no completed responses.
        3. Initiates export tasks for polls with data.
        4. Monitors export progress and downloads completed exports.
        5. Issues warnings for polls with no completes.

        Args:
            poll_id (Union[int, List[int]]): One or more poll IDs to export data from.
            export_dir (Optional[str]): Directory to save downloaded files. Defaults to None (implementation dependent).
            export_format (Optional[dm.ExportFormat | None]): Desired export format (e.g., CSV, Excel).
            is_poll_complete (bool): Whether to include completed polls. Defaults to True.
            is_poll_in_progress (bool): Whether to include polls still in progress. Defaults to True.
            time_from (Optional[str]): Start of time range filter (ISO format). Optional.
            time_to (Optional[str]): End of time range filter (ISO format). Optional.
            filenames (Optional[Iterable[str]]): Optional custom filenames corresponding to poll IDs.
            domain_ids (Optional[List[int]]): Optional list of domain IDs to scope the data.

        Raises:
            utils.EmptyPollWarning: Issued as a warning (not an exception) when one or more polls have no completes.
            Exception: If export or download operations fail after retries.

        Returns:
            None: The method completes asynchronously. Files are saved to `export_dir`.

        Notes:
            - Splits polls into chunks to avoid database connection issues.
            - Automatically retries and waits during export polling loop.
        """

        p = dm.DownloadPayload(
            poll_id=poll_id,
            export_dir=export_dir,
            export_format=export_format,
            is_poll_complete=is_poll_complete,
            is_poll_in_progress=is_poll_in_progress,
            time_from=time_from,
            time_to=time_to,
            filenames=filenames,
            domain_ids=domain_ids
        )

        # print("MODEL", p.model_dump())

        filter_payload = p.model_dump(include={
            "is_poll_complete",
            "is_poll_in_progress",
            "time_from",
            "time_to",
            "domain_ids",
        }, exclude_none=True)

        # await self._login()

        empty_polls = []
        download_tasks = []

        # Split polls into separate chunks to avoid db closing :(
        dwnld_chunks = utils.split_into_chunks(p.poll_id, const.MAX_CONCURRENT_REQUESTS)

        for init_chunk in dwnld_chunks:

            # Filter out polls that has not any completes
            has_any_completes = await asyncio.gather(*(self.has_completes(poll_id) for poll_id in init_chunk))
            chunk = {p_id for p_id, has_any in zip(init_chunk, has_any_completes) if has_any}
            empty_polls.extend(p_id for p_id, has_any in zip(init_chunk, has_any_completes) if not has_any)

            await asyncio.gather(*[self._export_poll_data(
                poll_id=p_id,
                export_format=p.export_format_num,
                filter_=filter_payload
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

