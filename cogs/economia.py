import discord
from discord.ext import commands
import asyncio
import random
from datetime import datetime, timedelta
import os
from motor.motor_asyncio import AsyncIOMotorClient

class Economia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = None
        self.db = None
        self.users_collection = None
        self.shop_collection = None
        self.vip_collection = None
        self._connection_ready = False
        # Inicializa a conexão com MongoDB
        self.bot.loop.create_task(self.init_database())
        
        # Configurações do sistema
        self.daily_reward = 1000
        self.work_cooldown = 3600  # 1 hora
        self.crime_cooldown = 7200  # 2 horas
        self.daily_cooldown = 86400  # 24 horas
        
        # Multiplicadores VIP
        self.vip_daily_multiplier = 2.0
        self.vip_work_multiplier = 1.5
        self.vip_crime_success_bonus = 15
        self.vip_rob_success_bonus = 20
        
        # Empregos disponíveis
        self.jobs = {
            "entregador": {"salary": (200, 800), "desc": "Entrega comidas pela cidade"},
            "caixa": {"salary": (300, 600), "desc": "Atende clientes no supermercado"},
            "empresario": {"salary": (800, 2000), "desc": "Gerencia uma empresa"},
            "programador": {"salary": (1000, 1500), "desc": "Desenvolve aplicações"},
            "medico": {"salary": (1500, 2500), "desc": "Cuida da saúde das pessoas"}
        }
        
        # Crimes disponíveis
        self.crimes = {
            "roubar_loja": {"min": 100, "max": 1000, "success": 60},
            "hackear_banco": {"min": 500, "max": 3000, "success": 30},
            "contrabando": {"min": 1000, "max": 5000, "success": 20},
            "furto": {"min": 50, "max": 300, "success": 80}
        }

    async def init_database(self):
        """Inicializa a conexão com MongoDB"""
        try:
            mongo_uri = os.getenv("MONGO_URI")
            if not mongo_uri:
                print("❌ MONGO_URI não encontrada nas variáveis de ambiente!")
                return
            
            print("🔄 Conectando ao MongoDB (Economia)...")
            self.client = AsyncIOMotorClient(mongo_uri)
            
            # Testa a conexão
            await self.client.admin.command('ping')
            
            self.db = self.client['discord_bot']
            self.users_collection = self.db['users']
            self.shop_collection = self.db['shop']
            self.vip_collection = self.db['vip_users']
            self._connection_ready = True
            
            # Inicializa dados da loja
            await self.initialize_shop_data()
            
            print("✅ Conectado ao MongoDB (Economia) com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao conectar com MongoDB (Economia): {e}")
            self._connection_ready = False

    async def ensure_connection(self):
        """Garante que a conexão com MongoDB está ativa"""
        if not self._connection_ready:
            await self.init_database()
        return self._connection_ready

    async def initialize_shop_data(self):
        """Inicializa dados da loja no MongoDB se não existir"""
        try:
            if not await self.ensure_connection():
                return
                
            count = await self.shop_collection.count_documents({})
            if count == 0:
                shop_items = [
                    {"item": "smartphone", "price": 1500, "desc": "Smartphone moderno"},
                    {"item": "notebook", "price": 3000, "desc": "Notebook para trabalho"},
                    {"item": "carro", "price": 50000, "desc": "Carro popular"},
                    {"item": "casa", "price": 200000, "desc": "Casa própria"}
                ]
                await self.shop_collection.insert_many(shop_items)
                print("✅ Dados da loja inicializados no MongoDB")
        except Exception as e:
            print(f"❌ Erro ao inicializar loja: {e}")

    async def get_shop_data(self):
        """Obtém dados da loja do MongoDB"""
        try:
            if not await self.ensure_connection():
                return {}
                
            shop_data = {}
            async for item in self.shop_collection.find():
                shop_data[item["item"]] = {
                    "price": item["price"],
                    "desc": item["desc"]
                }
            return shop_data
        except Exception as e:
            print(f"❌ Erro ao buscar dados da loja: {e}")
            return {}

    async def is_vip(self, user_id, guild_id):
        """Verifica se usuário é VIP"""
        try:
            if not await self.ensure_connection():
                return False
                
            user_key = f"{guild_id}_{user_id}"
            vip_data = await self.vip_collection.find_one({"user_key": user_key})
            
            if vip_data:
                expiry_date = datetime.fromisoformat(vip_data['expiry'])
                return datetime.now() < expiry_date
            return False
        except Exception as e:
            print(f"❌ Erro ao verificar VIP: {e}")
            return False

    async def get_user_data(self, user_id):
        """Obtém dados do usuário do MongoDB"""
        try:
            if not await self.ensure_connection():
                return self.get_default_user_data(str(user_id))
                
            user_id = str(user_id)
            user_data = await self.users_collection.find_one({"user_id": user_id})
            
            if not user_data:
                default_data = self.get_default_user_data(user_id)
                await self.users_collection.insert_one(default_data)
                return default_data
            
            return user_data
        except Exception as e:
            print(f"❌ Erro ao buscar dados do usuário: {e}")
            return self.get_default_user_data(str(user_id))

    def get_default_user_data(self, user_id):
        """Retorna dados padrão do usuário"""
        return {
            "user_id": user_id,
            "balance": 0,
            "bank": 0,
            "inventory": {},
            "job": None,
            "last_daily": None,
            "last_work": None,
            "last_crime": None,
            "is_boss": False,
            "employees": []
        }

    async def update_user_data(self, user_id, data):
        """Atualiza dados do usuário no MongoDB"""
        try:
            if not await self.ensure_connection():
                print("❌ Conexão com MongoDB não está disponível para atualização")
                return False
                
            user_id = str(user_id)
            await self.users_collection.update_one(
                {"user_id": user_id},
                {"$set": data},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"❌ Erro ao atualizar dados do usuário: {e}")
            return False

    def format_money(self, amount):
        """Formata valor em reais"""
        return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @commands.command(name='saldo', aliases=['bal', 'balance'])
    async def balance(self, ctx, user: discord.Member = None):
        """Mostra o saldo do usuário"""
        if user is None:
            user = ctx.author
        
        data = await self.get_user_data(user.id)
        is_vip_user = await self.is_vip(user.id, ctx.guild.id)
        
        embed = discord.Embed(
            title=f"💰 Saldo de {user.display_name}",
            color=0xFFD700 if is_vip_user else 0x00ff00
        )
        embed.add_field(name="Carteira", value=self.format_money(data["balance"]), inline=True)
        embed.add_field(name="Banco", value=self.format_money(data["bank"]), inline=True)
        embed.add_field(name="Total", value=self.format_money(data["balance"] + data["bank"]), inline=True)
        
        if data["job"]:
            embed.add_field(name="Emprego", value=data["job"].title(), inline=False)
        
        if is_vip_user:
            embed.add_field(name="👑 Status", value="VIP ATIVO", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name='diario', aliases=['daily'])
    async def daily(self, ctx):
        """Recompensa diária"""
        user_data = await self.get_user_data(ctx.author.id)
        now = datetime.now()
        is_vip_user = await self.is_vip(ctx.author.id, ctx.guild.id)
        
        if user_data["last_daily"]:
            last_daily = datetime.fromisoformat(user_data["last_daily"])
            if now - last_daily < timedelta(days=1):
                time_left = timedelta(days=1) - (now - last_daily)
                hours = int(time_left.total_seconds() // 3600)
                minutes = int((time_left.total_seconds() % 3600) // 60)
                
                embed = discord.Embed(
                    title="⏰ Recompensa Diária",
                    description=f"Você já coletou hoje! Volte em {hours}h {minutes}m",
                    color=0xff0000
                )
                return await ctx.send(embed=embed)
        
        reward = self.daily_reward
        if is_vip_user:
            reward = int(reward * self.vip_daily_multiplier)
        
        # Atualiza dados no MongoDB
        update_data = {
            "balance": user_data["balance"] + reward,
            "last_daily": now.isoformat()
        }
        success = await self.update_user_data(ctx.author.id, update_data)
        
        if not success:
            return await ctx.send("❌ Erro ao processar recompensa. Tente novamente.")
        
        embed = discord.Embed(
            title="🎁 Recompensa Diária",
            description=f"Você recebeu {self.format_money(reward)}!",
            color=0xFFD700 if is_vip_user else 0x00ff00
        )
        
        if is_vip_user:
            embed.add_field(name="👑 Bônus VIP", value=f"2x recompensa aplicada!", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name='trabalhar', aliases=['work'])
    async def work(self, ctx):
        """Trabalhar para ganhar dinheiro"""
        user_data = await self.get_user_data(ctx.author.id)
        now = datetime.now()
        is_vip_user = await self.is_vip(ctx.author.id, ctx.guild.id)
        
        if not user_data["job"]:
            available_jobs = list(self.jobs.keys())
            new_job = random.choice(available_jobs)
            
            await self.update_user_data(ctx.author.id, {"job": new_job})
            user_data["job"] = new_job
            
            embed = discord.Embed(
                title="💼 Novo Emprego",
                description=f"Você conseguiu um emprego como {new_job}!",
                color=0x00ff00
            )
            await ctx.send(embed=embed)
        
        if user_data["last_work"]:
            last_work = datetime.fromisoformat(user_data["last_work"])
            if now - last_work < timedelta(seconds=self.work_cooldown):
                time_left = timedelta(seconds=self.work_cooldown) - (now - last_work)
                minutes = int(time_left.total_seconds() // 60)
                
                embed = discord.Embed(
                    title="⏰ Cooldown",
                    description=f"Você precisa descansar! Volte em {minutes} minutos.",
                    color=0xff0000
                )
                return await ctx.send(embed=embed)
        
        job = user_data["job"]
        min_salary, max_salary = self.jobs[job]["salary"]
        
        # Bônus VIP: chance de ganhar mais
        if is_vip_user and random.randint(1, 100) <= 30:
            max_salary = int(max_salary * 1.5)
        
        earnings = random.randint(min_salary, max_salary)
        
        if is_vip_user:
            earnings = int(earnings * self.vip_work_multiplier)
        
        # Atualiza dados no MongoDB
        update_data = {
            "balance": user_data["balance"] + earnings,
            "last_work": now.isoformat()
        }
        success = await self.update_user_data(ctx.author.id, update_data)
        
        if not success:
            return await ctx.send("❌ Erro ao processar trabalho. Tente novamente.")
        
        embed = discord.Embed(
            title="💼 Trabalho Concluído",
            description=f"Você trabalhou como {job} e ganhou {self.format_money(earnings)}!",
            color=0xFFD700 if is_vip_user else 0x00ff00
        )
        
        if is_vip_user:
            embed.add_field(name="👑 Bônus VIP", value="1.5x salário + chance de bônus!", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name='loja', aliases=['shop'])
    async def shop(self, ctx):
        """Mostra itens da loja"""
        shop_data = await self.get_shop_data()
        embed = discord.Embed(title="🛒 Loja", color=0x0099ff)
        
        for item, data in shop_data.items():
            embed.add_field(
                name=item.title(),
                value=f"{data['desc']}\n**Preço:** {self.format_money(data['price'])}",
                inline=True
            )
        
        embed.set_footer(text="Use !comprar <item> para comprar")
        await ctx.send(embed=embed)

    @commands.command(name='comprar', aliases=['buy'])
    async def buy(self, ctx, *, item_name: str):
        """Comprar um item da loja"""
        user_data = await self.get_user_data(ctx.author.id)
        shop_data = await self.get_shop_data()
        item_name = item_name.lower()
        
        if item_name not in shop_data:
            return await ctx.send("❌ Item não encontrado!")
        
        price = shop_data[item_name]["price"]
        
        if user_data["balance"] < price:
            return await ctx.send("❌ Saldo insuficiente!")
        
        # Atualiza inventário
        inventory = user_data.get("inventory", {})
        if item_name not in inventory:
            inventory[item_name] = 0
        inventory[item_name] += 1
        
        # Atualiza dados no MongoDB
        update_data = {
            "balance": user_data["balance"] - price,
            "inventory": inventory
        }
        success = await self.update_user_data(ctx.author.id, update_data)
        
        if not success:
            return await ctx.send("❌ Erro ao processar compra. Tente novamente.")
        
        embed = discord.Embed(
            title="🛒 Compra Realizada",
            description=f"Você comprou {item_name} por {self.format_money(price)}!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)

    async def cog_unload(self):
        """Fecha a conexão com MongoDB quando o cog é descarregado"""
        if self.client:
            self.client.close()
            print("🔌 Conexão com MongoDB (Economia) fechada")

async def setup(bot):
    await bot.add_cog(Economia(bot))