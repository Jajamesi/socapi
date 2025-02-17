
import asyncio

from . import constants as const
from . import utils


class Statistic:

    async def _get_quota_values(self, poll_id: int):
        """
        Fetch quota values for a specific poll.

        Parameters:
        poll_id (int): The ID of the poll for which quota values are to be fetched.

        Returns:
        dict: A dictionary containing quota values for the specified poll.

        Raises:
        ValueError: If an error occurs while fetching quota values.
        """

        list_quota_payload = {
            "poll_id": poll_id,
        }

        result = await self._request(
            endpoint=const.QUOTA_LIST_ENDPOINT,
            payload=list_quota_payload,
            headers=self.headers,
            request_name="List quota"
        )

        result_json = await result.json()

        if result_json.get("error") != "":
            raise ValueError(f"Error in listing quota: {result_json.get("error")}")

        return result_json["result"]

    async def _get_metadata(self, poll_id: int, sources_only=False):
        """
        Fetch metadata for sources associated with a specific poll.

        Parameters:
        poll_id (int): The ID of the poll for which source metadata is to be fetched.

        Returns:
        list: A list of dictionaries, each containing metadata for a source associated with the specified poll.
              Each dictionary has the following keys: "id" (source ID), "name" (source name).

        Raises:
        ValueError: If an error occurs while fetching source metadata.
        """

        sources_metadata_payload = {
            "id": poll_id,
        }

        result = await self._request(
            endpoint=const.POLL_GET_ENDPOINT,
            payload=sources_metadata_payload,
            headers=self.headers,
            request_name="Get metadata"
        )

        result_json = await result.json()

        if result_json.get("error") != "":
            raise ValueError(f"Error in getting metadata: {result_json.get('error')}")

        return result_json["result"]["sources"] if sources_only else result_json["result"]


    async def get_quota(self, poll_id: int):
        """
        Fetch quota information for a specific poll, including quota values and associated sources.

        Parameters:
        poll_id (int): The ID of the poll for which quota information is to be fetched.

        Returns:
        dict: A dictionary containing quota information for the specified poll.
              The dictionary has the following structure:
              {
                  quota_id: {
                      "name": quota_name,
                      "hits": number_of_hits,
                      "quota": total_quota,
                      "left": remaining_quota,
                      "sources": [source_name1, source_name2, ...]
                  },
                  ...
              }

        Raises:
        ValueError: If an error occurs while fetching quota values or source metadata.
        """

        await self._login()

        quotas, sources = await asyncio.gather(
            self._get_quota_values(poll_id),
            self._get_metadata(poll_id, sources_only=True)
        )

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


    # def quota(self, poll_id: int):
    #     return asyncio.run(self._get_quota(poll_id))


    async def get_conversions(self, poll_id: int):

        await self._login()

        conversion_payload = {
            "id":poll_id,
            "domain_ids":[1],
            "is_poll_complete":True,
            "is_poll_in_progress":True,
            "is_disqualified":True
        }

        result = await self._request(
            endpoint=const.CONVERSION_ENDPOINT,
            payload=conversion_payload,
            headers=self.headers,
            request_name="Get conversions"
        )

        result_json = await result.json()

        if result_json.get("error") != "":
            raise ValueError(f"Error in getting conversions: {result_json.get('error')}")

        return result_json["result"]


    async def get_poll_target_metadata(self, poll_id: int):

        await self._login()

        quotas, meta, conversions = await asyncio.gather(
            self._get_quota_values(poll_id),
            self._get_metadata(poll_id, sources_only=False),
            self.get_conversions(poll_id)
        )

        sources_labels = {source["id"]: source["name"] for source in meta["sources"]}

        poll_target_metadata = {
            "name": meta["name"],
            "status_id": meta["status_id"],
            "quotas": [
                {
                    "quota_id": quota["id"],
                    "quota_name": quota['name'],
                    "sources_names": ', '.join([sources_labels[source_id] for source_id in quota['source_ids']]),
                    "hits": quota["hits"],
                    "quota": quota["quota"],
                    "left": quota["quota"] - quota["hits"],
                } for quota in quotas
                    ]
            ,
            "conversions": conversions
        }

        return poll_target_metadata

