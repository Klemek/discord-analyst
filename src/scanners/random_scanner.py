from typing import List

# Custom libs

from .history_scanner import HistoryScanner
from utils import generate_help


class RandomScanner(HistoryScanner):
    @staticmethod
    def help() -> str:
        return generate_help(
            "rand",
            "Read a random message (add text to filter like %find)",
            args=["image - pull an image instead of a message"],
        )

    def __init__(self):
        super().__init__(help=RandomScanner.help())

    async def get_results(self, intro: str) -> List[str]:
        if self.images_only:
            return await self.history.to_string_image(type="random")
        else:
            return self.history.to_string(type="random")
