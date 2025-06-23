import discord
from discord.ext import commands
import json
import os

class WelcomeSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "welcome_config.json"
        self.config = self.load_config()
        # Garante que o arquivo seja criado na inicialização
        self.ensure_config_file()

    def load_config(self):
        """Carrega a configuração do arquivo JSON"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Erro ao carregar configuração: {e}")
                return {}
        return {}

    def save_config(self):
        """Salva a configuração no arquivo JSON"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar configuração: {e}")

    def ensure_config_file(self):
        """Garante que o arquivo de configuração existe"""
        if not os.path.exists(self.config_file):
            self.save_config()
            print(f"Arquivo {self.config_file} criado com sucesso!")

    def get_guild_config(self, guild_id):
        """Obtém a configuração de um servidor específico"""
        return self.config.get(str(guild_id), {})

    def set_guild_config(self, guild_id, key, value):
        """Define uma configuração para um servidor específico"""
        guild_id = str(guild_id)
        if guild_id not in self.config:
            self.config[guild_id] = {}
        self.config[guild_id][key] = value
        self.save_config()

    @commands.command(name='canalconfig')
    @commands.has_permissions(administrator=True)
    async def canal_config(self, ctx, canal: discord.TextChannel):
        """Define o canal onde os comandos de configuração podem ser usados"""
        self.set_guild_config(ctx.guild.id, 'canal_config', canal.id)
        embed = discord.Embed(
            title="✅ Canal de Configuração Definido",
            description=f"Canal configurado para: {canal.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name='canalentrada')
    @commands.has_permissions(administrator=True)
    async def canal_entrada(self, ctx, canal: discord.TextChannel):
        """Define o canal para mensagens de boas-vindas"""
        config = self.get_guild_config(ctx.guild.id)
        if 'canal_config' not in config or ctx.channel.id != config['canal_config']:
            embed = discord.Embed(
                title="❌ Erro",
                description="Use este comando apenas no canal configurado com `!canalconfig`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        self.set_guild_config(ctx.guild.id, 'canal_entrada', canal.id)
        embed = discord.Embed(
            title="✅ Canal de Entrada Definido",
            description=f"Canal de entrada configurado para: {canal.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name='canalsaida')
    @commands.has_permissions(administrator=True)
    async def canal_saida(self, ctx, canal: discord.TextChannel):
        """Define o canal para mensagens de despedida"""
        config = self.get_guild_config(ctx.guild.id)
        if 'canal_config' not in config or ctx.channel.id != config['canal_config']:
            embed = discord.Embed(
                title="❌ Erro",
                description="Use este comando apenas no canal configurado com `!canalconfig`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        self.set_guild_config(ctx.guild.id, 'canal_saida', canal.id)
        embed = discord.Embed(
            title="✅ Canal de Saída Definido",
            description=f"Canal de saída configurado para: {canal.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name='msgentrada')
    @commands.has_permissions(administrator=True)
    async def msg_entrada(self, ctx, *, mensagem):
        """Define a mensagem de boas-vindas
        
        Variáveis disponíveis:
        {user} - Menciona o usuário
        {server} - Nome do servidor
        {count} - Número de membros
        """
        config = self.get_guild_config(ctx.guild.id)
        if 'canal_config' not in config or ctx.channel.id != config['canal_config']:
            embed = discord.Embed(
                title="❌ Erro",
                description="Use este comando apenas no canal configurado com `!canalconfig`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        self.set_guild_config(ctx.guild.id, 'msg_entrada', mensagem)
        embed = discord.Embed(
            title="✅ Mensagem de Entrada Definida",
            description=f"**Mensagem:** {mensagem}\n\n**Variáveis disponíveis:**\n`{user}` - Menciona o usuário\n`{server}` - Nome do servidor\n`{count}` - Número de membros",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name='msgsaida')
    @commands.has_permissions(administrator=True)
    async def msg_saida(self, ctx, *, mensagem):
        """Define a mensagem de despedida
        
        Variáveis disponíveis:
        {user} - Nome do usuário
        {server} - Nome do servidor
        {count} - Número de membros
        """
        config = self.get_guild_config(ctx.guild.id)
        if 'canal_config' not in config or ctx.channel.id != config['canal_config']:
            embed = discord.Embed(
                title="❌ Erro",
                description="Use este comando apenas no canal configurado com `!canalconfig`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        self.set_guild_config(ctx.guild.id, 'msg_saida', mensagem)
        embed = discord.Embed(
            title="✅ Mensagem de Saída Definida",
            description=f"**Mensagem:** {mensagem}\n\n**Variáveis disponíveis:**\n`{user}` - Nome do usuário\n`{server}` - Nome do servidor\n`{count}` - Número de membros",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name='configmsg')
    @commands.has_permissions(administrator=True)
    async def config_msg(self, ctx):
        """Mostra a configuração atual das mensagens"""
        config = self.get_guild_config(ctx.guild.id)
        if 'canal_config' not in config or ctx.channel.id != config['canal_config']:
            embed = discord.Embed(
                title="❌ Erro",
                description="Use este comando apenas no canal configurado com `!canalconfig`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="⚙️ Configuração das Mensagens",
            color=discord.Color.blue()
        )
        
        canal_entrada = config.get('canal_entrada')
        canal_saida = config.get('canal_saida')
        msg_entrada = config.get('msg_entrada', 'Não configurada')
        msg_saida = config.get('msg_saida', 'Não configurada')

        embed.add_field(
            name="📥 Canal de Entrada",
            value=f"<#{canal_entrada}>" if canal_entrada else "❌ Não configurado",
            inline=False
        )
        embed.add_field(
            name="📤 Canal de Saída",
            value=f"<#{canal_saida}>" if canal_saida else "❌ Não configurado",
            inline=False
        )
        embed.add_field(
            name="💬 Mensagem de Entrada",
            value=msg_entrada if msg_entrada != 'Não configurada' else "❌ Não configurada",
            inline=False
        )
        embed.add_field(
            name="👋 Mensagem de Saída",
            value=msg_saida if msg_saida != 'Não configurada' else "❌ Não configurada",
            inline=False
        )

        embed.set_footer(text="Use !testentrada e !testsaida para testar as configurações")
        await ctx.send(embed=embed)

    @commands.command(name='testentrada')
    @commands.has_permissions(administrator=True)
    async def test_entrada(self, ctx):
        """Testa a mensagem de boas-vindas"""
        config = self.get_guild_config(ctx.guild.id)
        if 'canal_config' not in config or ctx.channel.id != config['canal_config']:
            embed = discord.Embed(
                title="❌ Erro",
                description="Use este comando apenas no canal configurado com `!canalconfig`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        canal_entrada = config.get('canal_entrada')
        msg_entrada = config.get('msg_entrada')

        if not canal_entrada or not msg_entrada:
            embed = discord.Embed(
                title="❌ Configuração Incompleta",
                description="Configure o canal de entrada e a mensagem primeiro usando:\n`!canalentrada #canal`\n`!msgentrada sua mensagem aqui`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        canal = self.bot.get_channel(canal_entrada)
        if not canal:
            embed = discord.Embed(
                title="❌ Canal Não Encontrado",
                description="O canal configurado não foi encontrado. Configure novamente com `!canalentrada`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Formatar mensagem com as variáveis
        mensagem_formatada = self.format_message(msg_entrada, ctx.author, ctx.guild)

        embed = discord.Embed(
            title="🎉 Bem-vindo(a)!",
            description=mensagem_formatada,
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text="Esta é uma mensagem de teste")
        await canal.send(embed=embed)

        embed_test = discord.Embed(
            title="✅ Teste Realizado",
            description=f"Mensagem de entrada enviada em {canal.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed_test)

    @commands.command(name='testsaida')
    @commands.has_permissions(administrator=True)
    async def test_saida(self, ctx):
        """Testa a mensagem de despedida"""
        config = self.get_guild_config(ctx.guild.id)
        if 'canal_config' not in config or ctx.channel.id != config['canal_config']:
            embed = discord.Embed(
                title="❌ Erro",
                description="Use este comando apenas no canal configurado com `!canalconfig`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        canal_saida = config.get('canal_saida')
        msg_saida = config.get('msg_saida')

        if not canal_saida or not msg_saida:
            embed = discord.Embed(
                title="❌ Configuração Incompleta",
                description="Configure o canal de saída e a mensagem primeiro usando:\n`!canalsaida #canal`\n`!msgsaida sua mensagem aqui`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        canal = self.bot.get_channel(canal_saida)
        if not canal:
            embed = discord.Embed(
                title="❌ Canal Não Encontrado",
                description="O canal configurado não foi encontrado. Configure novamente com `!canalsaida`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Formatar mensagem com as variáveis (para saída usamos str(member) ao invés de mention)
        mensagem_formatada = msg_saida.replace('{user}', str(ctx.author))
        mensagem_formatada = mensagem_formatada.replace('{server}', ctx.guild.name)
        mensagem_formatada = mensagem_formatada.replace('{count}', str(ctx.guild.member_count))

        embed = discord.Embed(
            title="👋 Até logo!",
            description=mensagem_formatada,
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text="Esta é uma mensagem de teste")
        await canal.send(embed=embed)

        embed_test = discord.Embed(
            title="✅ Teste Realizado",
            description=f"Mensagem de saída enviada em {canal.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed_test)

    def format_message(self, message, member, guild):
        """Formata a mensagem substituindo as variáveis"""
        if isinstance(member, discord.Member):
            user_reference = member.mention
        else:
            user_reference = str(member)
        
        formatted = message.replace('{user}', user_reference)
        formatted = formatted.replace('{server}', guild.name)
        formatted = formatted.replace('{count}', str(guild.member_count))
        return formatted

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Evento disparado quando um membro entra no servidor"""
        config = self.get_guild_config(member.guild.id)
        canal_entrada = config.get('canal_entrada')
        msg_entrada = config.get('msg_entrada')

        if canal_entrada and msg_entrada:
            canal = self.bot.get_channel(canal_entrada)
            if canal:
                mensagem_formatada = self.format_message(msg_entrada, member, member.guild)

                embed = discord.Embed(
                    title="🎉 Bem-vindo(a)!",
                    description=mensagem_formatada,
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await canal.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Evento disparado quando um membro sai do servidor"""
        config = self.get_guild_config(member.guild.id)
        canal_saida = config.get('canal_saida')
        msg_saida = config.get('msg_saida')

        if canal_saida and msg_saida:
            canal = self.bot.get_channel(canal_saida)
            if canal:
                # Para saída, usamos str(member) em vez de mention
                mensagem_formatada = msg_saida.replace('{user}', str(member))
                mensagem_formatada = mensagem_formatada.replace('{server}', member.guild.name)
                mensagem_formatada = mensagem_formatada.replace('{count}', str(member.guild.member_count))

                embed = discord.Embed(
                    title="👋 Até logo!",
                    description=mensagem_formatada,
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                await canal.send(embed=embed)

    @commands.command(name='helpwelcome')
    async def help_welcome(self, ctx):
        """Mostra ajuda sobre os comandos do sistema de boas-vindas"""
        embed = discord.Embed(
            title="🤖 Sistema de Boas-vindas - Ajuda",
            description="Lista de comandos disponíveis:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🔧 Configuração Inicial",
            value="`!canalconfig #canal` - Define o canal para configurações",
            inline=False
        )
        
        embed.add_field(
            name="📥 Configurar Entrada",
            value="`!canalentrada #canal` - Canal para boas-vindas\n`!msgentrada mensagem` - Mensagem de boas-vindas",
            inline=False
        )
        
        embed.add_field(
            name="📤 Configurar Saída",
            value="`!canalsaida #canal` - Canal para despedidas\n`!msgsaida mensagem` - Mensagem de despedida",
            inline=False
        )
        
        embed.add_field(
            name="📋 Verificar e Testar",
            value="`!configmsg` - Ver configurações\n`!testentrada` - Testar boas-vindas\n`!testsaida` - Testar despedida",
            inline=False
        )
        
        embed.add_field(
            name="📝 Variáveis Disponíveis",
            value="`{user}` - Usuário (mention na entrada, nome na saída)\n`{server}` - Nome do servidor\n`{count}` - Número de membros",
            inline=False
        )
        
        embed.set_footer(text="Todos os comandos (exceto !helpwelcome) requerem permissão de Administrador")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WelcomeSystem(bot))