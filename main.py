import uuid
from util import rand_lobby_name
import yaml
import time
import boto3
import telebot
import discord
import requests
from discord_slash import SlashCommand
from discord_slash.model import SlashCommandOptionType, ButtonStyle
from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_components import create_button, create_actionrow, ComponentContext


with open('config.yml', 'r') as cfg:
    try:
        CFG = (yaml.safe_load(cfg))
    except yaml.YAMLError as exc:
        print(exc)


LOBBIES = boto3.resource('dynamodb').Table(CFG['TABLE'])
client = discord.Client(intents=discord.Intents.all())
slash = SlashCommand(client, sync_commands=True)
bot = telebot.TeleBot(CFG['T_TOKEN'])


def notifyDiscord(payload):
    for hook in CFG['D_WEBHOOKS']:
        r = requests.post(hook, json=payload)
        print(r.status_code)


def notifyChannel(msg=''):
    # notify telegram channels
    for chan in CFG['T_CHANNELS']:
        bot.send_message(text=msg, chat_id=chan, parse_mode='Markdown')


def sendInvites(lobby):
    # send telegram invite links
    for slotId in lobby['slots']:
        user = lobby['slots'][slotId]
        chatId = CFG['USERS'][user]['telegram']
        inviteUrl = CFG['API'] + lobby['lobbyId'] + '/' + slotId + '/join'
        msg = f"[Join {lobby['name']}!]({inviteUrl})",
        bot.send_message(text=msg, chat_id=chatId, parse_mode='Markdown')


def createLobby(user, m2, m3, m4, public, max=5):
    # defaults
    lobby = {
        'creator': user,
        'expires': int(time.time()) + 3600,  # 1 hour
        'lobbyId': str(uuid.uuid4())[:8],
        'name': rand_lobby_name(),
        'joined': [user],
        'max': max,
        'public': public,
        'slots': {},
    }

    # add joined users
    print([m2, m3, m4])
    for mutant in [m2, m3, m4]:
        if mutant:
            lobby['joined'].append(str(mutant))

    # create slots for invites
    for user in CFG['USERS']:
        if user not in lobby['joined']:
            slotId = str(uuid.uuid4())[:8]
            lobby['slots'][slotId] = user

    LOBBIES.put_item(Item=lobby)
    return lobby


@client.event
async def on_ready():
    print("Connected")


@client.event
async def on_component(ctx: ComponentContext):
    parts = ctx.custom_id.split('-')
    lobbyId = parts[0]
    action = parts[1]
    user = str(ctx.author)

    lobby = LOBBIES.get_item(Key={'lobbyId': lobbyId})
    if 'Item' in lobby:  # exists
        lobby = lobby['Item']
    else: # lobby not found
        await ctx.send('Lobby no longer exists.', hidden=True)

    if action == 'join':
        # private lobby
        if not lobby['public'] and user not in CFG['USERS']:
            await ctx.send('Not a public lobby.', hidden=True)

        # full
        elif len(lobby['joined']) >= int(lobby['max']):
            await ctx.send('Too many mutants, lobby is full.', hidden=True)

        # already in lobby
        elif user in lobby['joined']:
            await ctx.send("You've already joined the lobby.", hidden=True)

        else:  # join
            lobby['joined'].append(user)
#                for s in list(lobby['slots']):
#                    if lobby['slots'][s] == user:
#                        lobby['slots'].pop(s, None)
            LOBBIES.put_item(Item=lobby)

            msg = f'`{user}` joined {lobby["name"]}.'
            await ctx.send(msg, hidden=True)
            notifyChannel(msg=msg)
            notifyDiscord({'username': lobby['name'], 'content': f'`{user}` joined'})

    elif action == 'view':
        joined = ', '.join(lobby['joined'])
        await ctx.send(f'Mutants: {joined}', hidden=True)


@slash.slash(name='mutants',
             guild_ids=CFG['D_SERVERS'],
             description='Start a mutant lobby',
             options=[
                 create_option(
                     name='mutant2',
                     description='mutant1',
                     option_type=SlashCommandOptionType.USER,
                     required=False
                 ),
                 create_option(
                     name='mutant3',
                     description='mutant2',
                     option_type=SlashCommandOptionType.USER,
                     required=False
                 ),
                 create_option(
                     name='mutant4',
                     description='mutant3',
                     option_type=SlashCommandOptionType.USER,
                     required=False
                 ),
                 create_option(
                     name='public',
                     description='Allow public discord users to join, defaults to False',
                     option_type=SlashCommandOptionType.BOOLEAN,
                     required=False
                 )
             ]
             )
async def _createLobby(ctx, mutant2=None, mutant3=None, mutant4=None, public=False):
    if str(ctx.author) not in CFG['USERS']:
        await ctx.send(f'Who the fuck are you.')
        return

    lobby = createLobby(str(ctx.author),
                        mutant2, mutant3, mutant4,
                        public)

    buttons = [
        create_button(
            custom_id=f'{lobby["lobbyId"]}-join',
            style=ButtonStyle.blue,
            label="Join Lobby"
        )
#        create_button(
#            custom_id=f'{lobby["lobbyId"]}-view',
#            style=ButtonStyle.grey,
#            label="View"
#        )
    ]

    msg = f'`{lobby["creator"]}` created `{lobby["name"]}`'
    await ctx.send(msg, components=[create_actionrow(*buttons)])
    notifyChannel(msg=msg)
    sendInvites(lobby)

    for j in lobby['joined']:
        if j == lobby['creator']:
            continue
        msg = f'`{j}` joined `{lobby["name"]}`'
        #await ctx.send(msg)
        payload = {'username': lobby['name'], 'content': f'`{j}` joined'}
        notifyDiscord(payload)
        notifyChannel(msg=msg)


client.run(CFG['D_TOKEN'])
