import discord
from discord.ext import commands
import psutil
import platform
import datetime
import time

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.command(name='botinfo', aliases=['bot'])
    async def mostrar_botinfo(self, ctx):
        uptime = time.time() - self.start_time
        uptime_str = str(datetime.timedelta(seconds=int(uptime)))

        total_members = sum(guild.member_count for guild in self.bot.guilds)
        total_channels = sum(len(guild.channels) for guild in self.bot.guilds)

        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_usage = f"{memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB ({memory.percent}%)"

        embed = discord.Embed(
            title="🤖 Informações do Bot",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )

        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)

        embed.add_field(name="📊 Estatísticas", value=(
            f"**Servidores:** {len(self.bot.guilds):,}\n"
            f"**Usuários:** {total_members:,}\n"
            f"**Canais:** {total_channels:,}\n"
            f"**Comandos:** {len(self.bot.commands)}"
        ), inline=True)

        embed.add_field(name="💻 Sistema", value=(
            f"**CPU:** {cpu_usage}%\n"
            f"**RAM:** {memory_usage}\n"
            f"**Python:** {platform.python_version()}\n"
            f"**Discord.py:** {discord.__version__}"
        ), inline=True)

        embed.add_field(name="⏰ Informações", value=(
            f"**Uptime:** {uptime_str}\n"
            f"**Ping:** {round(self.bot.latency * 1000)}ms\n"
            f"**ID:** {self.bot.user.id}\n"
            f"**Criado:** <t:{int(self.bot.user.created_at.timestamp())}:R>"
        ), inline=True)

        embed.set_footer(text="Desenvolvido com ❤️", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command(name='ping')
    async def mostrar_ping(self, ctx):
        start_time = time.time()
        message = await ctx.send("🏓 Calculando ping...")
        end_time = time.time()

        api_latency = round(self.bot.latency * 1000)
        msg_latency = round((end_time - start_time) * 1000)

        emoji, status = "🔴", "Ruim"
        if api_latency < 100:
            emoji, status = "🟢", "Excelente"
        elif api_latency < 200:
            emoji, status = "🟡", "Bom"
        elif api_latency < 300:
            emoji, status = "🗾", "Médio"

        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )

        embed.add_field(name="📱 Latência da API", value=f"{emoji} {api_latency}ms", inline=True)
        embed.add_field(name="💬 Latência da Mensagem", value=f"⚡ {msg_latency}ms", inline=True)
        embed.add_field(name="📊 Status", value=status, inline=True)

        await message.edit(content=None, embed=embed)

    @commands.command(name='uptime')
    async def mostrar_uptime(self, ctx):
        uptime = time.time() - self.start_time
        uptime_str = str(datetime.timedelta(seconds=int(uptime)))

        embed = discord.Embed(
            title="⏰ Tempo Online",
            description=f"Estou online há **{uptime_str}**",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )

        await ctx.send(embed=embed)

    @commands.command(name='invite', aliases=['convite'])
    async def mostrar_convite(self, ctx):
        permissions = discord.Permissions(administrator=True)
        invite_url = discord.utils.oauth_url(self.bot.user.id, permissions=permissions)

        embed = discord.Embed(
            title="🔗 Convide o Bot!",
            description=f"[Clique aqui para me adicionar ao seu servidor!]({invite_url})",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)

        await ctx.send(embed=embed)

    @commands.command(name='membercount', aliases=['membros'])
    async def contar_membros(self, ctx):
        guild = ctx.guild

        total = guild.member_count
        humans = sum(1 for member in guild.members if not member.bot)
        bots = total - humans
        online = sum(1 for member in guild.members if member.status != discord.Status.offline)

        embed = discord.Embed(
            title="👥 Contador de Membros",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )

        embed.add_field(name="📊 Total", value=f"{total:,}", inline=True)
        embed.add_field(name="👤 Humanos", value=f"{humans:,}", inline=True)
        embed.add_field(name="🤖 Bots", value=f"{bots:,}", inline=True)
        embed.add_field(name="🟢 Online", value=f"{online:,}", inline=True)
        embed.add_field(name="⚫ Offline", value=f"{total - online:,}", inline=True)
        embed.add_field(name="📈 Percentual Online", value=f"{round((online/total)*100, 1)}%", inline=True)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utilities(bot))
