from typing import List

# Custom libs

from .history_scanner import HistoryScanner
from utils import generate_help


class LastScanner(HistoryScanner):
    @staticmethod
    def help() -> str:
        return generate_help(
            "last",
            "Read last message (add text to filter like %find)",
            args=[
                "image/gif - pull an image instead of a message",
                "spoiler:allow/only - allow spoiler images",
            ],
        )

    def __init__(self):
        super().__init__(help=LastScanner.help())

    async def get_results(self, intro: str) -> List[str]:
        if self.images_only:
            return await self.history.to_string_image(
                type="last", spoiler=self.spoiler, gif_only=self.gif_only
            )
        else:
            return self.history.to_string(type="last")
