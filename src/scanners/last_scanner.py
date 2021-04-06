from typing import List

# Custom libs

from .history_scanner import HistoryScanner


class LastScanner(HistoryScanner):
    @staticmethod
    def help() -> str:
        return super(LastScanner, LastScanner).help(
            cmd="last", text="Read last message"
        )

    def __init__(self):
        super().__init__(help=LastScanner.help())

    def get_results(self, intro: str) -> List[str]:
        return self.history.to_string(type="last")
