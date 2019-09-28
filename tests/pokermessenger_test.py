from time import sleep
from argparse import ArgumentParser
from os import chdir, getcwd
from sys import path

from fbchat import Client
from fbchat.models import *

chdir('../pokermessenger')
path.append(getcwd())

from app import *

PRIVATE_THREAD = {'thread_type': ThreadType.USER}
PUBLIC_THREAD = {'thread_type': ThreadType.GROUP}

class TestDealer(Dealer):
    def __init__(self, username, password):
        self.tables = {}
        self.uid = username

    def sendMessage(self, *args, **kwargs):
        print(args)

    def fetchUserInfo(self, user_id):
        return {user_id: type(
            'thread_object', (),
            {'name': user_id}
        )()}  

class TestPlayer():
    dealer = None
    
    def __init__(self, _id, name, table_id):
        self.id = _id
        self.name = name
        self.table_id = table_id

    def send(self, message):
        if message in [
            PLAYER_SIGN_UP,
            SHOW_USER_MONEY,
            REQUEST_MONEY
        ]:
            thread_id = self.id
            kwargs = PRIVATE_THREAD
            
        elif message in STATEMENTS \
            or message.startswith(RAISE+' '):
            thread_id = self.table_id
            kwargs = PUBLIC_THREAD
            
        else: return
        
        self.dealer.onMessage(
            self.id,
            message,
            thread_id,
            **kwargs
        )
        
def simpleGame(nplayers, action):
    dealer = TestDealer(None, None)
    TestPlayer.dealer = dealer
    thread_id = '250'

    players = []
    for i in range(nplayers):
        p = TestPlayer(str(i), 'user' + str(i), thread_id)
        players.append(p)

    players[0].send(INITIALIZE_TABLE)
    for player in players:
        player.send(PLAYER_SIGN_UP)
        player.send(PLAYER_BUYIN)
    players[0].send(START_ROUND)

    table = dealer.tables[thread_id]
    while table:
        for player in players:
            if table.round.current_player.id == player.id:
                player.send(action(player))
                break

args = ArgumentParser(
    description = 'test the pokermessenger app'
)
args.add_argument(
    'npl',
    metavar = 'number_of_players',
    type = int
)
args.add_argument(
    'ttp',
    metavar = 'test_type',
    type = str,
    choices = [
        'inputgame',
        'callround'
    ]
)
vals = args.parse_args()

if vals.ttp == 'inputgame':
    action = lambda p: input(f"{p.id}: ")
    simpleGame(vals.npl, action)
elif vals.ttp == 'callround':
    action = lambda player: (CALL, sleep(0.5))[0]
    simpleGame(vals.npl, action)
