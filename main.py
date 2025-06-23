import os
import discord
from discord.ext import commands
from flask import Flask
import asyncio

TOKEN = os.getenv("TOKEN")
AUTOPING = os.getenv("AUTOPING")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Auto Ping Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot está rodando!"

async def auto_ping():
    import aiohttp
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                await session.get(AUTOPING)
        except Exception as e:
            print(f"[autoping] Erro: {e}")
        await asyncio.sleep(300)  # a cada 5 minutos

# Substitui o antigo create_task no topo
class CustomBot(commands.Bot):
    async def setup_hook(self):
        # Carregar todos os cogs automaticamente
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"cogs.{filename[:-3]}")
        # Rodar tarefa de autoping
        self.loop.create_task(auto_ping())

# Substitui a instância antiga
bot = CustomBot(command_prefix="!", intents=intents)

if __name__ == "__main__":
    import threading

    # Flask roda em uma thread separada
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()

    # Roda o bot com asyncio
    import asyncio
    asyncio.run(bot.start(TOKEN))
