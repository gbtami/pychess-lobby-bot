import aiohttp
import argparse
import json
import logging
import os

import discord
from discord.ext.commands import Bot

log = logging.getLogger('discord')
log.setLevel(logging.INFO)

PYCHESS = os.getenv("PYCHESS", "http://127.0.0.1:8080")

TOKEN = os.getenv('DISCORD_TOKEN')
SERVER_ID = 634298688663191582
PYCHESS_LOBBY_CHANNEL_ID = 653203449927827456
GAME_SEEK_CHANNEL_ID = 823862902648995910
TOURNAMENT_CHANNEL_ID = 861234739820888074
ANNOUNCEMENT_CHANNEL_ID = 865964574507008000

ROLES = {
    "gladiator": 867894147900637215,
    "crazyhouse": 658544490830757919,
    "capablanca": 658544637467951124,
    "grand": 658544867269541899,
    "atomic": 867889563087274034,
    "hoppelpoppel": 867889843357876254,
    "xiangqi": 658544904011644938,
    "shogi": 658544950677340161,
    "shogun": 675143932912599041,
    "seirawan": 658753848982110209,
    "shako": 658544983623860235,
    "janggi": 695975424433455145,
    "makruk": 658545040234119178,
    "sittuyin": 658545093011046420,
    "orda": 702977517018939444,
    "synochess": 730903272080277524,
    "shinobi": 867889352704131132,
    "empire": 867892839493009478,
    "chess": 658545185571209221,
}

CATEGORIES = {
    "chess": ("chess", "chess960", "crazyhouse", "crazyhouse960", "placement", "atomic", "atomic960"),
    "fairy": ("capablanca", "capablanca960", "capahouse", "capahouse960", "seirawan", "seirawan960", "shouse", "grand", "grandhouse", "shako", "shogun", "hoppelpoppel"),
    "army": ("orda", "synochess", "shinobi", "empire", "ordamirror", "chak", "chennis"),
    "makruk": ("makruk", "makpong", "cambodian", "sittuyin", "asean"),
    "shogi": ("shogi", "minishogi", "kyotoshogi", "dobutsu", "gorogoroplus", "torishogi"),
    "xiangqi": ("xiangqi", "manchu", "janggi", "minixiangqi"),
}

intents = discord.Intents(messages=True, guilds=True)


class MyBot(Bot):

    async def on_message(self, msg):
        log.debug("---on_message() %s", msg)
        if msg.author.id == self.user.id or msg.channel.id != PYCHESS_LOBBY_CHANNEL_ID:
            log.debug("---self.user msg OR other channel.id -> return")
            return

        if self.lobby_ws is None:
            log.debug("---self.lobby_ws is None -> return")
            return
        log.debug("+++ msg is OK -> send_json()")
        await self.lobby_ws.send_json({"type": "lobbychat", "user": "", "message": "%s: %s" % (msg.author.name, msg.content)})


bot = MyBot(command_prefix="!", intents=intents)


def get_role_mentions(bot, message):
    guild = bot.get_guild(SERVER_ID)
    gladiator_role = guild.get_role(ROLES["gladiator"])
    log.debug("guild, role, intent are: %s %s %s", guild, gladiator_role, gladiator_role.mention)

    variant = message.split()[1]

    if variant in CATEGORIES["shogi"]:
        role = guild.get_role(ROLES["shogi"])

    elif variant in CATEGORIES["makruk"]:
        role = guild.get_role(ROLES["makruk"])

    elif variant == "janggi":
        role = guild.get_role(ROLES["janggi"])

    elif variant in CATEGORIES["xiangqi"]:
        role = guild.get_role(ROLES["xiangqi"])

    elif variant == "grand":
        role = guild.get_role(ROLES["grand"])

    elif variant == "shako":
        role = guild.get_role(ROLES["shako"])

    elif variant.startswith("atomic"):
        role = guild.get_role(ROLES["atomic"])

    elif variant.startswith("crazyhouse") or variant in ("shouse", "capahouse", "capahouse960", "grandhouse"):
        role = guild.get_role(ROLES["crazyhouse"])

    elif variant.startswith("capablanca"):
        role = guild.get_role(ROLES["capablanca"])

    elif variant.startswith("seirawan"):
        role = guild.get_role(ROLES["seirawan"])

    elif variant == "hoppelpoppel":
        role = guild.get_role(ROLES["hoppelpoppel"])

    elif variant == "shogun":
        role = guild.get_role(ROLES["shogun"])
    elif variant.startswith("orda"):
        role = guild.get_role(ROLES["orda"])
    elif variant == "synochess":
        role = guild.get_role(ROLES["synochess"])
    elif variant == "shinobi":
        role = guild.get_role(ROLES["shinobi"])
    elif variant == "empire":
        role = guild.get_role(ROLES["empire"])
