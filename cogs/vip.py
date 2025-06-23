import discord
from discord.ext import commands, tasks
import json
import asyncio
from datetime import datetime, timedelta
import os

class VIPSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vip_file = "vip_data.json"
        self.config_file = "vip_config.json"
        self.vip_data = self.load_vip_data()
        self.vip_config = self.load_vip_config()
        self.check_vip_expiry.start()

    def load_vip_data(self):
        """Carrega dados dos usuários VIP"""
        if os.path.exists(self.vip_file):
            try:
                with open(self.vip_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_vip_data(self):
        """Salva dados dos usuários VIP"""
        with open(self.vip_file, 'w', encoding='utf-8') as f:
            json.dump(self.vip_data, f, indent=4, ensure_ascii=False)

    def load_vip_config(self):
        """Carrega configurações do VIP"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_vip_config(self):
        """Salva configurações do VIP"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.vip_config, f, indent=4, ensure_ascii=False)

    async def get_vip_role(self, guild):
        """Obtém o cargo VIP configurado para o servidor"""
        guild_id = str(guild.id)
        if guild_id in self.vip_config and 'vip_role_id' in self.vip_config[guild_id]:
            role_id = self.vip_config[guild_id]['vip_role_id']
            return guild.get_role(role_id)
        return None

    async def is_vip(self, user_id, guild_id):
        """Verifica se um usuário é VIP"""
        user_key = f"{guild_id}_{user_id}"
        if user_key in self.vip_data:
            expiry_date = datetime.fromisoformat(self.vip_data[user_key]['expiry'])
            return datetime.now() < expiry_date
        return False

    async def get_vip_multiplier(self, guild_id, type_bonus="xp"):
        """Obtém multiplicador VIP para XP, economia, etc."""
        guild_id = str(guild_id)
        if guild_id in self.vip_config:
            multipliers = self.vip_config[guild_id].get('multipliers', {})
            return multipliers.get(type_bonus, 1.0)
        return 1.0

    @commands.command(name='vip')
    @commands.has_permissions(administrator=True)
    async def add_vip(self, ctx, member: discord.Member, dias: int):
        """Adiciona VIP a um usuário por X dias"""
        if dias <= 0:
            embed = discord.Embed(
                title="❌ Erro",
                description="O número de dias deve ser maior que 0!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Calcula data de expiração
        expiry_date = datetime.now() + timedelta(days=dias)
        user_key = f"{ctx.guild.id}_{member.id}"
        
        # Salva dados do VIP
        self.vip_data[user_key] = {
            'user_id': member.id,
            'guild_id': ctx.guild.id,
            'expiry': expiry_date.isoformat(),
            'added_by': ctx.author.id,
            'added_at': datetime.now().isoformat()
        }
        
        # Adiciona cargo VIP se configurado
        vip_role = await self.get_vip_role(ctx.guild)
        if vip_role:
            try:
                await member.add_roles(vip_role)
            except discord.Forbidden:
                pass

        self.save_vip_data()

        embed = discord.Embed(
            title="✅ VIP Adicionado",
            description=f"{member.mention} agora é VIP por **{dias} dias**!",
            color=discord.Color.gold()
        )
        embed.add_field(name="Expira em", value=expiry_date.strftime("%d/%m/%Y às %H:%M"), inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)

    @commands.command(name='removervip')
    @commands.has_permissions(administrator=True)
    async def remove_vip(self, ctx, member: discord.Member):
        """Remove VIP de um usuário"""
        user_key = f"{ctx.guild.id}_{member.id}"
        
        if user_key not in self.vip_data:
            embed = discord.Embed(
                title="❌ Erro",
                description=f"{member.mention} não é VIP!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Remove dados do VIP
        del self.vip_data[user_key]
        
        # Remove cargo VIP se configurado
        vip_role = await self.get_vip_role(ctx.guild)
        if vip_role and vip_role in member.roles:
            try:
                await member.remove_roles(vip_role)
            except discord.Forbidden:
                pass

        self.save_vip_data()

        embed = discord.Embed(
            title="✅ VIP Removido",
            description=f"VIP removido de {member.mention}!",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='cargovip')
    @commands.has_permissions(administrator=True)
    async def set_vip_role(self, ctx, role_id: int):
        """Define o cargo VIP do servidor"""
        role = ctx.guild.get_role(role_id)
        
        if not role:
            embed = discord.Embed(
                title="❌ Erro",
                description="Cargo não encontrado! Verifique o ID.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        guild_id = str(ctx.guild.id)
        if guild_id not in self.vip_config:
            self.vip_config[guild_id] = {}
        
        self.vip_config[guild_id]['vip_role_id'] = role_id
        self.save_vip_config()

        embed = discord.Embed(
            title="✅ Cargo VIP Definido",
            description=f"Cargo VIP definido como: {role.mention}",
            color=discord.Color.gold()
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='configvip')
    @commands.has_permissions(administrator=True)
    async def config_vip(self, ctx):
        """Configura multiplicadores e vantagens VIP"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.vip_config:
            self.vip_config[guild_id] = {
                'multipliers': {
                    'xp': 2.0,
                    'coins': 1.5,
                    'daily': 2.0
                }
            }
        
        config = self.vip_config[guild_id]
        vip_role = await self.get_vip_role(ctx.guild)
        
        embed = discord.Embed(
            title="⚙️ Configurações VIP",
            description="Configurações atuais do sistema VIP",
            color=discord.Color.gold()
        )
        
        # Cargo VIP
        role_text = vip_role.mention if vip_role else "❌ Não configurado"
        embed.add_field(name="🎭 Cargo VIP", value=role_text, inline=False)
        
        # Multiplicadores
        multipliers = config.get('multipliers', {})
        xp_mult = multipliers.get('xp', 1.0)
        coins_mult = multipliers.get('coins', 1.0)
        daily_mult = multipliers.get('daily', 1.0)
        
        embed.add_field(
            name="📈 Multiplicadores",
            value=f"**XP:** {xp_mult}x\n**Moedas:** {coins_mult}x\n**Daily:** {daily_mult}x",
            inline=True
        )
        
        # VIPs ativos
        active_vips = 0
        for key, data in self.vip_data.items():
            if str(data['guild_id']) == guild_id:
                expiry = datetime.fromisoformat(data['expiry'])
                if datetime.now() < expiry:
                    active_vips += 1
        
        embed.add_field(name="👑 VIPs Ativos", value=str(active_vips), inline=True)
        
        # Como usar
        embed.add_field(
            name="📝 Como configurar",
            value="Use `!cargovip <ID>` para definir o cargo VIP\n"
                  "Use `!vip @user <dias>` para dar VIP\n"
                  "Use `!removervip @user` para remover VIP",
            inline=False
        )
        
        self.save_vip_config()
        await ctx.send(embed=embed)

    @commands.command(name='listvip')
    @commands.has_permissions(administrator=True)
    async def list_vip(self, ctx):
        """Lista todos os VIPs ativos do servidor"""
        guild_id = str(ctx.guild.id)
        active_vips = []
        
        for key, data in self.vip_data.items():
            if str(data['guild_id']) == guild_id:
                expiry = datetime.fromisoformat(data['expiry'])
                if datetime.now() < expiry:
                    user = self.bot.get_user(data['user_id'])
                    if user:
                        days_left = (expiry - datetime.now()).days
                        active_vips.append(f"{user.mention} - **{days_left} dias**")
        
        if not active_vips:
            embed = discord.Embed(
                title="👑 Lista VIP",
                description="Nenhum VIP ativo no servidor.",
                color=discord.Color.gold()
            )
        else:
            vip_list = "\n".join(active_vips[:10])  # Máximo 10 por página
            embed = discord.Embed(
                title="👑 Lista VIP",
                description=vip_list,
                color=discord.Color.gold()
            )
            
            if len(active_vips) > 10:
                embed.set_footer(text=f"Mostrando 10 de {len(active_vips)} VIPs")
        
        await ctx.send(embed=embed)

    @commands.command(name='checkvip')
    async def check_vip(self, ctx, member: discord.Member = None):
        """Verifica status VIP de um usuário"""
        if not member:
            member = ctx.author
            
        user_key = f"{ctx.guild.id}_{member.id}"
        
        if user_key in self.vip_data:
            expiry = datetime.fromisoformat(self.vip_data[user_key]['expiry'])
            if datetime.now() < expiry:
                days_left = (expiry - datetime.now()).days
                hours_left = (expiry - datetime.now()).seconds // 3600
                
                embed = discord.Embed(
                    title="👑 Status VIP",
                    description=f"{member.mention} é **VIP**!",
                    color=discord.Color.gold()
                )
                embed.add_field(name="Expira em", value=f"{days_left} dias e {hours_left} horas", inline=True)
                embed.add_field(name="Data de expiração", value=expiry.strftime("%d/%m/%Y às %H:%M"), inline=True)
                embed.set_thumbnail(url=member.display_avatar.url)
            else:
                embed = discord.Embed(
                    title="❌ Status VIP",
                    description=f"{member.mention} não é VIP.",
                    color=discord.Color.red()
                )
        else:
            embed = discord.Embed(
                title="❌ Status VIP",
                description=f"{member.mention} não é VIP.",
                color=discord.Color.red()
            )
        
        await ctx.send(embed=embed)

    @tasks.loop(hours=1)
    async def check_vip_expiry(self):
        """Verifica VIPs expirados a cada hora"""
        expired_keys = []
        
        for key, data in self.vip_data.items():
            expiry = datetime.fromisoformat(data['expiry'])
            if datetime.now() >= expiry:
                expired_keys.append(key)
                
                # Remove cargo VIP se possível
                try:
                    guild = self.bot.get_guild(data['guild_id'])
                    if guild:
                        member = guild.get_member(data['user_id'])
                        vip_role = await self.get_vip_role(guild)
                        
                        if member and vip_role and vip_role in member.roles:
                            await member.remove_roles(vip_role)
                except:
                    pass  # Ignora erros de permissão
        
        # Remove VIPs expirados
        for key in expired_keys:
            del self.vip_data[key]
        
        if expired_keys:
            self.save_vip_data()

    @check_vip_expiry.before_loop
    async def before_check_vip_expiry(self):
        await self.bot.wait_until_ready()

    # Métodos auxiliares para outros sistemas usarem
    async def apply_vip_bonus_xp(self, user_id, guild_id, base_xp):
        """Aplica bônus VIP no XP"""
        if await self.is_vip(user_id, guild_id):
            multiplier = await self.get_vip_multiplier(guild_id, "xp")
            return int(base_xp * multiplier)
        return base_xp

    async def apply_vip_bonus_coins(self, user_id, guild_id, base_coins):
        """Aplica bônus VIP nas moedas"""
        if await self.is_vip(user_id, guild_id):
            multiplier = await self.get_vip_multiplier(guild_id, "coins")
            return int(base_coins * multiplier)
        return base_coins

    async def apply_vip_bonus_daily(self, user_id, guild_id, base_daily):
        """Aplica bônus VIP no daily"""
        if await self.is_vip(user_id, guild_id):
            multiplier = await self.get_vip_multiplier(guild_id, "daily")
            return int(base_daily * multiplier)
        return base_daily

    # Error handlers
    @add_vip.error
    @remove_vip.error
    @set_vip_role.error
    @config_vip.error
    async def vip_error_handler(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa ser **Administrador** para usar este comando!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(
                title="❌ Erro",
                description="Usuário não encontrado!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ Erro",
                description="Argumentos inválidos! Verifique o comando.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(VIPSystem(bot))