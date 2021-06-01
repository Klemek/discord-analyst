from typing import List

# Custom libs

from .history_scanner import HistoryScanner
from utils import generate_help


class FirstScanner(HistoryScanner):
    @staticmethod
    def help() -> str:
        return generate_help(
            "first",
            "Read first message  (add text to filter like %find)",
            args=[
                "image/gif - pull an image instead of a message",
                "spoiler:allow/only - allow spoiler images",
            ],
        )

    def __init__(self):
        super().__init__(help=FirstScanner.help())

    async def get_results(self, intro: str) -> List[str]:
        if self.images_only:
            return await self.history.to_string_image(
                type="first", spoiler=self.spoiler, gif_only=self.gif_only
            )
        else:
            return self.history.to_string(type="first")