# TODO: self-roles?
#    elif variant == "chak":
#        role = guild.get_role(ROLES["chak"])
#    elif variant == "chennis":
#        role = guild.get_role(ROLES["chennis"])
    else:
        role = guild.get_role(ROLES["chess"])

    return "%s %s" % (gladiator_role.mention, role.mention)


async def lobby_task(bot):
    await bot.wait_until_ready()

    # Get the pychess-lobby channel
    pychess_lobby_channel = bot.get_channel(PYCHESS_LOBBY_CHANNEL_ID)
    log.debug("pychess_lobby_channel is: %s", pychess_lobby_channel)

    game_seek_channel = bot.get_channel(GAME_SEEK_CHANNEL_ID)
    log.debug("game_seek_channel is: %s", game_seek_channel)

    tournament_channel = bot.get_channel(TOURNAMENT_CHANNEL_ID)
    log.debug("tournament_channel is: %s", tournament_channel)

    announcement_channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    log.debug("announcement_channel is: %s", announcement_channel)

    while True:
        log.debug("+++ Creating new aiohttp.ClientSession()")
        session = aiohttp.ClientSession()

        async with session.ws_connect(PYCHESS + '/wsl') as ws:
            bot.lobby_ws = ws
            await ws.send_json({"type": "lobby_user_connected", "username": "Discord-Relay"})
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    # print("msg.data", msg.data)
                    try:
                        if msg.data == 'close':
                            log.debug("!!! Lobby ws got 'close' msg")
                            await ws.close()
                            break
                        else:
                            data = json.loads(msg.data)
                            if data['type'] == 'ping':
                                await ws.send_json({"type": "pong"})
                            elif data['type'] == 'lobbychat' and data['user'] and data['user'] != "Discord-Relay":
                                log.debug("+++ lobbychat msg: %s %s", data['user'], data["message"])
                                await pychess_lobby_channel.send("**%s**: %s" % (data['user'], data['message']))
                            elif data['type'] == 'create_seek':
                                log.debug("+++ create_seek msg: %s", data["message"])
                                await game_seek_channel.send("%s" % data['message'])
                            elif data['type'] == 'create_tournament':
                                log.debug("+++ create_tournament msg: %s", data["message"])
                                await tournament_channel.send("%s" % data['message'])
                            elif data['type'] == 'notify_tournament':
                                log.debug("+++ notify_tournament msg: %s", data["message"])
                                await announcement_channel.send("%s %s" % (get_role_mentions(bot, data['message']), data['message']))
                    except Exception:
                        logging.exception("baj van")
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    log.debug("!!! Lobby ws connection closed with aiohttp.WSMsgType.CLOSE")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    log.debug("!!! Lobby ws connection closed with exception %s", ws.exception())
                else:
                    log.debug("!!! Lobby ws other msg.type %s %s", msg.type, msg)

        bot.lobby_ws = None
        await session.close()


background_task = bot.loop.create_task(lobby_task(bot))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='PyChess-Variants discord bot')
    parser.add_argument('-v', action='store_true', help='Verbose output. Changes log level from INFO to DEBUG.')
    parser.add_argument('-w', action='store_true', help='Less verbose output. Changes log level from INFO to WARNING.')
    args = parser.parse_args()

    logging.basicConfig()
    logging.getLogger("discord").setLevel(level=logging.DEBUG if args.v else logging.WARNING if args.w else logging.INFO)

    bot.run(TOKEN)
