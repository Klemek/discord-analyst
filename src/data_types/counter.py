from typing import Optional, Callable
from datetime import datetime
from collections import defaultdict

# Custom libs

from utils import plural, from_now, percent, val_sum, top_key, utc_today


class Counter:
    def __init__(self):
        self.usages = defaultdict(int)
        self.last_used = None

    def update_use(self, count: int, date: datetime, item: int = 0):
        self.usages[item] += count
        if count > 0 and (self.last_used is None or date > self.last_used):
            self.last_used = date

    def score(self) -> float:
        # Score is compose of usages + reactions
        # When 2 emojis have the same score,
        # the days since last use is stored in the digits
        # (more recent first)
        if self.last_used is None:
            return 0
        return self.all_usages() + 1 / (
            100000 * ((utc_today() - self.last_used).days + 1)
        )

    def all_usages(self) -> int:
        return val_sum(self.usages)

    def to_string(
        self,
        i: int,
        name: str,
        *,
        total_usage: int,
        counted: str = "time",
        transform: Optional[Callable[[int], str]] = None,
        ranking: bool = True,
        top: bool = True,
    ) -> str:
        # place
        output = ""
        if ranking:
            if i == 0:
                output += ":first_place: "
            elif i == 1:
                output += ":second_place: "
            elif i == 2:
                output += ":third_place: "
            else:
                output += f"**#{i + 1}** "
        else:
            output += f"- "
        sum = val_sum(self.usages)
        if sum > 0:
            output += f"{name} - {plural(sum, counted)} ({percent(sum/total_usage)}, last {from_now(self.last_used)})"
        else:
            output += f"{name} - unused"
        top_item = top_key(self.usages)
        if sum > 0 and top and top_item != 0 and transform is not None:
            if self.usages[top_item] == sum:
                output += f" (all{transform(top_item)})"
            else:
                output += f" ({self.usages[top_item]:,}{transform(top_item)}, {percent(self.usages[top_item]/sum)})"
        return output

    @staticmethod
    def total(d: dict) -> int:
        return sum([val_sum(counter.usages) for counter in d.values()])
