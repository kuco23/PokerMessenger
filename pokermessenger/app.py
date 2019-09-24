# Originaly made with fbchat Version 1.3.9
# Dealer class is a singleton!

from sys import path
from pathlib import Path
import argparse
import sqlite3

from fbchat import Client
from fbchat.models import *

path.append(str(Path().cwd().parent))

from pokerlib.enums import *
from pokerlib import HandParser, HandParserGroup
from pokerlib import Player, PlayerGroup

from config.config_vars import *
from lib import sqlmeths, timemeths
from lib.messengerround import MessengerRound
from lib.messengertable import MessengerTable
from lib.messengerhand import reprCards, reprKickers, describeHand

# this is the documentation and the link is sent to every new player
DOC = 'https://kuco23.github.io/pokermessenger/documentation.html'

DATABASE_PATH = Path().cwd() / DATABASE_PATH
CONNECTION = sqlite3.connect(DATABASE_PATH)

TABLE_LENGTH = {
    Turn.PREFLOP: 0,
    Turn.FLOP: 3,
    Turn.TURN: 4,
    Turn.RIVER: 5
}

statement_section_names = [
    'statements-table',
    'statements-user',
    'statements-round'
]

STATEMENTS = [
    cfg.get(section, option)
    for section in statement_section_names
    for option in cfg.options(section)
]

ROUND_STATEMENTS  = {
    FOLD : PlayerAction.FOLD,
    CHECK : PlayerAction.CHECK,
    CALL : PlayerAction.CALL,
    ALLIN  : PlayerAction.ALLIN,
    RAISE : PlayerAction.RAISE
}

