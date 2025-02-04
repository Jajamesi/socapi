
import asyncio
from . import constants as const


class Searcher:
    async def search_by_name(
            self,
            name: str,
            is_in_track=False,
            chunk_size=50
    ):
        await self._login()

        return_dict = dict()
        counter = 0

        while True:
            search_payload = {
                "is_in_track": is_in_track,
                "name": name,
                "limit": chunk_size + 1,
                "offset": chunk_size * counter
            }

            result = await self._request(
                endpoint=const.SEARCH_LIST_ENDPOINT,
                request_name="Search by name",
                headers=self.headers,
                payload=search_payload,
            )

            try:
                result_json = await result.json()
            except:
                raise ValueError("Failed to json search by name")

            if result_json.get("error") != "":
                raise ValueError(f"Error in search by name: {result_json.get("error")}")

            chunk = {poll["id"]: {par: poll[par] for par in const.SEARCH_RETURNS} for poll in result_json["result"]}
            return_dict.update(chunk)

            if len(chunk) < chunk_size:
                break

            counter+=1

        return return_dict


    # def search_by_name(self, name: str, *args, **kwargs):
    #     return asyncio.run(self._search_by_name(name, *args, **kwargs))


    async def search_by_number(
            self,
            num: int,
            is_in_track=False,
            chunk_size=50
    ):
        await self._login()

        return_dict = dict()
        counter = 0

        while True:
            search_payload = {
                "is_in_track": is_in_track,
                "num": num,
                "limit": chunk_size + 1,
                "offset": chunk_size * counter
            }

            result = await self._request(
                endpoint=const.SEARCH_LIST_ENDPOINT,
                request_name="Search by name",
                headers=self.headers,
                payload=search_payload,
            )

            try:
                result_json = await result.json()
            except:
                raise ValueError("Failed to json search by number")

            if result_json.get("error") != "":
                raise ValueError(f"Error in search by number: {result_json.get("error")}")

            chunk = {poll["id"]: {par: poll[par] for par in const.SEARCH_RETURNS} for poll in result_json["result"]}
            return_dict.update(chunk)

            if len(chunk) < chunk_size:
                break

            counter += 1

        return return_dict


    # def search_by_number(self, name: str, *args, **kwargs):
    #     return asyncio.run(self._search_by_number(name, *args, **kwargs))


