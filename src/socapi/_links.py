
from . import endpoints

class Links:

    async def create_link(self,
            poll_id: int,
            link_count: int = 1,
    ):
        await self._login()

        links_payload = {
            "poll_id": poll_id,
            "link_count": link_count
        }

        result = await self._request(
            endpoint=endpoints.LINKS_ENDPOINT,
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