from typing import List

# Custom libs

from .history_scanner import HistoryScanner
from utils import generate_help


class FirstScanner(HistoryScanner):
    @staticmethod
    def help() -> str:
        return generate_help("first", "Read first message")

    def __init__(self):
        super().__init__(help=FirstScanner.help())

    def get_results(self, intro: str) -> List[str]:
        return self.history.to_string(type="first")
