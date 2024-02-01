import discord
from discord.ext import commands
from discord.ext import tasks
import requests
import json
import asyncio
import datetime
import pytz
import string

#This Function is used to retreive information about the bets placed, and the coins that are being tracked and is formatted
#in a way that it can be used to update the leaderboards
def writeinto(filename,d):
    f = open(filename,"r+")
    guild = open("GuildMembers.txt","r")
    lines = guild.readlines()
    flines = f.readlines()
    guild.close()
    for ids,j in d.items():
        count = 0
        refinedlist = j.split(",")
        for k in refinedlist:
            ultimaterefine = k.split(":")
            for l in ultimaterefine:
                for i in lines:
                    if l == i.strip("\n"):
                        primarystring = ids+":"+l+"-"+str(5-count)+","+"\n"
                        # f.write(primarystring)
                        checkstring = ids+":"+l
                        refined_list = []
                        indexcount = 0
                        print(flines)
                        for n in flines:
                            refined_list.append(n.split("-")[0])
                        
                        if checkstring in refined_list:
                            new_score = (5 - count)
                            old_score = flines[refined_list.index(checkstring)].split("-")[1].strip(",\n")
                            final_score = int(old_score) + new_score
                            f.write(checkstring+"-"+str(final_score)+","+"\n")
                        else:
                            f.write(primarystring)
                        
                        
                        count += 2
 
#This Function is used to remove duplicates from the leaderboards, as the leaderboards are updated every hour, and the
#same user can bet on the same coin multiple times, this function is used to remove the duplicates and update the scores
def removeduplicates(filename):
  newdict = {}
  f = open(filename,"r")
  lines = f.readlines()
  f.close()
  for i in lines:
    newdict[i.split("-")[0]] = i.split("-")[1].strip(",\n")
  refinedlines = []
  for j in lines:
    refinedlines.append(j.split("-")[0])
    
  finallist = []
  for k,l in newdict.items():
        if k in refinedlines:
          index = refinedlines.index(k)
          if int(l) > int(lines[index].split("-")[1].strip(",\n")):
                finallist.append(k+"-"+l)
          else:
              finallist.append(k+"-"+l)
  
  f = open(filename,"w")
  for item in finallist:
    f.write(item+",\n")
  f.close()
                    
                
#This Function is used to compress the data that is retreived from the API, and is used to update the prices of the coins
#every 10 minutes 
def datacompressor(data,price,highest,lowest,volume,price_change):
    for i in range(0,6):
        price[data[i]['symbol']] = data[i]['current_price']
        highest[data[i]['symbol']] = data[i]['high_24h']
        lowest[data[i]['symbol']] = data[i]['low_24h']
        volume[data[i]['symbol']] = data[i]['total_volume']
        price_change[data[i]['symbol']] = data[i]['price_change_24h']
    return price,highest,lowest,volume,price_change
    
#This Function is used to retreive the price information of a particular coin
def CoinPriceInfo(coin = ""):
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=" + coin
    data = requests.get(url).json()
    return data

#This Function is used to retreive the price information of a particular coin
def LoopPriceInfo(coin = None):
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&symbols=" + coin
    data = requests.get(url).json()
    return data

bot = commands.Bot(command_prefix='!',intents=discord.Intents.all())

#This Function is used to add the members of the guild to the list of members that are tracked for the betting system
def addguildmembers():
    f = open("GuildMembers.txt","r")
    lines = f.readlines()
    f.close()
    List = []
    newlist = []
    for i in lines:
        j = i.strip("\n")
        newlist.append(j)
    for i in bot.guilds[0].members:
        List.append(i.id)
    for i in List:
        if str(i) in newlist:
            pass
        else:
            f = open("GuildMembers.txt","a")
            f.write(str(i)+"\n")
            f.close()
            print("Added " + str(i) + " to the list")
        

@bot.event
async def on_ready():
    # scheduler = AsyncIOScheduler()
    # scheduler.add_job(LeaderBoard_Loop, CronTrigger(second='40'))
    addguildmembers()
    print("Bot is ready")

#This Command is used to retreive the price information of a particular coin
@bot.command()

