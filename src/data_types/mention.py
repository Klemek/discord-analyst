from datetime import datetime

# Custom libs

from utils import plural, from_now, percent


class Mention:
    def __init__(self):
        self.usages = 0
        self.last_used = None

    def update_use(self, count: int, date: datetime):
        self.usages += count
        if self.last_used is None or date > self.last_used:
            self.last_used = date

    def score(self) -> float:
        # Score is compose of usages + reactions
        # When 2 emotes have the same score,
        # the days since last use is stored in the digits
        # (more recent first)
        return self.usages + 1 / (
            100000 * ((datetime.today() - self.last_used).days + 1)
        )

    def to_string(
        self,
        i: int,
        name: str,
        *,
        total_usage: int,
    ) -> str:
        # place
        output = ""
        if i == 0:
            output += ":first_place:"
        elif i == 1:
            output += ":second_place:"
        elif i == 2:
            output += ":third_place:"
        else:
            output += f"**#{i + 1}**"
        output += f" {name} - {plural(self.usages, 'time')} ({percent(self.usages/total_usage)}) (last {from_now(self.last_used)})"
        return output
