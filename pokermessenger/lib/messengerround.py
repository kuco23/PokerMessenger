from pokerlib.enums import PlayerAction
from pokerlib import Round

class MessengerRound(Round):

    def __init__(self, *args):
        self.publicOutSchedule = []
        self.privateOutSchedule = []
        super().__init__(*args)

    def privateIn(self, player_id, action, raise_by=0):
        player = self.current_player
        to_call = self.turn_stake - player.turn_stake[self.turn]
        
        if action == PlayerAction.FOLD:
            self.processAction(PlayerAction.FOLD)
            
        elif action == PlayerAction.CHECK and to_call == 0:
            self.processAction(PlayerAction.CHECK)

        elif action == PlayerAction.CALL:
            self.processAction(PlayerAction.CALL)

        elif action == PlayerAction.RAISE:
            if to_call < player.money:
                self.processAction(PlayerAction.RAISE, raise_by)

        elif action == PlayerAction.ALLIN:
            self.processAction(PlayerAction.ALLIN)

    def privateOut(self, *args, **kwargs):
        self.privateOutSchedule.append((args, kwargs))

    def publicOut(self, *args, **kwargs):
        self.publicOutSchedule.append((args, kwargs))

        
