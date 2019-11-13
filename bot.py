import os
import discord
import emotes
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

client = discord.Client()


@client.event
async def on_ready():
    await client.change_presence(
        activity=discord.Game("%emotes help"),
        status=discord.Status.online
    )
    print(f'{client.user} has connected to Discord\nto the following guilds:')
    for guild in client.guilds:
        print(f'- {guild.name}(id: {guild.id})')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    args = message.content.split(" ")

    if args[0] == "%emotes":
        await emotes.compute(client, message, args)

client.run(token)
