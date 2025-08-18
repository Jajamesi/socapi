from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from __init__ import SocAPIClient

import asyncio
from http import HTTPMethod

from . import utils


from .models import _client_model as cm
from .models import _download_models as dm
from .models import _stat_models as sm

class Statistic:
    async def _get_quota_values(self: "SocAPIClient", poll_id: int):
        r = await self._request(
            method=HTTPMethod.POST,
            endpoint=cm.Endpoints.QUOTAS,
            payload={"poll_id": poll_id},
            headers=self.headers,
            request_name=cm.RequestNames.QUOTAS,
            extract_result=True
        )

        return r


    @cm.validate_login
    async def get_quota(self: "SocAPIClient", poll_id: int):

        quotas, sources = await asyncio.gather(
            self._get_quota_values(poll_id),
            self.get_sources(poll_id)
        )

        sources_labels = {source["id"] : source["name"] for source in sources}

        quota_dict = {
            quota["id"]: {
                "name":quota["name"],
                "hits": quota["hits"],
                "quota": quota["quota"],
                "left": quota["quota"] - quota["hits"],
                "sources": quota["source_ids"],
                "sources_labels": [sources_labels[s] for s in quota["source_ids"]],
            } for quota in quotas
            }

        return quota_dict


    @cm.validate_login
    async def get_conversions(self: "SocAPIClient", poll_id: int):

        conversion_payload = {
            "id":poll_id,
            "domain_ids":cm.DEFAULT_DOMAIN_IDS,
            "is_poll_complete":True,
            "is_poll_in_progress":True,
            "is_disqualified":True
        }

        r = await self._request(
            method=HTTPMethod.POST,
            endpoint=cm.Endpoints.CONVERSION,
            payload=conversion_payload,
            headers=self.headers,
            request_name=cm.RequestNames.CONVERSION,
            extract_result=True
        )

        return r


    @cm.validate_login
    async def get_statistics(
            self: "SocAPIClient",
            poll_id: int,

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

        filter_params = sm.StatFilter(
            is_poll_complete=is_poll_complete,
            is_poll_in_progress=is_poll_in_progress,
            questions=questions,
            utm_source=utm_source,
            counters_ids=counters_ids,
            from_=time_from,  # it is ok
            to=time_to,
            is_disqualified=is_disqualified,
            domain_ids=domain_ids
        )

        statistic_payload = {
            "id": poll_id,
            **filter_params.model_dump()
        }

        r = await self._request(
            method=HTTPMethod.POST,
            endpoint=cm.Endpoints.STATISTIC,
            payload=statistic_payload,
            headers=self.headers,
            request_name=cm.RequestNames.STATISTIC,
            extract_result=True
        )
        return r


    # @cm.validate_login
    # async def get_poll_target_metadata(self: "SocAPIClient", poll_id: int):
    #
    #     quotas, meta, conversions = await asyncio.gather(
    #         self._get_quota_values(poll_id),
    #         self.get_metadata(poll_id, sources_only=False),
    #         self.get_conversions(poll_id)
    #     )
    #
    #     sources_labels = {source["id"]: source["name"] for source in meta["sources"]}
    #
    #     poll_target_metadata = {
    #         "name": meta["name"],
    #         "status_id": meta["status_id"],
    #         "quotas": [
    #             {
    #                 "quota_id": quota["id"],
    #                 "quota_name": quota['name'],
    #                 "sources_names": ', '.join([sources_labels[source_id] for source_id in quota['source_ids']]),
    #                 "hits": quota["hits"],
    #                 "quota": quota["quota"],
    #                 "left": quota["quota"] - quota["hits"],
    #             } for quota in quotas
    #                 ]
    #         ,
    #         "conversions": conversions
    #     }
    #
    #     return poll_target_metadata
    #
