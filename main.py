import asyncio
import os

import aiohttp
from aiohttp import web


class YandexTranslate:
    def __init__(self):
        self.oauth_token = os.getenv("YANDEX_OAUTH_TOKEN")
        self.iam_token = None

    async def _refresh_iam_token(self) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://iam.api.cloud.yandex.net/iam/v1/tokens",
                json={
                    "yandexPassportOauthToken": os.getenv("YANDEX_OAUTH_TOKEN"),
                },
            ) as response:
                result = await response.json()
                self.iam_token = result["iamToken"]

    async def translate(self, source: str) -> str:
        if self.iam_token is None:
            await self._refresh_iam_token()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://translate.api.cloud.yandex.net/translate/v2/translate",
                json={
                    "sourceLanguageCode": "en",
                    "targetLanguageCode": "ru",
                    "folder_id": os.getenv("YANDEX_FOLDER_ID"),
                    "texts": [source],
                },
                headers={
                    "Authorization": f"Bearer {self.iam_token}",
                },
            ) as response:
                # TODO: handle errors
                # TODO: refresh token if it's expired
                result = await response.json()
                return result["translations"][0]["text"]


async def main():
    translator = YandexTranslate()

    async def translate_handler(request):
        return web.Response(text=await translator.translate(request.query["text"]))

    app = web.Application()
    app.add_routes([web.get("/translate", translate_handler)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, port=1984)
    await site.start()
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
