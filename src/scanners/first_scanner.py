from typing import List

# Custom libs

from .history_scanner import HistoryScanner


class FirstScanner(HistoryScanner):
    @staticmethod
    def help() -> str:
        return super(FirstScanner, FirstScanner).help(
            cmd="first", text="Read first message"
        )

    def __init__(self):
        super().__init__(help=FirstScanner.help())

    def get_results(self, intro: str) -> List[str]:
        return self.history.to_string(type="first")
