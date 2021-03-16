from typing import List, Tuple
import os
import discord
import json
import gzip
from datetime import datetime
import logging
import asyncio


from . import ChannelLogs
from utils import code_message, delta, deltas


LOG_DIR = "logs"

current_analysis = []


ALREADY_RUNNING = -100
CANCELLED = -200


class Worker:
    def __init__(self, channel_log: ChannelLogs, channel: discord.TextChannel):
        self.channel_log = channel_log
        self.channel = channel
        self.start_msg = len(channel_log.messages)
        self.total_msg = self.start_msg
        self.queried_msg = 0
        self.done = False
        self.cancelled = False
        self.loop = asyncio.get_event_loop()

    def start(self):
        asyncio.run_coroutine_threadsafe(self.process(), self.loop)

    async def process(self):
        async for count, done in self.channel_log.load(self.channel):
            if count > 0:
                self.queried_msg = count - self.start_msg
                self.total_msg = count
            self.done = done
            if self.cancelled:
                return


class GuildLogs:
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.log_file = os.path.join(LOG_DIR, f"{guild.id}.logz")
        self.channels = {}

    def dict(self) -> dict:
        return {id: self.channels[id].dict() for id in self.channels}

    def check_cancelled(self) -> bool:
        return self.log_file not in current_analysis

    async def load(
        self,
        progress: discord.Message,
        target_channels: List[discord.TextChannel] = [],
        *,
        fast: bool,
        fresh: bool,
    ) -> Tuple[int, int]:
        global current_analysis
        if self.log_file in current_analysis:
            return ALREADY_RUNNING, 0
        current_analysis += [self.log_file]
        t00 = datetime.now()
        # read logs
        if not os.path.exists(LOG_DIR):
            os.mkdir(LOG_DIR)
        if os.path.exists(self.log_file):
            channels = {}
            try:
                gziped_data = None
                await code_message(progress, "Reading saved history (1/4)...")
                t0 = datetime.now()
                with open(self.log_file, mode="rb") as f:
                    gziped_data = f.read()
                logging.info(f"log {self.guild.id} > read in {delta(t0):,}ms")
                if self.check_cancelled():
                    return CANCELLED, 0
                await code_message(progress, "Reading saved history (2/4)...")
                t0 = datetime.now()
                json_data = gzip.decompress(gziped_data)
                logging.info(
                    f"log {self.guild.id} > gzip decompress in {delta(t0):,}ms"
                )
                if self.check_cancelled():
                    return CANCELLED, 0
                await code_message(progress, "Reading saved history (3/4)...")
                t0 = datetime.now()
                channels = json.loads(json_data)
                logging.info(f"log {self.guild.id} > json parse in {delta(t0):,}ms")
                if self.check_cancelled():
                    return CANCELLED, 0
                await code_message(progress, "Reading saved history (4/4)...")
                t0 = datetime.now()
                self.channels = {int(id): ChannelLogs(channels[id]) for id in channels}
                # remove invalid format
                self.channels = {
                    id: self.channels[id]
                    for id in self.channels
                    if self.channels[id].is_format()
                }
                logging.info(f"log {self.guild.id} > loaded in {delta(t0):,}ms")
            except json.decoder.JSONDecodeError:
                logging.error(f"log {self.guild.id} > invalid JSON")
            except IOError:
                logging.error(f"log {self.guild.id} > cannot read")
        else:
            fast = False

        total_msg = 0
        total_chan = 0
        if fast:
            if len(target_channels) == 0:
                total_msg = sum(
                    [len(channel.messages) for channel in self.channels.values()]
                )
                total_chan = len(self.channels)
            else:
                target_channels_id = [channel.id for channel in target_channels]
                total_msg = sum(
                    [
                        len(channel.messages)
                        for channel in self.channels.values()
                        if channel.id in target_channels_id
                    ]
                )
                total_chan = len(target_channels)
        else:
            # load channels
            t0 = datetime.now()
            if len(target_channels) == 0:
                target_channels = (
                    self.guild.text_channels if not fast else self.channels.keys()
                )
            loading_new = 0
            queried_msg = 0
            total_chan = 0
            max_chan = len(target_channels)
            if self.check_cancelled():
                return CANCELLED, 0
            workers = []
            for channel in target_channels:
                if channel.id not in self.channels or fresh:
                    loading_new += 1
                    self.channels[channel.id] = ChannelLogs(channel)
                workers += [Worker(self.channels[channel.id], channel)]
            warning_msg = "(this might take a while)"
            if len(target_channels) > 5 and loading_new > 5:
                warning_msg = "(most channels are new, this will take a long while)"
            elif loading_new > 0:
                warning_msg = "(some channels are new, this might take a long while)"
            await code_message(
                progress,
                f"Reading new history...\n0 messages in 0/{max_chan:,} channels\n{warning_msg}",
            )
            for worker in workers:
                worker.start()
            done = False
            while not done:
                if self.check_cancelled():
                    for worker in workers:
                        worker.cancelled = True
                    return CANCELLED, 0

                await asyncio.sleep(0.5)

                remaining = [
                    worker.channel.name for worker in workers if not worker.done
                ]
                total_chan = max_chan - len(remaining)
                queried_msg = sum([worker.queried_msg for worker in workers])
                total_msg = sum([worker.total_msg for worker in workers])

                if total_chan == max_chan:
                    done = True

                remaining_msg = ""

                if len(remaining) <= 5:
                    remaining_msg = "\nRemaining: " + ", ".join(remaining)

                await code_message(
                    progress,
                    f"Reading new history...\n{total_msg:,} messages in {total_chan:,}/{max_chan:,} channels ({round(queried_msg/deltas(t0)):,}m/s)\n{warning_msg}{remaining_msg}",
                )
            logging.info(
                f"log {self.guild.id} > queried in {delta(t0):,}ms -> {queried_msg / deltas(t0):,.3f} m/s"
            )
            # write logs
            real_total_msg = sum(
                [len(channel.messages) for channel in self.channels.values()]
            )
            real_total_chan = len(self.channels)
            if self.check_cancelled():
                return CANCELLED, 0
            await code_message(
                progress,
                f"Saving history (1/3)...\n{real_total_msg:,} messages in {real_total_chan:,} channels",
            )
            t0 = datetime.now()
            json_data = bytes(json.dumps(self.dict()), "utf-8")
            logging.info(
                f"log {self.guild.id} > json dump in {delta(t0):,}ms -> {real_total_msg / deltas(t0):,.3f} m/s"
            )
            if self.check_cancelled():
                return CANCELLED, 0
            await code_message(
                progress,
                f"Saving history (2/3)...\n{real_total_msg:,} messages in {real_total_chan:,} channels",
            )
            t0 = datetime.now()
            gziped_data = gzip.compress(json_data)
            logging.info(
                f"log {self.guild.id} > gzip in {delta(t0):,}ms -> {real_total_msg / deltas(t0):,.3f} m/s"
            )
            if self.check_cancelled():
                return CANCELLED, 0
            await code_message(
                progress,
                f"Saving history (3/3)...\n{real_total_msg:,} messages in {real_total_chan:,} channels",
            )
            t0 = datetime.now()
            with open(self.log_file, mode="wb") as f:
                f.write(gziped_data)
            logging.info(
                f"log {self.guild.id} > saved in {delta(t0):,}ms -> {real_total_msg / deltas(t0):,.3f} m/s"
            )
        if self.check_cancelled():
            return CANCELLED, 0
        await code_message(
            progress,
            f"Analysing...\n{total_msg:,} messages in {total_chan:,} channels",
        )
        logging.info(f"log {self.guild.id} > TOTAL TIME: {delta(t00):,}ms")
        current_analysis.remove(self.log_file)
        return total_msg, total_chan

    @staticmethod
    async def cancel(client: discord.client, message: discord.Message, *args: str):
        logs = GuildLogs(message.guild)
        if logs.log_file in current_analysis:
            current_analysis.remove(logs.log_file)
        else:
            await message.channel.send(
                f"No analysis are currently running on this server", reference=message
            )
