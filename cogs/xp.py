import discord
from discord.ext import commands, tasks
import json
import asyncio
from datetime import datetime, timedelta
import os
import math
import random

class XPSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_file = "xp_data.json"
        self.xp_config_file = "xp_config.json"
        self.xp_data = self.load_xp_data()
        self.xp_config = self.load_xp_config()
        self.message_cooldowns = {}

    def load_xp_data(self):
        if os.path.exists(self.xp_file):
            try:
                with open(self.xp_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_xp_data(self):
        with open(self.xp_file, 'w', encoding='utf-8') as f:
            json.dump(self.xp_data, f, indent=2, ensure_ascii=False)

    def load_xp_config(self):
        if os.path.exists(self.xp_config_file):
            try:
                with open(self.xp_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_xp_config(self):
        with open(self.xp_config_file, 'w', encoding='utf-8') as f:
            json.dump(self.xp_config, f, indent=2, ensure_ascii=False)

    def get_guild_config(self, guild_id):
        guild_id = str(guild_id)
        if guild_id not in self.xp_config:
            self.xp_config[guild_id] = {
                'base_xp': 15,
                'xp_per_message': 25,
                'xp_per_level': 100,
                'cooldown': 60,
                'vip_cooldown': 30,
                'vip_multiplier': 2.0
            }
            self.save_xp_config()
        return self.xp_config[guild_id]

    def get_user_data(self, user_id, guild_id):
        user_key = f"{guild_id}_{user_id}"
        if user_key not in self.xp_data:
            self.xp_data[user_key] = {
                'xp': 0,
                'level': 1,
                'messages': 0,
                'last_message': None
            }
        return self.xp_data[user_key]

    def calculate_level(self, xp, xp_per_level):
        return int(math.sqrt(xp / xp_per_level)) + 1

    def calculate_xp_for_level(self, level, xp_per_level):
        return ((level - 1) ** 2) * xp_per_level

    async def is_user_vip(self, user_id, guild_id):
        vip_cog = self.bot.get_cog('VIPSystem')
        if vip_cog:
            return await vip_cog.is_vip(user_id, guild_id)
        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        user_id = message.author.id
        guild_id = message.guild.id
        config = self.get_guild_config(guild_id)
        
        # Verificar cooldown
        cooldown_key = f"{guild_id}_{user_id}"
        now = datetime.now()
        
        # Cooldown menor para VIPs
        is_vip = await self.is_user_vip(user_id, guild_id)
        cooldown_time = config['vip_cooldown'] if is_vip else config['cooldown']
        
        if cooldown_key in self.message_cooldowns:
            time_diff = (now - self.message_cooldowns[cooldown_key]).total_seconds()
            if time_diff < cooldown_time:
                return

        self.message_cooldowns[cooldown_key] = now
        
        # Calcular XP ganho
        base_xp = random.randint(config['base_xp'], config['xp_per_message'])
        
        # Aplicar multiplicador VIP
        if is_vip:
            base_xp = int(base_xp * config['vip_multiplier'])
        
        # Atualizar dados do usuário
        user_data = self.get_user_data(user_id, guild_id)
        old_level = user_data['level']
        user_data['xp'] += base_xp
        user_data['messages'] += 1
        user_data['last_message'] = now.isoformat()
        
        new_level = self.calculate_level(user_data['xp'], config['xp_per_level'])
        user_data['level'] = new_level
        
        self.save_xp_data()
        
        # Verificar level up
        if new_level > old_level:
            embed = discord.Embed(
                title="🎉 Level Up!",
                description=f"{message.author.mention} subiu para o **Level {new_level}**!",
                color=discord.Color.gold()
            )
            embed.add_field(name="XP Total", value=f"{user_data['xp']:,}", inline=True)
            embed.set_thumbnail(url=message.author.display_avatar.url)
            
            if is_vip:
                embed.add_field(name="👑 VIP Bonus", value="XP em dobro!", inline=True)
            
            await message.channel.send(embed=embed)

    @commands.command(name='xp')
    async def check_xp(self, ctx, member: discord.Member = None):
        if not member:
            member = ctx.author
            
        user_data = self.get_user_data(member.id, ctx.guild.id)
        config = self.get_guild_config(ctx.guild.id)
        
        current_level_xp = self.calculate_xp_for_level(user_data['level'], config['xp_per_level'])
        next_level_xp = self.calculate_xp_for_level(user_data['level'] + 1, config['xp_per_level'])
        xp_needed = next_level_xp - user_data['xp']
        
        is_vip = await self.is_user_vip(member.id, ctx.guild.id)
        
        embed = discord.Embed(
            title=f"📊 XP de {member.display_name}",
            color=discord.Color.gold() if is_vip else discord.Color.blue()
        )
        
        embed.add_field(name="Level", value=f"**{user_data['level']}**", inline=True)
        embed.add_field(name="XP Total", value=f"**{user_data['xp']:,}**", inline=True)
        embed.add_field(name="Mensagens", value=f"**{user_data['messages']:,}**", inline=True)
        embed.add_field(name="XP para próximo level", value=f"**{xp_needed:,}**", inline=True)
        
        if is_vip:
            embed.add_field(name="👑 Status", value="**VIP**", inline=True)
            embed.add_field(name="Bônus XP", value=f"**{config['vip_multiplier']}x**", inline=True)
        
        # Barra de progresso
        progress = ((user_data['xp'] - current_level_xp) / (next_level_xp - current_level_xp)) * 100
        bar_length = 20
        filled = int(bar_length * progress / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        embed.add_field(name="Progresso", value=f"`{bar}` {progress:.1f}%", inline=False)
        
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name='topxp')
    async def leaderboard_xp(self, ctx, page: int = 1):
        guild_users = []
        
        for key, data in self.xp_data.items():
            if key.startswith(str(ctx.guild.id)):
                user_id = int(key.split('_')[1])
                user = ctx.guild.get_member(user_id)
                if user:
                    guild_users.append((user, data))
        
        guild_users.sort(key=lambda x: x[1]['xp'], reverse=True)
        
        if not guild_users:
            embed = discord.Embed(
                title="📊 Top XP",
                description="Nenhum usuário com XP encontrado!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        per_page = 10
        max_pages = math.ceil(len(guild_users) / per_page)
        if page > max_pages or page < 1:
            page = 1
        
        start = (page - 1) * per_page
        end = start + per_page
        
        embed = discord.Embed(
            title="🏆 Top XP",
            description=f"Página {page}/{max_pages}",
            color=discord.Color.gold()
        )
        
        leaderboard_text = ""
        for i, (user, data) in enumerate(guild_users[start:end], start + 1):
            is_vip = await self.is_user_vip(user.id, ctx.guild.id)
            vip_icon = "👑" if is_vip else ""
            
            medal = ""
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            
            leaderboard_text += f"{medal} **#{i}** {vip_icon} {user.mention}\n"
            leaderboard_text += f"Level **{data['level']}** • **{data['xp']:,}** XP\n\n"
        
        embed.description = leaderboard_text
        embed.set_footer(text=f"👑 = VIP | Página {page}/{max_pages}")
        
        await ctx.send(embed=embed)

    @commands.command(name='mensagemporxp')
    @commands.has_permissions(administrator=True)
    async def set_xp_per_message(self, ctx, min_xp: int, max_xp: int):
        if min_xp <= 0 or max_xp <= 0 or min_xp > max_xp:
            embed = discord.Embed(
                title="❌ Erro",
                description="Valores inválidos! Min deve ser menor que Max e ambos positivos.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        config = self.get_guild_config(ctx.guild.id)
        config['base_xp'] = min_xp
        config['xp_per_message'] = max_xp
        self.save_xp_config()
        
        embed = discord.Embed(
            title="✅ XP por Mensagem Configurado",
            description=f"XP por mensagem: **{min_xp} - {max_xp}**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name='basexp')
    @commands.has_permissions(administrator=True)
    async def set_base_xp(self, ctx, base_xp: int):
        if base_xp <= 0:
            embed = discord.Embed(
                title="❌ Erro",
                description="XP base deve ser maior que 0!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        config = self.get_guild_config(ctx.guild.id)
        config['base_xp'] = base_xp
        self.save_xp_config()
        
        embed = discord.Embed(
            title="✅ XP Base Configurado",
            description=f"XP base por mensagem: **{base_xp}**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name='adicionarxppornivel')
    @commands.has_permissions(administrator=True)
    async def set_xp_per_level(self, ctx, xp_per_level: int):
        if xp_per_level <= 0:
            embed = discord.Embed(
                title="❌ Erro",
                description="XP por nível deve ser maior que 0!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        config = self.get_guild_config(ctx.guild.id)
        config['xp_per_level'] = xp_per_level
        self.save_xp_config()
        
        embed = discord.Embed(
            title="✅ XP por Nível Configurado",
            description=f"XP necessário por nível: **{xp_per_level:,}**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name='tempodexp')
    @commands.has_permissions(administrator=True)
    async def set_xp_cooldown(self, ctx, normal_cooldown: int, vip_cooldown: int = None):
        if normal_cooldown <= 0:
            embed = discord.Embed(
                title="❌ Erro",
                description="Cooldown deve ser maior que 0!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if vip_cooldown is None:
            vip_cooldown = normal_cooldown // 2
        
        config = self.get_guild_config(ctx.guild.id)
        config['cooldown'] = normal_cooldown
        config['vip_cooldown'] = vip_cooldown
        self.save_xp_config()
        
        embed = discord.Embed(
            title="✅ Cooldown de XP Configurado",
            description=f"Cooldown normal: **{normal_cooldown}s**\nCooldown VIP: **{vip_cooldown}s**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name='configxp')
    @commands.has_permissions(administrator=True)
    async def config_xp(self, ctx):
        config = self.get_guild_config(ctx.guild.id)
        
        # Contar usuários ativos
        active_users = 0
        for key in self.xp_data.keys():
            if key.startswith(str(ctx.guild.id)):
                active_users += 1
        
        embed = discord.Embed(
            title="⚙️ Configurações XP",
            description="Configurações atuais do sistema de XP",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📊 XP por Mensagem",
            value=f"{config['base_xp']} - {config['xp_per_message']}",
            inline=True
        )
        embed.add_field(
            name="📈 XP por Nível",
            value=f"{config['xp_per_level']:,}",
            inline=True
        )
        embed.add_field(
            name="⏰ Cooldown",
            value=f"Normal: {config['cooldown']}s\nVIP: {config['vip_cooldown']}s",
            inline=True
        )
        embed.add_field(
            name="👑 Multiplicador VIP",
            value=f"{config['vip_multiplier']}x",
            inline=True
        )
        embed.add_field(
            name="👥 Usuários Ativos",
            value=f"{active_users:,}",
            inline=True
        )
        
        embed.add_field(
            name="📝 Comandos Admin",
            value="`!mensagemporxp <min> <max>`\n`!basexp <valor>`\n`!adicionarxppornivel <valor>`\n`!tempodexp <normal> [vip]`",
            inline=False
        )
        
        await ctx.send(embed=embed)

    # Error handlers
    @set_xp_per_message.error
    @set_base_xp.error
    @set_xp_per_level.error
    @set_xp_cooldown.error
    @config_xp.error
    async def xp_error_handler(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa ser **Administrador** para usar este comando!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ Erro",
                description="Argumentos inválidos! Use números válidos.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(XPSystem(bot))