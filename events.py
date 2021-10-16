import discord, os, operator, threading, time, pytz
from discord.ext import commands, tasks
from util.ledger import Ledger
from util.stocks import IEXCloud
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from config import TOKEN, INITIAL_BALANCE
from util.helpers import *

ledger = Ledger()
stocks = IEXCloud()
stocks.run()
intents = discord.Intents().all()
command_prefix = "!"
bot = commands.Bot(command_prefix=command_prefix, intents=intents)
bot.remove_command("help")
embed_color = 0x00FF00


def add_embed(
    title=None,
    description=None,
    fields=None,
    inline=False,
    ctx=None,
    thumbnail=None,
    author=None,
    image=None,
    footer=None,
    color=embed_color,
):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
    )
    if fields != None:
        for name, value in fields:
            embed.add_field(
                name=name,
                value=value,
                inline=inline,
            )
    if author != None:
        embed.set_author(name=author.name, icon_url=author.avatar_url)
    if image != None:
        embed.set_image(url=image)
    if footer != None:
        embed.set_footer(text=footer)
    if thumbnail != None:
        embed.set_thumbnail(url=thumbnail)
    return embed


@bot.command()
async def help(ctx):
    fields = [
        ("!add", "Sign up for StocksBot"),
        ("!buy (type) (symbol) (amount)", "To purchase shares ex. !buy cash AAPL 1000"),
        ("!sell (type) (symbol) (amount)", "To sell shares ex. !sell qty TSLA 1000"),
        ("!liquidate", "To liquidate all assets"),
        ("!portfolio (id)", "To view all your assets"),
        ("!stock (symbol)", "To view the stock trend of a specific company ex. !stock AMZN"),
    ]
    embed = add_embed("Help", description="Descriptions for all the commmands", fields=fields)
    await ctx.send(embed=embed)


@bot.command()
async def echo(ctx, *, content: str):
    await ctx.send(content)


@bot.command()
async def add(ctx):
    id = str(ctx.author.id)
    name = ctx.author.name
    if ledger.contains(id):
        embed = add_embed(
            "StocksBot",
            "Error: Already registered with StocksBot!",
            color=0xFF0000,
            author=ctx.author,
        )
    else:
        ledger.add_user(id, name)
        embed = add_embed("StocksBot", "You have been added to StocksBot!", author=ctx.author)
    await ctx.send(embed=embed)


@bot.command(aliases=["b"])
async def buy(ctx, type: str, symbol: str, amount: str):
    symbol = symbol.upper()
    id = str(ctx.author.id)
    name = ctx.author.name
    try:
        price = stocks.latest_price(symbol)
        if price == None:
            raise
    except:
        embed = add_embed(f'"{symbol}" couldn\'t be found', author=ctx.author)
        await ctx.send(embed=embed)
        return
    if amount == "all":
        qty = None
    elif type == "cash":
        qty = float(amount) / price
    elif type == "qty":
        qty = float(amount)
    else:
        await ctx.send(f"Invalid Command {ctx.author.mention}")

    if qty != None and qty < 0.1:
        embed = add_embed(
            "Error in Transaction",
            f"{ctx.author.mention} need to buy more than .1 shares",
            author=ctx.author,
        )
        await ctx.send(embed=embed)
        return
    pqty = ledger.enter_position(str(id), "long", symbol, price, qty)
    if pqty == False:
        embed = add_embed(
            "Error in Transaction",
            f"{ctx.author.mention} error processing transaction! (Maybe Overbought)",
            author=ctx.author,
        )
        await ctx.send(embed=embed)
    else:
        fields = [
            ("Share Price", f"${rnd(price)}"),
            ("Quantity", f"{rnd(pqty)} shares"),
            ("Worth", f"${rnd(pqty * price)}"),
        ]
        footer = f"Transaction at {sdate()}"
        embed = add_embed(
            f"Bought {symbol}",
            f"Remaining Balance: ${rnd(ledger.get_balance(id))}",
            fields=fields,
            author=ctx.author,
            inline=True,
            footer=footer,
        )
        await ctx.send(embed=embed)



