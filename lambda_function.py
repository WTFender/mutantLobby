from mutants import *


CFG = load_config()


def error(code=500):
    return {
			"statusCode": code,
			"body": 'Error',
			"headers": {"Content-Type": "text/plain"}
	}


def not_found(msg='Not found.'):
    return {
			"statusCode": 404,
			"body": 'Lobby not found.',
			"headers": {"Content-Type": "text/plain"}
	}


def ok(msg='ok'):
    return {
            "statusCode": 200,
            "body": msg,
            "headers": {"Content-Type": "text/plain"}
    }


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
    lobbyId, slotId, action = parse_path(path)
    if not lobbyId and not slotId:
        return not_found('Not found.')

    if action == 'join':
        try:
            lobby = Lobby(CFG, lobbyId)
            
            if slotId in lobby.slots:
                user = lobby.slots[slotId]
                lobby.join(user)
                return ok(msg=f'{user[:-5]} joined the lobby.')

            else:
                return not_found(msg='Lobby slot not found.')

        except LobbyNotFound:
            return not_found('Lobby not found.')
        except LobbyPermissions:
            return error(code=403)
        except LobbyUserExists:
            return ok(msg='User already joined lobby.')
        except LobbyMaxUsers:
            return ok(msg='Too many mutants, lobby is full.')
        except Exception as e:
            print(e)
            return error()
    else:
        return not_found('Unknown')
    
