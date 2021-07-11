import json
import boto3
import logging
from util import rand_lobby_name
import yaml
import boto3
import telebot
import requests

with open('config.yml', 'r') as cfg:
    try:
        CFG = (yaml.safe_load(cfg))
    except yaml.YAMLError as exc:
        print(exc)

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)
LOBBIES = boto3.resource('dynamodb').Table(CFG['TABLE'])
bot = telebot.TeleBot(CFG['T_TOKEN'])


def notifyDiscord(msg=''):
    for hook in CFG['D_WEBHOOKS']:
        r = requests.post(hook, json=msg)


def error(code=500):
    return {
			"statusCode": code,
			"body": 'Error',
			"headers": {"Content-Type": "text/plain"}
	}


def not_found(code=404):
    return {
			"statusCode": code,
			"body": 'Lobby not found.',
			"headers": {"Content-Type": "text/plain"}
	}


def ok(msg='ok'):
    return {
            "statusCode": 200,
            "body": msg,
            "headers": {"Content-Type": "text/plain"}
    }


def notifyChannel(msg=''):
    # notify telegram channels
    for chan in CFG['T_CHANNELS']:
        bot.send_message(text=msg, chat_id=chan, parse_mode='Markdown')


def join_lobby(lobby, slotId):
    lobby = lobby['Item']
    
    # unk user
    if slotId not in lobby['slots']:
        return ok('User not found.')
    
    # no slots
    elif len(lobby['joined']) >= int(lobby['max']):
        return ok('Lobby is full, too many mutants!')

    # already joined
    elif lobby['slots'][slotId] in lobby['joined']:
        return ok("You've already joined the lobby.")

    # update lobby
    user = lobby['slots'][slotId]
    lobby['joined'].append(user)
    LOBBIES.put_item(Item=lobby)
    msg = f'`{user}` joined `{lobby["name"]}`'
    notifyChannel(msg=msg)
    notifyDiscord({'username': lobby['name'], 'content': f'`{user}` joined'})

    return ok('%s joined the lobby!' % user)


def parse_path(path):
    parts = path.split('/')
    if (len(parts[0]) == 8 and   # 8 char lobbyId
        len(parts[1]) == 8 and   # 8 char slotId
        parts[2] in ['join'] and # action
        ''.join(parts).isalnum() # alphanumeric
        ):
        return parts[0], parts[1], parts[2]
    else:
        return None, None, None


def lambda_handler(event, context):
    # avoid prefetching
    if event['headers']['user-agent'].startswith('Telegram'):
        return ok()
    
    path = event['path'][1:] # remove preceeding '/'
    
    try:
        lobbyId, slotId, action = parse_path(path)
        if not lobbyId:
            return ok() # ignore
        
        if action == 'join':
            lobby = LOBBIES.get_item(Key={'lobbyId': lobbyId})
            if 'Item' in lobby: # exists
                return join_lobby(lobby, slotId)
        
        else: # does not existv
            return not_found()

    except Exception as e:
        LOG.error(e)
        return error(code=500)