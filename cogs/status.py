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
            {"type": "playing", "text": "Economia BR | Reais brasileiros"},
            {"type": "playing", "text": "!diario | Recompensa diária"},
            {"type": "watching", "text": "você se divertir"},
            {"type": "listening", "text": "suas conquistas"},
            {"type": "playing", "text": "!investir | Multiplique seu dinheiro"},
            {"type": "watching", "text": "o mercado financeiro"}
        ]
        
        self.current_status_index = 0
        self.status_interval = 10  # Intervalo em minutos (padrão: 10min)
        
    @commands.Cog.listener()
    async def on_ready(self):
        """Inicia o sistema de status quando o bot fica online"""
        print(f"📊 Sistema de Status iniciado para {self.bot.user}")
        
        if not self.change_status.is_running():
            self.change_status.start()
    
    @tasks.loop(minutes=10)  # Status muda a cada 10 minutos
    async def change_status(self):
        """Muda status aleatoriamente"""
        try:
            status_info = random.choice(self.status_list)
            await self._set_status(status_info)
            print(f"🔄 Status alterado: {status_info['type']} {status_info['text']}")
            
        except Exception as e:
            print(f"❌ Erro ao mudar status: {e}")
    
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
    
    @commands.command(name='statusintervalo')
    @commands.has_permissions(administrator=True)
    async def set_status_interval(self, ctx, minutos: int):
        """Altera o intervalo de mudança de status (Apenas administradores)"""
        if minutos < 1:
            embed = discord.Embed(
                title="❌ Erro",
                description="O intervalo deve ser de pelo menos 1 minuto!",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        if minutos > 1440:  # 24 horas
            embed = discord.Embed(
                title="❌ Erro",
                description="O intervalo não pode ser maior que 1440 minutos (24 horas)!",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        self.status_interval = minutos
        
        # Reinicia o loop com o novo intervalo
        self.change_status.cancel()
        self.change_status.change_interval(minutes=minutos)
        self.change_status.start()
        
        embed = discord.Embed(
            title="⚙️ Intervalo de Status Alterado",
            description=f"Novo intervalo: **{minutos} minutos**",
            color=0x00ff00
        )
        
        embed.add_field(
            name="ℹ️ Informação",
            value=f"O status agora mudará a cada {minutos} minuto(s)",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='statusmanual')
    @commands.has_permissions(administrator=True)
    async def manual_status_change(self, ctx):
        """Força uma mudança manual de status (Apenas administradores)"""
        try:
            status_info = random.choice(self.status_list)
            await self._set_status(status_info)
            
            embed = discord.Embed(
                title="🔄 Status Alterado Manualmente",
                description=f"**Novo status:** {status_info['text']}",
                color=0x00ff00
            )
            
            type_emoji = {
                "playing": "🎮",
                "listening": "🎵", 
                "watching": "👀",
                "streaming": "📺"
            }
            
            embed.add_field(
                name="Tipo",
                value=f"{type_emoji.get(status_info['type'], '🎮')} {status_info['type'].title()}",
                inline=True
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erro",
                description=f"Não foi possível alterar o status: {e}",
                color=0xff0000
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='listarstatus')
    async def list_status(self, ctx):
        """Mostra todos os status disponíveis"""
        embed = discord.Embed(
            title="📊 Lista de Status do Bot",
            description=f"O bot possui **{len(self.status_list)}** status diferentes",
            color=0x0099ff
        )
        
        # Divide os status em grupos para melhor visualização
        status_text = ""
        for i, status in enumerate(self.status_list, 1):
            emoji = "🎮" if status["type"] == "playing" else "🎵" if status["type"] == "listening" else "👀" if status["type"] == "watching" else "📺"
            status_text += f"{emoji} {status['text']}\n"
            
            # Adiciona campo a cada 10 status para não ficar muito longo
            if i % 10 == 0 or i == len(self.status_list):
                embed.add_field(
                    name=f"Status {i-9 if i >= 10 else 1}-{i}",
                    value=status_text,
                    inline=False
                )
                status_text = ""
        
        embed.add_field(
            name="⚙️ Configuração Atual",
            value=f"**Intervalo:** {self.status_interval} minutos\n**Status Aleatório:** Ativo",
            inline=False
        )
        
        embed.set_footer(text="Use !statusintervalo <minutos> para alterar o intervalo | !statusmanual para mudar agora")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(StatusSystem(bot))