class Dealer(Client):

    def __init__(self, *args):
        super().__init__(*args)
        self.tables = {}

    def __resolveRoundPrivateOutSchedule(self, _round):
        while _round.privateOutSchedule:
            args, kwargs = _round.privateOutSchedule.pop(0)
            self.roundPrivateOut(_round, *args, **kwargs)

    def __resolveRoundPublicOutSchedule(self, _round):
        while _round.publicOutSchedule:
            args, kwargs = _round.publicOutSchedule.pop(0)
            self.roundPublicOut(_round, *args, **kwargs)

    def __resolveRoundSchedule(self, _round):
        self.__resolveRoundPrivateOutSchedule(_round)
        self.__resolveRoundPublicOutSchedule(_round)

    def __playerUpdateDbMoney(self, player):
        sqlmeths.update(
            CONNECTION,
            'tablemoneys',
            {'money': player.money},
            {'fbid': player.id, 'tblid': player.table_id}
        )

    def __initializePlayer(self, thread_id, p_id):
        args = CONNECTION, 'players', 'fbid', p_id
        db_data =  sqlmeths.getasdict(*args)

        money = (
            DEFAULT_BUYIN
            if db_data['money'] >= DEFAULT_BUYIN
            else db_data['money']
        )

        db_data['money'] -= money
        sqlmeths.insert(
            CONNECTION,
            'tablemoneys',
            fbid=p_id,
            tblid=thread_id,
            money=money
        )
        sqlmeths.update(
            CONNECTION,
            'players',
            db_data,
            {'fbid': p_id}
        )

        user_info = self.fetchUserInfo(p_id)[p_id]
        return Player(thread_id, p_id, user_info.name, money)

    def __resolvePlayer(self, player):
        args = CONNECTION, 'players', 'fbid', player_id
        pl_data = sqlmeths.getasdict(*args)
        tbl_data = sqlmeths.getasdicts(
            CONNECTION,
            'tablemoneys',
            'tblid',
            'money',
            {'fbid': player_id}
        )

        pl_data['money'] += tbl_data[player.table_id]
        player.money = 0

        sqlmeths.deletefromtable(
            CONNECTION,
            'tablemoneys',
            {'fbid': player.id, 'tblid': player.table_id}
        )
        sqlmeths.update(
            CONNECTION,
            'players',
            pl_data,
            {'fbid': player.id}
        )

    def __refillPlayerMoney(self, player):
        args = CONNECTION, 'players', 'fbid', player_id
        pl_data = sqlmeths.getasdict(*args)

        money = pl_data['money']
        money_to_fill = DEFAULT_BUYIN - player.money

        filled = min(money, money_to_fill)
        player.money += filled
        pl_data['money'] -= filled


    def _initializeTable(self, thread_id):
        if thread_id in self.tables:
            return self.sendMessage(
                INITIALIZE_TABLE_FAILURE,
                thread_id = thread_id,
                thread_type = ThreadType.GROUP
            )
        self.tables[thread_id] = MessengerTable(
            thread_id,
            PlayerGroup([]),
            DEFAULT_SMALL_BLIND,
            DEFAULT_BIG_BLIND
        )
        self.sendMessage(
            INITIALIZE_TABLE_SUCCESS,
            thread_id = thread_id,
            thread_type = ThreadType.GROUP
        )

    def _startRound(self, thread_id):
        if thread_id not in self.tables:
            return self.sendMessage(
                START_ROUND_FAILURE_NOT_INIT,
                thread_id = thread_id,
                thread_type = ThreadType.GROUP
            )

        table = self.tables[thread_id]
        if table.round:
            return self.sendMessage(
                START_ROUND_FAILURE,
                thread_id = thread_id,
                thread_type = ThreadType.GROUP
            )
        if not table:
            return self.sendMessage(
                START_ROUND_FAILURE_NOT_ENOUGH_PLAYERS,
                thread_id = thread_id,
                thread_type = ThreadType.GROUP
            )

        self.sendMessage(
            START_ROUND_SUCCESS,
            thread_id = thread_id,
            thread_type = ThreadType.GROUP
        )

        if table and table.round is None:
            table.newRound(thread_id)

        while table and not table.round:
            self.__resolveRoundSchedule(table.round)
            table.newRound(thread_id)

        self.__resolveRoundSchedule(table.round)

    def _playerBuyin(self, thread_id, author_id):
        if thread_id not in self.tables:
            return self.sendMessage(
                BUYIN_FAILURE_NOT_INIT,
                thread_id = thread_id,
                thread_type = ThreadType.GROUP
            )

        table = self.tables[thread_id]
        if author_id in table:
            return self.sendMessage(
                BUYIN_FAILURE_ALREADY_IN_GAME,
                thread_id = thread_id,
                thread_type = ThreadType.GROUP
            )

        if len(table.all_players) >= 9:
            return self.sendMessage(
                BUYIN_FAILURE_MAXIMUM_PLAYERS,
                thread_id = thread_id,
                thread_type = ThreadType.GROUP
            )

        args = CONNECTION, 'players', 'fbid', author_id
        if not sqlmeths.getasdict(*args):
            return self.sendMessage(
                BUYIN_FAILURE_NOT_SIGNED_UP,
                thread_id = thread_id,
                thread_type = ThreadType.GROUP
            )

        player = self.__initializePlayer(thread_id, author_id)
        table += [player]

        self.sendMessage(
            BUYIN_SUCCESS.format(
                player.name,
                player.money
            ),
            thread_id = thread_id,
            thread_type = ThreadType.GROUP
        )

    def _toggleLastRound(self, thread_id, author_id):
        if thread_id not in self.tables: return

        table = self.tables[thread_id]
        if not table.round: return

        table.interrupt = not table.interrupt
        send = [
            TOGGLE_LAST_ROUND_UNDO,
            TOGGLE_LAST_ROUND_END
        ][table.interrupt]

        self.sendMessage(
            send,
            thread_id = thread_id,
            thread_type = ThreadType.GROUP
        )

    def _leaveTable(self, thread_id, author_id):
        if thread_id not in self.tables: return
        table = self.tables[thread_id]
        if author_id not in table: return

        player = table.all_players.getPlayerById(author_id)
        table -= [player]
        self.__resolvePlayer(player)

        self.sendMessage(
            LEAVE_TABLE_SUCCESS.format(player.name),
            thread_id = thread_id,
            thread_type = ThreadType.GROUP
        )

    def _refillBuyin(self, thread_id, author_id):
        if thread_id not in self.tables: return
        table = self.tables[thread_id]
        if author_id not in table: return

        player = table.all_players.getPlayerById(author_id)
        if player.money > DEFAULT_BUYIN: return

        if (table.round and
            player.id in table.round and
            not player.is_folded): return

        self.__refillPlayerMoney(player)
        self.sendMessage(
            REFILL_BUYIN_SUCCESS.format(player.money),
            thread_id = thread_id,
            thread_type = ThreadType.GROUP
        )

    def _showUserTableMoney(self, thread_id, author_id):
        if thread_id not in self.tables: return
        table = self.tables[thread_id]
        if author_id not in table: return
        player = table.all_players.getPlayerById(author_id)

        self.sendMessage(
            SHOW_TABLE_MONEY_SUCCESS.format(player.money),
            thread_id = thread_id,
            thread_type = ThreadType.GROUP
        )

    def _signUpPlayer(self, thread_id):
        args = CONNECTION, 'players', 'fbid', thread_id
        sql_data = sqlmeths.getasdict(*args)

        if sql_data:
            return self.sendMessage(
                PLAYER_SIGN_UP_FAILURE,
                thread_id = thread_id
            )

        user_info = self.fetchUserInfo(thread_id)
        user_info = user_info[thread_id]
        sqlmeths.insert(
            CONNECTION,
            'players',
            name = user_info.name,
            fbid = thread_id,
            money = PLAYER_STARTING_MONEY,
            timestamp = timemeths.formatted_timestamp()
        )
        self.sendMessage(
            PLAYER_SIGN_UP_SUCCESS.format(
                user_info.name,
                PLAYER_STARTING_MONEY,
                DOC
            ),
            thread_id = thread_id
        )

    def _showUserMoney(self, thread_id):
        args = CONNECTION, 'players', 'fbid', thread_id
        pl_data = sqlmeths.getasdict(*args)

        if not pl_data:
            return self.sendMessage(
                NOT_SIGNED_UP_ERROR,
                thread_id = thread_id
            )

        self.sendMessage(
            SHOW_USER_MONEY_SUCCESS.format(
                pl_data['money']
            ),
            thread_id = thread_id,
        )

    def _requestMoney(self, thread_id):
        args = CONNECTION, 'players', 'fbid', thread_id
        pl_data = sqlmeths.getasdict(*args)

        if not pl_data:
            return self.sendMessage(
                NOT_SIGNED_UP_ERROR,
                thread_id = thread_id
            )

        timestamp = timemeths.formatted_timestamp()
        diff = timemeths.get_time_diff(
            timestamp,
            pl_data['timestamp']
        )

        hours_waited = diff['days'] * 24 + diff['hours']
        if hours_waited < MONEY_WAITING_PERIOD:
            remainder = timemeths.get_time_remainder(
                timestamp,
                pl_data['timestamp'],
                MONEY_WAITING_PERIOD
            )
            to_wait = ', '.join(
                str(remainder[timeframe]) + ' ' + timeframe
                for timeframe in remainder
                if remainder[timeframe]
            )
            return self.sendMessage(
                REQUEST_MONEY_FAILURE.format(to_wait),
                thread_id = thread_id
            )

        pl_data['timestamp'] = timestamp
        pl_data['money'] += MONEY_ADD_PER_PERIOD
        sqlmeths.update(
            CONNECTION,
            'players',
            pl_data,
            {'fbid': thread_id}
        )
        self.sendMessage(
            REQUEST_MONEY_SUCCESS.format(
                MONEY_ADDED_PER_REQUEST
            ),
            thread_id = thread_id
        )

    def _roundInput(self, thread_id, author_id, message):
        if thread_id not in self.tables: return
        table = self.tables[thread_id]
        if not table.round: return
        if author_id != table.round.current_player.id: return

        if message.startswith(RAISE):
            if message.split()[1].isdigit():
                raise_by = int(float(message.split()[1]))
                table.round.privateIn(
                    author_id,
                    ROUND_STATEMENTS[RAISE],
                    raise_by
                )

        else: table.round.privateIn(
            author_id,
            ROUND_STATEMENTS[message]
        )

        if table.round.finished and table.interrupt:
            self.__resolveRoundSchedule(table.round)
            return self._emptyTable(table.id)

        # round can end after calling newRound
        while table and table.round.finished:
            self.__resolveRoundSchedule(table.round)
            table.newRound(table.id)

        self.__resolveRoundSchedule(table.round)

    def onPersonRemoved(self, removed_id, author_id,
                        thread_id, **kwargs):

        if thread_id not in self.tables: return
        if removed_id == self.uid:
            return self._removeTable(thread_id)
        if removed_id not in self.tables[thread_id]: return
        if removed_id != author_id:
            return self._removeTable(thread_id)

        table = self.tables[thread_id]
        player = table.players.getPlayerById(removed_id)
        table -= [player]
        player.resolve()

    def onMessage(self, author_id, message, thread_id, **kwargs):
        if author_id == self.uid: return

        thread_type = kwargs['thread_type']
        message = message.lower()

        if thread_type == ThreadType.GROUP:

            if message == INITIALIZE_TABLE:
                self._initializeTable(thread_id)

            elif message == START_ROUND:
                self._startRound(thread_id)

            elif message == PLAYER_BUYIN:
                self._playerBuyin(thread_id, author_id)

            elif message == TOGGLE_LAST_ROUND:
                self._toggleLastRound(thread_id, author_id)

            elif message == LEAVE_TABLE:
                self._leaveTable(thread_id, author_id)

            elif message == REFILL_BUYIN:
                self._refillBuyin(thread_id, author_id)

            # this is experimental and ugly
            elif message == SHOW_USER_TABLE_MONEY:
                self._showUserTableMoney(thread_id, author_id)

            elif message in ROUND_STATEMENTS \
                or message.startswith(RAISE + ' '):
                self._roundInput(
                    thread_id,
                    author_id,
                    message
                )

        elif thread_type == ThreadType.USER:

            if message == PLAYER_SIGN_UP:
                self._signUpPlayer(thread_id)

            elif message == SHOW_USER_MONEY:
                self._showUserMoney(thread_id)

            elif message == REQUEST_MONEY:
                self._requestMoney(thread_id)


    def roundPrivateOut(self, _round, _id, player_id, **kwargs):
        player = _round.players.getPlayerById(player_id)

        if _id == PrivateOutId.DEALTCARDS:
            repr_cards = reprCards(player.cards)
            send = DEALT_CARDS.format(repr_cards)

        if send: self.sendMessage(
            send,
            thread_id = player.id,
            thread_type = ThreadType.USER
        )

    def roundPublicOut(self, _round, _id, **kwargs):
        globals().update(kwargs) # not permanant

        if _id == PublicOutId.NEWROUND:
            send = NEW_ROUND

        elif _id == PublicOutId.ROUNDFINISHED:
            send = ROUND_FINISHED

        elif _id == PublicOutId.NEWTURN:
            turn_name = TURN_NAMES[turn]
            table_cards = _round.table[:TABLE_LENGTH[turn]]
            cards_repr = reprCards(table_cards)
            send = NEW_TURN.format(turn_name, cards_repr)

        elif _id == PublicOutId.SMALLBLIND:
            player = _round.players.getPlayerById(player_id)
            self.__playerUpdateDbMoney(player)
            send = SMALL_BLIND.format(player.name, turn_stake)

        elif _id == PublicOutId.BIGBLIND:
            player = _round.players.getPlayerById(player_id)
            self.__playerUpdateDbMoney(player)
            send = BIG_BLIND.format(player.name, turn_stake)

        elif _id == PublicOutId.PLAYERFOLD:
            player = _round.players.getPlayerById(player_id)
            send = PLAYER_FOLD.format(player.name)

        elif _id == PublicOutId.PLAYERCHECK:
            player = _round.players.getPlayerById(player_id)
            send = PLAYER_CHECK.format(player.name)

        elif _id == PublicOutId.PLAYERCALL:
            player = _round.players.getPlayerById(player_id)
            self.__playerUpdateDbMoney(player)
            send = PLAYER_CALL.format(player.name, called)

        elif _id == PublicOutId.PLAYERRAISE:
            player = _round.players.getPlayerById(player_id)
            self.__playerUpdateDbMoney(player)
            send = PLAYER_RAISE(player.name, raise_by)

        elif _id == PublicOutId.PLAYERALLIN:
            player = _round.players.getPlayerById(player_id)
            self.__playerUpdateDbMoney(player)
            send = PLAYER_ALL_IN.format(
                player.name, all_in_stake
            )

        elif _id == PublicOutId.PLAYERAMOUNTTOCALL:
            player = _round.players.getPlayerById(player_id)
            self.__playerUpdateDbMoney(player)
            send = PLAYER_AMOUNT_TO_CALL.format(
                player.name, to_call
            )

        elif _id == PublicOutId.DECLAREPREMATUREWINNER:
            player = _round.players.getPlayerById(player_id)
            self.__playerUpdateDbMoney(player)
            send = DECLARE_PREMATURE_WINNER.format(
                player.name, money_won
            )

        elif _id == PublicOutId.DECLAREFINISHEDWINNER:
            player = _round.players.getPlayerById(player_id)
            self.__playerUpdateDbMoney(player)
            hand_repr = describeHand(player.hand)
            kickers_repr = reprKickers(kickers)
            send = DECLARE_FINISHED_WINNER.format(
                player.name, money_won,
                hand_repr, kickers_repr
            )

        elif _id == PublicOutId.PUBLICCARDSHOW:
            player = _round.players.getPlayerById(player_id)
            cards_repr = reprCards(player.cards)
            send = PUBLIC_CARD_SHOW.format(
                player.name, cards_repr
            )

        if send: self.sendMessage(
            send,
            thread_id = _round.id,
            thread_type = ThreadType.GROUP
        )

    def _removeTable(self, table_id):
        for player in self.tables.pop(table_id).all_players:
            self.__resolvePlayer(player)

    def _emptyTable(self, table_id):
        for player in self.tables[table_id].all_players:
            self.__resolvePlayer(player)


