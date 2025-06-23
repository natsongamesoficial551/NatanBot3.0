import discord
from discord.ext import commands
import os
from datetime import datetime, timedelta
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

class Aniversario(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = None
        self.db = None
        self.collection = None
        self._connection_ready = False
        # Inicializa a conexão com MongoDB
        self.bot.loop.create_task(self.init_database())

    async def init_database(self):
        """Inicializa a conexão com MongoDB"""
        try:
            # URL de conexão do MongoDB (vem de variável de ambiente)
            mongo_uri = os.getenv("MONGO_URI")
            
            if not mongo_uri:
                print("❌ MONGO_URI não encontrada nas variáveis de ambiente!")
                return
            
            print("🔄 Conectando ao MongoDB (Aniversários)...")
            self.client = AsyncIOMotorClient(mongo_uri)
            
            # Testa a conexão
            await self.client.admin.command('ping')
            
            self.db = self.client['discord_bot']
            self.collection = self.db['aniversarios']
            self._connection_ready = True
            
            print("✅ Conectado ao MongoDB (Aniversários) com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao conectar com MongoDB (Aniversários): {e}")
            self._connection_ready = False

    async def ensure_connection(self):
        """Garante que a conexão com MongoDB está ativa"""
        if not self._connection_ready:
            await self.init_database()
        return self._connection_ready

    async def save_birthday(self, user_id, name, date, day, month):
        """Salva aniversário no MongoDB"""
        try:
            if not await self.ensure_connection():
                return False
                
            await self.collection.update_one(
                {'user_id': user_id},
                {
                    '$set': {
                        'user_id': user_id,
                        'name': name,
                        'date': date,
                        'day': day,
                        'month': month
                    }
                },
                upsert=True
            )
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar aniversário: {e}")
            return False

    async def get_birthday(self, user_id):
        """Busca aniversário específico no MongoDB"""
        try:
            if not await self.ensure_connection():
                return None
            return await self.collection.find_one({'user_id': user_id})
        except Exception as e:
            print(f"❌ Erro ao buscar aniversário: {e}")
            return None

    async def get_all_birthdays(self):
        """Busca todos os aniversários no MongoDB"""
        try:
            if not await self.ensure_connection():
                return []
            cursor = self.collection.find({})
            return await cursor.to_list(length=None)
        except Exception as e:
            print(f"❌ Erro ao buscar aniversários: {e}")
            return []

    async def delete_birthday(self, user_id):
        """Remove aniversário do MongoDB"""
        try:
            if not await self.ensure_connection():
                return False
            result = await self.collection.delete_one({'user_id': user_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"❌ Erro ao deletar aniversário: {e}")
            return False

    @commands.command(name='adicionardata', aliases=['addbd'])
    async def adicionar_aniversario(self, ctx, data: str, *, membro: discord.Member = None):
        """Adiciona uma data de aniversário. Formato: DD/MM"""
        if membro is None:
            membro = ctx.author
        
        try:
            # Valida formato DD/MM
            day, month = map(int, data.split('/'))
            if not (1 <= day <= 31) or not (1 <= month <= 12):
                raise ValueError
            
            user_id = str(membro.id)
            success = await self.save_birthday(user_id, membro.display_name, data, day, month)
            
            if success:
                embed = discord.Embed(
                    title="🎂 Aniversário Adicionado",
                    description=f"Data de aniversário de **{membro.display_name}** salva: {data}",
                    color=0x00ff7f
                )
            else:
                embed = discord.Embed(
                    title="❌ Erro de Conexão",
                    description="Não foi possível salvar. Verifique a conexão com o banco de dados.",
                    color=0xff4444
                )
            await ctx.send(embed=embed)
            
        except (ValueError, IndexError):
            embed = discord.Embed(
                title="❌ Formato Inválido",
                description="Use o formato **DD/MM** (ex: 15/03)",
                color=0xff4444
            )
            await ctx.send(embed=embed)

    @commands.command(name='aniversariantes', aliases=['bds'])
    async def listar_aniversariantes(self, ctx):
        """Lista todos os aniversariantes do servidor"""
        birthdays = await self.get_all_birthdays()
        
        if not birthdays:
            embed = discord.Embed(
                title="📅 Aniversariantes",
                description="Nenhum aniversário cadastrado ainda.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        # Ordena por mês e dia
        sorted_birthdays = sorted(
            birthdays,
            key=lambda x: (x['month'], x['day'])
        )
        
        description = ""
        for data in sorted_birthdays:
            member = ctx.guild.get_member(int(data['user_id']))
            if member:  # Só mostra se o membro ainda está no servidor
                description += f"🎉 **{data['name']}** - {data['date']}\n"
        
        embed = discord.Embed(
            title="🎂 Lista de Aniversariantes",
            description=description if description else "Nenhum membro encontrado.",
            color=0x9966ff
        )
        await ctx.send(embed=embed)

    @commands.command(name='meuaniversario', aliases=['mybd'])
    async def meu_aniversario(self, ctx):
        """Mostra seu aniversário cadastrado"""
        user_id = str(ctx.author.id)
        birthday = await self.get_birthday(user_id)
        
        if birthday:
            data = birthday['date']
            embed = discord.Embed(
                title="🎂 Seu Aniversário",
                description=f"Sua data cadastrada: **{data}**",
                color=0x00aaff
            )
        else:
            embed = discord.Embed(
                title="❓ Aniversário Não Encontrado",
                description="Use `!adicionardata DD/MM` para cadastrar seu aniversário",
                color=0xffaa00
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='removeraniversario', aliases=['rmbd'])
    async def remover_aniversario(self, ctx, *, membro: discord.Member = None):
        """Remove um aniversário (próprio ou de outro membro se for admin)"""
        if membro is None:
            membro = ctx.author
        elif membro != ctx.author and not ctx.author.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Apenas administradores podem remover aniversários de outros membros.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        user_id = str(membro.id)
        removed = await self.delete_birthday(user_id)
        
        if removed:
            embed = discord.Embed(
                title="🗑️ Aniversário Removido",
                description=f"Aniversário de **{membro.display_name}** foi removido.",
                color=0xff6666
            )
        else:
            embed = discord.Embed(
                title="❓ Não Encontrado",
                description=f"**{membro.display_name}** não tem aniversário cadastrado.",
                color=0xffaa00
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='proximosaniversarios', aliases=['nextbds'])
    async def proximos_aniversarios(self, ctx):
        """Mostra os próximos aniversários (próximos 30 dias)"""
        birthdays = await self.get_all_birthdays()
        
        if not birthdays:
            embed = discord.Embed(
                title="📅 Próximos Aniversários",
                description="Nenhum aniversário cadastrado.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        hoje = datetime.now()
        proximos = []
        
        for data in birthdays:
            # Calcula próximo aniversário
            try:
                aniversario = datetime(hoje.year, data['month'], data['day'])
                if aniversario < hoje:
                    aniversario = datetime(hoje.year + 1, data['month'], data['day'])
                
                dias_restantes = (aniversario - hoje).days
                if dias_restantes <= 30:
                    member = ctx.guild.get_member(int(data['user_id']))
                    if member:
                        proximos.append((dias_restantes, data['name'], data['date']))
            except ValueError:
                continue  # Data inválida (ex: 29/02 em ano não bissexto)
        
        if not proximos:
            embed = discord.Embed(
                title="📅 Próximos Aniversários",
                description="Nenhum aniversário nos próximos 30 dias.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        # Ordena por dias restantes
        proximos.sort(key=lambda x: x[0])
        
        description = ""
        for dias, nome, data in proximos:
            if dias == 0:
                description += f"🎉 **{nome}** - HOJE! ({data})\n"
            else:
                description += f"🎂 **{nome}** - em {dias} dias ({data})\n"
        
        embed = discord.Embed(
            title="📅 Próximos Aniversários (30 dias)",
            description=description,
            color=0x00ff7f
        )
        await ctx.send(embed=embed)

    async def cog_unload(self):
        """Fecha a conexão com MongoDB quando o cog é descarregado"""
        if self.client:
            self.client.close()
            print("🔌 Conexão com MongoDB (Aniversários) fechada")

async def setup(bot):
    await bot.add_cog(Aniversario(bot))