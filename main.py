import os
import discord
from discord.ext import commands
from flask import Flask
import asyncio
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

TOKEN = os.getenv("TOKEN")
AUTOPING = os.getenv("AUTOPING")

# Intents e prefixo
intents = discord.Intents.all()

# Flask App para manter online no Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot está rodando com sucesso! ✅"

# Tarefa de auto-ping a cada 5 minutos
async def auto_ping():
    import aiohttp
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                await session.get(AUTOPING)
                print("[AutoPing] Ping enviado com sucesso.")
        except Exception as e:
            print(f"[AutoPing] Erro ao enviar ping: {e}")
        await asyncio.sleep(300)  # 5 minutos

# Bot customizado com setup_hook
class CustomBot(commands.Bot):
    async def setup_hook(self):
        # Carregar todos os cogs da pasta /cogs
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"[COG] Carregado: {filename}")
                except Exception as e:
                    print(f"[ERRO] Ao carregar {filename}: {e}")

        # Iniciar auto-ping
        self.loop.create_task(auto_ping())

# Instância do bot
bot = CustomBot(command_prefix="!", intents=intents)

# Iniciar Flask em uma thread separada
if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()

    # Iniciar bot
    asyncio.run(bot.start(TOKEN))
