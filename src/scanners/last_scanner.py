from typing import List

# Custom libs

from .history_scanner import HistoryScanner
from utils import generate_help


class LastScanner(HistoryScanner):
    @staticmethod
    def help() -> str:
        return generate_help("last", "Read last message")

    def __init__(self):
        super().__init__(help=LastScanner.help())

    def allow_message(self, *_) -> bool:
        return True

    def get_results(self, intro: str) -> List[str]:
        return self.history.to_string(type="last")
