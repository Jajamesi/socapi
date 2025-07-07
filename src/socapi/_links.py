from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from __init__ import SocAPIClient

from pydantic import BaseModel, validate_call

from . import endpoints
from .models import _client_model as cm

# class LinksPayload(BaseModel):
#     poll_id: int
#     link_count: Optional[int] = 1


class Links:

    @cm.validate_login
    async def create_link(
            self: "SocAPIClient",
            poll_id: int,
            link_count: Optional[int] = 1,
    ):

        links_payload = {
            "poll_id": poll_id,
            "link_count": link_count
        }

        result = await self._request(
            endpoint=cm.Endpoints.LINKS_ENDPOINT,
            request_name="Generating links",
            headers=self.headers,
            payload=links_payload,
        )

        try:
            result_json = await result.json()
        except:
            raise ValueError("Failed to json Generating links")

        if result_json.get("error") != "":
            raise ValueError(f"Error in Generating links: {result_json.get("error")}")