async def price(ctx, coin = "btc" ):
    '''
    This command is used to retreive the price information of a particular coin
    Please use the SymbolInfo command to get the symbol of the coin
    The command is used as follows:
    !price <coin-symbol>
    '''
    data = LoopPriceInfo(coin)
    embed = discord.Embed(title=data[0]['name'].upper(), description="Price Information", color=discord.Color.blue())
    embed.add_field(name="Symbol", value=data[0]['symbol'], inline=True)
    embed.add_field(name="Current Price", value="$" + str(data[0]['current_price']), inline=True)
    embed.add_field(name="Total Volume", value="$" + str(data[0]['total_volume']), inline=True)
    embed.add_field(name="High 24h", value="$" + str(data[0]['high_24h']), inline=True)
    embed.add_field(name="Low 24h", value="$" + str(data[0]['low_24h']), inline=True)
    embed.add_field(name="Price Change 24h", value="$" + str(data[0]['price_change_24h']), inline=True)
    embed.add_field(name="Price Change Percentage 24h", value=str(data[0]['price_change_percentage_24h']) + "%", inline=True)
    await ctx.send(embed=embed)

#This Command is start the 10 minute updates of the prices of the coins that are being tracked
@bot.command()
@commands.has_role("admin")
async def UpdateStart(ctx):
    '''
    This command is used to start the 10 minute updates of the prices of the coins that are being tracked
    The command is used as follows:
    !UpdateStart
    Roles Required : Admin
    '''
    price_loop.start(ctx)
    await ctx.send("Price Update Started")
    
@tasks.loop(minutes = 10)
async def price_loop(ctx):
    string = ""
    f = open("CoinList.txt","r+")
    lines = f.readlines()
    for i in lines:
        string = string + i.strip("\n") + ","
    price = {}
    highest = {}
    lowest = {}
    volume = {}
    price_change = {}
    data = LoopPriceInfo(string)
    price, highest, lowest, volume, price_change = datacompressor(data, price, highest, lowest, volume, price_change)
    Embed = discord.Embed(title="Price Update", description="Price Information for each crypto are listed below", color=discord.Color.blue())
    for i in range(0, len(price)):
        symbol = list(price.keys())[i]
        embed_value = f"Current Price: ${price[symbol]}\nHighest: ${highest[symbol]}\nLowest: ${lowest[symbol]}\nVolume: ${volume[symbol]}\nPrice Change: ${price_change[symbol]}"
        Embed.add_field(name=symbol.upper(), value=embed_value, inline=True)
    await ctx.send(embed=Embed)
    
@bot.command()
@commands.has_role("admin")
#This Command is used to stop the 10 minute updates of the prices of the coins that are being tracked
async def UpdateStop(ctx):
    '''
    This command is used to stop the 10 minute updates of the prices of the coins that are being tracked
    The command is used as follows:
    !UpdateStop
    Roles Required : Admin
    '''
    price_loop.stop()
    await ctx.send("Price Update Stopped")

@price_loop.before_loop
async def before():
    await bot.wait_until_ready()
    
#This Command is used to retreive the symbol of a particular coin
@bot.command()
async def SymbolInfo(ctx, coin = "bitcoin"):
    '''
    This command is used to retreive the symbol of a particular coin,
    which is used in the price command,!Betadd and !Betremove commands
    The command is used as follows:
    !SymbolInfo <coin-name>
    '''
    data = CoinPriceInfo()
    xy = False
    for i in data:
        if i['name'] == coin:
            xy = True
            await ctx.send(f"The Symbol Of the Coin is : {i['symbol']}")
            break
        else:
            xy = False
    if xy == False:
        await ctx.send("Invalid Coin Name, Please recheck the coin name")      

#This Command is used to add a coin to the list of coins that are being tracked
@bot.command()
@commands.has_role("admin")
async def AddCoin(ctx, coin = None):
    '''
    This command is used to add a coin to the list of coins that are being tracked
    The command is used as follows:
    !AddCoin <coin-symbol>
    '''
    if coin == None:
        await ctx.send("Please Enter the Coin Symbol you want to add to the 10 Minute Updates")
    else:
        f = open("CoinList.txt","a")
        f.write("\n"+coin)
        await ctx.send(f"Coin {coin} has been added to the 10 Minute Updates")
        
