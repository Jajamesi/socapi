
import asyncio

from . import constants as const
from . import utils


class Quota:

    async def _get_quota_values(self, poll_id: int):

        list_quota_payload = {
            "poll_id": poll_id,
        }

        result = await self._request(
            endpoint=const.QUOTA_LIST_URL,
            payload=list_quota_payload,
            headers=self.headers,
            request_name="List quota"
        )

        result_json = await result.json()

        if result_json.get("error") != "":
            raise ValueError(f"Error in listing quota: {result_json.get("error")}")

        return result_json["result"]

    async def _get_sources_metadata(self, poll_id: int):

        sources_metadata_payload = {
            "id": poll_id,
        }

        result = await self._request(
            endpoint=const.POLL_GET_URL,
            payload=sources_metadata_payload,
            headers=self.headers,
            request_name="Get sources metadata"
        )

        result_json = await result.json()

        if result_json.get("error") != "":
            raise ValueError(f"Error in geting sources metadata: {result_json.get("error")}")

        return result_json["result"]["sources"]


    async def _get_quota(self, pol_id: int):

        await self._login()

        quotas, sources = await asyncio.gather(self._get_quota_values(pol_id), self._get_sources_metadata(pol_id))
        sources_labels = {source["id"] : source["name"] for source in sources}

        quota_dict = {quota["id"]: {
            "name":quota["name"],
            "hits": quota["hits"],
            "quota": quota["quota"],
            "left": quota["quota"] - quota["hits"],
            "sources":[sources_labels[source_id] for source_id in quota["source_ids"]]
        } for quota in quotas
        }

        return quota_dict


    def quota(self, poll_id: int):
        return asyncio.run(self._get_quota(poll_id))