@bot.command(aliases=["s"])
async def sell(ctx, type: str, symbol: str, amount: str):
    symbol = symbol.upper()
    id = str(ctx.author.id)
    name = ctx.author.name
    price = stocks.latest_price(symbol)
    try:
        price = stocks.latest_price(symbol)
        if price == None:
            raise
    except:
        embed = add_embed(f'"{symbol}" couldn\'t be found', author=ctx.author)
        await ctx.send(embed=embed)
        return
    if amount == "all":
        qty = None
    elif type == "cash":
        qty = float(amount) / price
    elif type == "qty":
        qty = float(amount)
    else:
        await ctx.send(f"Invalid Command {ctx.author.mention}")

    if qty != None and qty < 0.1:
        embed = add_embed(
            "Error in Transaction",
            f"{ctx.author.mention} need to sell more than .1 shares",
            author=ctx.author,
        )
        await ctx.send(embed=embed)
        return
    pqty = ledger.exit_position(id, "sell", symbol, price, qty)
    if pqty == False:
        embed = add_embed(
            "Error in Transaction",
            f"{ctx.author.mention} error processing transaction! (Maybe Oversold)",
            author=ctx.author,
        )
        await ctx.send(embed=embed)
    else:
        fields = [
            ("Share Price", f"${rnd(price)}"),
            ("Quantity", f"{rnd(pqty)} shares"),
            ("Worth", f"${rnd(pqty * price)}"),
        ]
        footer = f"Transaction at {sdate()}"
        embed = add_embed(
            f"Sold {symbol}",
            f"Remaining Balance: ${rnd(ledger.get_balance(id))}",
            fields=fields,
            author=ctx.author,
            inline=True,
            footer=footer,
        )
        await ctx.send(embed=embed)


@bot.command()
async def short(ctx, type: str, symbol: str, amount: str):
    symbol = symbol.upper()
    id = str(ctx.author.id)
    name = ctx.author.name
    try:
        price = stocks.latest_price(symbol)
        if price == None:
            raise
    except:
        embed = add_embed(f'"{symbol}" couldn\'t be found', author=ctx.author)
        await ctx.send(embed=embed)
        return
    if amount == "all":
        qty = None
    elif type == "cash":
        qty = float(amount) / price
    elif type == "qty":
        qty = float(amount)
    else:
        await ctx.send(f"Invalid Command {ctx.author.mention}")

    if qty != None and qty < 0.1:
        embed = add_embed(
            "Error in Transaction",
            f"{ctx.author.mention} need to short more than .1 shares",
            author=ctx.author,
        )
        await ctx.send(embed=embed)
        return
    pqty = ledger.enter_position(str(id), "short", symbol, price, qty)
    if pqty == False:
        embed = add_embed(
            "Error in Transaction",
            f"{ctx.author.mention} error processing transaction! (Maybe Overbought)",
            author=ctx.author,
        )
        await ctx.send(embed=embed)
    else:
        fields = [
            ("Share Price", f"${rnd(price)}"),
            ("Quantity", f"{rnd(pqty)} shares"),
            ("Worth", f"${rnd(pqty * price)}"),
        ]
        footer = f"Transaction at {sdate()}"
        embed = add_embed(
            f"Shorted {symbol}",
            f"Remaining Balance: ${rnd(ledger.get_balance(id))}",
            fields=fields,
            author=ctx.author,
            inline=True,
            footer=footer,
        )
        await ctx.send(embed=embed)


