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

    @commands.command(name='userinfo', aliases=['user', 'ui'])
    async def mostrar_userinfo(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author

        # Calcular tempo no servidor
        if user.joined_at:
            joined_days = (datetime.datetime.now() - user.joined_at.replace(tzinfo=None)).days
        else:
            joined_days = 0

        # Calcular tempo de criação da conta
        created_days = (datetime.datetime.now() - user.created_at.replace(tzinfo=None)).days

        # Status do usuário
        status_emoji = {
            discord.Status.online: "🟢",
            discord.Status.idle: "🟡",
            discord.Status.dnd: "🔴",
            discord.Status.offline: "⚫"
        }

        embed = discord.Embed(
            title=f"👤 Informações do Usuário",
            color=user.color if user.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )

        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)

        embed.add_field(name="🏷️ Usuário", value=(
            f"**Nome:** {user.display_name}\n"
            f"**Tag:** {user.name}#{user.discriminator}\n"
            f"**ID:** {user.id}\n"
            f"**Status:** {status_emoji.get(user.status, '❓')} {str(user.status).title()}"
        ), inline=True)

        embed.add_field(name="📅 Datas", value=(
            f"**Conta criada:** <t:{int(user.created_at.timestamp())}:R>\n"
            f"**Entrou no servidor:** <t:{int(user.joined_at.timestamp())}:R>" if user.joined_at else "**Entrou no servidor:** Desconhecido\n"
            f"**Dias no servidor:** {joined_days}"
        ), inline=True)

        # Cargos do usuário
        roles = [role.mention for role in user.roles[1:]]  # Remove @everyone
        roles_str = ", ".join(roles[:10]) if roles else "Nenhum"
        if len(roles) > 10:
            roles_str += f" e mais {len(roles) - 10} cargos..."

        embed.add_field(name=f"🎭 Cargos ({len(user.roles) - 1})", value=roles_str, inline=False)

        # Permissões importantes
        perms = user.guild_permissions
        important_perms = []
        if perms.administrator:
            important_perms.append("Administrador")
        if perms.manage_guild:
            important_perms.append("Gerenciar Servidor")
        if perms.manage_roles:
            important_perms.append("Gerenciar Cargos")
        if perms.ban_members:
            important_perms.append("Banir Membros")
        if perms.kick_members:
            important_perms.append("Expulsar Membros")

        if important_perms:
            embed.add_field(name="🔐 Permissões Importantes", value=", ".join(important_perms), inline=False)

        embed.set_footer(text=f"Solicitado por {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name='serverinfo', aliases=['server', 'si'])
    async def mostrar_serverinfo(self, ctx):
        guild = ctx.guild

        # Contadores de membros
        total_members = guild.member_count
        humans = sum(1 for member in guild.members if not member.bot)
        bots = total_members - humans
        online = sum(1 for member in guild.members if member.status != discord.Status.offline)

        # Contadores de canais
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)

        # Nível de verificação
        verification_levels = {
            discord.VerificationLevel.none: "Nenhuma",
            discord.VerificationLevel.low: "Baixa",
            discord.VerificationLevel.medium: "Média",
            discord.VerificationLevel.high: "Alta",
            discord.VerificationLevel.highest: "Muito Alta"
        }

        embed = discord.Embed(
            title=f"🏰 {guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="📊 Membros", value=(
            f"**Total:** {total_members:,}\n"
            f"**Humanos:** {humans:,}\n"
            f"**Bots:** {bots:,}\n"
            f"**Online:** {online:,}"
        ), inline=True)

        embed.add_field(name="📢 Canais", value=(
            f"**Texto:** {text_channels}\n"
            f"**Voz:** {voice_channels}\n"
            f"**Categorias:** {categories}\n"
            f"**Total:** {len(guild.channels)}"
        ), inline=True)

        embed.add_field(name="ℹ️ Informações", value=(
            f"**ID:** {guild.id}\n"
            f"**Dono:** {guild.owner.mention if guild.owner else 'Desconhecido'}\n"
            f"**Criado:** <t:{int(guild.created_at.timestamp())}:R>\n"
            f"**Cargos:** {len(guild.roles)}"
        ), inline=True)

        embed.add_field(name="🔒 Segurança", value=(
            f"**Verificação:** {verification_levels.get(guild.verification_level, 'Desconhecida')}\n"
            f"**Boost:** Nível {guild.premium_tier}\n"
            f"**Boosts:** {guild.premium_subscription_count}\n"
            f"**Emojis:** {len(guild.emojis)}/{guild.emoji_limit}"
        ), inline=True)

        # Recursos do servidor
        features = []
        if "COMMUNITY" in guild.features:
            features.append("Comunidade")
        if "VERIFIED" in guild.features:
            features.append("Verificado")
        if "PARTNERED" in guild.features:
            features.append("Parceiro")
        if "VANITY_URL" in guild.features:
            features.append("URL Personalizada")

        if features:
            embed.add_field(name="✨ Recursos", value=", ".join(features), inline=False)

        embed.set_footer(text=f"Solicitado por {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
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
            emoji, status = "🟠", "Médio"

        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )

        embed.add_field(name="📱 Latência da API", value=f"{emoji} {api_latency}ms", inline=True)
        embed.add_field(name="💬 Latência da Mensagem", value=f"⚡ {msg_latency}ms", inline=True)
        embed.add_field(name="📊 Status", value=status, inline=True)

        await message.edit(content=None, embed=embed)

    @commands.command(name='avatar', aliases=['av'])
    async def mostrar_avatar(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author

        embed = discord.Embed(
            title=f"🖼️ Avatar de {user.display_name}",
            color=user.color if user.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )

        avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
        embed.set_image(url=avatar_url)

        embed.add_field(name="🔗 Links", value=(
            f"[PNG]({avatar_url}?format=png) | "
            f"[JPG]({avatar_url}?format=jpg) | "
            f"[WEBP]({avatar_url}?format=webp)"
        ), inline=False)

        embed.set_footer(text=f"Solicitado por {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name='banner')
    async def mostrar_banner(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author

        # Buscar informações completas do usuário
        try:
            user_info = await self.bot.fetch_user(user.id)
        except:
            user_info = user

        embed = discord.Embed(
            title=f"🎨 Banner de {user.display_name}",
            color=user.color if user.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )

        if hasattr(user_info, 'banner') and user_info.banner:
            embed.set_image(url=user_info.banner.url)
            embed.add_field(name="🔗 Links", value=(
                f"[PNG]({user_info.banner.url}?format=png) | "
                f"[JPG]({user_info.banner.url}?format=jpg) | "
                f"[WEBP]({user_info.banner.url}?format=webp)"
            ), inline=False)
        else:
            embed.description = "❌ Este usuário não possui um banner personalizado."

        embed.set_footer(text=f"Solicitado por {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name='invite', aliases=['convite'])
    async def mostrar_convite(self, ctx):
        permissions = discord.Permissions(administrator=True)
        invite_url = discord.utils.oauth_url(self.bot.user.id, permissions=permissions)

        embed = discord.Embed(
            title="🔗 Convide o Bot!",
            description=f"[Clique aqui para me adicionar ao seu servidor!]({invite_url})",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.now()
        )
        
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        
        embed.add_field(name="🔐 Permissões", value=(
            "O link inclui permissões de **Administrador** para funcionamento completo.\n"
            "Você pode ajustar as permissões durante a adição se preferir."
        ), inline=False)

        embed.set_footer(text="Obrigado por usar nosso bot! ❤️")
        await ctx.send(embed=embed)

    @commands.command(name='uptime')
    async def mostrar_uptime(self, ctx):
        uptime = time.time() - self.start_time
        uptime_str = str(datetime.timedelta(seconds=int(uptime)))

        # Calcular componentes do uptime
        days = int(uptime // 86400)
        hours = int((uptime % 86400) // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)

        embed = discord.Embed(
            title="⏰ Tempo Online",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )

        embed.add_field(name="📊 Uptime Total", value=f"**{uptime_str}**", inline=False)
        
        embed.add_field(name="📅 Dias", value=f"{days:,}", inline=True)
        embed.add_field(name="🕐 Horas", value=f"{hours:,}", inline=True)
        embed.add_field(name="⏱️ Minutos", value=f"{minutes:,}", inline=True)

        embed.add_field(name="🚀 Iniciado em", value=f"<t:{int(self.start_time)}:F>", inline=False)

        embed.set_footer(text="Bot funcionando perfeitamente! ✅")
        await ctx.send(embed=embed)

    @commands.command(name='membercount', aliases=['membros'])
    async def contar_membros(self, ctx):
        guild = ctx.guild

        total = guild.member_count
        humans = sum(1 for member in guild.members if not member.bot)
        bots = total - humans
        online = sum(1 for member in guild.members if member.status != discord.Status.offline)

        # Status detalhados
        status_counts = {
            'online': sum(1 for m in guild.members if m.status == discord.Status.online),
            'idle': sum(1 for m in guild.members if m.status == discord.Status.idle),
            'dnd': sum(1 for m in guild.members if m.status == discord.Status.dnd),
            'offline': sum(1 for m in guild.members if m.status == discord.Status.offline)
        }

        embed = discord.Embed(
            title="👥 Contador de Membros",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )

        embed.add_field(name="📊 Geral", value=(
            f"**Total:** {total:,}\n"
            f"**Humanos:** {humans:,}\n"
            f"**Bots:** {bots:,}"
        ), inline=True)

        embed.add_field(name="🔄 Status", value=(
            f"🟢 **Online:** {status_counts['online']:,}\n"
            f"🟡 **Ausente:** {status_counts['idle']:,}\n"
            f"🔴 **Ocupado:** {status_counts['dnd']:,}\n"
            f"⚫ **Offline:** {status_counts['offline']:,}"
        ), inline=True)

        embed.add_field(name="📈 Estatísticas", value=(
            f"**Online:** {online:,} ({round((online/total)*100, 1)}%)\n"
            f"**Offline:** {total - online:,} ({round(((total-online)/total)*100, 1)}%)\n"
            f"**Humanos:** {round((humans/total)*100, 1)}%\n"
            f"**Bots:** {round((bots/total)*100, 1)}%"
        ), inline=True)

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.set_footer(text=f"Servidor: {guild.name}", icon_url=guild.icon.url if guild.icon else None)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utilities(bot))