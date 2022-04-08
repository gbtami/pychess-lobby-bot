# pychess-lobby-bot

A discord bot that connects [Pychess](https://www.pychess.org) to [discord](https://discord.gg/aPs8RKr) using [discord.py](https://github.com/Rapptz/discord.py). The Bot is hosted on [Heroku's](https://heroku.com/) worker dynos. Check ['Environments'](https://github.com/gbtami/pychess-lobby-bot/deployments) to view hosted app (though only the app name can be seen as it runs on worker dynos not web dynos).

## Local Installation
### Setup

Get a [Discord Bot Token from the Developer Portal](https://discord.com/developers/applications).

```bash
# Install Dependencies
pip install -r requirements.txt

# Linux
export DISCORD_TOKEN='xxxxxxxxx' # Add your discord token in place of xxxxxxxxx. The quotes must be kept.
export PYCHESS=https://www.pychess.org # url to which your bot must communicate. Don't add a '/' at the end of the url.

# Windows
setx DISCORD_TOKEN 'xxxxxxxxx' # Add your discord token in place of xxxxxxxxx. The quotes must be kept.
setx PYCHESS https://www.pychess.org # url to which your bot must communicate. Don't add a '/' at the end of the url.
```

### Run
```bash
python3 bot.py

# List of supported commands
python3 bot.py --help
```

## Heroku Installation
### Setup
Create a Heroku app (both app name and region do not really matter). Then go to the `Deploys` tab in Heroku UI and select `Connect to GitHub` and click to search and select your fork of pychess-lobby-bot. Once that is done click on `deploy` (you could also select automatic deploy if you want heroku to automatically publish changes to your Dev instance).

In Heroku UI set config var `DISCORD_TOKEN` to the Token of your Discord Bot (which you can get from [here](https://discord.com/developers/applications)) and set `PYCHESS` to the url to which your bot must communicate. Don't add a '/' at the end of the url (example, `https://www.pychess.org`).

### Run
To start your heroku instance go to the `Resources` tab and enable the worker dyno. This will automatically start your discord bot.