from mutants import *
import discord
from discord_slash import SlashCommand
from discord_slash.model import SlashCommandOptionType, ButtonStyle
from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_components import create_button, create_actionrow, ComponentContext


CFG = load_config()
client = discord.Client(intents=discord.Intents.all())
slash = SlashCommand(client, sync_commands=True)


OPTIONS = [
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


def buttons(lobbyId):
    return [
        create_button(
            custom_id=f'{lobbyId}-join',
            style=ButtonStyle.blue,
            label="Join Lobby"
        ),
        create_button(
            custom_id=f'{lobbyId}-view',
            style=ButtonStyle.green,
            label="View Lobby"
        )
    ]


@client.event
async def on_ready():
    print("Connected")


@client.event
async def on_component(ctx: ComponentContext):
    parts = ctx.custom_id.split('-')
    lobbyId = parts[0]
    action = parts[1]
    user = str(ctx.author)
    
    try:
        lobby = Lobby(CFG, lobbyId)
    except LobbyNotFound:
        await ctx.send('Lobby no longer exists.', hidden=True)
        return
    
    if action == 'join':
        try:
            lobby.join(user)
            await ctx.send('Joined lobby.', hidden=True)
        except LobbyPermissions:
            await ctx.send('Not a public lobby.', hidden=True)
        except LobbyUserExists:
            await ctx.send("You've already joined the lobby.", hidden=True)
        except LobbyMaxUsers:
            await ctx.send('Too many mutants, lobby is full.', hidden=True)

    elif action == 'view':
        joined = [j[:-5] for j in lobby.joined]
        await ctx.send(f'Mutants: {", ".join(joined)}', hidden=True)


@slash.slash(name='mutants',
             guild_ids=CFG['D_SERVERS'],
             description='Start a mutant lobby',
             options=OPTIONS
             )
async def _createLobby(ctx, mutant2=None, mutant3=None, mutant4=None, public=False):
    creator = str(ctx.author)
    if creator not in CFG['USERS']:
        await ctx.send(f'Who the fuck are you.')
        return

    joined = []
    for m in [mutant2, mutant3, mutant4]:
        if m:
            joined.append(str(m))

    lobby = Lobby(CFG).new(creator=creator, joined=joined, public=public)

    msg = f'Created `{lobby.name}`'
    await ctx.send(msg, components=[create_actionrow(*buttons(lobby.lobbyId))])


client.run(CFG['D_TOKEN'])
