import os
import discord
from datetime import datetime
from dotenv import load_dotenv
import emotes
import help
from utils import debug

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

client = discord.Client()

VERSION = "1.0"

t0 = datetime.now()

@client.event
async def on_ready():
    await client.change_presence(
        activity=discord.Game(f"v{VERSION} | %help"),
        status=discord.Status.online
    )
    print(f'{client.user} v{VERSION} has connected to Discord\nto the following guilds:')
    for guild in client.guilds:
        print(f'- {guild.name}(id: {guild.id})')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    permissions = message.channel.permissions_for(message.guild.me)
    if not permissions.send_messages:
        debug(message, f"missing 'send_messages' permission")
        await message.author.create_dm()
        await message.author.dm_channel.send(
            f"Hi, this bot doesn\'t have the permission to send a message to"
            f" #{message.channel} in server '{message.guild}'")
        return

    args = message.content.split(" ")

    if args[0] == "%info":
        debug(message, f"command '{message.content}'")
        await message.channel.send(f"Discord Analyst v{VERSION} started at {t0.isoformat()}")

    if args[0] == "%help":
        await help.compute(message, args)

    if args[0] == "%emotes":
        await emotes.compute(message, args)


client.run(token)
