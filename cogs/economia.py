import discord
from discord.ext import commands
import json
import asyncio
import random
from datetime import datetime, timedelta
import os

class Economia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "economy_data.json"
        self.shop_file = "shop_data.json"
        self.vip_file = "vip_data.json"
        self.load_data()
        self.load_shop()
        self.load_vip_data()
        
        # Configurações do sistema
        self.daily_reward = 1000
        self.work_cooldown = 3600  # 1 hora
        self.crime_cooldown = 7200  # 2 horas
        self.daily_cooldown = 86400  # 24 horas
        
        # Multiplicadores VIP
        self.vip_daily_multiplier = 2.0
        self.vip_work_multiplier = 1.5
        self.vip_crime_success_bonus = 15  # +15% chance
        self.vip_rob_success_bonus = 20  # +20% chance
        
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

    def load_data(self):
        """Carrega dados dos usuários"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.users_data = json.load(f)
        except FileNotFoundError:
            self.users_data = {}

    def save_data(self):
        """Salva dados dos usuários"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.users_data, f, indent=2, ensure_ascii=False)

    def load_shop(self):
        """Carrega dados da loja"""
        try:
            with open(self.shop_file, 'r', encoding='utf-8') as f:
                self.shop_data = json.load(f)
        except FileNotFoundError:
            self.shop_data = {
                "smartphone": {"price": 1500, "desc": "Smartphone moderno"},
                "notebook": {"price": 3000, "desc": "Notebook para trabalho"},
                "carro": {"price": 50000, "desc": "Carro popular"},
                "casa": {"price": 200000, "desc": "Casa própria"}
            }
            self.save_shop()

    def save_shop(self):
        """Salva dados da loja"""
        with open(self.shop_file, 'w', encoding='utf-8') as f:
            json.dump(self.shop_data, f, indent=2, ensure_ascii=False)

    def load_vip_data(self):
        """Carrega dados VIP"""
        try:
            with open(self.vip_file, 'r', encoding='utf-8') as f:
                self.vip_data = json.load(f)
        except FileNotFoundError:
            self.vip_data = {}

    def is_vip(self, user_id, guild_id):
        """Verifica se usuário é VIP"""
        user_key = f"{guild_id}_{user_id}"
        if user_key in self.vip_data:
            expiry_date = datetime.fromisoformat(self.vip_data[user_key]['expiry'])
            return datetime.now() < expiry_date
        return False

    def get_user_data(self, user_id):
        """Obtém dados do usuário"""
        user_id = str(user_id)
        if user_id not in self.users_data:
            self.users_data[user_id] = {
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
        return self.users_data[user_id]

    def format_money(self, amount):
        """Formata valor em reais"""
        return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @commands.command(name='saldo', aliases=['bal', 'balance'])
    async def balance(self, ctx, user: discord.Member = None):
        """Mostra o saldo do usuário"""
        if user is None:
            user = ctx.author
        
        data = self.get_user_data(user.id)
        is_vip_user = self.is_vip(user.id, ctx.guild.id)
        
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
        user_data = self.get_user_data(ctx.author.id)
        now = datetime.now()
        is_vip_user = self.is_vip(ctx.author.id, ctx.guild.id)
        
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
        
        user_data["balance"] += reward
        user_data["last_daily"] = now.isoformat()
        self.save_data()
        
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
        user_data = self.get_user_data(ctx.author.id)
        now = datetime.now()
        is_vip_user = self.is_vip(ctx.author.id, ctx.guild.id)
        
        if not user_data["job"]:
            available_jobs = list(self.jobs.keys())
            user_data["job"] = random.choice(available_jobs)
            
            embed = discord.Embed(
                title="💼 Novo Emprego",
                description=f"Você conseguiu um emprego como {user_data['job']}!",
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
        if is_vip_user and random.randint(1, 100) <= 30:  # 30% chance de bônus extra
            max_salary = int(max_salary * 1.5)
        
        earnings = random.randint(min_salary, max_salary)
        
        if is_vip_user:
            earnings = int(earnings * self.vip_work_multiplier)
        
        user_data["balance"] += earnings
        user_data["last_work"] = now.isoformat()
        self.save_data()
        
        embed = discord.Embed(
            title="💼 Trabalho Concluído",
            description=f"Você trabalhou como {job} e ganhou {self.format_money(earnings)}!",
            color=0xFFD700 if is_vip_user else 0x00ff00
        )
        
        if is_vip_user:
            embed.add_field(name="👑 Bônus VIP", value="1.5x salário + chance de bônus!", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name='crime')
    async def crime(self, ctx):
        """Cometer um crime"""
        user_data = self.get_user_data(ctx.author.id)
        now = datetime.now()
        is_vip_user = self.is_vip(ctx.author.id, ctx.guild.id)
        
        if user_data["last_crime"]:
            last_crime = datetime.fromisoformat(user_data["last_crime"])
            if now - last_crime < timedelta(seconds=self.crime_cooldown):
                time_left = timedelta(seconds=self.crime_cooldown) - (now - last_crime)
                hours = int(time_left.total_seconds() // 3600)
                minutes = int((time_left.total_seconds() % 3600) // 60)
                
                embed = discord.Embed(
                    title="🚔 Procurado",
                    description=f"A polícia está te procurando! Espere {hours}h {minutes}m",
                    color=0xff0000
                )
                return await ctx.send(embed=embed)
        
        crime_type = random.choice(list(self.crimes.keys()))
        crime_data = self.crimes[crime_type]
        success_chance = crime_data["success"]
        
        # Bônus VIP: +15% chance de sucesso
        if is_vip_user:
            success_chance += self.vip_crime_success_bonus
        
        if random.randint(1, 100) <= success_chance:
            earnings = random.randint(crime_data["min"], crime_data["max"])
            
            # Bônus VIP: chance de ganhar mais
            if is_vip_user and random.randint(1, 100) <= 25:  # 25% chance
                earnings = int(earnings * 1.3)
            
            user_data["balance"] += earnings
            
            embed = discord.Embed(
                title="🎯 Crime Bem-sucedido",
                description=f"Você cometeu um {crime_type.replace('_', ' ')} e ganhou {self.format_money(earnings)}!",
                color=0xFFD700 if is_vip_user else 0x00ff00
            )
            
            if is_vip_user:
                embed.add_field(name="👑 Bônus VIP", value="+15% chance + bônus em ganhos!", inline=False)
        else:
            fine = random.randint(100, 1000)
            user_data["balance"] = max(0, user_data["balance"] - fine)
            
            embed = discord.Embed(
                title="🚔 Preso!",
                description=f"Você foi pego e multado em {self.format_money(fine)}!",
                color=0xff0000
            )
        
        user_data["last_crime"] = now.isoformat()
        self.save_data()
        await ctx.send(embed=embed)

    @commands.command(name='roubar', aliases=['rob'])
    async def rob(self, ctx, user: discord.Member):
        """Roubar outro usuário"""
        if user == ctx.author:
            return await ctx.send("❌ Você não pode roubar a si mesmo!")
        
        if user.bot:
            return await ctx.send("❌ Você não pode roubar bots!")
        
        robber_data = self.get_user_data(ctx.author.id)
        target_data = self.get_user_data(user.id)
        is_vip_user = self.is_vip(ctx.author.id, ctx.guild.id)
        
        if target_data["balance"] < 100:
            return await ctx.send("❌ Esta pessoa não tem dinheiro suficiente para roubar!")
        
        if robber_data["balance"] < 50:
            return await ctx.send("❌ Você precisa de pelo menos R$ 50,00 para tentar roubar!")
        
        success_chance = 40  # Base 40%
        
        # Bônus VIP: +20% chance de sucesso
        if is_vip_user:
            success_chance += self.vip_rob_success_bonus
        
        if random.randint(1, 100) <= success_chance:
            stolen_amount = random.randint(50, min(1000, target_data["balance"] // 2))
            
            # Bônus VIP: chance de roubar mais
            if is_vip_user and random.randint(1, 100) <= 20:  # 20% chance
                stolen_amount = int(stolen_amount * 1.4)
                stolen_amount = min(stolen_amount, target_data["balance"])
            
            target_data["balance"] -= stolen_amount
            robber_data["balance"] += stolen_amount
            
            embed = discord.Embed(
                title="💰 Roubo Bem-sucedido",
                description=f"Você roubou {self.format_money(stolen_amount)} de {user.display_name}!",
                color=0xFFD700 if is_vip_user else 0x00ff00
            )
            
            if is_vip_user:
                embed.add_field(name="👑 Bônus VIP", value="+20% chance + possível bônus!", inline=False)
        else:
            fine = random.randint(100, 500)
            robber_data["balance"] = max(0, robber_data["balance"] - fine)
            
            embed = discord.Embed(
                title="🚔 Roubo Fracassado",
                description=f"Você foi pego tentando roubar e pagou {self.format_money(fine)} de multa!",
                color=0xff0000
            )
        
        self.save_data()
        await ctx.send(embed=embed)

    @commands.command(name='apostar', aliases=['bet'])
    async def bet(self, ctx, amount: int):
        """Apostar dinheiro"""
        user_data = self.get_user_data(ctx.author.id)
        is_vip_user = self.is_vip(ctx.author.id, ctx.guild.id)
        
        if amount <= 0:
            return await ctx.send("❌ Valor inválido!")
        
        if user_data["balance"] < amount:
            return await ctx.send("❌ Saldo insuficiente!")
        
        user_data["balance"] -= amount
        win_chance = 45  # Base 45%
        
        # Bônus VIP: +10% chance
        if is_vip_user:
            win_chance += 10
        
        if random.randint(1, 100) <= win_chance:
            winnings = amount * 2
            
            # Bônus VIP: chance de multiplicador maior
            if is_vip_user and random.randint(1, 100) <= 15:  # 15% chance
                winnings = amount * 3
            
            user_data["balance"] += winnings
            
            embed = discord.Embed(
                title="🎰 Você Ganhou!",
                description=f"Você apostou {self.format_money(amount)} e ganhou {self.format_money(winnings)}!",
                color=0xFFD700 if is_vip_user else 0x00ff00
            )
            
            if is_vip_user:
                embed.add_field(name="👑 Bônus VIP", value="+10% chance + possível 3x multiplicador!", inline=False)
        else:
            embed = discord.Embed(
                title="💸 Você Perdeu!",
                description=f"Você perdeu {self.format_money(amount)} na aposta!",
                color=0xff0000
            )
        
        self.save_data()
        await ctx.send(embed=embed)

    # Comandos restantes mantidos iguais para economizar espaço
    @commands.command(name='depositar', aliases=['dep'])
    async def deposit(self, ctx, amount: int):
        """Depositar dinheiro no banco"""
        user_data = self.get_user_data(ctx.author.id)
        
        if amount <= 0:
            return await ctx.send("❌ Valor inválido!")
        
        if user_data["balance"] < amount:
            return await ctx.send("❌ Saldo insuficiente!")
        
        user_data["balance"] -= amount
        user_data["bank"] += amount
        self.save_data()
        
        embed = discord.Embed(
            title="🏦 Depósito Realizado",
            description=f"Você depositou {self.format_money(amount)} no banco!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)

    @commands.command(name='sacar', aliases=['withdraw'])
    async def withdraw(self, ctx, amount: int):
        """Sacar dinheiro do banco"""
        user_data = self.get_user_data(ctx.author.id)
        
        if amount <= 0:
            return await ctx.send("❌ Valor inválido!")
        
        if user_data["bank"] < amount:
            return await ctx.send("❌ Saldo bancário insuficiente!")
        
        user_data["bank"] -= amount
        user_data["balance"] += amount
        self.save_data()
        
        embed = discord.Embed(
            title="🏦 Saque Realizado",
            description=f"Você sacou {self.format_money(amount)} do banco!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)

    @commands.command(name='loja', aliases=['shop'])
    async def shop(self, ctx):
        """Mostra itens da loja"""
        embed = discord.Embed(title="🛒 Loja", color=0x0099ff)
        
        for item, data in self.shop_data.items():
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
        user_data = self.get_user_data(ctx.author.id)
        item_name = item_name.lower()
        
        if item_name not in self.shop_data:
            return await ctx.send("❌ Item não encontrado!")
        
        price = self.shop_data[item_name]["price"]
        
        if user_data["balance"] < price:
            return await ctx.send("❌ Saldo insuficiente!")
        
        user_data["balance"] -= price
        
        if item_name not in user_data["inventory"]:
            user_data["inventory"][item_name] = 0
        user_data["inventory"][item_name] += 1
        
        self.save_data()
        
        embed = discord.Embed(
            title="🛒 Compra Realizada",
            description=f"Você comprou {item_name} por {self.format_money(price)}!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economia(bot))