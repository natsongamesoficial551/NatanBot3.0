import discord
from discord.ext import commands
import json
import os
import re

class Antipalavrao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "palavroes.json"
        self.load_data()
    
    def load_data(self):
        """Carrega dados do arquivo JSON ou cria um novo se não existir"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.palavroes = data.get('palavroes', [])
                self.configuracoes = data.get('configuracoes', {
                    'ativo': True,
                    'deletar_mensagem': True,
                    'avisar_usuario': True
                })
        else:
            self.palavroes = []
            self.configuracoes = {
                'ativo': True,
                'deletar_mensagem': True,
                'avisar_usuario': True
            }
            self.save_data()
    
    def save_data(self):
        """Salva dados no arquivo JSON"""
        data = {
            'palavroes': self.palavroes,
            'configuracoes': self.configuracoes
        }
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @commands.command(name='adicionarpalavrao', aliases=['addword'])
    @commands.has_permissions(manage_messages=True)
    async def adicionar_palavrao(self, ctx, *, palavra):
        """Adiciona uma palavra à lista de palavrões"""
        palavra = palavra.lower().strip()
        
        if not palavra:
            embed = discord.Embed(
                title="❌ Erro",
                description="Você precisa especificar uma palavra.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        if palavra in self.palavroes:
            embed = discord.Embed(
                title="⚠️ Palavra Já Existe",
                description=f"A palavra `{palavra}` já está na lista de palavrões.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        self.palavroes.append(palavra)
        self.save_data()
        
        embed = discord.Embed(
            title="🚫 Palavra Adicionada",
            description=f"A palavra `{palavra}` foi adicionada à lista de palavrões.",
            color=0x00ff7f
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='removerpalavrao', aliases=['rmword'])
    @commands.has_permissions(manage_messages=True)
    async def remover_palavrao(self, ctx, *, palavra):
        """Remove uma palavra da lista de palavrões"""
        palavra = palavra.lower().strip()
        
        if not palavra:
            embed = discord.Embed(
                title="❌ Erro",
                description="Você precisa especificar uma palavra.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        if palavra not in self.palavroes:
            embed = discord.Embed(
                title="❓ Palavra Não Encontrada",
                description=f"A palavra `{palavra}` não está na lista de palavrões.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        self.palavroes.remove(palavra)
        self.save_data()
        
        embed = discord.Embed(
            title="✅ Palavra Removida",
            description=f"A palavra `{palavra}` foi removida da lista de palavrões.",
            color=0x00ff7f
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='palavroes', aliases=['listwords'])
    @commands.has_permissions(manage_messages=True)
    async def listar_palavroes(self, ctx):
        """Lista todos os palavrões cadastrados"""
        if not self.palavroes:
            embed = discord.Embed(
                title="📝 Lista de Palavrões",
                description="Nenhuma palavra cadastrada ainda.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        # Organiza em páginas se tiver muitas palavras
        palavras_por_pagina = 20
        total_paginas = (len(self.palavroes) + palavras_por_pagina - 1) // palavras_por_pagina
        
        # Primeira página
        pagina_atual = 1
        inicio = 0
        fim = min(palavras_por_pagina, len(self.palavroes))
        
        palavras_formatadas = []
        for i, palavra in enumerate(self.palavroes[inicio:fim], 1):
            palavras_formatadas.append(f"`{i + inicio}.` {palavra}")
        
        embed = discord.Embed(
            title="🚫 Lista de Palavrões",
            description="\n".join(palavras_formatadas),
            color=0xff6666
        )
        
        if total_paginas > 1:
            embed.set_footer(text=f"Página {pagina_atual}/{total_paginas} • Total: {len(self.palavroes)} palavras")
        else:
            embed.set_footer(text=f"Total: {len(self.palavroes)} palavras")
        
        status = "🟢 Ativo" if self.configuracoes['ativo'] else "🔴 Inativo"
        embed.add_field(name="Status", value=status, inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='togglefiltro', aliases=['toggle'])
    @commands.has_permissions(manage_messages=True)
    async def toggle_filtro(self, ctx):
        """Ativa/desativa o filtro de palavrões"""
        self.configuracoes['ativo'] = not self.configuracoes['ativo']
        self.save_data()
        
        status = "ativado" if self.configuracoes['ativo'] else "desativado"
        cor = 0x00ff7f if self.configuracoes['ativo'] else 0xff6666
        emoji = "🟢" if self.configuracoes['ativo'] else "🔴"
        
        embed = discord.Embed(
            title=f"{emoji} Filtro {status.capitalize()}",
            description=f"O filtro de palavrões foi **{status}**.",
            color=cor
        )
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Monitora mensagens em busca de palavrões"""
        # Ignora bots e mensagens diretas
        if message.author.bot or not message.guild:
            return
        
        # Verifica se o filtro está ativo
        if not self.configuracoes.get('ativo', True):
            return
        
        # Ignora membros com permissão de gerenciar mensagens
        if message.author.guild_permissions.manage_messages:
            return
        
        # Verifica se a mensagem contém palavrões
        conteudo = message.content.lower()
        palavrao_encontrado = None
        
        for palavrao in self.palavroes:
            # Usa regex para encontrar a palavra como palavra completa
            padrao = r'\b' + re.escape(palavrao) + r'\b'
            if re.search(padrao, conteudo):
                palavrao_encontrado = palavrao
                break
        
        if palavrao_encontrado:
            # Deleta a mensagem se configurado
            if self.configuracoes.get('deletar_mensagem', True):
                try:
                    await message.delete()
                except discord.NotFound:
                    pass  # Mensagem já foi deletada
                except discord.Forbidden:
                    pass  # Sem permissão para deletar
            
            # Avisa o usuário se configurado
            if self.configuracoes.get('avisar_usuario', True):
                embed = discord.Embed(
                    title="⚠️ Linguagem Inadequada",
                    description=f"{message.author.mention}, por favor mantenha um linguajar adequado no servidor.",
                    color=0xffaa00
                )
                embed.set_footer(text="Esta mensagem será removida em 10 segundos")
                
                try:
                    aviso = await message.channel.send(embed=embed)
                    # Remove o aviso após 10 segundos
                    await aviso.delete(delay=10)
                except discord.Forbidden:
                    pass  # Sem permissão para enviar mensagem
    
    @adicionar_palavrao.error
    @remover_palavrao.error
    @listar_palavroes.error
    @toggle_filtro.error
    async def comando_error(self, ctx, error):
        """Trata erros de permissão"""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você precisa da permissão **Gerenciar Mensagens** para usar este comando.",
                color=0xff4444
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Antipalavrao(bot))