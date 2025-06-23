import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import asyncio

class Aniversario(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "aniversarios.json"
        self.load_data()
    
    def load_data(self):
        """Carrega dados do arquivo JSON ou cria um novo se não existir"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.birthdays = json.load(f)
        else:
            self.birthdays = {}
            self.save_data()
    
    def save_data(self):
        """Salva dados no arquivo JSON"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.birthdays, f, indent=2, ensure_ascii=False)
    
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
            self.birthdays[user_id] = {
                'name': membro.display_name,
                'date': data,
                'day': day,
                'month': month
            }
            self.save_data()
            
            embed = discord.Embed(
                title="🎂 Aniversário Adicionado",
                description=f"Data de aniversário de **{membro.display_name}** salva: {data}",
                color=0x00ff7f
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
        if not self.birthdays:
            embed = discord.Embed(
                title="📅 Aniversariantes",
                description="Nenhum aniversário cadastrado ainda.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        # Ordena por mês e dia
        sorted_birthdays = sorted(
            self.birthdays.items(),
            key=lambda x: (x[1]['month'], x[1]['day'])
        )
        
        description = ""
        for user_id, data in sorted_birthdays:
            member = ctx.guild.get_member(int(user_id))
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
        
        if user_id in self.birthdays:
            data = self.birthdays[user_id]['date']
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
        if user_id in self.birthdays:
            del self.birthdays[user_id]
            self.save_data()
            
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
        if not self.birthdays:
            embed = discord.Embed(
                title="📅 Próximos Aniversários",
                description="Nenhum aniversário cadastrado.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        hoje = datetime.now()
        proximos = []
        
        for user_id, data in self.birthdays.items():
            # Calcula próximo aniversário
            try:
                aniversario = datetime(hoje.year, data['month'], data['day'])
                if aniversario < hoje:
                    aniversario = datetime(hoje.year + 1, data['month'], data['day'])
                
                dias_restantes = (aniversario - hoje).days
                if dias_restantes <= 30:
                    member = ctx.guild.get_member(int(user_id))
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

async def setup(bot):
    await bot.add_cog(Aniversario(bot))