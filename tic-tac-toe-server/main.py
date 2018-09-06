#!/usr/bin/env python3

import asyncio
import json
import random

import websockets

SERVER = '0.0.0.0'
PORT = 8080
TURN_TIMEOUT = 10 # in seconds

ready_clients = []
# {token, name}
playing_clients = []
# token: {ws, name}
clients = {}
# Only if selected to play with alien: client: alien, alien: client
want_play_clients = {}

def get_clients_public_info(_clients, without_token=None):
    # _clients is playing or ready
    return [
        {
            'token': token,
            'name': clients[token]['name']
        }
        for token in _clients if token != without_token
    ]

async def echo(websocket, path):
    i = 0
    try:
        async for message in websocket:
            print('Got message {}'.format(i))
            i+=1

            m = json.loads(message)
            # TODO: don't accept commands from unknown token if not 'init'
            token = m['token']
            if m['command'] == 'init':
                clients[token] = {
                    'name': m['name'],
                    'ws': websocket,
                }
                ready_clients.append(token)
            elif m['command'] == 'get_clients':
                await websocket.send(json.dumps({
                    'answer': 'clients',
                    'data': {
                        'ready_clients': get_clients_public_info(ready_clients, token),
                        'playing_clients': get_clients_public_info(playing_clients, token),
                    }
                }))
            elif m['command'] == 'want_play_with':
                alien = clients.get(m['alien_token'])
                if not alien:
                    print('Error 0: ' + token + '  ' + m['alien_token'])
                    return

                want_play_clients[token] = m['alien_token']
                want_play_clients[m['alien_token']] = token

                await alien['ws'].send(json.dumps({
                    'answer': 'are_ready_to_play'
                }))
                # FIXME: timeout to the answer to this
            elif m['command'] == 'ready_to_play':
                # This is answer to 'are_ready_to_play'

                # Final check and if ok - start immediately
                alien = want_play_clients.get(token)
                print('Ready to play: {} \t {}'.format(token, alien))
                if (alien
                    and (token in ready_clients) and (token not in playing_clients)
                    and (alien in ready_clients) and (alien not in playing_clients)
                    and (token in want_play_clients.keys())
                    and want_play_clients.get(alien) == token
                ):

                    del want_play_clients[token]
                    del want_play_clients[alien]
                    ready_clients.remove(token)
                    ready_clients.remove(alien)
                    playing_clients.append(token)
                    playing_clients.append(alien)


                    client1, client2 = random.sample([token, alien], k=2)
                    await asyncio.wait([
                        clients[client1]['ws'].send(json.dumps({
                            'answer': 'game_started',
                            'turn_timeout': TURN_TIMEOUT,
                            'alien_name': clients[client2]['name'],
                            'first': True,
                        })),
                        clients[client2]['ws'].send(json.dumps({
                            'answer': 'game_started',
                            'turn_timeout': TURN_TIMEOUT,
                            'alien_name': clients[client1]['name'],
                            'first': False,
                        }))
                    ])
                else:
                    # don't ready to play
                    if token in want_play_clients:
                        del want_play_clients[token]
                    if alien in want_play_clients:
                        del want_play_clients[alien]

                    # alien because to 'want_to_play' source client
                    await clients[alien]['ws'].send(json.dumps({
                        'answer': 'client_not_available'
                    }))
            else:
                # Just 'echo'-server for unknown requests
                print(message)
                await websocket.send(message)
    except websockets.exceptions.ConnectionClosed as e:
        print(e)

random.seed()
asyncio.get_event_loop().run_until_complete(
    websockets.serve(echo, SERVER, PORT))
asyncio.get_event_loop().run_forever()
