from typing import TYPE_CHECKING

from typing_extensions import Literal
from http import HTTPMethod
if TYPE_CHECKING:
    from __init__ import SocAPIClient

import asyncio
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
        # chunk_size=50
     ):
        chunk_size=50
        return_dict = dict()
        counter = 0

        p = sm.SearchPayload(
            name=name,
            num=poll_id,
            status_id=status,
            is_in_track=is_in_track,
        ).model_dump(exclude_none=True)

        while True:
            r = await self._request(
                method=HTTPMethod.POST,
                endpoint=cm.Endpoints.SEARCH_POLS,
                request_name=cm.RequestNames.SEARCH_POLS,
                headers=self.headers,
                payload=p,
                extract_result=True,
            )

            chunk = {poll["id"]: poll for poll in r}
            return_dict.update(chunk)

            if len(chunk) < chunk_size:
                break

            counter+=1
            p["limit"] = chunk_size + 1
            p["offset"] = chunk_size * counter

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
    #             endpoint=endpoints.SEARCH_POLLS,
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
    #             endpoint=endpoints.SEARCH_POLLS,
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