#This Command is used to remove a coin from the list of coins that are being tracked
@bot.command()
@commands.has_role("admin")
async def RemoveCoin(ctx, coin = None):
    '''
    This command is used to remove a coin from the list of coins that are being tracked
    The command is used as follows:
    !RemoveCoin <coin-symbol>
    '''
    if coin == None:
        await ctx.send("Please Enter the Coin Symbol you want to remove from the 10 Minute Updates")
    else:
        f = open("CoinList.txt","r")
        lines = f.readlines()
        f.close()
        f = open("CoinList.txt","w")
        for line in lines:
            if line.strip("\n") != coin:
                f.write(line)
        f.close()
        await ctx.send(f"Coin {coin} has been removed from the 10 Minute Updates")

@bot.command()
@commands.has_role("admin")
async def cuurentCoins(ctx):
    '''
    This command is used to check the current coins being tracked
    '''
    snew = ""
    f = open("CoinList.txt","r")
    for i in f.readlines():
        snew = snew + i.strip("\n") + ","
    await ctx.send(f"The Current Coins that are being tracked are : {snew}")
    
@bot.command()
async def bet(ctx, coin = None, price = None):
    '''
    This command is used to bet on a particular coin, and the price you want to bet on
    The command is used as follows:
    !bet <coin-symbol> <price>
    '''
    if coin == None or price == None:
        await ctx.send("Please enter the coin name and the amount of price you want to bet")
    else:
        f = open("CoinList.txt","r")
        lines = f.readlines()
        f.close()
        Coinlist = []
        for i in lines:
            Coinlist.append(i.strip("\n"))
        if coin not in Coinlist:
            await ctx.send("Invalid Coin Name, Please recheck the coin name, or contact the admin to Start Tracking this coin")
            return
        userid = str(ctx.author.id)
        await ctx.send(f"Bet Placed for {coin} for {price} Dollars.<@{str(ctx.author.id)}>")       
        f = open("BettingAmounts.txt","a")
        f.write(userid + "," + coin + "," + price + "\n")
        f.close()

#This Command is used to start the Betting system every Noon and Midnight
@bot.command()
@commands.has_role("admin")
async def bettingsystemstart(ctx):
    '''
    This command is used to start the Betting system every Noon and Midnight
    The command is used as follows:
    !bettingsystemstart
    Roles Required : Admin
    '''
    betresults.start(ctx)
    leaderboards.start(ctx)
    await ctx.send("Bet Results Started")
    
