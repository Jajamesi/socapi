from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from __init__ import SocAPIClient

from typing import List, Literal, Union, get_args, Iterable, Dict, Optional, Any, Sequence, Set
import asyncio
import warnings
from http import HTTPMethod
from pathlib import Path, PurePath
import inspect

from . import expeptions
from . import utils
from .models import _download_models as dm
from .models import _client_model as cm

from pydantic import validate_call


@validate_call
def split_into_chunks(seq: Sequence, chunk_size: int):
    for i in range(0, len(seq), chunk_size):
        yield set(seq[i:i + chunk_size])


@validate_call
def validate_file_names_ids(
        poll_ids: Sequence[int],
        filenames: Sequence[str],
        export_format: dm.ExportFileFormat
):

    if filenames is None:
        filenames = [f"poll_{poll_id}.{export_format.name}" for poll_id in poll_ids]

    if len(poll_ids) != len(filenames):
        raise ValueError("Filenames list must be the same length as poll_ids")

    filenames = dict(zip(poll_ids, filenames))

    return filenames


def format_poll_id(poll_ids: Union[int, Set[int], List[int]]) -> List[int]:
    return list(poll_ids) if isinstance(poll_ids, Iterable) else [poll_ids]


def format_filenames(
        filenames: Optional[Sequence[str]],
        poll_ids: List[int],
        export_format: dm.ExportFileFormat
    ) -> List[str]:
    if filenames is not None:
        if len(filenames) != len(poll_ids): raise ValueError("Filenames Poll IDs must have same length")
        return list(filenames)
    return generate_filenames(poll_ids, export_format)


def generate_filenames(poll_ids: List[int], extension: dm.ExportFileFormat) -> List[str]:
    return [f"poll_{poll_id}.{extension.name}" for poll_id in poll_ids]


def validate_path(p: Optional[str]) -> Path:
    return Path(p) if p is not None else Path(".").resolve()


def generate_download_paths(poll_ids: List[int], filenames: List[str], export_dir: Path) -> Dict[int, Path]:
    return {
            p_i: Path(PurePath(export_dir, f_n))
            for p_i, f_n in zip(poll_ids, filenames)
        }


async def process_progress_status(
        statuses: list[Dict],
        ready_events: Dict[int, asyncio.Event],
        poll_uuids: Dict[int, str],
        failed_poll_ids: set[int],
):
    for s in statuses:
        uuid = s["uuid"]
        poll_id = s["params"]["poll_id"]

        if not poll_id in poll_uuids:
            poll_uuids[poll_id] = uuid

        match s["status"]:
            case dm.ExportStatuses.done:
                ready_events[poll_id].set()
            case dm.ExportStatuses.error:
                failed_poll_ids.add(poll_id)
                ready_events[poll_id].set()
            case _:
                continue






