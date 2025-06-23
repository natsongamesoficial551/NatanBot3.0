import discord
from discord.ext import commands
import json
import os
import random
from datetime import datetime

class Sorteio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "sorteios.json"
        self.load_data()
    
    def load_data(self):
        """Carrega dados do arquivo JSON ou cria um novo se não existir"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.sorteios = data.get('sorteios', {})
                self.configuracoes = data.get('configuracoes', {})
        else:
            self.sorteios = {}
            self.configuracoes = {}
            self.save_data()
    
    def save_data(self):
        """Salva dados no arquivo JSON"""
        data = {
            'sorteios': self.sorteios,
            'configuracoes': self.configuracoes
        }
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @commands.command(name='comecarsorteio', aliases=['startgw'])
    @commands.has_permissions(administrator=True)
    async def comecar_sorteio(self, ctx, *, premio):
        """Inicia um novo sorteio"""
        guild_id = str(ctx.guild.id)
        
        if not premio:
            embed = discord.Embed(
                title="❌ Erro",
                description="Você precisa especificar um prêmio.\n**Uso:** `!comecarsorteio <prêmio>`",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        # Verifica se já existe um sorteio ativo
        if guild_id in self.sorteios and self.sorteios[guild_id].get('ativo'):
            embed = discord.Embed(
                title="⚠️ Sorteio Já Ativo",
                description="Já existe um sorteio em andamento.\nUse `!encerrarsorteio` para encerrar antes de começar outro.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        # Verifica se os canais estão configurados
        configs = self.configuracoes.get(guild_id, {})
        canal_sorteio_id = configs.get('canal_sorteio')
        canal_comando_id = configs.get('canal_comando')
        
        if not canal_sorteio_id:
            embed = discord.Embed(
                title="❌ Canal Não Configurado",
                description="Configure o canal do sorteio primeiro:\n`!canaldosorteio #canal`",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        # Verifica se está no canal correto
        if canal_comando_id and ctx.channel.id != canal_comando_id:
            canal_comando = self.bot.get_channel(canal_comando_id)
            embed = discord.Embed(
                title="❌ Canal Incorreto",
                description=f"Use este comando no canal {canal_comando.mention if canal_comando else 'configurado'}.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        # Cria o sorteio
        self.sorteios[guild_id] = {
            'premio': premio,
            'ativo': True,
            'participantes': [],
            'criador': ctx.author.display_name,
            'criador_id': ctx.author.id,
            'data_inicio': datetime.now().strftime('%d/%m/%Y %H:%M')
        }
        self.save_data()
        
        # Envia mensagem no canal do sorteio
        canal_sorteio = self.bot.get_channel(canal_sorteio_id)
        if canal_sorteio:
            embed = discord.Embed(
                title="🎉 SORTEIO INICIADO!",
                description=f"**Prêmio:** {premio}\n\nReaja com 🎁 para participar!",
                color=0x00ff7f
            )
            embed.set_footer(text=f"Iniciado por {ctx.author.display_name}")
            
            msg = await canal_sorteio.send(embed=embed)
            await msg.add_reaction('🎁')
            
            # Salva ID da mensagem
            self.sorteios[guild_id]['mensagem_id'] = msg.id
            self.save_data()
        
        # Confirmação no canal de comando
        embed = discord.Embed(
            title="✅ Sorteio Iniciado",
            description=f"Sorteio do prêmio **{premio}** foi iniciado!",
            color=0x00ff7f
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='vencedor', aliases=['winner'])
    @commands.has_permissions(administrator=True)
    async def sortear_vencedor(self, ctx):
        """Sorteia um vencedor do sorteio ativo"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.sorteios or not self.sorteios[guild_id].get('ativo'):
            embed = discord.Embed(
                title="❌ Nenhum Sorteio Ativo",
                description="Não há sorteio em andamento.\nUse `!comecarsorteio <prêmio>` para iniciar um.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        # Verifica canal de comando
        configs = self.configuracoes.get(guild_id, {})
        canal_comando_id = configs.get('canal_comando')
        
        if canal_comando_id and ctx.channel.id != canal_comando_id:
            canal_comando = self.bot.get_channel(canal_comando_id)
            embed = discord.Embed(
                title="❌ Canal Incorreto",
                description=f"Use este comando no canal {canal_comando.mention if canal_comando else 'configurado'}.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        # Pega participantes da reação
        canal_sorteio_id = configs.get('canal_sorteio')
        canal_sorteio = self.bot.get_channel(canal_sorteio_id)
        
        if not canal_sorteio:
            embed = discord.Embed(
                title="❌ Canal do Sorteio Não Encontrado",
                description="O canal do sorteio foi removido ou não encontrado.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        try:
            msg_id = self.sorteios[guild_id].get('mensagem_id')
            if msg_id:
                msg = await canal_sorteio.fetch_message(msg_id)
                participantes = []
                
                for reaction in msg.reactions:
                    if str(reaction.emoji) == '🎁':
                        async for user in reaction.users():
                            if not user.bot:
                                participantes.append(user)
                        break
            else:
                participantes = []
        except:
            participantes = []
        
        if not participantes:
            embed = discord.Embed(
                title="❌ Sem Participantes",
                description="Nenhum participante encontrado no sorteio.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        # Sorteia vencedor
        vencedor = random.choice(participantes)
        premio = self.sorteios[guild_id]['premio']
        
        # Anuncia no canal do sorteio
        embed_vencedor = discord.Embed(
            title="🎊 TEMOS UM VENCEDOR!",
            description=f"🎉 Parabéns {vencedor.mention}!\n\n**Prêmio:** {premio}",
            color=0xffd700
        )
        embed_vencedor.set_footer(text=f"Sorteado entre {len(participantes)} participantes")
        
        await canal_sorteio.send(embed=embed_vencedor)
        
        # Confirmação no canal de comando
        embed = discord.Embed(
            title="🎊 Vencedor Sorteado",
            description=f"**Vencedor:** {vencedor.display_name}\n**Participantes:** {len(participantes)}",
            color=0xffd700
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='encerrarsorteio', aliases=['endgw'])
    @commands.has_permissions(administrator=True)
    async def encerrar_sorteio(self, ctx):
        """Encerra o sorteio ativo"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.sorteios or not self.sorteios[guild_id].get('ativo'):
            embed = discord.Embed(
                title="❌ Nenhum Sorteio Ativo",
                description="Não há sorteio em andamento para encerrar.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        # Verifica canal de comando
        configs = self.configuracoes.get(guild_id, {})
        canal_comando_id = configs.get('canal_comando')
        
        if canal_comando_id and ctx.channel.id != canal_comando_id:
            canal_comando = self.bot.get_channel(canal_comando_id)
            embed = discord.Embed(
                title="❌ Canal Incorreto",
                description=f"Use este comando no canal {canal_comando.mention if canal_comando else 'configurado'}.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        # Encerra o sorteio
        premio = self.sorteios[guild_id]['premio']
        self.sorteios[guild_id]['ativo'] = False
        self.save_data()
        
        # Anuncia encerramento no canal do sorteio
        canal_sorteio_id = configs.get('canal_sorteio')
        canal_sorteio = self.bot.get_channel(canal_sorteio_id)
        
        if canal_sorteio:
            embed_encerrado = discord.Embed(
                title="🔒 Sorteio Encerrado",
                description=f"O sorteio do prêmio **{premio}** foi encerrado.",
                color=0xff6666
            )
            await canal_sorteio.send(embed=embed_encerrado)
        
        # Confirmação
        embed = discord.Embed(
            title="✅ Sorteio Encerrado",
            description=f"O sorteio do prêmio **{premio}** foi encerrado com sucesso.",
            color=0x00ff7f
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='canaldecomando', aliases=['cmdchannel'])
    @commands.has_permissions(administrator=True)
    async def canal_comando(self, ctx, canal: discord.TextChannel):
        """Define o canal onde os comandos de sorteio podem ser usados"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.configuracoes:
            self.configuracoes[guild_id] = {}
        
        self.configuracoes[guild_id]['canal_comando'] = canal.id
        self.save_data()
        
        embed = discord.Embed(
            title="✅ Canal de Comando Definido",
            description=f"Os comandos de sorteio agora só podem ser usados em {canal.mention}",
            color=0x00ff7f
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='canaldosorteio', aliases=['gwchannel'])
    @commands.has_permissions(administrator=True)
    async def canal_sorteio(self, ctx, canal: discord.TextChannel):
        """Define o canal onde os sorteios serão realizados"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.configuracoes:
            self.configuracoes[guild_id] = {}
        
        self.configuracoes[guild_id]['canal_sorteio'] = canal.id
        self.save_data()
        
        embed = discord.Embed(
            title="✅ Canal do Sorteio Definido",
            description=f"Os sorteios serão realizados em {canal.mention}",
            color=0x00ff7f
        )
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Trata erros de permissão"""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você precisa ser **Administrador** para usar este comando.",
                color=0xff4444
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Sorteio(bot))