players_sql = '''
CREATE TABLE IF NOT EXISTS players(
    id integer PRIMARY KEY,
    fbid integer NOT NULL,
    name text NOT NULL,
    money integer,
    timestamp text
)
'''
tablemoneys_sql = '''
CREATE TABLE IF NOT EXISTS tablemoneys(
    id integer PRIMARY KEY,
    fbid integer NOT NULL,
    tblid integer NOT NULL,
    money integer
)
'''
sqlmeths.executesql(CONNECTION, players_sql, tablemoneys_sql)

# this has to be done before every app rerun
# in case anyone left the money on some table
for fbid in sqlmeths.getcol(CONNECTION, 'players', 'fbid'):
    fbid = fbid[0]
    leftovers = sqlmeths.getasdicts(
        CONNECTION,
        'tablemoneys',
        'tblid',
        'money',
        {'fbid': fbid}
    )
    playerdata = sqlmeths.getasdict(
        CONNECTION,
        'players',
        'fbid',
        fbid
    )
    playerdata['money'] += sum(leftovers.values())
    sqlmeths.update(
        CONNECTION,
        'players',
        playerdata,
        {'fbid': fbid}
    )
sqlmeths.emptytable(CONNECTION, 'tablemoneys')

# game continuation
if __name__ == '__main__':
    dealer = Dealer(USERNAME, PASSWORD)
    dealer.listen()
