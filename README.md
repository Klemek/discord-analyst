[![Scc Count Badge](https://sloc.xyz/github/klemek/discord-analyst/?category=code)](https://github.com/boyter/scc/#badges-beta)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/Klemek/discord-analyst.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Klemek/discord-analyst/context:python)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/Klemek/discord-analyst.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Klemek/discord-analyst/alerts/)

# Discord Analyst

When you need statistics about your discord server



* `%help (command)` - info about commands
* `%info` - version and uptime
* `%scan` - full analysis
* `%freq` - frequency analysis
* `%compo` - composition analysis
* `%pres` - presence analysis
* `%emojis` - rank emotes by their usage
  * arguments:
    * `<n>` - top <n> emojis, default is 20
    * `all` - list all common emojis in addition to this guild's
    * `members` - show top member for each emote
    * `sort:usage/reaction` - other sorting methods
* `%mentions` - rank mentions by their usage
  * arguments:
    * `<n>` - top <n> mentions, default is 10
    * `all` - show role/channel/everyone/here mentions
* `%mentioned` - rank specific user mentions by their usage
  * arguments:
    * `<n>` - top <n> mentions, default is 10
    * `all` - show role/channel/everyone/here mentions
* `%cancel` - cancel current analysis

* Common arguments:
    * @member/me : filter for one or more member
    * #channel/here : filter for one or more channel
    * fast : only read cache

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
python3 src/main.py
```

## Changelog

* **v1.7(wip)**:
  * emojis percents
  * emojis other sorting
  * mentions ranking
  * cancel
* **v1.6**:
  * more scans : `%scan`, `%freq`, `%compo`, `%pres`
  * huge bug fix
* **v1.5**:
  * top <n> emotes
  * bug fix
* **v1.4**:
  * integrate miniscord
  * insane speed with bot-side logging
  * bug fix
* **v1.3**: revert to v1.1 and update requirements
* **v1.2**: don't quit on occasional exception
* **v1.1**:
  * coma separator for big numbers
  * history loading by chunks for big channels (performance increase)
  * bug fix
* **v1.0**: stable release
