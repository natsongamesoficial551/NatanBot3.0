import discord
from discord.ext import commands
import json
import os

class WelcomeSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "welcome_config.json"
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def get_guild_config(self, guild_id):
        return self.config.get(str(guild_id), {})

    def set_guild_config(self, guild_id, key, value):
        guild_id = str(guild_id)
        if guild_id not in self.config:
            self.config[guild_id] = {}
        self.config[guild_id][key] = value
        self.save_config()

    @commands.command(name='canalconfig')
    @commands.has_permissions(administrator=True)
    async def canal_config(self, ctx, canal: discord.TextChannel):
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
        config = self.get_guild_config(ctx.guild.id)
        if 'canal_config' not in config or ctx.channel.id != config['canal_config']:
            embed = discord.Embed(
                title="❌ Erro",
                description="Use este comando apenas no canal configurado com !canalconfig",
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
        config = self.get_guild_config(ctx.guild.id)
        if 'canal_config' not in config or ctx.channel.id != config['canal_config']:
            embed = discord.Embed(
                title="❌ Erro",
                description="Use este comando apenas no canal configurado com !canalconfig",
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
        config = self.get_guild_config(ctx.guild.id)
        if 'canal_config' not in config or ctx.channel.id != config['canal_config']:
            embed = discord.Embed(
                title="❌ Erro",
                description="Use este comando apenas no canal configurado com !canalconfig",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        self.set_guild_config(ctx.guild.id, 'msg_entrada', mensagem)
        embed = discord.Embed(
            title="✅ Mensagem de Entrada Definida",
            description=f"Mensagem: {mensagem}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name='msgsaida')
    @commands.has_permissions(administrator=True)
    async def msg_saida(self, ctx, *, mensagem):
        config = self.get_guild_config(ctx.guild.id)
        if 'canal_config' not in config or ctx.channel.id != config['canal_config']:
            embed = discord.Embed(
                title="❌ Erro",
                description="Use este comando apenas no canal configurado com !canalconfig",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        self.set_guild_config(ctx.guild.id, 'msg_saida', mensagem)
        embed = discord.Embed(
            title="✅ Mensagem de Saída Definida",
            description=f"Mensagem: {mensagem}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name='configmsg')
    @commands.has_permissions(administrator=True)
    async def config_msg(self, ctx):
        config = self.get_guild_config(ctx.guild.id)
        if 'canal_config' not in config or ctx.channel.id != config['canal_config']:
            embed = discord.Embed(
                title="❌ Erro",
                description="Use este comando apenas no canal configurado com !canalconfig",
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
            name="Canal de Entrada",
            value=f"<#{canal_entrada}>" if canal_entrada else "Não configurado",
            inline=False
        )
        embed.add_field(
            name="Canal de Saída",
            value=f"<#{canal_saida}>" if canal_saida else "Não configurado",
            inline=False
        )
        embed.add_field(
            name="Mensagem de Entrada",
            value=msg_entrada,
            inline=False
        )
        embed.add_field(
            name="Mensagem de Saída",
            value=msg_saida,
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.command(name='testentrada')
    @commands.has_permissions(administrator=True)
    async def test_entrada(self, ctx):
        config = self.get_guild_config(ctx.guild.id)
        if 'canal_config' not in config or ctx.channel.id != config['canal_config']:
            embed = discord.Embed(
                title="❌ Erro",
                description="Use este comando apenas no canal configurado com !canalconfig",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        canal_entrada = config.get('canal_entrada')
        msg_entrada = config.get('msg_entrada')

        if not canal_entrada or not msg_entrada:
            embed = discord.Embed(
                title="❌ Erro",
                description="Configure o canal de entrada e a mensagem primeiro",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        canal = self.bot.get_channel(canal_entrada)
        if canal:
            mensagem_formatada = msg_entrada.replace('{user}', ctx.author.mention)
            mensagem_formatada = mensagem_formatada.replace('{server}', ctx.guild.name)
            mensagem_formatada = mensagem_formatada.replace('{count}', str(ctx.guild.member_count))

            embed = discord.Embed(
                title="🎉 Bem-vindo(a)!",
                description=mensagem_formatada,
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            await canal.send(embed=embed)

            embed_test = discord.Embed(
                title="✅ Teste Realizado",
                description="Mensagem de entrada enviada com sucesso!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed_test)

    @commands.command(name='testsaida')
    @commands.has_permissions(administrator=True)
    async def test_saida(self, ctx):
        config = self.get_guild_config(ctx.guild.id)
        if 'canal_config' not in config or ctx.channel.id != config['canal_config']:
            embed = discord.Embed(
                title="❌ Erro",
                description="Use este comando apenas no canal configurado com !canalconfig",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        canal_saida = config.get('canal_saida')
        msg_saida = config.get('msg_saida')

        if not canal_saida or not msg_saida:
            embed = discord.Embed(
                title="❌ Erro",
                description="Configure o canal de saída e a mensagem primeiro",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        canal = self.bot.get_channel(canal_saida)
        if canal:
            mensagem_formatada = msg_saida.replace('{user}', ctx.author.mention)
            mensagem_formatada = mensagem_formatada.replace('{server}', ctx.guild.name)
            mensagem_formatada = mensagem_formatada.replace('{count}', str(ctx.guild.member_count))

            embed = discord.Embed(
                title="👋 Até logo!",
                description=mensagem_formatada,
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            await canal.send(embed=embed)

            embed_test = discord.Embed(
                title="✅ Teste Realizado",
                description="Mensagem de saída enviada com sucesso!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed_test)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        config = self.get_guild_config(member.guild.id)
        canal_entrada = config.get('canal_entrada')
        msg_entrada = config.get('msg_entrada')

        if canal_entrada and msg_entrada:
            canal = self.bot.get_channel(canal_entrada)
            if canal:
                mensagem_formatada = msg_entrada.replace('{user}', member.mention)
                mensagem_formatada = mensagem_formatada.replace('{server}', member.guild.name)
                mensagem_formatada = mensagem_formatada.replace('{count}', str(member.guild.member_count))

                embed = discord.Embed(
                    title="🎉 Bem-vindo(a)!",
                    description=mensagem_formatada,
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await canal.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        config = self.get_guild_config(member.guild.id)
        canal_saida = config.get('canal_saida')
        msg_saida = config.get('msg_saida')

        if canal_saida and msg_saida:
            canal = self.bot.get_channel(canal_saida)
            if canal:
                mensagem_formatada = msg_saida.replace('{user}', str(member))
                mensagem_formatada = mensagem_formatada.replace('{server}', member.guild.name)
                mensagem_formatada = mensagem_formatada.replace('{count}', str(member.guild.member_count))

                embed = discord.Embed(
                    title="👋 Até logo!",
                    description=mensagem_formatada,
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await canal.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WelcomeSystem(bot))