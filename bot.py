import os
import discord
from datetime import datetime
from dotenv import load_dotenv

# Custom libs
import emotes
import help
from utils import debug

VERSION = "1.1"
t0 = datetime.now()

# Loading token
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

client = discord.Client()


async def info(message, args):
    """
    Computes the %info command

    :param message: message sent
    :type message: :class:`discord.Message`
    :param args: arguments of the command
    :type args: list[:class:`str`]
    """
    await message.channel.send(f"```Discord Analyst v{VERSION} started at {t0:%Y-%m-%d %H:%M}```")


COMMANDS = {
    "%help": help.compute,
    "%emotes": emotes.compute,
    "%info": info
}


@client.event
async def on_ready():
    """
    Called when client is connected
    """
    # Change status
    await client.change_presence(
        activity=discord.Game(f"v{VERSION} | %help"),
        status=discord.Status.online
    )
    # Debug connected guilds
    print(f'{client.user} v{VERSION} has connected to Discord\nto the following guilds:')
    for guild in client.guilds:
        print(f'- {guild.name}(id: {guild.id})')


@client.event
async def on_message(message):
    """
    Called when a message is sent to any channel on any guild

    :param message: message sent
    :type message: discord.Message
    """

    # Ignore self messages
    if message.author == client.user:
        return

    args = message.content.split(" ")

    if len(args) < 1 or args[0] not in COMMANDS:
        return

    debug(message, f"command '{message.content}'")

    # Check if bot can respond on current channel or DM user
    permissions = message.channel.permissions_for(message.guild.me)
    if not permissions.send_messages:
        debug(message, f"missing 'send_messages' permission")
        await message.author.create_dm()
        await message.author.dm_channel.send(
            f"Hi, this bot doesn\'t have the permission to send a message to"
            f" #{message.channel} in server '{message.guild}'")
        return

    # Redirect to the correct command
    await COMMANDS[args[0]](message, args)


# Launch client
client.run(token)
