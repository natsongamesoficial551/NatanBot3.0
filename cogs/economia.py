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
        self.load_data()
        self.load_shop()
        
        # Configurações do sistema
        self.daily_reward = 1000
        self.work_cooldown = 3600  # 1 hora em segundos
        self.crime_cooldown = 7200  # 2 horas
        self.daily_cooldown = 86400  # 24 horas
        
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
        embed = discord.Embed(
            title=f"💰 Saldo de {user.display_name}",
            color=0x00ff00
        )
        embed.add_field(name="Carteira", value=self.format_money(data["balance"]), inline=True)
        embed.add_field(name="Banco", value=self.format_money(data["bank"]), inline=True)
        embed.add_field(name="Total", value=self.format_money(data["balance"] + data["bank"]), inline=True)
        
        if data["job"]:
            embed.add_field(name="Emprego", value=data["job"].title(), inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name='diario', aliases=['daily'])
    async def daily(self, ctx):
        """Recompensa diária"""
        user_data = self.get_user_data(ctx.author.id)
        now = datetime.now()
        
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
        
        user_data["balance"] += self.daily_reward
        user_data["last_daily"] = now.isoformat()
        self.save_data()
        
        embed = discord.Embed(
            title="🎁 Recompensa Diária",
            description=f"Você recebeu {self.format_money(self.daily_reward)}!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)

    @commands.command(name='trabalhar', aliases=['work'])
    async def work(self, ctx):
        """Trabalhar para ganhar dinheiro"""
        user_data = self.get_user_data(ctx.author.id)
        now = datetime.now()
        
        if not user_data["job"]:
            # Atribuir trabalho aleatório se não tiver
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
        earnings = random.randint(min_salary, max_salary)
        
        user_data["balance"] += earnings
        user_data["last_work"] = now.isoformat()
        self.save_data()
        
        embed = discord.Embed(
            title="💼 Trabalho Concluído",
            description=f"Você trabalhou como {job} e ganhou {self.format_money(earnings)}!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)

    @commands.command(name='empregos', aliases=['jobs'])
    async def jobs_list(self, ctx):
        """Lista empregos disponíveis"""
        embed = discord.Embed(title="💼 Empregos Disponíveis", color=0x0099ff)
        
        for job, info in self.jobs.items():
            min_sal, max_sal = info["salary"]
            embed.add_field(
                name=job.title(),
                value=f"{info['desc']}\n**Salário:** {self.format_money(min_sal)} - {self.format_money(max_sal)}",
                inline=False
            )
        
        embed.set_footer(text="Use !trabalhar para conseguir um trabalho aleatório")
        await ctx.send(embed=embed)

    @commands.command(name='crime')
    async def crime(self, ctx):
        """Cometer um crime"""
        user_data = self.get_user_data(ctx.author.id)
        now = datetime.now()
        
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
        
        if random.randint(1, 100) <= crime_data["success"]:
            earnings = random.randint(crime_data["min"], crime_data["max"])
            user_data["balance"] += earnings
            
            embed = discord.Embed(
                title="🎯 Crime Bem-sucedido",
                description=f"Você cometeu um {crime_type.replace('_', ' ')} e ganhou {self.format_money(earnings)}!",
                color=0x00ff00
            )
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

    @commands.command(name='inventario', aliases=['inv'])
    async def inventory(self, ctx, user: discord.Member = None):
        """Mostra o inventário do usuário"""
        if user is None:
            user = ctx.author
        
        user_data = self.get_user_data(user.id)
        
        if not user_data["inventory"]:
            embed = discord.Embed(
                title="📦 Inventário Vazio",
                description="Nenhum item encontrado!",
                color=0xff0000
            )
            return await ctx.send(embed=embed)
        
        embed = discord.Embed(
            title=f"📦 Inventário de {user.display_name}",
            color=0x0099ff
        )
        
        for item, quantity in user_data["inventory"].items():
            embed.add_field(
                name=item.title(),
                value=f"Quantidade: {quantity}",
                inline=True
            )
        
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
        
        if target_data["balance"] < 100:
            return await ctx.send("❌ Esta pessoa não tem dinheiro suficiente para roubar!")
        
        if robber_data["balance"] < 50:
            return await ctx.send("❌ Você precisa de pelo menos R$ 50,00 para tentar roubar!")
        
        success_chance = random.randint(1, 100)
        
        if success_chance <= 40:  # 40% chance de sucesso
            stolen_amount = random.randint(50, min(1000, target_data["balance"] // 2))
            target_data["balance"] -= stolen_amount
            robber_data["balance"] += stolen_amount
            
            embed = discord.Embed(
                title="💰 Roubo Bem-sucedido",
                description=f"Você roubou {self.format_money(stolen_amount)} de {user.display_name}!",
                color=0x00ff00
            )
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
        
        if amount <= 0:
            return await ctx.send("❌ Valor inválido!")
        
        if user_data["balance"] < amount:
            return await ctx.send("❌ Saldo insuficiente!")
        
        user_data["balance"] -= amount
        
        if random.randint(1, 100) <= 45:  # 45% chance de ganhar
            winnings = amount * 2
            user_data["balance"] += winnings
            
            embed = discord.Embed(
                title="🎰 Você Ganhou!",
                description=f"Você apostou {self.format_money(amount)} e ganhou {self.format_money(winnings)}!",
                color=0x00ff00
            )
        else:
            embed = discord.Embed(
                title="💸 Você Perdeu!",
                description=f"Você perdeu {self.format_money(amount)} na aposta!",
                color=0xff0000
            )
        
        self.save_data()
        await ctx.send(embed=embed)

    @commands.command(name='loteria', aliases=['lottery'])
    async def lottery(self, ctx):
        """Participar da loteria"""
        user_data = self.get_user_data(ctx.author.id)
        ticket_price = 100
        
        if user_data["balance"] < ticket_price:
            return await ctx.send("❌ Você precisa de R$ 100,00 para comprar um bilhete!")
        
        user_data["balance"] -= ticket_price
        
        # Números sorteados
        user_numbers = [random.randint(1, 60) for _ in range(6)]
        winning_numbers = [random.randint(1, 60) for _ in range(6)]
        
        matches = len(set(user_numbers) & set(winning_numbers))
        
        prizes = {6: 100000, 5: 10000, 4: 1000, 3: 100, 2: 50}
        
        if matches in prizes:
            prize = prizes[matches]
            user_data["balance"] += prize
            
            embed = discord.Embed(
                title="🎉 Loteria - Você Ganhou!",
                description=f"Você acertou {matches} números e ganhou {self.format_money(prize)}!",
                color=0x00ff00
            )
        else:
            embed = discord.Embed(
                title="🎲 Loteria - Não foi desta vez!",
                description=f"Você acertou {matches} números. Tente novamente!",
                color=0xff9900
            )
        
        embed.add_field(name="Seus números", value=", ".join(map(str, sorted(user_numbers))), inline=True)
        embed.add_field(name="Números sorteados", value=", ".join(map(str, sorted(winning_numbers))), inline=True)
        
        self.save_data()
        await ctx.send(embed=embed)

    @commands.command(name='vender', aliases=['sell'])
    async def sell(self, ctx, item_name: str, quantity: int = 1):
        """Vender item do inventário"""
        user_data = self.get_user_data(ctx.author.id)
        item_name = item_name.lower()
        
        if item_name not in user_data["inventory"]:
            return await ctx.send("❌ Você não possui este item!")
        
        if user_data["inventory"][item_name] < quantity:
            return await ctx.send("❌ Quantidade insuficiente!")
        
        if item_name not in self.shop_data:
            return await ctx.send("❌ Este item não pode ser vendido!")
        
        sell_price = int(self.shop_data[item_name]["price"] * 0.7)  # 70% do preço original
        total_price = sell_price * quantity
        
        user_data["inventory"][item_name] -= quantity
        if user_data["inventory"][item_name] == 0:
            del user_data["inventory"][item_name]
        
        user_data["balance"] += total_price
        self.save_data()
        
        embed = discord.Embed(
            title="💰 Venda Realizada",
            description=f"Você vendeu {quantity}x {item_name} por {self.format_money(total_price)}!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)

    @commands.command(name='adicionaritem', aliases=['additem'])
    @commands.has_permissions(administrator=True)
    async def add_item(self, ctx, name: str, price: int, *, description: str):
        """Adicionar item à loja (Apenas administradores)"""
        name = name.lower()
        
        self.shop_data[name] = {
            "price": price,
            "desc": description
        }
        
        self.save_shop()
        
        embed = discord.Embed(
            title="✅ Item Adicionado",
            description=f"Item '{name}' adicionado à loja por {self.format_money(price)}!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)

    @commands.command(name='presentear', aliases=['gift'])
    async def gift(self, ctx, user: discord.Member, amount: int):
        """Presentear dinheiro para outro usuário"""
        if user == ctx.author:
            return await ctx.send("❌ Você não pode presentear a si mesmo!")
        
        if user.bot:
            return await ctx.send("❌ Você não pode presentear bots!")
        
        if amount <= 0:
            return await ctx.send("❌ Valor inválido!")
        
        giver_data = self.get_user_data(ctx.author.id)
        receiver_data = self.get_user_data(user.id)
        
        if giver_data["balance"] < amount:
            return await ctx.send("❌ Saldo insuficiente!")
        
        giver_data["balance"] -= amount
        receiver_data["balance"] += amount
        self.save_data()
        
        embed = discord.Embed(
            title="🎁 Presente Enviado",
            description=f"{ctx.author.display_name} presenteou {user.display_name} com {self.format_money(amount)}!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)

    @commands.command(name='contratar', aliases=['hire'])
    async def hire(self, ctx, user: discord.Member):
        """Contratar funcionário (Apenas empresários)"""
        boss_data = self.get_user_data(ctx.author.id)
        employee_data = self.get_user_data(user.id)
        
        if boss_data["job"] != "empresario":
            return await ctx.send("❌ Apenas empresários podem contratar funcionários!")
        
        if user == ctx.author:
            return await ctx.send("❌ Você não pode contratar a si mesmo!")
        
        if str(user.id) in boss_data["employees"]:
            return await ctx.send("❌ Este usuário já é seu funcionário!")
        
        boss_data["employees"].append(str(user.id))
        employee_data["job"] = "funcionario"
        self.save_data()
        
        embed = discord.Embed(
            title="🤝 Contratação Realizada",
            description=f"{user.display_name} foi contratado por {ctx.author.display_name}!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)

    @commands.command(name='demitir', aliases=['fire'])
    async def fire(self, ctx, user: discord.Member):
        """Demitir funcionário (Apenas empresários)"""
        boss_data = self.get_user_data(ctx.author.id)
        employee_data = self.get_user_data(user.id)
        
        if boss_data["job"] != "empresario":
            return await ctx.send("❌ Apenas empresários podem demitir funcionários!")
        
        if str(user.id) not in boss_data["employees"]:
            return await ctx.send("❌ Este usuário não é seu funcionário!")
        
        boss_data["employees"].remove(str(user.id))
        employee_data["job"] = None
        self.save_data()
        
        embed = discord.Embed(
            title="❌ Demissão Realizada",
            description=f"{user.display_name} foi demitido por {ctx.author.display_name}!",
            color=0xff0000
        )
        await ctx.send(embed=embed)

    @commands.command(name='dar', aliases=['give'])
    @commands.has_permissions(administrator=True)
    async def give_money(self, ctx, user: discord.Member, amount: int):
        """Dar dinheiro para usuário (Apenas administradores)"""
        if amount <= 0:
            return await ctx.send("❌ Valor inválido!")
        
        user_data = self.get_user_data(user.id)
        user_data["balance"] += amount
        self.save_data()
        
        embed = discord.Embed(
            title="💰 Dinheiro Concedido",
            description=f"Administrador deu {self.format_money(amount)} para {user.display_name}!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economia(bot))