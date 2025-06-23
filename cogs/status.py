import discord
from discord.ext import commands, tasks
import asyncio
import random
from datetime import datetime

class StatusSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status_list = [
            {"type": "playing", "text": "!ajuda | Criador: Natan"},
            {"type": "listening", "text": "NatsonGames"},
            {"type": "playing", "text": "!saldo | Sistema de Economia"},
            {"type": "watching", "text": "você ganhar dinheiro"},
            {"type": "playing", "text": "!trabalhar | Faça seu dinheiro"},
            {"type": "listening", "text": "comandos de economia"},
            {"type": "playing", "text": "!crime | Vida de bandido"},
            {"type": "watching", "text": "o servidor crescer"},
            {"type": "playing", "text": "!loteria | Tente a sorte"},
            {"type": "streaming", "text": "NatsonGames no Twitch"},
            {"type": "playing", "text": "!loja | Compre itens legais"},
            {"type": "watching", "text": "transações bancárias"},
            {"type": "playing", "text": "!apostar | Jogue com moderação"},
            {"type": "listening", "text": "música do Natan"},
            {"type": "playing", "text": "Economia BR | Reais brasileiros"}
        ]
        
        # 7 status que mudam a cada 24h (1 por dia da semana)
        self.weekly_status = [
            {"type": "playing", "text": "Segunda-feira | !diario grátis"},     # Segunda
            {"type": "listening", "text": "Terça | NatsonGames"},               # Terça  
            {"type": "watching", "text": "Quarta | Você trabalhar"},            # Quarta
            {"type": "playing", "text": "Quinta | !crime perigoso"},            # Quinta
            {"type": "streaming", "text": "Sexta | Live do Natan"},             # Sexta
            {"type": "playing", "text": "Sábado | !loteria da sorte"},          # Sábado
            {"type": "listening", "text": "Domingo | Descanso merecido"}        # Domingo
        ]
        
        self.current_status_index = 0
        self.using_weekly_status = True  # True = status semanal, False = status aleatório
        
    @commands.Cog.listener()
    async def on_ready(self):
        """Inicia o sistema de status quando o bot fica online"""
        print(f"📊 Sistema de Status iniciado para {self.bot.user}")
        
        if not self.change_random_status.is_running():
            self.change_random_status.start()
            
        if not self.change_daily_status.is_running():
            self.change_daily_status.start()
    
    @tasks.loop(minutes=10)  # Status aleatório a cada 10 minutos
    async def change_random_status(self):
        """Muda status aleatoriamente quando não está no modo semanal"""
        if self.using_weekly_status:
            return
            
        try:
            status_info = random.choice(self.status_list)
            await self._set_status(status_info)
            print(f"🔄 Status aleatório: {status_info['type']} {status_info['text']}")
            
        except Exception as e:
            print(f"❌ Erro ao mudar status aleatório: {e}")
    
    @tasks.loop(hours=24)  # Status semanal muda a cada 24 horas
    async def change_daily_status(self):
        """Muda status diário (ciclo de 7 dias)"""
        if not self.using_weekly_status:
            return
            
        try:
            # Pega o status do dia atual (0-6 = Segunda a Domingo)
            today = datetime.now().weekday()  # 0=Segunda, 6=Domingo
            status_info = self.weekly_status[today]
            
            await self._set_status(status_info)
            
            dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
            print(f"📅 Status diário ({dias_semana[today]}): {status_info['text']}")
            
        except Exception as e:
            print(f"❌ Erro ao mudar status diário: {e}")
    
    async def _set_status(self, status_info):
        """Define o status do bot"""
        # Define o tipo de atividade
        if status_info["type"] == "playing":
            activity = discord.Game(name=status_info["text"])
        elif status_info["type"] == "listening":
            activity = discord.Activity(type=discord.ActivityType.listening, name=status_info["text"])
        elif status_info["type"] == "watching":
            activity = discord.Activity(type=discord.ActivityType.watching, name=status_info["text"])
        elif status_info["type"] == "streaming":
            activity = discord.Streaming(name=status_info["text"], url="https://twitch.tv/natsongames")
        else:
            activity = discord.Game(name=status_info["text"])
        
        # Muda o status
        await self.bot.change_presence(
            status=discord.Status.online,
            activity=activity
        )
    
    @commands.command(name='statusmodo')
    @commands.has_permissions(administrator=True)
    async def toggle_status_mode(self, ctx):
        """Alterna entre status semanal e aleatório (Apenas administradores)"""
        self.using_weekly_status = not self.using_weekly_status
        
        modo = "Semanal (1 por dia)" if self.using_weekly_status else "Aleatório (a cada 10min)"
        
        embed = discord.Embed(
            title="⚙️ Modo de Status Alterado",
            description=f"Modo atual: **{modo}**",
            color=0x00ff00
        )
        
        if self.using_weekly_status:
            embed.add_field(
                name="📅 Status Semanal",
                value="Cada dia da semana tem um status específico que muda a cada 24h",
                inline=False
            )
        else:
            embed.add_field(
                name="🎲 Status Aleatório", 
                value="Status muda aleatoriamente a cada 10 minutos",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='listarstatus')
    async def list_status(self, ctx):
        """Mostra todos os status disponíveis"""
        embed = discord.Embed(
            title="📊 Lista de Status do Bot",
            color=0x0099ff
        )
        
        # Status semanais
        dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        weekly_text = ""
        for i, status in enumerate(self.weekly_status):
            emoji = "🎮" if status["type"] == "playing" else "🎵" if status["type"] == "listening" else "👀" if status["type"] == "watching" else "📺"
            weekly_text += f"{emoji} **{dias[i]}:** {status['text']}\n"
        
        embed.add_field(
            name="📅 Status Semanais (24h cada)",
            value=weekly_text,
            inline=False
        )
        
        # Status atual
        current_day = datetime.now().weekday()
        mode = "Semanal" if self.using_weekly_status else "Aleatório"
        
        embed.add_field(
            name="⚙️ Configuração Atual",
            value=f"**Modo:** {mode}\n**Hoje:** {dias[current_day]}",
            inline=False
        )
        
        embed.set_footer(text="Use !statusmodo para alternar entre os modos (Admin)")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(StatusSystem(bot))