@bot.command()
async def end_short(ctx, type: str, symbol: str, amount: str):
    symbol = symbol.upper()
    id = str(ctx.author.id)
    name = ctx.author.name
    price = stocks.latest_price(symbol)
    try:
        price = stocks.latest_price(symbol)
        if price == None:
            raise
    except:
        embed = add_embed(f'"{symbol}" couldn\'t be found', author=ctx.author)
        await ctx.send(embed=embed)
        return
    if amount == "all":
        qty = None
    elif type == "cash":
        qty = float(amount) / price
    elif type == "qty":
        qty = float(amount)
    else:
        await ctx.send(f"Invalid Command {ctx.author.mention}")
    if qty != None and qty < 0.1:
        embed = add_embed(
            "Error in Transaction",
            f"{ctx.author.mention} need to end short on more than .1 shares",
            author=ctx.author,
        )
        await ctx.send(embed=embed)
        return
    pqty = ledger.exit_position(id, "end_short", symbol, price, qty)
    if pqty == False:
        embed = add_embed(
            "Error in Transaction",
            f"{ctx.author.mention} error processing transaction! (Maybe Oversold)",
            author=ctx.author,
        )
        await ctx.send(embed=embed)
    else:
        fields = [
            ("Share Price", f"${rnd(price)}"),
            ("Quantity", f"{rnd(pqty)} shares"),
            ("Worth", f"${rnd(pqty * price)}"),
        ]
        footer = f"Transaction at {sdate()}"
        embed = add_embed(
            f"Ended Short on {symbol}",
            f"Remaining Balance: ${rnd(ledger.get_balance(id))}",
            fields=fields,
            author=ctx.author,
            inline=True,
            footer=footer,
        )
        await ctx.send(embed=embed)


@bot.command()
async def stock(ctx, symbol: str):
    symbol = symbol.upper()
    
    bars, stats = stocks.get_stats(symbol)
    open, high, low, price = stats
    o, h, l, c = bars
    trend = rnd(price - open)
    trend_perc = rnd((price - open) / open * 100)
    if trend > 0:
        trend = f"+${trend}"
        trend_perc = f"+{trend_perc}%"
    else:
        trend = f"-${abs(trend)}"
        trend_perc = f"-{abs(trend_perc)}%"
    fields = [
        ("Current Price", f"${price}"),
        ("Open Price", f"${open}"),
        ("High Price", f"${high}"),
        ("Low Price", f"${low}"),
        ("Trend Today", trend),
        ("Trend Today %", trend_perc),
    ]
    
    layout = go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        width=1200,
        height=800,
        xaxis=go.layout.XAxis(showticklabels=False),
        yaxis=go.layout.YAxis(color="white"),
    )
    fig = go.Figure(data=[go.Candlestick(open=o, high=h, low=l, close=c)], layout=layout)
    fig.update_layout(xaxis_rangeslider_visible=False)
    if not os.path.exists("images"):
        os.mkdir("images")
    fig.write_image("images/" + symbol + ".png")
    file = discord.File("images/" + symbol + ".png", filename="image.png")
    description = f"https://finance.yahoo.com/quote/{symbol}?p={symbol}"
    footer = f"Stats as of ({sdate()})"
    embed = add_embed(
        title=symbol,
        description=description,
        fields=fields,
        author=ctx.author,
        inline=True,
        footer=footer,
        image="attachment://image.png",
    )
    await ctx.send(file=file, embed=embed)
    os.remove("images/" + symbol + ".png")


