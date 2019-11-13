# Discord Analyst

When you need statistics about your server

* `%emotes` - gives you a full ranking of the server emotes by usage
* `%emotes #channel` - same for a specific channel
* `%emotes @member` - same for a specific member of this server

## Running this bot

**1. Install requirements**

```
pip3 install -r requirements.txt
```

**2. Make a .env file as following**

```
#.env
DISCORD_TOKEN=<bot token from discordapp.com/developers>
```

**3.Invite bot in your discord server**

Generate and use the OAuth2 link in [discordapp.com/developers](https://discordapp.com/developers) to invite it.

You will need:
* Scopes:
  * bot
* Bot Permissions:
  * View Channels
  * Send Messages
  * Read Message History

**4. Launch bot**

```
python3 bot.py
```