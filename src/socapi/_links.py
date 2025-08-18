from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from __init__ import SocAPIClient

from http import HTTPMethod
from .models import _client_model as cm
from . import expeptions

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



        try:
            await self._request(
                method=HTTPMethod.POST,
                endpoint=cm.Endpoints.PERSONAL_LINKS,
                request_name=cm.RequestNames.PERSONAL_LINKS,
                headers=self.headers,
                payload=links_payload,
            )
        except expeptions.PlatformError as ex:
            return
        return
