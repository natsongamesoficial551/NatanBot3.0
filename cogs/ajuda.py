import discord
from discord.ext import commands

class Ajuda(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ajuda", help="Mostra todos os comandos organizados por categoria")
    async def ajuda(self, ctx):
        embed = discord.Embed(
            title="📖 Comandos do NatanBot",
            description="Veja abaixo os comandos organizados por categoria.",
            color=discord.Color.blue()
        )

        embed.add_field(name="🎉 Aniversário", value=(
            "`!adicionardata DD/MM`\n"
            "`!aniversariantes`\n"
            "`!meuaniversario`\n"
            "`!removeraniversario`\n"
            "`!proximosaniversarios`"
        ), inline=False)

        embed.add_field(name="🛡️ Antipalavrão", value=(
            "`!adicionarpalavrao <palavra>`\n"
            "`!removerpalavrao <palavra>`\n"
            "`!palavroes`\n"
            "`!togglefiltro`"
        ), inline=False)

        embed.add_field(name="🎁 Sorteios", value=(
            "`!comecarsorteio <premio>`\n"
            "`!vencedor`\n"
            "`!encerrarsorteio`\n"
            "`!canaldecomando #canal`\n"
            "`!canaldosorteio #canal`"
        ), inline=False)

        embed.add_field(name="📈 XP", value=(
            "`!mensagemporxp <min> <max>`\n"
            "`!basexp <valor>`\n"
            "`!adicionarxppornivel <valor>`\n"
            "`!tempodexp <normal> [vip]`\n"
            "`!configxp`"
        ), inline=False)

        embed.add_field(name="💎 VIP", value=(
            "`!vip @user dias`\n"
            "`!removervip @user`\n"
            "`!configvip`\n"
            "`!cargovip <ID>`\n"
            "`!listvip`\n"
            "`!checkvip [@user]`"
        ), inline=False)

        embed.add_field(name="🔨 Moderação", value=(
            "`!aviso @user [motivo]`\n"
            "`!removeraviso @user [número]`\n"
            "`!avisos [@user]`\n"
            "`!mutar @user tempo [motivo]`\n"
            "`!desmutar @user`\n"
            "`!banir @user`\n"
            "`!expulsar @user`\n"
            "`!limparmensagem [quantidade]`\n"
            "`!configmod`"
        ), inline=False)

        embed.add_field(name="👋 Boas-Vindas", value=(
            "`!canalconfig #canal`\n"
            "`!canalentrada #canal`\n"
            "`!canalsaida #canal`\n"
            "`!msgentrada mensagem`\n"
            "`!msgsaida mensagem`\n"
            "`!configmsg`\n"
            "`!testentrada`\n"
            "`!testsaida`"
        ), inline=False)

        embed.add_field(name="📜 Logs", value="`!canaldelogs #canal`", inline=False)

        embed.add_field(name="🎫 Tickets", value=(
            "`!ticket`\n"
            "`!fecharticket`\n"
            "`!adicionarcategoriaticket ID`\n"
            "`!canaldecomandoticket #canal`\n"
            "`!configticket`"
        ), inline=False)

        embed.add_field(name="💰 Economia", value=(
            "`!saldo / !bal`\n"
            "`!diario / !daily`\n"
            "`!inventario / !inv`\n"
            "`!trabalhar / !work`\n"
            "`!empregos / !jobs`\n"
            "`!depositar / !dep`\n"
            "`!sacar / !withdraw`\n"
            "`!loja / !shop`\n"
            "`!comprar / !buy`\n"
            "`!vender / !sell`\n"
            "`!crime`\n"
            "`!roubar / !rob`\n"
            "`!apostar / !bet`\n"
            "`!loteria / !lottery`\n"
            "`!presentear / !gift`\n"
            "`!contratar / !hire`\n"
            "`!demitir / !fire`\n"
            "`!adicionaritem / !additem`\n"
            "`!dar / !give`"
        ), inline=False)

        embed.add_field(name="🔧 Utilidades", value=(
            "`!botinfo`\n"
            "`!userinfo`\n"
            "`!serverinfo`\n"
            "`!ping`\n"
            "`!avatar`\n"
            "`!banner`\n"
            "`!invite`\n"
            "`!uptime`\n"
            "`!membercount`"
        ), inline=False)

        embed.add_field(name="📡 Status", value=(
            "`!statusmodo`\n"
            "`!listarstatus`\n"
            "`!statusintervalo <minutos>`\n"
            "`!statusmanual`"
        ), inline=False)

        embed.set_footer(text="Use os comandos com ! no início. Ex: !ping")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Ajuda(bot))
