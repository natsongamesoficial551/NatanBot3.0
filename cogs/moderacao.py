import discord
from discord.ext import commands, tasks
import json
import asyncio
from datetime import datetime, timedelta
import os

class ModerationSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mod_file = "moderation_data.json"
        self.mod_config_file = "mod_config.json"
        self.mod_data = self.load_mod_data()
        self.mod_config = self.load_mod_config()
        self.check_mutes.start()

    def load_mod_data(self):
        if os.path.exists(self.mod_file):
            try:
                with open(self.mod_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_mod_data(self):
        with open(self.mod_file, 'w', encoding='utf-8') as f:
            json.dump(self.mod_data, f, indent=2, ensure_ascii=False)

    def load_mod_config(self):
        if os.path.exists(self.mod_config_file):
            try:
                with open(self.mod_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_mod_config(self):
        with open(self.mod_config_file, 'w', encoding='utf-8') as f:
            json.dump(self.mod_config, f, indent=2, ensure_ascii=False)

    def get_guild_data(self, guild_id):
        guild_id = str(guild_id)
        if guild_id not in self.mod_data:
            self.mod_data[guild_id] = {
                'warnings': {},
                'mutes': {},
                'logs': []
            }
        return self.mod_data[guild_id]

    def get_guild_config(self, guild_id):
        guild_id = str(guild_id)
        if guild_id not in self.mod_config:
            self.mod_config[guild_id] = {
                'mute_role_id': None,
                'log_channel_id': None,
                'max_warnings': 3,
                'auto_punish': True
            }
            self.save_mod_config()
        return self.mod_config[guild_id]

    async def log_action(self, guild, action, moderator, target, reason=None, duration=None):
        config = self.get_guild_config(guild.id)
        guild_data = self.get_guild_data(guild.id)
        
        log_entry = {
            'action': action,
            'moderator_id': moderator.id,
            'target_id': target.id,
            'reason': reason,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        
        guild_data['logs'].append(log_entry)
        self.save_mod_data()
        
        # Enviar para canal de logs se configurado
        if config['log_channel_id']:
            channel = guild.get_channel(config['log_channel_id'])
            if channel:
                embed = discord.Embed(
                    title=f"🔨 {action.upper()}",
                    color=discord.Color.orange()
                )
                embed.add_field(name="Moderador", value=moderator.mention, inline=True)
                embed.add_field(name="Usuário", value=target.mention, inline=True)
                if reason:
                    embed.add_field(name="Motivo", value=reason, inline=False)
                if duration:
                    embed.add_field(name="Duração", value=duration, inline=True)
                embed.timestamp = datetime.now()
                
                try:
                    await channel.send(embed=embed)
                except:
                    pass

    @commands.command(name='aviso')
    @commands.has_permissions(administrator=True)
    async def warn_user(self, ctx, member: discord.Member, *, reason="Não especificado"):
        guild_data = self.get_guild_data(ctx.guild.id)
        config = self.get_guild_config(ctx.guild.id)
        
        user_id = str(member.id)
        if user_id not in guild_data['warnings']:
            guild_data['warnings'][user_id] = []
        
        warning = {
            'reason': reason,
            'moderator': ctx.author.id,
            'timestamp': datetime.now().isoformat()
        }
        
        guild_data['warnings'][user_id].append(warning)
        warning_count = len(guild_data['warnings'][user_id])
        self.save_mod_data()
        
        embed = discord.Embed(
            title="⚠️ Aviso Aplicado",
            description=f"{member.mention} recebeu um aviso!",
            color=discord.Color.yellow()
        )
        embed.add_field(name="Motivo", value=reason, inline=False)
        embed.add_field(name="Avisos Totais", value=f"{warning_count}/{config['max_warnings']}", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
        await self.log_action(ctx.guild, "warn", ctx.author, member, reason)
        
        # Auto punição
        if config['auto_punish'] and warning_count >= config['max_warnings']:
            try:
                mute_role = await self.get_mute_role(ctx.guild)
                if mute_role:
                    await member.add_roles(mute_role)
                    
                    mute_key = f"{ctx.guild.id}_{member.id}"
                    guild_data['mutes'][mute_key] = {
                        'expires': (datetime.now() + timedelta(hours=1)).isoformat(),
                        'reason': f"Auto-mute por {config['max_warnings']} avisos"
                    }
                    self.save_mod_data()
                    
                    embed = discord.Embed(
                        title="🔇 Auto-Mute Aplicado",
                        description=f"{member.mention} foi mutado por atingir {config['max_warnings']} avisos!",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
            except:
                pass

        # DM para o usuário
        try:
            dm_embed = discord.Embed(
                title="⚠️ Você recebeu um aviso",
                description=f"**Servidor:** {ctx.guild.name}\n**Motivo:** {reason}",
                color=discord.Color.yellow()
            )
            await member.send(embed=dm_embed)
        except:
            pass

    @commands.command(name='removeraviso')
    @commands.has_permissions(administrator=True)
    async def remove_warning(self, ctx, member: discord.Member, index: int = None):
        guild_data = self.get_guild_data(ctx.guild.id)
        user_id = str(member.id)
        
        if user_id not in guild_data['warnings'] or not guild_data['warnings'][user_id]:
            embed = discord.Embed(
                title="❌ Erro",
                description=f"{member.mention} não possui avisos!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if index is None:
            # Remove último aviso
            removed_warning = guild_data['warnings'][user_id].pop()
        else:
            # Remove aviso específico
            if index < 1 or index > len(guild_data['warnings'][user_id]):
                embed = discord.Embed(
                    title="❌ Erro",
                    description="Número do aviso inválido!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            removed_warning = guild_data['warnings'][user_id].pop(index - 1)
        
        self.save_mod_data()
        
        embed = discord.Embed(
            title="✅ Aviso Removido",
            description=f"Aviso removido de {member.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="Motivo Removido", value=removed_warning['reason'], inline=False)
        embed.add_field(name="Avisos Restantes", value=len(guild_data['warnings'][user_id]), inline=True)
        
        await ctx.send(embed=embed)
        await self.log_action(ctx.guild, "unwarn", ctx.author, member)

    @commands.command(name='avisos')
    @commands.has_permissions(administrator=True)
    async def list_warnings(self, ctx, member: discord.Member = None):
        guild_data = self.get_guild_data(ctx.guild.id)
        
        if member:
            # Avisos de um usuário específico
            user_id = str(member.id)
            if user_id not in guild_data['warnings'] or not guild_data['warnings'][user_id]:
                embed = discord.Embed(
                    title="📋 Avisos",
                    description=f"{member.mention} não possui avisos!",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"📋 Avisos de {member.display_name}",
                color=discord.Color.orange()
            )
            
            for i, warning in enumerate(guild_data['warnings'][user_id], 1):
                moderator = self.bot.get_user(warning['moderator'])
                mod_name = moderator.name if moderator else "Desconhecido"
                date = datetime.fromisoformat(warning['timestamp']).strftime("%d/%m/%Y %H:%M")
                
                embed.add_field(
                    name=f"Aviso #{i}",
                    value=f"**Motivo:** {warning['reason']}\n**Moderador:** {mod_name}\n**Data:** {date}",
                    inline=False
                )
            
            embed.set_thumbnail(url=member.display_avatar.url)
        else:
            # Todos os avisos do servidor
            all_warnings = []
            for user_id, warnings in guild_data['warnings'].items():
                if warnings:
                    user = ctx.guild.get_member(int(user_id))
                    if user:
                        all_warnings.append((user, len(warnings)))
            
            if not all_warnings:
                embed = discord.Embed(
                    title="📋 Avisos do Servidor",
                    description="Nenhum aviso encontrado!",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                return
            
            all_warnings.sort(key=lambda x: x[1], reverse=True)
            
            embed = discord.Embed(
                title="📋 Avisos do Servidor",
                color=discord.Color.orange()
            )
            
            warning_text = ""
            for user, count in all_warnings[:10]:
                warning_text += f"{user.mention}: **{count}** avisos\n"
            
            embed.description = warning_text
        
        await ctx.send(embed=embed)

    async def get_mute_role(self, guild):
        config = self.get_guild_config(guild.id)
        if config['mute_role_id']:
            return guild.get_role(config['mute_role_id'])
        
        # Criar cargo de mute se não existir
        mute_role = discord.utils.get(guild.roles, name="Mutado")
        if not mute_role:
            try:
                mute_role = await guild.create_role(
                    name="Mutado",
                    color=discord.Color.dark_gray(),
                    permissions=discord.Permissions(send_messages=False, speak=False)
                )
                
                # Configurar permissões em todos os canais
                for channel in guild.channels:
                    try:
                        await channel.set_permissions(mute_role, send_messages=False, speak=False)
                    except:
                        pass
                
                config['mute_role_id'] = mute_role.id
                self.save_mod_config()
            except:
                return None
        
        return mute_role

    @commands.command(name='mutar')
    @commands.has_permissions(administrator=True)
    async def mute_user(self, ctx, member: discord.Member, tempo="30m", *, reason="Não especificado"):
        mute_role = await self.get_mute_role(ctx.guild)
        if not mute_role:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível criar/encontrar o cargo de mute!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Converter tempo
        duration = self.parse_duration(tempo)
        if not duration:
            embed = discord.Embed(
                title="❌ Erro",
                description="Formato de tempo inválido! Use: 30s, 5m, 2h, 1d",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            await member.add_roles(mute_role)
            
            guild_data = self.get_guild_data(ctx.guild.id)
            mute_key = f"{ctx.guild.id}_{member.id}"
            guild_data['mutes'][mute_key] = {
                'expires': (datetime.now() + duration).isoformat(),
                'reason': reason
            }
            self.save_mod_data()
            
            embed = discord.Embed(
                title="🔇 Usuário Mutado",
                description=f"{member.mention} foi mutado!",
                color=discord.Color.red()
            )
            embed.add_field(name="Duração", value=tempo, inline=True)
            embed.add_field(name="Motivo", value=reason, inline=False)
            embed.set_thumbnail(url=member.display_avatar.url)
            
            await ctx.send(embed=embed)
            await self.log_action(ctx.guild, "mute", ctx.author, member, reason, tempo)
            
            # DM para o usuário
            try:
                dm_embed = discord.Embed(
                    title="🔇 Você foi mutado",
                    description=f"**Servidor:** {ctx.guild.name}\n**Duração:** {tempo}\n**Motivo:** {reason}",
                    color=discord.Color.red()
                )
                await member.send(embed=dm_embed)
            except:
                pass
                
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não tenho permissão para mutar este usuário!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name='desmutar')
    @commands.has_permissions(administrator=True)
    async def unmute_user(self, ctx, member: discord.Member):
        mute_role = await self.get_mute_role(ctx.guild)
        if not mute_role:
            embed = discord.Embed(
                title="❌ Erro",
                description="Cargo de mute não encontrado!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if mute_role not in member.roles:
            embed = discord.Embed(
                title="❌ Erro",
                description=f"{member.mention} não está mutado!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            await member.remove_roles(mute_role)
            
            guild_data = self.get_guild_data(ctx.guild.id)
            mute_key = f"{ctx.guild.id}_{member.id}"
            if mute_key in guild_data['mutes']:
                del guild_data['mutes'][mute_key]
                self.save_mod_data()
            
            embed = discord.Embed(
                title="🔊 Usuário Desmutado",
                description=f"{member.mention} foi desmutado!",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            
            await ctx.send(embed=embed)
            await self.log_action(ctx.guild, "unmute", ctx.author, member)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não tenho permissão para desmutar este usuário!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name='banir')
    @commands.has_permissions(administrator=True)
    async def ban_user(self, ctx, member: discord.Member, *, reason="Não especificado"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Erro",
                description="Você não pode banir este usuário!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # DM antes do ban
            try:
                dm_embed = discord.Embed(
                    title="🔨 Você foi banido",
                    description=f"**Servidor:** {ctx.guild.name}\n**Motivo:** {reason}",
                    color=discord.Color.red()
                )
                await member.send(embed=dm_embed)
            except:
                pass
            
            await member.ban(reason=reason)
            
            embed = discord.Embed(
                title="🔨 Usuário Banido",
                description=f"{member.mention} foi banido!",
                color=discord.Color.red()
            )
            embed.add_field(name="Motivo", value=reason, inline=False)
            embed.set_thumbnail(url=member.display_avatar.url)
            
            await ctx.send(embed=embed)
            await self.log_action(ctx.guild, "ban", ctx.author, member, reason)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não tenho permissão para banir este usuário!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name='expulsar')
    @commands.has_permissions(administrator=True)
    async def kick_user(self, ctx, member: discord.Member, *, reason="Não especificado"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Erro",
                description="Você não pode expulsar este usuário!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # DM antes do kick
            try:
                dm_embed = discord.Embed(
                    title="👢 Você foi expulso",
                    description=f"**Servidor:** {ctx.guild.name}\n**Motivo:** {reason}",
                    color=discord.Color.orange()
                )
                await member.send(embed=dm_embed)
            except:
                pass
            
            await member.kick(reason=reason)
            
            embed = discord.Embed(
                title="👢 Usuário Expulso",
                description=f"{member.mention} foi expulso!",
                color=discord.Color.orange()
            )
            embed.add_field(name="Motivo", value=reason, inline=False)
            embed.set_thumbnail(url=member.display_avatar.url)
            
            await ctx.send(embed=embed)
            await self.log_action(ctx.guild, "kick", ctx.author, member, reason)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não tenho permissão para expulsar este usuário!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name='limparmensagem', aliases=['clear', 'purge'])
    @commands.has_permissions(administrator=True)
    async def clear_messages(self, ctx, amount: int = 10):
        if amount <= 0 or amount > 100:
            embed = discord.Embed(
                title="❌ Erro",
                description="Quantidade deve ser entre 1 e 100!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 para incluir o comando
            
            embed = discord.Embed(
                title="🧹 Mensagens Limpas",
                description=f"**{len(deleted) - 1}** mensagens foram deletadas!",
                color=discord.Color.green()
            )
            
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await msg.delete()
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não tenho permissão para deletar mensagens!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name='configmod')
    @commands.has_permissions(administrator=True)
    async def config_moderation(self, ctx):
        config = self.get_guild_config(ctx.guild.id)
        guild_data = self.get_guild_data(ctx.guild.id)
        
        embed = discord.Embed(
            title="⚙️ Configurações de Moderação",
            color=discord.Color.blue()
        )
        
        # Cargo de mute
        mute_role = await self.get_mute_role(ctx.guild)
        mute_text = mute_role.mention if mute_role else "❌ Não configurado"
        embed.add_field(name="🔇 Cargo de Mute", value=mute_text, inline=True)
        
        # Canal de logs
        log_channel = ctx.guild.get_channel(config['log_channel_id']) if config['log_channel_id'] else None
        log_text = log_channel.mention if log_channel else "❌ Não configurado"
        embed.add_field(name="📋 Canal de Logs", value=log_text, inline=True)
        
        # Configurações
        embed.add_field(name="⚠️ Max Avisos", value=config['max_warnings'], inline=True)
        embed.add_field(name="🤖 Auto Punir", value="✅ Ativo" if config['auto_punish'] else "❌ Inativo", inline=True)
        
        # Estatísticas
        total_warnings = sum(len(warnings) for warnings in guild_data['warnings'].values())
        active_mutes = len(guild_data['mutes'])
        total_logs = len(guild_data['logs'])
        
        embed.add_field(name="📊 Avisos Totais", value=total_warnings, inline=True)
        embed.add_field(name="🔇 Mutes Ativos", value=active_mutes, inline=True)
        
        embed.add_field(
            name="📝 Comandos Disponíveis",
            value="`!aviso` `!removeraviso` `!avisos` `!mutar` `!desmutar` `!banir` `!expulsar` `!limparmensagem`",
            inline=False
        )
        
        await ctx.send(embed=embed)

    def parse_duration(self, duration_str):
        """Converte string de duração em timedelta"""
        try:
            unit = duration_str[-1].lower()
            value = int(duration_str[:-1])
            
            if unit == 's':
                return timedelta(seconds=value)
            elif unit == 'm':
                return timedelta(minutes=value)
            elif unit == 'h':
                return timedelta(hours=value)
            elif unit == 'd':
                return timedelta(days=value)
        except:
            pass
        return None

    @tasks.loop(minutes=1)
    async def check_mutes(self):
        """Verifica mutes expirados"""
        for guild in self.bot.guilds:
            guild_data = self.get_guild_data(guild.id)
            expired_mutes = []
            
            for mute_key, mute_data in guild_data['mutes'].items():
                expire_time = datetime.fromisoformat(mute_data['expires'])
                if datetime.now() >= expire_time:
                    expired_mutes.append(mute_key)
                    
                    # Remover cargo de mute
                    try:
                        user_id = int(mute_key.split('_')[1])
                        member = guild.get_member(user_id)
                        mute_role = await self.get_mute_role(guild)
                        
                        if member and mute_role and mute_role in member.roles:
                            await member.remove_roles(mute_role)
                    except:
                        pass
            
            # Remover mutes expirados
            for mute_key in expired_mutes:
                del guild_data['mutes'][mute_key]
            
            if expired_mutes:
                self.save_mod_data()

    @check_mutes.before_loop
    async def before_check_mutes(self):
        await self.bot.wait_until_ready()

    # Error handlers
    @warn_user.error
    @mute_user.error
    @ban_user.error
    @kick_user.error
    @clear_messages.error
    async def mod_error_handler(self, ctx, error):
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

async def setup(bot):
    await bot.add_cog(ModerationSystem(bot))