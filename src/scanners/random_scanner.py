from typing import List

# Custom libs

from .history_scanner import HistoryScanner


class RandomScanner(HistoryScanner):
    @staticmethod
    def help() -> str:
        return super(RandomScanner, RandomScanner).help(
            cmd="rand", text="Read a random message"
        )

    def __init__(self):
        super().__init__(help=RandomScanner.help())

    def get_results(self, intro: str) -> List[str]:
        return self.history.to_string(type="random")
