from typing import TYPE_CHECKING

from typing_extensions import Literal

if TYPE_CHECKING:
    from __init__ import SocAPIClient

import asyncio
from . import constants as const
from . import endpoints
from .models import _searcher_models as sm
from .models import _client_model as cm


class Searcher:

    @cm.validate_login
    async def search(
            self: "SocAPIClient",
            name: str = None,
            poll_id: int = None,
            status: Literal["active", "deleted", "published", "closed"] = None,
            is_in_track=False,
            chunk_size=50
                     ):

        # await self._login()

        req_name = "Search"
        return_dict = dict()
        counter = 0

        while True:
            p = sm.SearchPayload(
                name=name,
                num=poll_id,
                status_id=status,
                is_in_track=is_in_track,
                limit=chunk_size + 1,
                offset=chunk_size * counter
            )

            # print(p.model_dump())

            result = await self._request(
                method=cm.ValidRequestsMethods.post,
                endpoint=cm.Endpoints.SEARCH_LIST_ENDPOINT,
                request_name=req_name,
                headers=self.headers,
                payload=p.model_dump(exclude_none=True),
            )

            result_json = await self._parse_json_result(result, context=req_name)

            chunk = {poll["id"]: {par: poll[par] for par in const.SEARCH_RETURNS} for poll in result_json}
            # print(chunk.keys())
            return_dict.update(chunk)

            if len(chunk) < chunk_size:
                break

            counter+=1

        return return_dict




    # async def search_by_name(
    #         self: "SocAPIClient",
    #         name: str,
    #         is_in_track=False,
    #         chunk_size=50
    # ):
    #     await self._login()
    #
    #     return_dict = dict()
    #     counter = 0
    #
    #     while True:
    #         search_payload = {
    #             "is_in_track": is_in_track,
    #             "name": name,
    #             "limit": chunk_size + 1,
    #             "offset": chunk_size * counter
    #         }
    #
    #         result = await self._request(
    #             endpoint=endpoints.SEARCH_LIST_ENDPOINT,
    #             request_name="Search by name",
    #             headers=self.headers,
    #             payload=search_payload,
    #         )
    #
    #         try:
    #             result_json = await result.json()
    #         except:
    #             raise ValueError("Failed to json search by name")
    #
    #         if result_json.get("error") != "":
    #             raise ValueError(f"Error in search by name: {result_json.get("error")}")
    #
    #         chunk = {poll["id"]: {par: poll[par] for par in const.SEARCH_RETURNS} for poll in result_json["result"]}
    #         return_dict.update(chunk)
    #
    #         if len(chunk) < chunk_size:
    #             break
    #
    #         counter+=1
    #
    #     return return_dict
    #
    #
    # # def search_by_name(self, name: str, *args, **kwargs):
    # #     return asyncio.run(self._search_by_name(name, *args, **kwargs))
    #
    #
    # async def search_by_number(
    #         self: "SocAPIClient",
    #         num: int,
    #         is_in_track=False,
    #         chunk_size=50
    # ):
    #     await self._login()
    #
    #     return_dict = dict()
    #     counter = 0
    #
    #     while True:
    #         search_payload = {
    #             "is_in_track": is_in_track,
    #             "num": num,
    #             "limit": chunk_size + 1,
    #             "offset": chunk_size * counter
    #         }
    #
    #         result = await self._request(
    #             endpoint=endpoints.SEARCH_LIST_ENDPOINT,
    #             request_name="Search by name",
    #             headers=self.headers,
    #             payload=search_payload,
    #         )
    #
    #         try:
    #             result_json = await result.json()
    #         except:
    #             raise ValueError("Failed to json search by number")
    #
    #         if result_json.get("error") != "":
    #             raise ValueError(f"Error in search by number: {result_json.get("error")}")
    #
    #         chunk = {poll["id"]: {par: poll[par] for par in const.SEARCH_RETURNS} for poll in result_json["result"]}
    #         return_dict.update(chunk)
    #
    #         if len(chunk) < chunk_size:
    #             break
    #
    #         counter += 1
    #
    #     return return_dict


    # def search_by_number(self, name: str, *args, **kwargs):
    #     return asyncio.run(self._search_by_number(name, *args, **kwargs))


