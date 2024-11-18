
import asyncio
from pathlib import Path

import constants as const
import utils


class Downloader:
    async def _export_poll_data(
            self,
            poll_id: int,
            export_format = const.EXPORT_FORMATS.get("sav", 2),
            is_completes=True,
            is_in_progress=True,
            export_interval=None
    ):
        print(f"started _export_poll_data {poll_id}")
        export_payload = {
            "poll_id": poll_id,
            "format_id": export_format,
            "filter": {
                "domain_ids": [1],  # idk just keep it
                "is_poll_complete": is_completes,
                "is_poll_in_progress": is_in_progress,
            }
        }

        date_mapper = {
            "from": 0,
            "to": 1,
        }

        for d, i in date_mapper.items():
            if export_interval[i] is not None:
                export_payload["filter"][d] = export_interval[i]

        await self._request(
            endpoint=const.EXPORT_URL,
            payload=export_payload,
            headers=self.headers,
            request_name="Export"
        )


    async def _check_export_progress(self):
        print(f"started _check_export_progress")

        result = await self._request(endpoint=const.PROGRESS_URL, request_name="Progress", headers=self.headers)

        try:
            result_json = await result.json()
        except:
            raise ValueError("Failed to json progress")

        if result_json.get("error") != "":
            raise ValueError(f"Error in progress check: {result_json.get("error")}")

        return result_json["result"]


    async def _download_poll(
            self,
            uuid: str,
            export_path: Path
    ):
        print(f"started _download_poll {uuid}, {export_path}")

        # Download and write data
        download_payload = {"uuid": uuid}

        result = await self._request(
            endpoint=const.DOWNLOAD_URL,
            request_name="Download",
            headers=self.headers,
            payload=download_payload,
        )

        if result.status == const.SUCCESS_STATUS:
            content = await result.read()

            with open(export_path, 'wb') as f:
                f.write(content)

            print("ended downlaod")

            await self._done_export(uuid=uuid)


    async def _done_export(self, uuid: str):
        print(f"started _done_export {uuid}")
        done_payload = {"uuid": uuid}

        await self._request(
            endpoint=const.DONE_URL,
            request_name="Done",
            headers=self.headers,
            payload=done_payload,
        )


    async def download_poll(
            self,
            poll_id,
            export_path = None,
            is_completes=True,
            is_in_progress=True,
            time_from=None,
            time_to=None
    ):

        export_interval = (utils.convert_to_iso8601(time_from), utils.convert_to_iso8601(time_to))

        if export_path is None:
            export_format = const.EXPORT_FORMATS.get("sav", 2)
            export_path = Path(f"poll_{poll_id}.{export_format}")
        else:
            export_path = Path(export_path)

            # Create directory if it doesn't exist'
            path_to_save = export_path.parent
            path_to_save.mkdir(parents=True, exist_ok=True)

            export_format_str = export_path.suffix.strip('.')
            export_format = utils.validate_file_format(export_format_str)


        await self._login()

        await self._export_poll_data(
            poll_id=poll_id,
            export_format=export_format,
            is_completes=is_completes,
            is_in_progress=is_in_progress,
            export_interval=export_interval,
        )

        while True:
            result = await self._check_export_progress()
            for inst in result:
                inst_id = inst.get("params").get("poll_id")
                inst_status = inst.get("status")
                if (inst_id==poll_id) and (inst_status=="done"):
                    inst_uuid = inst.get("uuid")
                    break
            else:
                await asyncio.sleep(1)
                continue
            break

        await self._download_poll(
            uuid=inst_uuid,
            export_path=export_path
        )


    async def download_polls(
            self,
            poll_ids: list[int],
            export_dir=None,
            export_format = const.EXPORT_FORMATS.get("sav", 2),
            filenames=None,
            is_completes=True,
            is_in_progress=True,
            time_from=None,
            time_to=None
    ):
        # Validations
        export_interval = (utils.convert_to_iso8601(time_from), utils.convert_to_iso8601(time_to))

        export_dir = Path() if export_dir is None else Path(export_dir)

        filenames = utils.validate_file_names_ids(poll_ids, filenames, export_format)

        export_format = utils.validate_file_format(export_format)

        # Execution
        await self._login()

        download_tasks = []

        # Split polls into separate chunks to avoid db closing :(
        dwnld_chunks = utils.split_into_chunks(poll_ids, const.MAX_CONCURRENT_REQUESTS)

        for chunk in dwnld_chunks:
            await asyncio.gather(*[self._export_poll_data(
                poll_id=poll_id,
                export_format=export_format,
                is_completes=is_completes,
                is_in_progress=is_in_progress,
                export_interval=export_interval,
            ) for poll_id in chunk])

            started = set()

            while chunk.difference(started):
                result = await self._check_export_progress()
                for inst in result:
                    inst_id = int(inst.get("params").get("poll_id"))
                    inst_status = inst.get("status")
                    if (inst_id in chunk) and (inst_status == "done") and (inst_id not in started):
                        started.add(inst_id)
                        inst_uuid = inst.get("uuid")
                        print("inst_status", inst_uuid)
                        download_task = asyncio.create_task(self._download_poll(
                            uuid=inst_uuid,
                            export_path=export_dir / filenames[inst_id]
                        ))
                        download_tasks.append(download_task)

                await asyncio.sleep(1)

        # Ensure all tasks complete
        await asyncio.gather(*download_tasks)