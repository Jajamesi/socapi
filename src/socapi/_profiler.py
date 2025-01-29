
import asyncio

from . import constants as const
from . import utils


class Profile:

    async def _get_poll_profile(self, poll_id: int):
        await self._login()

        sources_payload = {
            "id": poll_id,
        }

        result = await self._request(
            endpoint=const.POLL_GET_URL,
            payload=sources_payload,
            headers=self.headers,
            request_name="Get poll metadata"
        )

        result_json = await result.json()

        if result_json.get("error") != "":
            raise ValueError(f"Error in geting profile: {result_json.get("error")}")

        return result_json

    def get_poll_profile(self, poll_id: int):
        return asyncio.run(self._get_poll_profile(poll_id))