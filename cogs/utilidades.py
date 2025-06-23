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
    async def bot_info(self, ctx):
        """Informações sobre o bot"""
        uptime = time.time() - self.start_time
        uptime_str = str(datetime.timedelta(seconds=int(uptime)))
        
        # Estatísticas do bot
        total_members = sum(guild.member_count for guild in self.bot.guilds)
        total_channels = sum(len(guild.channels) for guild in self.bot.guilds)
        
        # Informações do sistema
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_usage = f"{memory.used / 1024 / 1024 / 1024:.1f}GB / {memory.total / 1024 / 1024 / 1024:.1f}GB ({memory.percent}%)"
        
        embed = discord.Embed(
            title="🤖 Informações do Bot",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        
        # Informações básicas
        embed.add_field(name="📊 Estatísticas", value=f"""
**Servidores:** {len(self.bot.guilds):,}
**Usuários:** {total_members:,}
**Canais:** {total_channels:,}
**Comandos:** {len(self.bot.commands)}
        """, inline=True)
        
        # Sistema
        embed.add_field(name="💻 Sistema", value=f"""
**CPU:** {cpu_usage}%
**RAM:** {memory_usage}
**Python:** {platform.python_version()}
**Discord.py:** {discord.__version__}
        """, inline=True)
        
        # Bot info
        embed.add_field(name="⏰ Informações", value=f"""
**Uptime:** {uptime_str}
**Ping:** {round(self.bot.latency * 1000)}ms
**ID:** {self.bot.user.id}
**Criado:** <t:{int(self.bot.user.created_at.timestamp())}:R>
        """, inline=True)
        
        embed.set_footer(text=f"Desenvolvido com ❤️", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='userinfo', aliases=['user', 'ui'])
    async def user_info(self, ctx, *, user: discord.Member = None):
        """Informações sobre um usuário"""
        user = user or ctx.author
        
        embed = discord.Embed(
            title=f"👤 Informações de {user.display_name}",
            color=user.color if user.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        
        # Informações básicas
        embed.add_field(name="📋 Básico", value=f"""
**Nome:** {user.name}
**Apelido:** {user.nick or "Nenhum"}
**ID:** {user.id}
**Bot:** {"Sim" if user.bot else "Não"}
        """, inline=True)
        
        # Datas
        embed.add_field(name="📅 Datas", value=f"""
**Conta criada:** <t:{int(user.created_at.timestamp())}:R>
**Entrou aqui:** <t:{int(user.joined_at.timestamp())}:R>
**Entrou há:** {(datetime.datetime.now() - user.joined_at.replace(tzinfo=None)).days} dias
        """, inline=True)
        
        # Status e atividade
        status_emoji = {
            discord.Status.online: "🟢",
            discord.Status.idle: "🟡", 
            discord.Status.dnd: "🔴",
            discord.Status.offline: "⚫"
        }
        
        activity = "Nenhuma"
        if user.activities:
            activity_list = []
            for act in user.activities:
                if isinstance(act, discord.Game):
                    activity_list.append(f"🎮 Jogando **{act.name}**")
                elif isinstance(act, discord.Streaming):
                    activity_list.append(f"🔴 Transmitindo **{act.name}**")
                elif isinstance(act, discord.Activity):
                    activity_list.append(f"📱 {act.name}")
                elif isinstance(act, discord.CustomActivity):
                    if act.name:
                        activity_list.append(f"✨ {act.name}")
            activity = "\n".join(activity_list) if activity_list else "Nenhuma"
        
        embed.add_field(name="💡 Status", value=f"""
**Status:** {status_emoji.get(user.status, "❓")} {str(user.status).title()}
**Atividade:** {activity}
        """, inline=False)
        
        # Cargos (top 10)
        if user.roles[1:]:  # Remove @everyone
            roles = [role.mention for role in user.roles[1:]]
            roles.reverse()  # Maior cargo primeiro
            roles_text = ", ".join(roles[:10])
            if len(user.roles) > 11:
                roles_text += f" e mais {len(user.roles) - 11} cargos..."
            embed.add_field(name=f"🎭 Cargos ({len(user.roles) - 1})", value=roles_text, inline=False)
        
        # Permissões chave
        key_perms = []
        if user.guild_permissions.administrator:
            key_perms.append("👑 Administrador")
        if user.guild_permissions.manage_guild:
            key_perms.append("🛠️ Gerenciar Servidor")
        if user.guild_permissions.manage_channels:
            key_perms.append("📁 Gerenciar Canais")
        if user.guild_permissions.manage_roles:
            key_perms.append("🎭 Gerenciar Cargos")
        if user.guild_permissions.kick_members:
            key_perms.append("👢 Expulsar Membros")
        if user.guild_permissions.ban_members:
            key_perms.append("🔨 Banir Membros")
        
        if key_perms:
            embed.add_field(name="🔑 Permissões Chave", value="\n".join(key_perms), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='serverinfo', aliases=['server', 'si', 'guildinfo'])
    async def server_info(self, ctx):
        """Informações sobre o servidor"""
        guild = ctx.guild
        
        embed = discord.Embed(
            title=f"🏠 Informações do Servidor",
            color=discord.Color.gold(),
            timestamp=datetime.datetime.now()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Informações básicas
        embed.add_field(name="📋 Básico", value=f"""
**Nome:** {guild.name}
**ID:** {guild.id}
**Dono:** {guild.owner.mention}
**Criado:** <t:{int(guild.created_at.timestamp())}:R>
**Região:** {guild.preferred_locale}
        """, inline=True)
        
        # Contadores
        bots = sum(1 for member in guild.members if member.bot)
        humans = guild.member_count - bots
        
        online = sum(1 for member in guild.members if member.status != discord.Status.offline)
        
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed.add_field(name="👥 Membros", value=f"""
**Total:** {guild.member_count:,}
**Humanos:** {humans:,}
**Bots:** {bots:,}
**Online:** {online:,}
        """, inline=True)
        
        embed.add_field(name="📁 Canais", value=f"""
**Total:** {len(guild.channels)}
**Texto:** {text_channels}
**Voz:** {voice_channels}
**Categorias:** {categories}
        """, inline=True)
        
        # Recursos do servidor
        features = []
        feature_names = {
            'COMMUNITY': '🌟 Comunidade',
            'PARTNERED': '🤝 Parceiro',
            'VERIFIED': '✅ Verificado',
            'VANITY_URL': '🔗 URL Personalizada',
            'INVITE_SPLASH': '🎨 Splash de Convite',
            'BANNER': '🖼️ Banner',
            'ANIMATED_ICON': '🎭 Ícone Animado',
            'DISCOVERABLE': '🔍 Descobrível',
            'FEATURABLE': '⭐ Destacável',
            'NEWS': '📰 Canais de Notícias',
            'THREADS_ENABLED': '🧵 Threads',
            'WELCOME_SCREEN_ENABLED': '👋 Tela de Boas-vindas'
        }
        
        for feature in guild.features:
            if feature in feature_names:
                features.append(feature_names[feature])
        
        if features:
            embed.add_field(name="✨ Recursos", value="\n".join(features), inline=False)
        
        # Boosts
        if guild.premium_tier > 0:
            embed.add_field(name="💎 Nitro Boost", value=f"""
**Nível:** {guild.premium_tier}
**Boosts:** {guild.premium_subscription_count}
**Boosters:** {len(guild.premium_subscribers)}
            """, inline=True)
        
        # Segurança
        verification_levels = {
            discord.VerificationLevel.none: "Nenhuma",
            discord.VerificationLevel.low: "Baixa",
            discord.VerificationLevel.medium: "Média", 
            discord.VerificationLevel.high: "Alta",
            discord.VerificationLevel.highest: "Máxima"
        }
        
        embed.add_field(name="🛡️ Segurança", value=f"""
**Verificação:** {verification_levels.get(guild.verification_level, "Desconhecida")}
**Filtro Explícito:** {str(guild.explicit_content_filter).replace('_', ' ').title()}
**2FA:** {"Obrigatório" if guild.mfa_level else "Opcional"}
        """, inline=True)
        
        # Estatísticas adicionais
        embed.add_field(name="📊 Estatísticas", value=f"""
**Cargos:** {len(guild.roles)}
**Emojis:** {len(guild.emojis)}/{guild.emoji_limit}
**Stickers:** {len(guild.stickers)}
        """, inline=True)
        
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='ping')
    async def ping(self, ctx):
        """Mostra a latência do bot"""
        start_time = time.time()
        message = await ctx.send("🏓 Calculando ping...")
        end_time = time.time()
        
        # Latência da API
        api_latency = round(self.bot.latency * 1000)
        
        # Latência da mensagem
        msg_latency = round((end_time - start_time) * 1000)
        
        # Emoji baseado na latência
        if api_latency < 100:
            emoji = "🟢"
            status = "Excelente"
        elif api_latency < 200:
            emoji = "🟡"
            status = "Bom"
        elif api_latency < 300:
            emoji = "🟠"
            status = "Médio"
        else:
            emoji = "🔴"
            status = "Ruim"
        
        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="📡 Latência da API", value=f"{emoji} {api_latency}ms", inline=True)
        embed.add_field(name="💬 Latência da Mensagem", value=f"⚡ {msg_latency}ms", inline=True)
        embed.add_field(name="📊 Status", value=status, inline=True)
        
        await message.edit(content=None, embed=embed)
    
    @commands.command(name='avatar', aliases=['av', 'pfp'])
    async def avatar(self, ctx, *, user: discord.User = None):
        """Mostra o avatar de um usuário"""
        user = user or ctx.author
        
        embed = discord.Embed(
            title=f"🖼️ Avatar de {user.display_name}",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.now()
        )
        
        avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
        embed.set_image(url=avatar_url)
        
        # Links de download
        if user.avatar:
            embed.add_field(name="📥 Downloads", value=f"""
[PNG]({user.avatar.replace(format='png').url}) | [JPG]({user.avatar.replace(format='jpg').url}) | [WEBP]({user.avatar.replace(format='webp').url})
{f"| [GIF]({user.avatar.replace(format='gif').url})" if user.avatar.is_animated() else ""}
            """, inline=False)
        
        # Avatar do servidor (se for membro)
        if isinstance(user, discord.Member) and user.guild_avatar:
            embed.add_field(name="🏠 Avatar do Servidor", value="[Clique aqui para ver](hidden)", inline=False)
            embed.set_footer(text="💡 Use o comando novamente para ver o avatar global")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='banner')
    async def banner(self, ctx, *, user: discord.User = None):
        """Mostra o banner de um usuário"""
        user = user or ctx.author
        
        # Busca informações completas do usuário
        try:
            user = await self.bot.fetch_user(user.id)
        except:
            pass
        
        embed = discord.Embed(
            title=f"🎨 Banner de {user.display_name}",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.now()
        )
        
        if user.banner:
            embed.set_image(url=user.banner.url)
            embed.add_field(name="📥 Downloads", value=f"""
[PNG]({user.banner.replace(format='png').url}) | [JPG]({user.banner.replace(format='jpg').url}) | [WEBP]({user.banner.replace(format='webp').url})
{f"| [GIF]({user.banner.replace(format='gif').url})" if user.banner.is_animated() else ""}
            """, inline=False)
        else:
            embed.description = "❌ Este usuário não possui banner personalizado."
            embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        
        await ctx.send(embed=embed)
    
    # COMANDOS EXTRAS
    
    @commands.command(name='invite', aliases=['convite'])
    async def invite(self, ctx):
        """Link de convite do bot"""
        permissions = discord.Permissions(administrator=True)
        invite_url = discord.utils.oauth_url(self.bot.user.id, permissions=permissions)
        
        embed = discord.Embed(
            title="🔗 Convite o Bot!",
            description=f"[Clique aqui para me adicionar ao seu servidor!]({invite_url})",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='uptime')
    async def uptime(self, ctx):
        """Tempo que o bot está online"""
        uptime = time.time() - self.start_time
        uptime_str = str(datetime.timedelta(seconds=int(uptime)))
        
        embed = discord.Embed(
            title="⏰ Tempo Online",
            description=f"Estou online há **{uptime_str}**",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='membercount', aliases=['membros'])
    async def member_count(self, ctx):
        """Contador de membros do servidor"""
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