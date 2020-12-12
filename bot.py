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
GUILD = os.getenv('DISCORD_GUILD')
CHANNEL_ID = 653203449927827456

intents = discord.Intents(messages=True, guilds=True)


class MyBot(Bot):

    async def on_message(self, msg):
        log.debug("---on_message()", msg)
        if msg.author.id == self.user.id or msg.channel.id != CHANNEL_ID:
            log.debug("---self.user msg OR other channel.id -> return")
            return

        if self.lobby_ws is None:
            log.debug("---self.lobby_ws is None -> return")
            return
        log.debug("+++ msg is OK -> send_json()")
        await self.lobby_ws.send_json({"type": "lobbychat", "user": "", "message": "%s: %s" % (msg.author.name, msg.content)})


bot = MyBot(command_prefix="!", intents=intents)


async def lobby_task(bot):
    await bot.wait_until_ready()

    # Get the pychess-lobby channel
    channel = bot.get_channel(CHANNEL_ID)
    log.debug("Our channel is:", channel)

    while True:
        log.debug("+++ Creating new aiohttp.ClientSession()")
        session = aiohttp.ClientSession()

        async with session.ws_connect(PYCHESS + '/wsl') as ws:
            bot.lobby_ws = ws
            await ws.send_json({"type": "lobby_user_connected", "username": "Discord-Relay"})
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    print("msg.data", msg.data)
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
                                await channel.send("%s: %s" % (data['user'], data['message']))
                    except Exception:
                        logging.exception("baj van")
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    log.debug("!!! Lobby ws connection closed with aiohttp.WSMsgType.CLOSE")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    log.debug("!!! Lobby ws connection closed with exception %s" % ws.exception())
                else:
                    log.debug("!!! Lobby ws other msg.type %s %s" % (msg.type, msg))

        bot.lobby_ws = None
        await session.close()


background_task = bot.loop.create_task(lobby_task(bot))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='PyChess-Variants discord bot')
    parser.add_argument('-v', action='store_true', help='Verbose output. Changes log level from INFO to DEBUG.')
    parser.add_argument('-w', action='store_true', help='Less verbose output. Changes log level from INFO to WARNING.')
    args = parser.parse_args()

    logging.basicConfig()
    logging.getLogger().setLevel(level=logging.DEBUG if args.v else logging.WARNING if args.w else logging.INFO)

    bot.run(TOKEN)