@tasks.loop(hours = 1)
async def betresults(ctx):
    current_time = datetime.datetime.now(pytz.timezone('UTC'))
    print(current_time.hour)
    if current_time.hour == 17 or current_time.hour == 18 or current_time.hour == 16:
        f = open("CoinList.txt","r")
        lines = f.readlines()
        f.close()
        Coinlist = [] # Gets the coins that are present in the current tracking
        string = "" # Gets the string of the coins that are present in the current tracking
        count = 0 # Gets the number of coins that are present in the current tracking
        for i in lines:
            Coinlist.append(i.strip("\n"))
            string += i.strip("\n") + ","
            count += 1
        data = LoopPriceInfo(string)
        # print(data)
        # print(Coinlist)
        resultsdict = {}
        
        for i in Coinlist:
            resultsdict[i] = " "
            
        for i in Coinlist:
            coinsymb = i
            currentprice = 0
            coinname = ""
            for j in range(0,count):
                if data[j]['symbol'] == i:
                    currentprice = data[j]['current_price']
                    coinname = data[j]['name']
                    # print(coinname)
            # print("HELLO")
            f = open("BettingAmounts.txt","r")
            betL = f.readlines()
            f.close()
            coindict = {}
            mainstring = ""
            peoplepercoin = 0
            for person in betL:
                if person.split(",")[1] == i:
                    name = person.split(",")[0]
                    betprice = person.split(",")[2].strip("\n")
                    delta = abs(float(betprice) - float(currentprice))
                    coindict[name] = delta
                    
                    peoplepercoin += 1
                    
            if peoplepercoin == 0:
                resultsdict[i] = "No one bet on this coin"
                continue
            # print(coindict)

            sortedcoindict = sorted(coindict.items(), key=lambda x: x[1])
            
            # print(sortedcoindict)
            
            for i in range(0,len(sortedcoindict)):
                if i < 3:
                    mainstring += f"{sortedcoindict[i][0]}:{sortedcoindict[i][1]},"
                else:
                    break     
            resultsdict[coinsymb] = mainstring           
            converted_dict = {}
        
        Embed = discord.Embed(title="Bet Results", description="Top 3 from Each Coin are shown Below :", color=discord.Color.blue())        

        for i in resultsdict:
            if(resultsdict[i] == "No one bet on this coin"):
                Embed.add_field(name=i.upper(), value=resultsdict[i], inline=True)
            else:
                unrefined_string = resultsdict[i]
                refined_string_list = unrefined_string.split(",")
                # print(refined_string_list)
                if len(refined_string_list) == 2:
                    Embed.add_field(name=f"{i.upper()}", value=f"1)<@{refined_string_list[0].split(':')[0]}>", inline=True)
                elif len(refined_string_list) == 3:
                    Embed.add_field(name=f"{i.upper()}", value=f"1)<@{refined_string_list[0].split(':')[0]}>\n2)<@{refined_string_list[1].split(':')[0]}>", inline=True)
                elif len(refined_string_list) == 4:
                    Embed.add_field(name=f"{i.upper()}", value=f"1)<@{refined_string_list[0].split(':')[0]}>\n2)<@{refined_string_list[1].split(':')[0]}>\n3)<@{refined_string_list[2].split(':')[0]}>", inline=True)
        
        
               
        await ctx.send(embed=Embed)
        print(resultsdict) 
        writeinto("Leaderboards.txt",resultsdict)
        removeduplicates("Leaderboards.txt")


       
@bot.command()
@commands.has_role("admin")
async def bettingsystemstop(ctx):
    '''
    This command is used to stop the Betting system every Noon and Midnight
    The command is used as follows:
    !bettingsystemstop
    Roles Required : Admin
    '''
    betresults.cancel()
    leaderboards.cancel()
    await ctx.send("Bet Results Stopped")
    
@betresults.before_loop
async def before():
    await bot.wait_until_ready() 
        
@tasks.loop(hours = 1)
async def leaderboards(ctx):
    current_time = datetime.datetime.now(pytz.timezone('UTC'))
    print(current_time.hour)
    if current_time.hour == 16 or current_time.hour == 17 or current_time.hour == 18:
        f = open("Leaderboards.txt","r")
        lines = f.readlines()
        f.close()
        idslist = {}
        for i in lines:
            refinedlist = i.split(":")
            if refinedlist[0] in idslist:
                idslist[refinedlist[0]] += refinedlist[1]
            else:
                idslist[refinedlist[0]] = refinedlist[1]
        print(idslist)
        Embed = discord.Embed(title="Leaderboards Of Each Crypto", color=discord.Color.blue())
        for key, value in idslist.items():
            try:
                formatted_value = f"{int(value):,}" # Format the value as an integer with commas
            except ValueError:
                formatted_value = value.strip() # Remove leading/trailing whitespaces
            
            new_list = formatted_value.split(",")
            print(new_list)
            
            for i in range(0,len(new_list)-1):
                initial_string_value = new_list[i]
                modified_string_value = initial_string_value.split("-")[0]
                if "\n" in modified_string_value:
                    modified_string_value = modified_string_value.strip("\n")
                    modified2 = "<@"+modified_string_value+">"
                    new_list[i] = "\n"+modified2 + "-" + initial_string_value.split("-")[1]
                else:
                    modified2 = "<@"+modified_string_value+">"
                    new_list[i] = modified2 + "-" + initial_string_value.split("-")[1]

            print("THIS IS CHANGED:")
            print(new_list)
            print("----------------")
            new_formatted_value = "\n".join(new_list)
            Embed.add_field(name=key.upper(), value=new_formatted_value, inline=False)
            
        await ctx.send(embed=Embed)
    
