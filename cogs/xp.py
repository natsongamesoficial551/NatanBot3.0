import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta
import math
import random
import os
from motor.motor_asyncio import AsyncIOMotorClient

class XPSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_cooldowns = {}
        
        # Configuração do MongoDB usando variável de ambiente
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        self.mongo_client = AsyncIOMotorClient(mongo_uri)
        self.db = self.mongo_client['discord_bot']
        self.xp_collection = self.db['xp_data']
        self.config_collection = self.db['xp_config']
        
        # Verificar conexão no startup
        self.bot.loop.create_task(self.test_db_connection())

    async def test_db_connection(self):
        """Testa a conexão com o banco de dados"""
        try:
            # Tenta fazer uma operação simples para verificar a conexão
            await self.mongo_client.admin.command('ping')
            print("✅ Conexão com MongoDB estabelecida com sucesso!")
            
            # Lista as coleções existentes
            collections = await self.db.list_collection_names()
            print(f"📊 Coleções encontradas: {collections}")
            
        except Exception as e:
            print(f"❌ Erro ao conectar com MongoDB: {e}")

    async def get_guild_config(self, guild_id):
        """Obtém configuração da guild"""
        guild_id = str(guild_id)
        try:
            config = await self.config_collection.find_one({'guild_id': guild_id})
            
            if not config:
                default_config = {
                    'guild_id': guild_id,
                    'base_xp': 15,
                    'xp_per_message': 25,
                    'xp_per_level': 100,
                    'cooldown': 60,
                    'vip_cooldown': 30,
                    'vip_multiplier': 2.0,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                await self.config_collection.insert_one(default_config)
                print(f"🆕 Configuração padrão criada para guild {guild_id}")
                return default_config
            
            return config
            
        except Exception as e:
            print(f"❌ Erro ao buscar config da guild {guild_id}: {e}")
            # Retorna config padrão em caso de erro
            return {
                'guild_id': guild_id,
                'base_xp': 15,
                'xp_per_message': 25,
                'xp_per_level': 100,
                'cooldown': 60,
                'vip_cooldown': 30,
                'vip_multiplier': 2.0
            }

    async def save_guild_config(self, guild_id, config):
        """Salva configuração da guild"""
        guild_id = str(guild_id)
        try:
            config['updated_at'] = datetime.now().isoformat()
            result = await self.config_collection.update_one(
                {'guild_id': guild_id},
                {'$set': config},
                upsert=True
            )
            
            if result.upserted_id:
                print(f"🆕 Nova configuração criada para guild {guild_id}")
            elif result.modified_count > 0:
                print(f"✏️ Configuração atualizada para guild {guild_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar config da guild {guild_id}: {e}")
            return False

    async def get_user_data(self, user_id, guild_id):
        """Obtém dados do usuário"""
        user_key = f"{guild_id}_{user_id}"
        try:
            user_data = await self.xp_collection.find_one({'user_key': user_key})
            
            if not user_data:
                default_data = {
                    'user_key': user_key,
                    'user_id': str(user_id),
                    'guild_id': str(guild_id),
                    'xp': 0,
                    'level': 1,
                    'messages': 0,
                    'last_message': None,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                await self.xp_collection.insert_one(default_data)
                print(f"🆕 Dados de XP criados para usuário {user_id} na guild {guild_id}")
                return default_data
            
            return user_data
            
        except Exception as e:
            print(f"❌ Erro ao buscar dados do usuário {user_id}: {e}")
            # Retorna dados padrão em caso de erro
            return {
                'user_key': user_key,
                'user_id': str(user_id),
                'guild_id': str(guild_id),
                'xp': 0,
                'level': 1,
                'messages': 0,
                'last_message': None
            }

    async def save_user_data(self, user_id, guild_id, data):
        """Salva dados do usuário"""
        user_key = f"{guild_id}_{user_id}"
        try:
            data['updated_at'] = datetime.now().isoformat()
            result = await self.xp_collection.update_one(
                {'user_key': user_key},
                {'$set': data},
                upsert=True
            )
            
            if result.upserted_id:
                print(f"🆕 Novos dados de XP criados para usuário {user_id}")
            elif result.modified_count > 0:
                print(f"✏️ Dados de XP atualizados para usuário {user_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar dados do usuário {user_id}: {e}")
            return False

    def calculate_level(self, xp, xp_per_level):
        """Calcula o nível baseado no XP"""
        return int(math.sqrt(xp / xp_per_level)) + 1

    def calculate_xp_for_level(self, level, xp_per_level):
        """Calcula XP necessário para um nível específico"""
        return ((level - 1) ** 2) * xp_per_level

    async def is_user_vip(self, user_id, guild_id):
        """Verifica se o usuário é VIP"""
        vip_cog = self.bot.get_cog('VIPSystem')
        if vip_cog:
            return await vip_cog.is_vip(user_id, guild_id)
        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        """Processa mensagens para dar XP"""
        if message.author.bot or not message.guild:
            return

        user_id = message.author.id
        guild_id = message.guild.id
        config = await self.get_guild_config(guild_id)
        
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
        user_data = await self.get_user_data(user_id, guild_id)
        old_level = user_data['level']
        user_data['xp'] += base_xp
        user_data['messages'] += 1
        user_data['last_message'] = now.isoformat()
        
        new_level = self.calculate_level(user_data['xp'], config['xp_per_level'])
        user_data['level'] = new_level
        
        # Salvar no banco
        success = await self.save_user_data(user_id, guild_id, user_data)
        
        if not success:
            print(f"⚠️ Falha ao salvar XP para usuário {user_id}")
            return
        
        # Verificar level up
        if new_level > old_level:
            embed = discord.Embed(
                title="🎉 Level Up!",
                description=f"{message.author.mention} subiu para o **Level {new_level}**!",
                color=discord.Color.gold()
            )
            embed.add_field(name="XP Total", value=f"{user_data['xp']:,}", inline=True)
            embed.add_field(name="XP Ganho", value=f"+{base_xp}", inline=True)
            embed.set_thumbnail(url=message.author.display_avatar.url)
            
            if is_vip:
                embed.add_field(name="👑 VIP Bonus", value="XP em dobro!", inline=True)
            
            await message.channel.send(embed=embed)

    @commands.command(name='xp')
    async def check_xp(self, ctx, member: discord.Member = None):
        """Mostra XP do usuário"""
        if not member:
            member = ctx.author
            
        user_data = await self.get_user_data(member.id, ctx.guild.id)
        config = await self.get_guild_config(ctx.guild.id)
        
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
        
        # Informações de banco de dados
        if user_data.get('updated_at'):
            embed.set_footer(text=f"Última atualização: {user_data['updated_at'][:19]}")
        
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name='topxp')
    async def leaderboard_xp(self, ctx, page: int = 1):
        """Mostra ranking de XP"""
        try:
            # Buscar todos os usuários do guild ordenados por XP
            guild_users_cursor = self.xp_collection.find(
                {'guild_id': str(ctx.guild.id)}
            ).sort('xp', -1)
            
            guild_users_data = await guild_users_cursor.to_list(length=None)
            
            # Filtrar apenas membros que ainda estão no servidor
            guild_users = []
            for data in guild_users_data:
                user_id = int(data['user_id'])
                user = ctx.guild.get_member(user_id)
                if user:
                    guild_users.append((user, data))
            
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
            embed.set_footer(text=f"👑 = VIP | Página {page}/{max_pages} | Total: {len(guild_users)} usuários")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Erro no comando topxp: {e}")
            embed = discord.Embed(
                title="❌ Erro",
                description="Erro ao buscar ranking de XP. Tente novamente.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name='testdb3')
    @commands.has_permissions(administrator=True)
    async def test_database(self, ctx):
        """Testa a conexão e operações do banco de dados"""
        embed = discord.Embed(
            title="🔧 Teste do Banco de Dados",
            description="Testando conexão e operações...",
            color=discord.Color.blue()
        )
        
        try:
            # Teste 1: Ping no banco
            start_time = datetime.now()
            await self.mongo_client.admin.command('ping')
            ping_time = (datetime.now() - start_time).total_seconds() * 1000
            
            embed.add_field(
                name="✅ Conexão",
                value=f"Ping: {ping_time:.2f}ms",
                inline=True
            )
            
            # Teste 2: Contar documentos
            user_count = await self.xp_collection.count_documents({'guild_id': str(ctx.guild.id)})
            config_count = await self.config_collection.count_documents({'guild_id': str(ctx.guild.id)})
            
            embed.add_field(
                name="📊 Documentos",
                value=f"Usuários: {user_count}\nConfigs: {config_count}",
                inline=True
            )
            
            # Teste 3: Operação de escrita/leitura
            test_data = {
                'test_key': f"test_{ctx.guild.id}_{datetime.now().timestamp()}",
                'guild_id': str(ctx.guild.id),
                'test_value': 'Database test successful',
                'timestamp': datetime.now().isoformat()
            }
            
            # Inserir
            result = await self.db.test_collection.insert_one(test_data)
            
            # Ler
            retrieved = await self.db.test_collection.find_one({'_id': result.inserted_id})
            
            # Deletar
            await self.db.test_collection.delete_one({'_id': result.inserted_id})
            
            if retrieved and retrieved['test_value'] == test_data['test_value']:
                embed.add_field(
                    name="✅ Operações",
                    value="Insert/Read/Delete OK",
                    inline=True
                )
            else:
                embed.add_field(
                    name="❌ Operações",
                    value="Falha no teste",
                    inline=True
                )
            
            # Teste 4: Informações do servidor
            server_info = await self.mongo_client.admin.command('serverStatus')
            version = server_info.get('version', 'Unknown')
            uptime = server_info.get('uptime', 0)
            
            embed.add_field(
                name="🖥️ Servidor",
                value=f"MongoDB {version}\nUptime: {uptime}s",
                inline=True
            )
            
            # Teste 5: Stats das coleções
            xp_stats = await self.db.command('collStats', 'xp_data')
            config_stats = await self.db.command('collStats', 'xp_config')
            
            embed.add_field(
                name="📈 Estatísticas",
                value=f"XP Collection: {xp_stats.get('size', 0)} bytes\nConfig Collection: {config_stats.get('size', 0)} bytes",
                inline=True
            )
            
            embed.color = discord.Color.green()
            embed.set_footer(text=f"Teste realizado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            
        except Exception as e:
            embed.add_field(
                name="❌ Erro",
                value=f"```{str(e)[:100]}```",
                inline=False
            )
            embed.color = discord.Color.red()
            print(f"❌ Erro no teste do banco: {e}")
        
        await ctx.send(embed=embed)

    @commands.command(name='mensagemporxp')
    @commands.has_permissions(administrator=True)
    async def set_xp_per_message(self, ctx, min_xp: int, max_xp: int):
        """Configura XP mínimo e máximo por mensagem"""
        if min_xp <= 0 or max_xp <= 0 or min_xp > max_xp:
            embed = discord.Embed(
                title="❌ Erro",
                description="Valores inválidos! Min deve ser menor que Max e ambos positivos.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        config = await self.get_guild_config(ctx.guild.id)
        config['base_xp'] = min_xp
        config['xp_per_message'] = max_xp
        success = await self.save_guild_config(ctx.guild.id, config)
        
        if success:
            embed = discord.Embed(
                title="✅ XP por Mensagem Configurado",
                description=f"XP por mensagem: **{min_xp} - {max_xp}**",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Falha ao salvar configuração no banco de dados.",
                color=discord.Color.red()
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='adicionarxppornivel')
    @commands.has_permissions(administrator=True)
    async def set_xp_per_level(self, ctx, xp_per_level: int):
        """Configura XP necessário por nível"""
        if xp_per_level <= 0:
            embed = discord.Embed(
                title="❌ Erro",
                description="XP por nível deve ser maior que 0!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        config = await self.get_guild_config(ctx.guild.id)
        config['xp_per_level'] = xp_per_level
        success = await self.save_guild_config(ctx.guild.id, config)
        
        if success:
            embed = discord.Embed(
                title="✅ XP por Nível Configurado",
                description=f"XP necessário por nível: **{xp_per_level:,}**",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Falha ao salvar configuração no banco de dados.",
                color=discord.Color.red()
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='tempodexp')
    @commands.has_permissions(administrator=True)
    async def set_xp_cooldown(self, ctx, normal_cooldown: int, vip_cooldown: int = None):
        """Configura cooldown de XP"""
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
        
        config = await self.get_guild_config(ctx.guild.id)
        config['cooldown'] = normal_cooldown
        config['vip_cooldown'] = vip_cooldown
        success = await self.save_guild_config(ctx.guild.id, config)
        
        if success:
            embed = discord.Embed(
                title="✅ Cooldown de XP Configurado",
                description=f"Cooldown normal: **{normal_cooldown}s**\nCooldown VIP: **{vip_cooldown}s**",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Falha ao salvar configuração no banco de dados.",
                color=discord.Color.red()
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='configxp')
    @commands.has_permissions(administrator=True)
    async def config_xp(self, ctx):
        """Mostra configurações atuais do sistema XP"""
        config = await self.get_guild_config(ctx.guild.id)
        
        # Contar usuários ativos
        try:
            active_users = await self.xp_collection.count_documents({'guild_id': str(ctx.guild.id)})
        except:
            active_users = 0
        
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
            name="🗃️ Banco de Dados",
            value=f"Guild ID: {config['guild_id']}\nÚltima atualização: {config.get('updated_at', 'N/A')[:19]}",
            inline=True
        )
        
        embed.add_field(
            name="📝 Comandos Admin",
            value="`!mensagemporxp <min> <max>`\n`!adicionarxppornivel <valor>`\n`!tempodexp <normal> [vip]`\n`!testdb3` - Testar banco",
            inline=False
        )
        
        await ctx.send(embed=embed)

    # Error handlers
    @set_xp_per_message.error
    @set_xp_per_level.error
    @set_xp_cooldown.error
    @config_xp.error
    @test_database.error
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
        else:
            print(f"❌ Erro no comando XP: {error}")
            embed = discord.Embed(
                title="❌ Erro Interno",
                description="Ocorreu um erro interno. Verifique os logs.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    async def cog_unload(self):
        """Cleanup quando o cog é descarregado"""
        if hasattr(self, 'mongo_client'):
            self.mongo_client.close()
            print("🔌 Conexão MongoDB fechada")

async def setup(bot):
    await bot.add_cog(XPSystem(bot))