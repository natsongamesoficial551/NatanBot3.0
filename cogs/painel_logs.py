import discord
from discord.ext import commands
import json
import datetime
import os

class AdvancedLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "logs_config.json"
        self.load_config()
    
    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {}
    
    def save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get_log_channel(self, guild_id):
        return self.config.get(str(guild_id), {}).get('log_channel')
    
    async def send_log(self, guild, embed):
        channel_id = self.get_log_channel(guild.id)
        if channel_id:
            channel = guild.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(embed=embed)
                except:
                    pass
    
    @commands.command(name='canaldelogs')
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            self.config[guild_id] = {}
        self.config[guild_id]['log_channel'] = channel.id
        self.save_config()
        
        embed = discord.Embed(
            title="✅ Canal de Logs Configurado",
            description=f"Canal de logs definido para {channel.mention}",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )
        await ctx.send(embed=embed)
    
    # LOGS DE MENSAGENS
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild:
            return
        
        embed = discord.Embed(
            title="🗑️ Mensagem Deletada",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="Autor", value=f"{message.author} ({message.author.id})", inline=True)
        embed.add_field(name="Canal", value=message.channel.mention, inline=True)
        embed.add_field(name="Conteúdo", value=message.content[:1000] or "Sem conteúdo de texto", inline=False)
        if message.attachments:
            embed.add_field(name="Anexos", value=f"{len(message.attachments)} arquivo(s)", inline=True)
        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url if message.author.avatar else None)
        
        await self.send_log(message.guild, embed)
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or not before.guild or before.content == after.content:
            return
        
        embed = discord.Embed(
            title="✏️ Mensagem Editada",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="Autor", value=f"{before.author} ({before.author.id})", inline=True)
        embed.add_field(name="Canal", value=before.channel.mention, inline=True)
        embed.add_field(name="Antes", value=before.content[:500] or "Sem conteúdo", inline=False)
        embed.add_field(name="Depois", value=after.content[:500] or "Sem conteúdo", inline=False)
        embed.set_author(name=before.author.display_name, icon_url=before.author.avatar.url if before.author.avatar else None)
        
        await self.send_log(before.guild, embed)
    
    # LOGS DE MEMBROS
    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(
            title="📥 Membro Entrou",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="Membro", value=f"{member} ({member.id})", inline=True)
        embed.add_field(name="Conta Criada", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Total de Membros", value=member.guild.member_count, inline=True)
        embed.set_author(name=member.display_name, icon_url=member.avatar.url if member.avatar else None)
        
        await self.send_log(member.guild, embed)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        embed = discord.Embed(
            title="📤 Membro Saiu",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="Membro", value=f"{member} ({member.id})", inline=True)
        embed.add_field(name="Entrou em", value=f"<t:{int(member.joined_at.timestamp())}:R>" if member.joined_at else "Desconhecido", inline=True)
        embed.add_field(name="Total de Membros", value=member.guild.member_count, inline=True)
        if member.roles[1:]:
            roles = ", ".join([role.name for role in member.roles[1:]])
            embed.add_field(name="Cargos", value=roles[:1000], inline=False)
        embed.set_author(name=member.display_name, icon_url=member.avatar.url if member.avatar else None)
        
        await self.send_log(member.guild, embed)
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        embed = discord.Embed(
            title="🔨 Membro Banido",
            color=discord.Color.dark_red(),
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="Usuário", value=f"{user} ({user.id})", inline=True)
        embed.set_author(name=user.display_name, icon_url=user.avatar.url if user.avatar else None)
        
        # Tenta pegar o motivo do ban
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
                if entry.target.id == user.id:
                    embed.add_field(name="Moderador", value=entry.user, inline=True)
                    if entry.reason:
                        embed.add_field(name="Motivo", value=entry.reason, inline=False)
                    break
        except:
            pass
        
        await self.send_log(guild, embed)
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        embed = discord.Embed(
            title="🔓 Membro Desbanido",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="Usuário", value=f"{user} ({user.id})", inline=True)
        embed.set_author(name=user.display_name, icon_url=user.avatar.url if user.avatar else None)
        
        # Tenta pegar quem desbaniu
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.unban, limit=1):
                if entry.target.id == user.id:
                    embed.add_field(name="Moderador", value=entry.user, inline=True)
                    if entry.reason:
                        embed.add_field(name="Motivo", value=entry.reason, inline=False)
                    break
        except:
            pass
        
        await self.send_log(guild, embed)
    
    # LOGS DE CARGOS
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            
            if added_roles or removed_roles:
                embed = discord.Embed(
                    title="👑 Cargos Alterados",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                embed.add_field(name="Membro", value=f"{after} ({after.id})", inline=True)
                
                if added_roles:
                    embed.add_field(name="Cargos Adicionados", value=", ".join([role.mention for role in added_roles]), inline=False)
                if removed_roles:
                    embed.add_field(name="Cargos Removidos", value=", ".join([role.mention for role in removed_roles]), inline=False)
                
                embed.set_author(name=after.display_name, icon_url=after.avatar.url if after.avatar else None)
                await self.send_log(after.guild, embed)
        
        # Mudança de nickname
        if before.nick != after.nick:
            embed = discord.Embed(
                title="📝 Apelido Alterado",
                color=discord.Color.purple(),
                timestamp=datetime.datetime.now()
            )
            embed.add_field(name="Membro", value=f"{after} ({after.id})", inline=True)
            embed.add_field(name="Antes", value=before.nick or before.name, inline=True)
            embed.add_field(name="Depois", value=after.nick or after.name, inline=True)
            embed.set_author(name=after.display_name, icon_url=after.avatar.url if after.avatar else None)
            
            await self.send_log(after.guild, embed)
    
    # LOGS DE CANAIS
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        embed = discord.Embed(
            title="➕ Canal Criado",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="Canal", value=f"{channel.mention} ({channel.id})", inline=True)
        embed.add_field(name="Tipo", value=str(channel.type).title(), inline=True)
        if hasattr(channel, 'category') and channel.category:
            embed.add_field(name="Categoria", value=channel.category.name, inline=True)
        
        await self.send_log(channel.guild, embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        embed = discord.Embed(
            title="🗑️ Canal Deletado",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="Canal", value=f"#{channel.name} ({channel.id})", inline=True)
        embed.add_field(name="Tipo", value=str(channel.type).title(), inline=True)
        if hasattr(channel, 'category') and channel.category:
            embed.add_field(name="Categoria", value=channel.category.name, inline=True)
        
        await self.send_log(channel.guild, embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        changes = []
        
        if before.name != after.name:
            changes.append(f"**Nome:** {before.name} → {after.name}")
        if hasattr(before, 'topic') and before.topic != after.topic:
            changes.append(f"**Tópico:** {before.topic or 'Nenhum'} → {after.topic or 'Nenhum'}")
        if hasattr(before, 'category') and before.category != after.category:
            before_cat = before.category.name if before.category else "Sem categoria"
            after_cat = after.category.name if after.category else "Sem categoria"
            changes.append(f"**Categoria:** {before_cat} → {after_cat}")
        
        if changes:
            embed = discord.Embed(
                title="🔧 Canal Atualizado",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.now()
            )
            embed.add_field(name="Canal", value=after.mention, inline=True)
            embed.add_field(name="Alterações", value="\n".join(changes), inline=False)
            
            await self.send_log(after.guild, embed)
    
    # LOGS DE SERVIDOR
    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        changes = []
        
        if before.name != after.name:
            changes.append(f"**Nome:** {before.name} → {after.name}")
        if before.icon != after.icon:
            changes.append("**Ícone:** Alterado")
        if before.owner != after.owner:
            changes.append(f"**Dono:** {before.owner} → {after.owner}")
        
        if changes:
            embed = discord.Embed(
                title="🏠 Servidor Atualizado",
                color=discord.Color.gold(),
                timestamp=datetime.datetime.now()
            )
            embed.add_field(name="Alterações", value="\n".join(changes), inline=False)
            
            await self.send_log(after, embed)
    
    # LOGS DE CONVITES
    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        embed = discord.Embed(
            title="🔗 Convite Criado",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="Código", value=invite.code, inline=True)
        embed.add_field(name="Canal", value=invite.channel.mention, inline=True)
        embed.add_field(name="Criado por", value=invite.inviter, inline=True)
        embed.add_field(name="Usos Máximos", value=invite.max_uses or "Ilimitado", inline=True)
        embed.add_field(name="Expira em", value=f"<t:{int((datetime.datetime.now() + invite.max_age * datetime.timedelta(seconds=1)).timestamp())}:R>" if invite.max_age else "Nunca", inline=True)
        
        await self.send_log(invite.guild, embed)
    
    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        embed = discord.Embed(
            title="🗑️ Convite Deletado",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="Código", value=invite.code, inline=True)
        embed.add_field(name="Canal", value=invite.channel.mention, inline=True)
        
        await self.send_log(invite.guild, embed)

async def setup(bot):
    await bot.add_cog(AdvancedLogs(bot))