@leaderboards.before_loop
async def before():
    await bot.wait_until_ready()
    
#This Command is used to reset the Leaderboards
@bot.command()
@commands.has_role("admin")
async def resetleaderboards(ctx):
    '''
    This command is used to reset the Leaderboards
    The command is used as follows:
    !resetleaderboards
    Roles Required : Admin
    '''
    f = open("Leaderboards.txt","w")
    f.close()
    await ctx.send("Leaderboards Reset")
    
    
#This Command is to let the user see the leaderboards at any time the want to
@bot.command()
async def showlbd(ctx):
    '''
    This command is to let the user see the leaderboards at any time the want to
    The command is used as follows:
    !showlbd
    '''
    f = open("Leaderboards.txt","r")
    lines = f.readlines()
    f.close()
    Embed = discord.Embed(title="Leaderboards Of Each Crypto", color=discord.Color.blue())
    if len(lines) == 0:
        Embed.add_field(name="Information : ", value="No one has bet yet", inline=False)
    idslist = {}
    for i in lines:
        refinedlist = i.split(":")
        if refinedlist[0] in idslist:
            idslist[refinedlist[0]] += refinedlist[1]
        else:
            idslist[refinedlist[0]] = refinedlist[1]
    print(idslist)
    for key, value in idslist.items():
        try:
            formatted_value = f"{int(value):,}" # Format the value as an integer with commas
        except ValueError:
            formatted_value = value.strip() # Remove leading/trailing whitespaces
        
        new_list = formatted_value.split(",")
        print(new_list)
        
        for i in range(0,len(new_list)-1):
            initial_string_value = new_list[i]
            modified_string_value = initial_string_value.split("-")[0]
            if "\n" in modified_string_value:
                modified_string_value = modified_string_value.strip("\n")
                modified2 = "<@"+modified_string_value+">"
                new_list[i] = "\n"+modified2 + "-" + initial_string_value.split("-")[1]
            else:
                modified2 = "<@"+modified_string_value+">"
                new_list[i] = modified2 + "-" + initial_string_value.split("-")[1]

        print("THIS IS CHANGED:")
        print(new_list)
        print("----------------")
        new_formatted_value = "\n".join(new_list)
        Embed.add_field(name=key.upper(), value=new_formatted_value, inline=False)
        
        
    await ctx.send(embed=Embed)
        

@bot.command()
async def helpme(ctx):
    '''
    This command shows all the available commands with their descriptions.
    '''
    commands = [
        ("cuurentCoins", "Shows the current coins.", "Usage: !cuurentCoins"),
        ("bet", "Starts a betting system.", "Usage: !bet [coin] [price]"),
        ("bettingsystemstart", "Starts the betting system every Noon and Midnight.", "Usage: !bettingsystemstart (Role Required: admin)"),
        ("betresults", "Shows the results of the betting system.", "Usage: !betresults"),
        ("bettingsystemstop", "Stops the betting system.", "Usage: !bettingsystemstop (Role Required: admin)"),
        ("leaderboards", "Shows the leaderboards.", "Usage: !leaderboards"),
        ("resetleaderboards", "Resets the leaderboards.", "Usage: !resetleaderboards (Role Required: admin)"),
        ("showlbd", "Shows the leaderboards of each crypto.", "Usage: !showlbd")
    ]
    
    embed = discord.Embed(title="CryptoBot Commands", color=discord.Color.blue())
    
    for command, description, usage in commands:
        embed.add_field(name=command.upper(), value=f"{description}\n`{usage}`", inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def usage(ctx):
    '''
    This command shows how to use the helpme command.
    '''
    await ctx.send("To use the helpme command, simply type `!helpme` in the chat.")

token = "MTE5NTI0NzQ4MjU5NTE4NDY1MA.GbqtBS.yC9tO2ls_xN9OgBGI3OE15AUkgUhr-C0UErQVk"
bot.run(token)