class Downloader:

    async def _poll_download_worker(
            self,
            name: str,
            id_queue: asyncio.Queue,

            export_format: dm.ExportFileFormat,
            filter_params: dm.ExportFilter,

            ready_events: Dict[int, asyncio.Event],
            poll_uuids: Dict[int, str],
            download_paths: Dict[int, Path],
            failed_poll_ids: Set[int],
    ):
        while True:
            poll_id = await id_queue.get()

            try:
                await self._export_poll_data(
                    poll_id=poll_id,
                    export_format=export_format,
                    filter_=filter_params,
                )
            except Exception as e:
                id_queue.task_done()
                continue

            # Wait for the signal that this ID is ready to download
            event = asyncio.Event()
            ready_events[poll_id] = event

            await event.wait()  # Wait for status_check to signal it's ready

            if poll_id not in failed_poll_ids:
                server_filename = cm.FileInput(name=f"{poll_uuids[poll_id]}.{export_format.name}")
                export_path = download_paths[poll_id]

                await self._download_poll(
                    server_filename=server_filename,
                    export_path=export_path,
                )

            # release task from export
            await self._done_export(uuid=poll_uuids[poll_id])

            ready_events.pop(poll_id, None)
            id_queue.task_done()


    @cm.validate_login
    async def _export_poll_data(
            self: "SocAPIClient",
            poll_id: int,
            export_format: dm.ExportFileFormat,
            filter_: dm.ExportFilter,
    ):

        p = dm.ExportPayload(
            poll_id=poll_id,
            export_format=export_format,
            filter=filter_,
        )

        await self._request(
            method=HTTPMethod.POST,
            endpoint=cm.Endpoints.EXPORT_START,
            payload=p.model_dump(),
            headers=self.headers,
            request_name=cm.RequestNames.EXPORT_START
        )


    @cm.validate_login
    async def _check_export_progress(self: "SocAPIClient") -> List[Dict]:
        r = await self._request(
            method=HTTPMethod.POST,
            endpoint=cm.Endpoints.EXPORT_PROGRESS,
            request_name=cm.RequestNames.PROGRESS,
            headers=self.headers,
            extract_result=True
        )
        return r


    async def _status_checker(self, ready_events, poll_uuids, failed_poll_ids) -> None:
        while True:
            await asyncio.sleep(1)
            statuses: List[Dict] = await self._check_export_progress()
            await process_progress_status(
                statuses=statuses,
                ready_events=ready_events,
                poll_uuids=poll_uuids,
                failed_poll_ids=failed_poll_ids)


    @cm.validate_login
    async def _download_poll(
            self: "SocAPIClient",
            server_filename: cm.FileInput,
            export_path: Path
    ) -> None:
        await self._download_request(
            endpoint=cm.Endpoints.DOWNLOAD_POLL,
            server_filename=server_filename,
            dest_path=export_path,
            request_name=cm.RequestNames.DOWNLOAD_POLL,
        )


    @cm.validate_login
    async def _done_export(self: "SocAPIClient", uuid: str):
        await self._request(
            method=HTTPMethod.POST,
            endpoint=cm.Endpoints.EXPORT_DONE,
            request_name=cm.RequestNames.EXPORT_DONE,
            headers=self.headers,
            payload={"uuid": uuid},
        )

    async def download_poll(
            self: "SocAPIClient",
            # export specs
            poll_ids: Union[int, Set[int], List[int]],
            export_dir: Optional[str] = None,
            export_format: Literal["sav", "xlsx"] = "sav",
            filenames: Optional[Sequence[str]] = None,

            # export filters
            time_from: Optional[str] = None,
            time_to: Optional[str] = None,
            is_poll_complete: Optional[bool] = True,
            is_poll_in_progress: Optional[bool] = True,
            is_disqualified: Optional[bool] = None,
            questions: Optional[List[dm.QuestionFilter]] = None,
            utm_source: Optional[List[int]] = None,
            counters_ids: Optional[List[int]] = None,
            domain_ids: Optional[List[int]] = None,


    ):
        # validations
        export_format = dm.ExportFileFormat[export_format]

        poll_ids = format_poll_id(poll_ids)
        filenames = format_filenames(filenames, poll_ids, export_format)

        export_dir = validate_path(export_dir)

        filter_params = dm.ExportFilter(
            is_poll_complete=is_poll_complete,
            is_poll_in_progress=is_poll_in_progress,
            questions=questions,
            utm_source=utm_source,
            counters_ids=counters_ids,
            from_=time_from, # it is ok
            to=time_to,
            is_disqualified=is_disqualified,
            domain_ids=domain_ids
        )

        # Queue setup
        poll_id_queue = asyncio.Queue()

        ready_events: Dict[int, asyncio.Event] = {}
        poll_uuids: Dict[int, str] = {}
        download_paths: Dict[int, Path] = generate_download_paths(poll_ids, filenames, export_dir)
        failed_poll_ids: set = set()

        for id_ in poll_ids: await poll_id_queue.put(id_)

        workers = [
            asyncio.create_task(self._poll_download_worker(
                    name=f"worker-{i}",
                    id_queue=poll_id_queue,
                    export_format=export_format,
                    filter_params=filter_params,
                    ready_events=ready_events,
                    poll_uuids=poll_uuids,
                    download_paths=download_paths,
                    failed_poll_ids=failed_poll_ids
                )
            )
            for i in range(cm.MAX_CONCURRENT_DOWNLOAD_REQUESTS)
        ]

        # Start status checker
        status_task = asyncio.create_task(self._status_checker(ready_events, poll_uuids, failed_poll_ids))

        # Wait for queue to be processed
        await poll_id_queue.join()

        # Cancel workers and status task
        for w in workers:
            w.cancel()
        status_task.cancel()

        if failed_poll_ids:
            raise expeptions.FailedDownloadPolls(failed_poll_ids)