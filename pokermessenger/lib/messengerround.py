from pokerlib.enums import PlayerAction
from pokerlib import Round

class MessengerRound(Round):

    def __init__(self, *args):
        self.publicOutSchedule = []
        self.privateOutSchedule = []
        super().__init__(*args)

    def privateOut(self, *args, **kwargs):
        self.privateOutSchedule.append((args, kwargs))

    def publicOut(self, *args, **kwargs):
        self.publicOutSchedule.append((args, kwargs))

        
