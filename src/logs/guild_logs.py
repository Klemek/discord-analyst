from typing import List, Tuple
import os
import discord
import json
import gzip
from datetime import datetime
import time
import logging
import asyncio
import threading


from . import ChannelLogs
from utils import code_message, delta, deltas


LOG_DIR = "logs"
LOG_EXT = ".logz"

current_analysis = []
current_analysis_lock = threading.Lock()


ALREADY_RUNNING = -100
CANCELLED = -200

# 5 minutes, assume 'fast' arg
MIN_MODIFICATION_TIME = 5 * 60
# ~6 months, remove log file
MAX_MODIFICATION_TIME = 6 * 30.5 * 24 * 60 * 60


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
        self.id = guild.id
        self.guild = guild
        self.log_file = os.path.join(LOG_DIR, f"{guild.id}{LOG_EXT}")
        self.channels = {}
        self.locked = False

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        del self.channels
        del self.guild
        if self.locked:
            self.unlock()

    def dict(self) -> dict:
        return {id: self.channels[id].dict() for id in self.channels}

    def check_cancelled(self) -> bool:
        return self.locked and self.log_file not in current_analysis

    def lock(self) -> bool:
        self.locked = True
        current_analysis_lock.acquire()
        if self.log_file in current_analysis:
            current_analysis_lock.release()
            return False
        current_analysis.append(self.log_file)
        current_analysis_lock.release()
        return True

    def unlock(self):
        self.locked = False
        current_analysis_lock.acquire()
        if self.log_file in current_analysis:
            current_analysis.remove(self.log_file)
        current_analysis_lock.release()

    async def load(
        self,
        progress: discord.Message,
        target_channels: List[discord.TextChannel] = [],
        *,
        fast: bool,
        fresh: bool,
    ) -> Tuple[int, int]:
        self.locked = False
        if not fast and not self.lock():
            return ALREADY_RUNNING, 0
        t00 = datetime.now()
        # read logs
        if not os.path.exists(LOG_DIR):
            os.mkdir(LOG_DIR)
        last_time = None
        if os.path.exists(self.log_file):
            channels = {}
            try:
                last_time = os.path.getmtime(self.log_file)
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
                del gziped_data
                logging.info(
                    f"log {self.guild.id} > gzip decompress in {delta(t0):,}ms"
                )
                if self.check_cancelled():
                    return CANCELLED, 0
                await code_message(progress, "Reading saved history (3/4)...")
                t0 = datetime.now()
                channels = json.loads(json_data)
                del json_data
                logging.info(f"log {self.guild.id} > json parse in {delta(t0):,}ms")
                if self.check_cancelled():
                    return CANCELLED, 0
                await code_message(progress, "Reading saved history (4/4)...")
                t0 = datetime.now()
                self.channels = {
                    int(id): ChannelLogs(channels[id], self) for id in channels
                }
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

        if len(target_channels) == 0:
            target_channels = (
                self.channels.values() if fast else self.guild.text_channels
            )
        elif fast:
            # select already loaded channels only
            target_channels_tmp = [
                channel for channel in target_channels if channel.id in self.channels
            ]
            if len(target_channels_tmp) == 0:
                fast = False
            else:
                target_channels = target_channels_tmp

        # assume fast if file is fresh
        if (
            not fast
            and not fresh
            and last_time is not None
            and (time.time() - last_time) < MIN_MODIFICATION_TIME
        ):
            invalid_target_channels = [
                channel
                for channel in target_channels
                if channel.id not in self.channels
            ]
            if len(invalid_target_channels) == 0:
                fast = True
                if self.locked:
                    self.unlock()

        total_msg = 0
        total_chan = 0
        if fast:
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
            if not self.locked and not self.lock():
                return ALREADY_RUNNING, 0
            # load channels
            t0 = datetime.now()
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
                    self.channels[channel.id] = ChannelLogs(channel, self)
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
            del json_data
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
            del gziped_data
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
        if self.locked:
            current_analysis_lock.acquire()
            current_analysis.remove(self.log_file)
            current_analysis_lock.release()
        return total_msg, total_chan

    @staticmethod
    async def cancel(client: discord.client, message: discord.Message, *args: str):
        logs = GuildLogs(message.guild)
        current_analysis_lock.acquire()
        if logs.log_file in current_analysis:
            current_analysis.remove(logs.log_file)
            current_analysis_lock.release()
        else:
            current_analysis_lock.release()
            await message.channel.send(
                f"No cancellable analysis are currently running on this server",
                reference=message,
            )

    @staticmethod
    def check_logs(guilds: List[discord.Guild]):
        logging.info(f"checking logs...")
        guild_ids = [str(guild.id) for guild in guilds]
        for item in os.listdir(LOG_DIR):
            path = os.path.join(LOG_DIR, item)
            name, ext = os.path.splitext(item)
            if os.path.isfile(path) and ext == LOG_EXT:
                if (
                    name in guild_ids
                    and (time.time() - os.path.getmtime(path)) > MAX_MODIFICATION_TIME
                ):
                    logging.info(f"> removing old log '{path}'")
                    os.unlink(path)
                elif name not in guild_ids:
                    logging.info(f"> removing unused log '{path}'")
                    os.unlink(path)
