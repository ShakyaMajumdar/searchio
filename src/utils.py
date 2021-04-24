from datetime import datetime
from src.loadingmessage import LoadingMessage
import discord, asyncio, yaml, textwrap, difflib, csv, os, random, traceback, re, requests

class Sudo:
    def __init__(
        self,
        bot,
        ctx,
        serverSettings,
        userSettings):

        self.bot = bot
        self.ctx = ctx
        self.serverSettings = serverSettings
        self.userSettings = userSettings

    @staticmethod
    def serverSettingsCheck(serverSettings, serverID):
        if serverID not in serverSettings.keys():
            serverSettings[serverID] = {}
        if 'blacklist' not in serverSettings[serverID].keys():
            serverSettings[serverID]['blacklist'] = []
        if 'commandprefix' not in serverSettings[serverID].keys():
            serverSettings[serverID]['commandprefix'] = '&'
        if 'adminrole' not in serverSettings[serverID].keys():
            serverSettings[serverID]['adminrole'] = None
        if 'sudoer' not in serverSettings[serverID].keys():
            serverSettings[serverID]['sudoer'] = []
        if 'safesearch' not in serverSettings[serverID].keys():
            serverSettings[serverID]['safesearch'] = False
        for searchEngines in ['wikipedia', 'scholar', 'google', 'mal', 'youtube', 'xkcd']:
            if searchEngines not in serverSettings[serverID].keys():
                serverSettings[serverID][searchEngines] = True
        
        return serverSettings

    @staticmethod
    def userSettingsCheck(userSettings, userID):
        olduserSetting = userSettings

        if userID not in userSettings.keys():
            userSettings[userID] = {}
        if 'locale' not in userSettings[userID].keys():
            userSettings[userID]['locale'] = None

        if olduserSetting != userSettings:
            with open('userSettings.yaml', 'w') as data:
                yaml.dump(userSettings, data, allow_unicode=True)

        return userSettings
        
    @staticmethod
    def isSudoer(bot, ctx, serverSettings=None):
        if serverSettings == None:
            with open('serverSettings.yaml', 'w') as data:
                yaml.dump(serverSettings, data, allow_unicode=True)

        #Checks if sudoer is owner
        isOwner = ctx.author.id == bot.owner_id
        
        #Checks if sudoer is server owner
        if ctx.guild:
            isServerOwner = ctx.author.id == ctx.guild.owner_id
        else: isServerOwner = False

        #Checks if sudoer has the designated adminrole or is a sudoer
        try:
            hasAdmin = True if serverSettings[ctx.guild.id]['adminrole'] in [role.id for role in ctx.author.roles] else False
            isSudoer = True if ctx.author.id in serverSettings[ctx.guild.id]['sudoer'] else False
        except: pass
        finally: return any([isOwner, isServerOwner, hasAdmin, isSudoer])

    @staticmethod
    def printPrefix(serverSettings, ctx=None):
        if ctx == None or ctx.guild == None:
            return '&'
        else: return serverSettings[ctx.guild.id]['commandprefix']

    async def userSearch(self, search):
        try:
            if search.isnumeric():
                user = self.ctx.guild.get_member(int(search))
            else:
                user = self.ctx.guild.get_member_named(search)
            
            if user == None:
                return None
            else: return user
        
        except Exception as e:
            raise

    async def echo(self, args):
        try:
            if "--channel" in args:
                channel = int(args[args.index("--channel")+1])
                args.pop(args.index("--channel")+1)
                args.pop(args.index("--channel"))

                if await self.bot.is_owner(self.ctx.author):
                    channel = await self.bot.fetch_channel(channel)
                else: #Prevents non-owner sudoers from using bot in other servers
                    channel = self.ctx.guild.get_channel(channel)

            else: channel = self.ctx.channel
               
            await channel.send(' '.join(args).strip()) if channel else self.ctx.send(' '.join(args).strip())

        except Exception as e:
            raise
        finally: return
    
    async def blacklist(self, args):
        try:
            if 'blacklist' not in self.serverSettings[self.ctx.guild.id].keys():
                self.serverSettings[self.ctx.guild.id]['blacklist'] = []

            if len(args) == 1:
                user = await self.userSearch(' '.join(args))
                role = self.ctx.guild.get_role(int(''.join(args)))
                if user is not None:
                    self.serverSettings[self.ctx.guild.id]['blacklist'].append(user.id)
                    await self.ctx.send(f"`{str(user)}` blacklisted")
                elif role is not None:
                    self.serverSettings[self.ctx.guild.id]['blacklist'].append(role.id)
                    await self.ctx.send(f"'{role.name}' is now blacklisted")
                else: 
                    await self.ctx.send(f"No user/role named `{''.join(args)}` was found in the guild")
        except Exception as e:
            raise
        finally: return
    
    async def whitelist(self, args):
        try: 
            if 'blacklist' not in self.serverSettings[self.ctx.guild.id].keys():
                self.serverSettings[self.ctx.guild.id]['blacklist'] = []

            if len(args) == 1:
                try:
                    user = await self.userSearch(' '.join(args))
                    role = self.ctx.guild.get_role(int(''.join(args)))
                    if user is not None:
                        self.serverSettings[self.ctx.guild.id]['blacklist'].remove(user.id)
                        await self.ctx.send(f"`{str(user)}` removed from blacklist")
                    elif role is not None:
                        self.serverSettings[self.ctx.guild.id]['blacklist'].remove(role.id)
                        await self.ctx.send(f"'{role.name}' removed from blacklist")
                    else: 
                        await self.ctx.send(f"No user/role with the ID `{''.join(args)}` was found in the guild")
                except ValueError:
                    await self.ctx.send(f"`{''.join(args)}` not in blacklist")
        except Exception as e:
            raise
        finally: return

    async def sudoer(self, args):
        try:
            if self.ctx.author.id == self.bot.owner_id or self.ctx.author.id == self.ctx.guild.owner_id:
                user = await self.userSearch(' '.join(args))
                if user.id not in self.serverSettings[self.ctx.guild.id]['sudoer']:
                    self.serverSettings[self.ctx.guild.id]['sudoer'].append(user.id)
                    await self.ctx.send(f"`{str(user)}` is now a sudoer")
                else: 
                    await self.ctx.send(f"`{str(user)}` is already a sudoer")
        except Exception as e:
            raise
        finally: return
    
    async def unsudoer(self, args):
        try:
            if self.ctx.author.id == self.bot.owner_id or self.ctx.author.id == self.ctx.guild.owner_id:
                user = await self.userSearch(' '.join(args))
                if user.id in self.serverSettings[self.ctx.guild.id]['sudoer']:
                    self.serverSettings[self.ctx.guild.id]['sudoer'].remove(user.id)
                    await self.ctx.send(f"`{str(user)}` has been removed from sudo")
                else: 
                    await self.ctx.send(f"`{str(user)}` is not a sudoer")
        except Exception as e:
            raise
        finally: return
    
    async def config(self, args):
        def check(reaction, user):
                return user == self.ctx.author and str(reaction.emoji) in ['✅', '❌']
        
        try:    
            adminrole = self.serverSettings[self.ctx.guild.id]['adminrole']
            if adminrole != None:
                adminrole = self.ctx.guild.get_role(int(adminrole)) 
            if not args:
                embed = discord.Embed(title="Configuration")
                embed.add_field(name="Guild Administration", value=f"""
                    ` Adminrole:` {adminrole.name if adminrole != None else 'None set'}
                    `Safesearch:` {'✅' if self.serverSettings[self.ctx.guild.id]['safesearch'] == True else '❌'}
                    `    Prefix:` {self.serverSettings[self.ctx.guild.id]['commandprefix']}""")
                embed.add_field(name="Guild Search Engines", value=f"""
                    `   Google:` {'✅' if self.serverSettings[self.ctx.guild.id]['google'] == True else '❌'}
                    `      MAL:` {'✅' if self.serverSettings[self.ctx.guild.id]['mal'] == True else '❌'}
                    `  Scholar:` {'✅' if self.serverSettings[self.ctx.guild.id]['scholar'] == True else '❌'}
                    `Wikipedia:` {'✅' if self.serverSettings[self.ctx.guild.id]['wikipedia'] == True else '❌'}
                    `     XKCD:` {'✅' if self.serverSettings[self.ctx.guild.id]['xkcd'] == True else '❌'}
                    `  Youtube:` {'✅' if self.serverSettings[self.ctx.guild.id]['youtube'] == True else '❌'}""")
                embed.add_field(name="User Configuration", value=f"""
                    `   Locale:` {self.userSettings[self.ctx.author.id]['locale'] if self.userSettings[self.ctx.author.id]['locale'] is not None else 'None Set'}""")

                embed.set_footer(text=f"Do {self.printPrefix(self.serverSettings)}config [setting] to change a specific setting")
                configMessage = await self.ctx.send(embed=embed)
                try:
                    await configMessage.add_reaction('🗑️')
                    reaction, user = await self.bot.wait_for("reaction_add", check=lambda reaction, user: all([user == self.ctx.author, str(reaction.emoji) == "🗑️", reaction.message == configMessage]), timeout=60)
                    if str(reaction.emoji) == '🗑️':
                        await configMessage.delete()
        
                except asyncio.TimeoutError as e: 
                    await configMessage.clear_reactions()
            elif args[0].lower() in ['wikipedia', 'scholar', 'google', 'myanimelist', 'youtube', 'safesearch', 'xkcd']:
                if bool(re.search('^enable', args[1].lower()) or re.search('^on', args[1].lower())):
                    self.serverSettings[self.ctx.guild.id][args[0].lower()] = True
                elif bool(re.search('^disable', args[1].lower()) or re.search('^off', args[1].lower())):
                    self.serverSettings[self.ctx.guild.id][args[0].lower()] = False
                else:
                    embed = discord.Embed(title=args[0].capitalize(), description=f"{'✅' if self.serverSettings[self.ctx.guild.id][args[0].lower()] == True else '❌'}")
                    embed.set_footer(text=f"React with ✅/❌ to enable/disable")
                    message = await self.ctx.send(embed=embed)
                    try:
                        await message.add_reaction('✅')
                        await message.add_reaction('❌')

                        reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=60)
                        if str(reaction.emoji) == '✅':
                            self.serverSettings[self.ctx.guild.id][args[0].lower()] = True
                        elif str(reaction.emoji) == '❌':
                            self.serverSettings[self.ctx.guild.id][args[0].lower()] = False
                        await message.delete()
                        return
                    except asyncio.TimeoutError as e: 
                        await message.clear_reactions()
                
                await self.ctx.send(f"{args[0].capitalize()} is {'enabled' if self.serverSettings[self.ctx.guild.id][args[0].lower()] == True else 'disabled'}")
            elif args[0].lower() == 'adminrole':
                if not args[1]:
                    embed = discord.Embed(title='Adminrole', description=f"{await self.ctx.guild.get_role(int(adminrole)) if adminrole != None else 'None set'}")
                    embed.set_footer(text=f"Reply with the roleID of the role you want to set")
                    message = await self.ctx.send(embed=embed)

                    try: 
                        userresponse = await self.bot.wait_for('message', check=lambda m: m.author == self.ctx.author, timeout=30)
                        await userresponse.delete()
                        await message.delete()
                        response = userresponse.content
                    except asyncio.TimeoutError as e:
                        return
                else: 
                    errorCount = 0
                    errorMsg = None
                    response = args[1]
                    while errorCount <= 1:
                        try: 
                            adminrole = self.ctx.guild.get_role(int(response))
                            self.serverSettings[self.ctx.guild.id]['adminrole'] = adminrole.id
                            await self.ctx.send(f"'{adminrole.name}' is now the admin role")
                            break
                        except (ValueError, AttributeError) as e:
                            errorMsg = await self.ctx.send(f"{response} is not a valid roleID. Please edit your message or reply with a valid roleID.")
                            messageEdit = asyncio.create_task(self.bot.wait_for('message_edit', check=lambda var, m: m.author == self.ctx.author, timeout=60))
                            reply = asyncio.create_task(self.bot.wait_for('message', check=lambda m: m.author == self.ctx.author, timeout=60))
                            
                            waiting = [messageEdit, reply]
                            done, waiting = await asyncio.wait(waiting, return_when=asyncio.FIRST_COMPLETED) # 30 seconds wait either reply or react

                            if messageEdit in done:
                                reply.cancel()
                                messageEdit = messageEdit.result()
                                response = ''.join([li for li in difflib.ndiff(messageEdit[0].content, messageEdit[1].content) if '+' in li]).replace('+ ', '')
                            elif reply in done:
                                messageEdit.cancel()
                                reply = reply.result()
                                await reply.delete()
                                
                                if reply.content == "cancel":
                                    messageEdit.cancel()
                                    reply.cancel()
                                    break
                                else: response = reply.content
                            await errorMsg.delete()
                            errorCount += 1
                            pass
            elif args[0].lower() == 'prefix':
                if not args[1]:
                    embed = discord.Embed(title='Prefix', description=f"{self.serverSettings[self.ctx.guild.id]['commandprefix']}")
                    embed.set_footer(text=f"Reply with the prefix that you want to set")
                    message = await self.ctx.send(embed=embed)

                    try: 
                        userresponse = await self.bot.wait_for('message', check=lambda m: m.author == self.ctx.author, timeout=30)
                        await userresponse.delete()
                        await message.delete()
                        response = userresponse.content

                    except asyncio.TimeoutError as e:
                        await message.delete()
                else: response = args[1]
                
                self.serverSettings[self.ctx.guild.id]['commandprefix'] = response
                await self.ctx.send(f"'{response}' is now the guild prefix")
            elif args[0].lower() == 'locale':
                msg = [await self.ctx.send(f'{LoadingMessage()} <a:loading:829119343580545074>')]
                UserCancel = KeyboardInterrupt
                uuleDB = open('./src/cache/googleUULE.csv', 'r', encoding='utf-8-sig').read().split('\n')
                fieldnames = uuleDB.pop(0).split(',')
                uuleDB = [dict(zip(fieldnames, [string.replace('"','') for string in lines.split('",')])) for lines in uuleDB] #parses get request into list of dicts
                uuleDB = [placeDict for placeDict in uuleDB if all(['Name' in placeDict.keys(), 'Canonical Name' in placeDict.keys()])]

                if len(args) == 1:
                    askUser = await self.ctx.send("Enter location or cancel to abort") #if empty, asks user for search query
                    try:
                        localequery = await self.bot.wait_for('message', check=lambda m: m.author == self.ctx.author, timeout = 30) # 30 seconds to reply
                        await localequery.delete()
                        localequery = localequery.content
                        await askUser.delete()
                        if localequery.lower() == 'cancel': 
                            raise UserCancel

                    except asyncio.TimeoutError:
                        await self.ctx.send(f'{self.ctx.author.mention} Error: You took too long. Aborting') #aborts if timeout
                else:
                    localequery = ' '.join(args[1:]).strip()
                
                userPlaces = [canonName for canonName in uuleDB if localequery.lower() in canonName['Name'].lower() and canonName['Status'] == 'Active'] #searches uuleDB for locale query
                result = [canonName['Canonical Name'] for canonName in userPlaces]
                
                if len(result) == 0:
                    embed=discord.Embed(description=f"No results found for '{localequery}'")
                    await msg[0].edit(content=None, embed=embed)

                elif len(result) == 1:
                    self.userSettings[self.ctx.author.id]['locale'] = result[0]
                    await msg[0].edit(content=f'Locale successfully set to `{result[0]}`')
                elif len(result) > 1:
                    result = [result[x:x+10] for x in range(0, len(result), 10)]
                    pages = len(result)
                    cur_page = 1

                    if len(result) > 1:
                        embed=discord.Embed(title=f"Locales matching '{localequery.capitalize()}'\n Page {cur_page}/{pages}:", description=
                        ''.join([f'[{index}]: {value}\n' for index, value in enumerate(result[cur_page-1])]))
                        embed.set_footer(text=f"Requested by {self.ctx.author}")
                        await msg[0].edit(content=None, embed=embed)
                        await msg[-1].add_reaction('◀️')
                        await msg[-1].add_reaction('▶️')
                    
                    else:
                        embed=discord.Embed(title=f"Locales matching '{localequery.capitalize()}':", description=
                            ''.join([f'[{index}]: {value}\n' for index, value in enumerate(result[0])]))
                        embed.set_footer(text=f"Requested by {self.ctx.author}")
                        await msg[0].edit(content=None, embed=embed)
                    msg.append(await self.ctx.send("Please choose option or cancel"))

                    while 1:
                        emojitask = asyncio.create_task(self.bot.wait_for("reaction_add", check=lambda reaction, user: all([user == self.ctx.author, str(reaction.emoji) in ["◀️", "▶️", "🗑️"], reaction.message == msg[0]]), timeout=30))
                        responsetask = asyncio.create_task(self.bot.wait_for('message', check=lambda m: m.author == self.ctx.author, timeout=30))
                        waiting = [emojitask,responsetask]
                        done, waiting = await asyncio.wait(waiting, return_when=asyncio.FIRST_COMPLETED) # 30 seconds wait either reply or react
                        
                        if emojitask in done: # if reaction input, change page
                            reaction, user = emojitask.result()
                            if str(reaction.emoji) == "▶️" and cur_page != pages:
                                cur_page += 1
                                embed=discord.Embed(title=f"Locales matching '{localequery.capitalize()}'\nPage {cur_page}/{pages}:", description=
                                    ''.join([f'[{index}]: {value}\n' for index, value in enumerate(result[cur_page-1])]))
                                embed.set_footer(text=f"Requested by {self.ctx.author}")
                                await msg[-2].edit(embed=embed)
                                await msg[-2].remove_reaction(reaction, user)
                            
                            elif str(reaction.emoji) == "◀️" and cur_page > 1:
                                cur_page -= 1
                                embed=discord.Embed(title=f"Locales matching '{localequery.capitalize()}'\n Page {cur_page}/{pages}:", description=
                                    ''.join([f'[{index}]: {value}\n' for index, value in enumerate(result[cur_page-1])]))
                                embed.set_footer(text=f"Requested by {self.ctx.author}")
                                await msg[-2].edit(embed=embed)
                                await msg[-2].remove_reaction(reaction, user)
                            
                            else:
                                await msg[-2].remove_reaction(reaction, user)
                                # removes reactions if the user tries to go forward on the last page or
                                # backwards on the first page
                        
                        elif responsetask in done:
                            emojitask.cancel()
                            input = responsetask.result() 
                            await input.delete()
                            if input.content == 'cancel':
                                raise UserCancel
                            elif input.content not in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                                continue
                            input = int(input.content)
                            
                            try:
                                for message in msg:
                                    await message.delete()
                            except:
                                pass

                            self.userSettings[self.ctx.author.id]['locale'] = result[cur_page-1][input]
                            await self.ctx.send(f'Locale successfully set to `{result[cur_page-1][input]}`')
                            break

        except UserCancel:
            await self.ctx.send('Aborting')
            if msg:
                for message in msg: await message.delete()
            
            return self.serverSettings, self.userSettings
        except Exception as e:
            args = args if len(args) > 0 else None
            await ErrorHandler(self.bot, self.ctx, e, args)
            return self.serverSettings, self.userSettings
        finally:
            if args: 
                with open('serverSettings.yaml', 'w') as data:
                    yaml.dump(self.serverSettings, data, allow_unicode=True)

                with open('userSettings.yaml', 'w') as data:
                    yaml.dump(self.userSettings, data, allow_unicode=True)
                Log.appendToLog(self.ctx, "config", args)
            return self.serverSettings, self.userSettings
                              
    async def sudo(self, args):
        try:
            if args:
                command = args.pop(0)
                if command == 'echo':
                    await self.echo(args)
                elif command == 'blacklist':
                    await self.blacklist(args)
                elif command == 'whitelist':
                    await self.whitelist(args)
                elif command == 'sudoer':
                    await self.sudoer(args)
                elif command == 'unsudoer':
                    await self.unsudoer(args)
                else:
                    await self.ctx.send(f"'{command}' is not a valid command.")
            else:
                embed = discord.Embed(title="Sudo", description=f"Admin commands. Server owner has sudo privilege by default.\nUsage: {self.printPrefix(self.ctx)}sudo [command] [args]")
                embed.add_field(name="Commands", inline=False, value=
                    f"""`     echo:` Have the bot say something. 
                        Args: message 
                        Optional flag: --channel [channelID]

                        `blacklist:` Block a user from using the bot. 
                        Args: userName OR userID 

                        `whitelist:` Unblock a user from using the bot. 
                        Args: userName OR userID

                        `   sudoer:` Add a user to the sudo list. Only guild owners can do this. 
                        Args: userName OR userID  

                        ` unsudoer:` Remove a user from the sudo list. Only guild owners can do this. 
                        Args: userName OR userID""")

                helpMessage = await self.ctx.send(embed=embed)
                try:
                    await helpMessage.add_reaction('🗑️')
                    reaction, user = await self.bot.wait_for("reaction_add", check=lambda reaction, user: all([user == self.ctx.author, str(reaction.emoji) == "🗑️", reaction.message == message]), timeout=60)
                    if str(reaction.emoji) == '🗑️':
                        await helpMessage.delete()
        
                except asyncio.TimeoutError as e: 
                    await helpMessage.clear_reactions()

        except Exception as e:
            args = args if len(args) > 0 else None
            await ErrorHandler(self.bot, self.ctx, e, args)
        finally: 
            if command in ['blacklist', 'whitelist', 'sudoer', 'unsudoer']:
                with open('serverSettings.yaml', 'w') as data:
                    yaml.dump(self.serverSettings, data, allow_unicode=True)

                with open('userSettings.yaml', 'w') as data:
                    yaml.dump(self.userSettings, data, allow_unicode=True)
            return self.serverSettings, self.userSettings

