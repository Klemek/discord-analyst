from typing import List

# Custom libs

from .history_scanner import HistoryScanner
from utils import generate_help


class RandomScanner(HistoryScanner):
    @staticmethod
    def help() -> str:
        return generate_help("rand", "Read a random message (add text to filter like %find)")

    def __init__(self):
        super().__init__(help=RandomScanner.help(), allow_queries=True)

    def allow_message(self, *_) -> bool:
        return True

    def get_results(self, intro: str) -> List[str]:
        return self.history.to_string(type="random")
