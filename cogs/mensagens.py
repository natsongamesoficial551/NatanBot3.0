import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime
import asyncio

class Mensagens(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "mensagens_automaticas.json"
        self.load_data()
        self.tarefas_ativas = {}
        self.iniciar_tarefas()
    
    def load_data(self):
        """Carrega dados do arquivo JSON ou cria um novo se não existir"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.mensagens = json.load(f)
        else:
            self.mensagens = {}
            self.save_data()
    
    def save_data(self):
        """Salva dados no arquivo JSON"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.mensagens, f, indent=2, ensure_ascii=False)
    
    def iniciar_tarefas(self):
        """Inicia todas as tarefas automáticas salvas"""
        for nome, dados in self.mensagens.items():
            if dados.get('ativo', True):
                self.criar_tarefa(nome, dados)
    
    def criar_tarefa(self, nome, dados):
        """Cria uma tarefa automática para enviar mensagens"""
        async def enviar_mensagem_automatica():
            while True:
                try:
                    await asyncio.sleep(dados['intervalo'] * 3600)  # Converte horas para segundos
                    
                    # Verifica se a tarefa ainda está ativa
                    if nome not in self.mensagens or not self.mensagens[nome].get('ativo', True):
                        break
                    
                    canal = self.bot.get_channel(dados['canal_id'])
                    if canal:
                        await canal.send(dados['mensagem'])
                        
                        # Atualiza contador de envios
                        self.mensagens[nome]['envios'] = self.mensagens[nome].get('envios', 0) + 1
                        self.save_data()
                
                except Exception as e:
                    print(f"Erro ao enviar mensagem automática '{nome}': {e}")
                    break
        
        # Cria e inicia a tarefa
        tarefa = asyncio.create_task(enviar_mensagem_automatica())
        self.tarefas_ativas[nome] = tarefa
    
    def parar_tarefa(self, nome):
        """Para uma tarefa específica"""
        if nome in self.tarefas_ativas:
            self.tarefas_ativas[nome].cancel()
            del self.tarefas_ativas[nome]
    
    @commands.command(name='adicionarmensagem', aliases=['addmsg'])
    @commands.has_permissions(manage_messages=True)
    async def adicionar_mensagem(self, ctx, horas: float, *, mensagem):
        """Adiciona uma mensagem automática. Uso: !adicionarmensagem <horas> <mensagem>"""
        
        if horas <= 0:
            embed = discord.Embed(
                title="❌ Erro",
                description="O intervalo deve ser maior que 0 horas.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        if not mensagem or len(mensagem.strip()) == 0:
            embed = discord.Embed(
                title="❌ Erro",
                description="Você precisa especificar uma mensagem.\n**Uso:** `!adicionarmensagem <horas> <mensagem>`",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        # Cria um nome único baseado no timestamp
        nome = f"msg_{int(datetime.now().timestamp())}"
        
        # Adiciona a mensagem
        dados_mensagem = {
            'mensagem': mensagem,
            'intervalo': horas,
            'canal_id': ctx.channel.id,
            'canal_nome': ctx.channel.name,
            'autor': ctx.author.display_name,
            'autor_id': ctx.author.id,
            'data_criacao': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'ativo': True,
            'envios': 0
        }
        
        self.mensagens[nome] = dados_mensagem
        self.save_data()
        
        # Inicia a tarefa
        self.criar_tarefa(nome, dados_mensagem)
        
        embed = discord.Embed(
            title="✅ Mensagem Automática Adicionada",
            description=f"Mensagem será enviada a cada **{horas}h** no canal {ctx.channel.mention}",
            color=0x00ff7f
        )
        embed.add_field(name="📝 Mensagem", value=mensagem[:200] + "..." if len(mensagem) > 200 else mensagem, inline=False)
        embed.add_field(name="⏰ Intervalo", value=f"{horas} horas", inline=True)
        embed.add_field(name="📍 Canal", value=ctx.channel.mention, inline=True)
        await ctx.send(embed=embed)
    
    @commands.command(name='removermensagem', aliases=['rmmsg'])
    @commands.has_permissions(manage_messages=True)
    async def remover_mensagem(self, ctx, *, mensagem_busca):
        """Remove uma mensagem automática pela mensagem ou parte dela"""
        
        if not mensagem_busca:
            embed = discord.Embed(
                title="❌ Erro",
                description="Você precisa especificar a mensagem ou parte dela para remover.\n**Uso:** `!removermensagem <mensagem>`",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        # Busca mensagem que contenha o texto
        mensagem_encontrada = None
        nome_encontrado = None
        
        for nome, dados in self.mensagens.items():
            if mensagem_busca.lower() in dados['mensagem'].lower():
                mensagem_encontrada = dados
                nome_encontrado = nome
                break
        
        if not mensagem_encontrada:
            embed = discord.Embed(
                title="❓ Mensagem Não Encontrada",
                description=f"Não foi encontrada nenhuma mensagem contendo: `{mensagem_busca}`\nUse `!mensagens` para ver todas as mensagens.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        # Para a tarefa e remove a mensagem
        self.parar_tarefa(nome_encontrado)
        del self.mensagens[nome_encontrado]
        self.save_data()
        
        embed = discord.Embed(
            title="🗑️ Mensagem Removida",
            description="A mensagem automática foi removida com sucesso.",
            color=0xff6666
        )
        embed.add_field(name="📝 Mensagem Removida", value=mensagem_encontrada['mensagem'][:200] + "..." if len(mensagem_encontrada['mensagem']) > 200 else mensagem_encontrada['mensagem'], inline=False)
        embed.add_field(name="⏰ Intervalo", value=f"{mensagem_encontrada['intervalo']}h", inline=True)
        embed.add_field(name="📊 Envios", value=str(mensagem_encontrada['envios']), inline=True)
        await ctx.send(embed=embed)
    
    @commands.command(name='mensagens', aliases=['listmsg'])
    async def listar_mensagens(self, ctx):
        """Lista todas as mensagens automáticas ativas"""
        if not self.mensagens:
            embed = discord.Embed(
                title="📝 Mensagens Automáticas",
                description="Nenhuma mensagem automática cadastrada ainda.\nUse `!adicionarmensagem <horas> <mensagem>` para adicionar uma.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        # Filtra apenas mensagens ativas
        mensagens_ativas = {nome: dados for nome, dados in self.mensagens.items() if dados.get('ativo', True)}
        
        if not mensagens_ativas:
            embed = discord.Embed(
                title="📝 Mensagens Automáticas",
                description="Nenhuma mensagem automática ativa no momento.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        # Cria a lista formatada
        lista_mensagens = []
        for nome, dados in mensagens_ativas.items():
            canal = self.bot.get_channel(dados['canal_id'])
            canal_nome = canal.mention if canal else f"#{dados['canal_nome']} (canal removido)"
            
            preview = dados['mensagem'][:80] + "..." if len(dados['mensagem']) > 80 else dados['mensagem']
            lista_mensagens.append(f"📌 **{preview}**")
            lista_mensagens.append(f"   └ ⏰ A cada {dados['intervalo']}h | 📍 {canal_nome} | 📊 {dados['envios']} envios")
            lista_mensagens.append("")  # Linha em branco para separar
        
        # Remove a última linha em branco
        if lista_mensagens:
            lista_mensagens.pop()
        
        embed = discord.Embed(
            title="📝 Mensagens Automáticas Ativas",
            description="\n".join(lista_mensagens),
            color=0x9966ff
        )
        embed.set_footer(text=f"Total: {len(mensagens_ativas)} mensagens ativas")
        await ctx.send(embed=embed)
    
    @commands.command(name='testmensagem', aliases=['testmsg'])
    @commands.has_permissions(manage_messages=True)
    async def testar_mensagem(self, ctx, *, mensagem_busca):
        """Testa uma mensagem automática enviando ela imediatamente"""
        
        if not mensagem_busca:
            embed = discord.Embed(
                title="❌ Erro",
                description="Você precisa especificar a mensagem ou parte dela para testar.\n**Uso:** `!testmensagem <mensagem>`",
                color=0xff4444
            )
            await ctx.send(embed=embed)
            return
        
        # Busca mensagem que contenha o texto
        mensagem_encontrada = None
        
        for nome, dados in self.mensagens.items():
            if mensagem_busca.lower() in dados['mensagem'].lower():
                mensagem_encontrada = dados
                break
        
        if not mensagem_encontrada:
            embed = discord.Embed(
                title="❓ Mensagem Não Encontrada",
                description=f"Não foi encontrada nenhuma mensagem contendo: `{mensagem_busca}`\nUse `!mensagens` para ver todas as mensagens.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        # Envia a mensagem de teste
        embed_teste = discord.Embed(
            title="🧪 Teste de Mensagem Automática",
            description="Esta é uma prévia da mensagem automática:",
            color=0x00aaff
        )
        await ctx.send(embed=embed_teste)
        
        # Envia a mensagem real
        await ctx.send(mensagem_encontrada['mensagem'])
        
        # Confirmação
        embed_confirmacao = discord.Embed(
            title="✅ Teste Realizado",
            description=f"A mensagem foi testada com sucesso!\n**Intervalo configurado:** {mensagem_encontrada['intervalo']}h",
            color=0x00ff7f
        )
        await ctx.send(embed=embed_confirmacao)
    
    @adicionar_mensagem.error
    @remover_mensagem.error
    @testar_mensagem.error
    async def comando_error(self, ctx, error):
        """Trata erros de permissão e conversão"""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você precisa da permissão **Gerenciar Mensagens** para usar este comando.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ Formato Inválido",
                description="O número de horas deve ser um número válido (ex: 3, 2.5, 0.5).",
                color=0xff4444
            )
            await ctx.send(embed=embed)
    
    def cog_unload(self):
        """Para todas as tarefas quando o cog é descarregado"""
        for tarefa in self.tarefas_ativas.values():
            tarefa.cancel()

async def setup(bot):
    await bot.add_cog(Mensagens(bot))