@bot.command()
async def liquidate(ctx):
    id = str(ctx.author.id)
    holdings = ledger.get_holdings(id)
    fields = []
    for symbol, qty, position in holdings:
        price = stocks.latest_price(symbol)
        if position == "long":
            ledger.exit_position(id, "sell", symbol, price, qty)
        else:
            ledger.exit_position(id, "end_short", symbol, price, qty)
        value = f"""
            {rnd(qty)} Shares
            ${rnd(qty * price)}
        """
        fields.append((symbol, value))
    embed = add_embed(f"Portfolio Liquidated", fields=fields, author=ctx.author, inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def leaders(ctx):
    first = -1
    try:
        ports, i, fields = ledger.get_all_owned(), 1, []
        worths = {}
        for id in ports:
            worth = ledger.get_balance(id)
            if worth != INITIAL_BALANCE or len(ports[id]) > 0:
                for sym, qty, tp, ep in ports[id]:
                    lp = stocks.latest_price(sym)
                    if tp == "long":
                        worth += qty * lp
                    else:
                        worth += qty * (2 * ep - lp)
                worths[id] = float(worth)
        sorted_worths = sorted(worths.items(), key=operator.itemgetter(1))
        sorted_worths.reverse()

        for id, bal in sorted_worths:
            if i == 1:
                first = int(id)
            user = await bot.fetch_user(int(id))
            if ledger.get_name(id) != user.name:
                ledger.set_name(id, user.name)
            fields.append((f"{i}: {user.name}#{user.discriminator}", f"Net Worth: ${rnd(bal)}"))
            i += 1
        first_user = await bot.fetch_user(first)
        footer = f"Updated at {sdate()}"
        embed = add_embed(
            title="Leaderboard", fields=fields, thumbnail=first_user.avatar_url, footer=footer
        )
        await ctx.send(embed = embed)
    except:
        pass

@tasks.loop(seconds=600)
async def leaderboard():
    first = -1
    try:
        ports, i, fields = ledger.get_all_owned(), 1, []
        worths = {}
        for id in ports:
            worth = ledger.get_balance(id)
            if worth != INITIAL_BALANCE or len(ports[id]) > 0:
                for sym, qty, tp, ep in ports[id]:
                    lp = stocks.latest_price(sym)
                    if tp == "long":
                        worth += qty * lp
                    else:
                        worth += qty * (2 * ep - lp)
                worths[id] = float(worth)
        sorted_worths = sorted(worths.items(), key=operator.itemgetter(1))
        sorted_worths.reverse()

        for id, bal in sorted_worths:
            if i == 1:
                first = int(id)
            user = await bot.fetch_user(int(id))
            if ledger.get_name(id) != user.name:
                ledger.set_name(id, user.name)
            fields.append((f"{i}: {user.name}#{user.discriminator}", f"Net Worth: ${rnd(bal)}"))
            i += 1
        first_user = await bot.fetch_user(first)
        footer = f"Updated at {sdate()}"
        embed = add_embed(
            title="Leaderboard", fields=fields, thumbnail=first_user.avatar_url, footer=footer
        )
        for guild in bot.guilds:
            channel = discord.utils.get(guild.channels, name="leaderboard")
            if channel == None:
                channel = await guild.create_text_channel("leaderboard")
            message_list = await channel.history(limit=1).flatten()
            if len(message_list) == 0:
                await channel.send(embed=embed)
            else:
                try:
                    await message_list[0].edit(embed=embed)
                except:
                    await channel.purge(limit=100)
                    await channel.send(embed=embed)
    except Exception as e:
        pass

@tasks.loop(hours=7 * 24)
async def add_all():
    await bot.wait_until_ready()
    for user in bot.users:
        if not ledger.contains(str(user.id)) and not user.bot:
            ledger.add_user(str(user.id), user.name)

aliases = ["p", "port", "porfolio"]
@bot.command(aliases=aliases)
async def portfolio(ctx):
    for a in aliases:
        try:
            after = ctx.message.content.lower().split(a)[1]
        except:
            pass
    
    author = ctx.message.mentions[0] if len(ctx.message.mentions) > 0 else ctx.author

    id = str(author.id)
    port = ledger.portfolio(id)
    fields = []
    cash_balance = ledger.get_balance(id)
    total_worth = cash_balance
    for sym, qty, ptype, price in port:
        current_price = stocks.latest_price(sym)
        if ptype == "long":
            profit = rnd((current_price - price) * qty)
            profit_perc = rnd((current_price - price) / price * 100)
            total_worth += current_price * qty
        else:
            total_worth += qty * (2 * price - current_price)
            profit = rnd((price - current_price) * qty)
            profit_perc = rnd((price - current_price) / price * 100)
        value = f"""
            Shares: {rnd(qty)}
            Position: {ptype}
            Worth: ${rnd(current_price*qty)}‎‎‎‎‎‎‎‎‏‏‎‎‏‏‎‏‏‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎
            Profit: ${profit}
            Profit %: {profit_perc}%‏‏‎

        """
        fields.append((f"{sym}", value))
    total_stats = f"""
        Net Worth: ${rnd(total_worth)}
        Cash Balance: ${rnd(cash_balance)}
        Total Profit:
        ${rnd(total_worth-INITIAL_BALANCE)} | {rnd((total_worth-INITIAL_BALANCE)/INITIAL_BALANCE*100)}%
    """
    embed = add_embed(f"Portfolio", total_stats, fields=fields, inline=True, author=author)
    await ctx.send(embed=embed)


if __name__ == '__main__':
    leaderboard.start()
    bot.run(TOKEN)