class Log():
    @staticmethod
    def appendToLog(ctx, optcommand=None, args=None):     
        if args is None: 
            if ctx.args is None:
                args = "None"
            else: args = ' '.join(list(ctx.args[2:]))
        elif isinstance(args, list): 
            args = ' '.join(args).strip()
        else:
            pass

        logFieldnames = ["Time", "Guild", "User", "User_Plaintext", "Command", "Args"]
        if ctx.guild: guild = ctx.guild.id
        else: guild = "DM"
         

        with open("logs.csv", "a", newline='', encoding='utf-8-sig') as file:
            writer = csv.DictWriter(file, fieldnames=logFieldnames, extrasaction='ignore')
            writer.writerow(dict(zip(logFieldnames, [datetime.utcnow().isoformat(), 
                guild, 
                ctx.author.id, 
                str(ctx.author), 
                optcommand if optcommand is not None else ctx.command, 
                args
            ])))              
        return
    
    @staticmethod
    async def logRequest(bot, ctx, serverSettings, userSettings):
        try:
            logFieldnames = ["Time", "Guild", "User", "User_Plaintext", "Command", "Args"]
            
            with open(f'./src/cache/{ctx.author}_userSettings.yaml') as file:
                setting = userSettings[ctx.author.id]
                yaml.dump(setting, file, allow_unicode=True)

            #if bot owner
            if await bot.is_owner(ctx.author):
                dm = await ctx.author.create_dm()
                await dm.send(file=discord.File(r'logs.csv'))
                return

            #if guild owner/guild sudoer
            elif Sudo.isSudoer(bot, ctx, serverSettings):
                filename = f'{ctx.guild}_guildLogs'
                with open("logs.csv", 'r', encoding='utf-8-sig') as file: 
                    line = [dict(row) for row in csv.DictReader(file) if int(row["Guild"]) == ctx.guild.id]
            
            #else just bot user
            else:
                filename = f'{ctx.author}_personalLogs'
                with open("logs.csv", 'r', encoding='utf-8-sig') as file: 
                    line = [dict(row) for row in csv.DictReader(file) if int(row["User"]) == ctx.author.id]

            with open(f"./src/cache/{filename}.csv", "w", newline='', encoding='utf-8-sig') as newFile:
                writer = csv.DictWriter(newFile, fieldnames=logFieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(line)
            
            dm = await ctx.author.create_dm()
            await dm.send(file=discord.File(f"./src/cache/{filename}.csv"))
            await dm.send(file=discord.File(f'./src/cache/{ctx.author}_userSettings.yaml'))
            os.remove(f"./src/cache/{ctx.author}_personalLogs.csv")
        
        except Exception as e:
            await ErrorHandler(bot, ctx, e)
        finally: return

async def ErrorHandler(bot, ctx, error, args=None):
    if args is None: 
            if ctx.args is None:
                args = "None"
            else: args = ' '.join(list(ctx.args[2:]))
    elif isinstance(args, list): 
        args = ' '.join(args).strip()
    else:
        pass
        
    with open("logs.csv", 'r', encoding='utf-8-sig') as file: 
        doesErrorCodeMatch = False
        errorCode = "%06x" % random.randint(0, 0xFFFFFF)
        while doesErrorCodeMatch == False:
            for line in csv.DictReader(file): 
                if line["Command"] == error:
                    if line["Args"] == errorCode:
                        doesErrorCodeMatch = True
                        errorCode = "%06x" % random.randint(0, 0xFFFFFF)
                        pass
            break
    
    Log.appendToLog(ctx, "error", errorCode)

    errorLoggingChannel = await bot.fetch_channel(829172391557070878)

    #prevents doxxing by removing username
    errorOut = '\n'.join([lines if r'C:\Users' not in lines else '\\'.join(lines.split('\\')[:2]+lines.split('\\')[3:]) for lines in str(traceback.format_exc()).split('\n')])
            
    await errorLoggingChannel.send(f"Error `{errorCode}`\n```\nIn Guild: {ctx.guild.id}\nBy User: {str(ctx.author)}\nCommand: {ctx.command}\nArgs: {args if type(args) != None else 'None'}\n{errorOut}```")

    embed = discord.Embed(description=f"An unknown error has occured. Please try again later. \n If you wish to report this error, send the error code `{errorCode}` to ACEslava#9735")
    errorMsg = await ctx.send(embed=embed)
    await asyncio.sleep(60)
    await errorMsg.delete()
    return