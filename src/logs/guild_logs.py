from typing import List, Tuple
import os
import discord
import json
import gzip
from datetime import datetime
import logging


from . import ChannelLogs
from utils import code_message


LOG_DIR = "logs"

current_analysis = []


class GuildLogs:
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.log_file = os.path.join(LOG_DIR, f"{guild.id}.logz")
        self.channels = {}

    def dict(self) -> dict:
        return {id: self.channels[id].dict() for id in self.channels}

    async def load(
        self, progress: discord.Message, target_channels: List[discord.TextChannel] = []
    ) -> Tuple[int, int]:
        global current_analysis
        if self.log_file in current_analysis:
            return -1, -1
        current_analysis += [self.log_file]
        # read logs
        t0 = datetime.now()
        if not os.path.exists(LOG_DIR):
            os.mkdir(LOG_DIR)
        if os.path.exists(self.log_file):
            channels = {}
            try:
                gziped_data = None
                await code_message(progress, "Reading saved history (1/4)...")
                with open(self.log_file, mode="rb") as f:
                    gziped_data = f.read()
                await code_message(progress, "Reading saved history (2/4)...")
                json_data = gzip.decompress(gziped_data)
                await code_message(progress, "Reading saved history (3/4)...")
                channels = json.loads(json_data)
                await code_message(progress, "Reading saved history (4/4)...")
                self.channels = {int(id): ChannelLogs(channels[id]) for id in channels}
                # remove invalid format
                self.channels = {
                    id: self.channels[id]
                    for id in self.channels
                    if self.channels[id].is_format()
                }
                dt = (datetime.now() - t0).total_seconds()
                logging.info(f"log {self.guild.id} > loaded in {dt} s")
            except json.decoder.JSONDecodeError:
                logging.error(f"log {self.guild.id} > invalid JSON")
            except IOError:
                logging.error(f"log {self.guild.id} > cannot read")
        # load channels
        t0 = datetime.now()
        if len(target_channels) == 0:
            target_channels = self.guild.text_channels
        loading_new = 0
        total_msg = 0
        queried_msg = 0
        total_chan = 0
        max_chan = len(target_channels)
        await code_message(
            progress,
            f"Reading history...\n0 messages in 0/{max_chan} channels\n(this might take a while)",
        )
        for channel in target_channels:
            if channel.id not in self.channels:
                loading_new += 1
                self.channels[channel.id] = ChannelLogs(channel)
            start_msg = len(self.channels[channel.id].messages)
            async for count, done in self.channels[channel.id].load(channel):
                if count > 0:
                    tmp_queried_msg = queried_msg + count - start_msg
                    tmp_msg = total_msg + count
                    warning_msg = "(this might take a while)"
                    if len(target_channels) > 5 and loading_new > 5:
                        warning_msg = (
                            "(most channels are new, this might take a looong while)"
                        )
                    elif loading_new > 0:
                        warning_msg = (
                            "(some channels are new, this might take a long while)"
                        )
                    dt = (datetime.now() - t0).total_seconds()
                    await code_message(
                        progress,
                        f"Reading history...\n{tmp_msg:,} messages in {total_chan + 1}/{max_chan} channels ({round(tmp_queried_msg/dt)}m/s)\n{warning_msg}",
                    )
                    if done:
                        total_chan += 1
            total_msg += len(self.channels[channel.id].messages)
            queried_msg += count - start_msg
        dt = (datetime.now() - t0).total_seconds()
        logging.info(
            f"log {self.guild.id} > queried in {dt} s -> {queried_msg / dt} m/s"
        )
        # write logs
        t0 = datetime.now()
        await code_message(
            progress,
            f"Saving (1/3)...\n{total_msg:,} messages in {total_chan} channels",
        )
        json_data = bytes(json.dumps(self.dict()), "utf-8")
        await code_message(
            progress,
            f"Saving (2/3)...\n{total_msg:,} messages in {total_chan} channels",
        )
        gziped_data = gzip.compress(json_data)
        await code_message(
            progress,
            f"Saving (3/3)...\n{total_msg:,} messages in {total_chan} channels",
        )
        with open(self.log_file, mode="wb") as f:
            f.write(gziped_data)
        dt = (datetime.now() - t0).total_seconds()
        logging.info(f"log {self.guild.id} > written in {dt} s")
        await code_message(
            progress, f"Analysing...\n{total_msg:,} messages in {total_chan} channels"
        )
        current_analysis.remove(self.log_file)
        return total_msg, total_chan
