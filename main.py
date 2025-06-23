import discord
from discord.ext import commands
import os
import threading
from flask import Flask
import requests

# === Variáveis de ambiente ===
TOKEN = os.getenv("TOKEN")         # Token do bot (defina no Render)
AUTOPING_URL = os.getenv("AUTOPING")  # URL para o Render dar ping no seu bot

# === Inicialização do Flask ===
app = Flask(__name__)

@app.route("/")
def home():
    return "NatanBot está online!"

def manter_online():
    app.run(host="0.0.0.0", port=10000)

# === Inicialização do Bot Discord ===
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Evento on_ready
@bot.event
async def on_ready():
    print(f"🤖 Bot conectado como {bot.user}")

# Carregamento automático dos Cogs na pasta ./cogs
@bot.event
async def setup_hook():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
    print("✅ Todos os cogs carregados.")

# Ping automático para manter o bot vivo no Render
async def auto_ping():
    await bot.wait_until_ready()
    if AUTOPING_URL:
        while not bot.is_closed():
            try:
                requests.get(AUTOPING_URL)
                print("🔁 Autoping enviado.")
            except Exception as e:
                print(f"❌ Falha no autoping: {e}")
            await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(minutes=14))

# Rodar Flask em paralelo
threading.Thread(target=manter_online).start()

# Iniciar autoping e rodar o bot
if __name__ == "__main__":
    bot.loop.create_task(auto_ping())
    bot.run(TOKEN)
