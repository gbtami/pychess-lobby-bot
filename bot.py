import aiohttp
import argparse
import json
import logging
import os

from discord.ext import commands

log = logging.getLogger('discord')
log.setLevel(logging.INFO)

PYCHESS = os.getenv("PYCHESS", "http://127.0.0.1:8080")

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
CHANNEL_ID = 653203449927827456


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!")
        self.lobby_ws = None
        self.background_task = self.loop.create_task(self.lobby_task())

    async def lobby_task(self):
        await self.wait_until_ready()

        # Get the pychess-lobby channel
        channel = self.get_channel(CHANNEL_ID)

        while True:
            log.debug("+++ Creating new aiohttp.ClientSession()")
            session = aiohttp.ClientSession()

            async with session.ws_connect(PYCHESS + '/wsl') as ws:
                self.lobby_ws = ws
                await ws.send_json({"type": "lobby_user_connected", "username": "Discord-Relay"})
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        print("msg.data", msg.data)
                        try:
                            if msg.data == 'close':
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

            self.lobby_ws = None
            session.close()

    async def on_message(self, msg):
        if msg.author == self.user or msg.channel.id != CHANNEL_ID:
            return

        if self.lobby_ws is None:
            return
        await self.lobby_ws.send_json({"type": "lobbychat", "user": "", "message": "%s: %s" % (msg.author.name, msg.content)})


bot = MyBot()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='PyChess-Variants discord bot')
    parser.add_argument('-v', action='store_true', help='Verbose output. Changes log level from INFO to DEBUG.')
    parser.add_argument('-w', action='store_true', help='Less verbose output. Changes log level from INFO to WARNING.')
    args = parser.parse_args()

    logging.basicConfig()
    logging.getLogger().setLevel(level=logging.DEBUG if args.v else logging.WARNING if args.w else logging.INFO)

    bot.run(TOKEN)
