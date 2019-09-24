from pokerlib.enums import *
from config.config_vars import *

def reprCards(cards):
    return '  '.join(
        VALUES[v] + SUITS[s] for v, s in cards
    )

def reprKickers(kickers):
    return '+'.join(VALUES[card] for card in kickers)

def describeHand(hand):
    base_cards = list(hand.handbasecards)
    
    status_suit = SUITS[base_cards[0][1]]
    status_vals = [
        VALUES[base_cards[i][0]]
        for i in range(len(base_cards))
    ]
    
    if hand.handenum == Hand.HIGHCARD:
        val = status_vals[0]
        return HIGH_CARD_DESCRIPTOR.format(val)
    
    elif hand.handenum == Hand.ONEPAIR:
        val = status_vals[0]
        return ONE_PAIR_DESCRIPTOR.format(val)
    
    elif hand.handenum == Hand.TWOPAIR:
        val1, val2 = status_vals[0], status_vals[2]
        return TWO_PAIR_DESCRIPTOR.format(val1, val2)
    
    elif hand.handenum == Hand.THREEOFAKIND:
        val = status_vals[0]
        return THREE_OF_A_KIND_DESCRIPTOR.format(val)
    
    elif hand.handenum == Hand.STRAIGHT:
        val1, val2 = status_vals[-1], status_vals[0]
        return STRAIGHT_DESCRIPTOR.format(val1, val2)
    
    elif hand.handenum == Hand.FLUSH:
        val = status_vals[0]
        return FLUSH_DESCRIPTOR.format(status_suit, val)
    
    elif hand.handenum == Hand.FULLHOUSE:
        val1, val2 = status_vals[0], status_vals[-1]
        return FULL_HOUSE_DESCRIPTOR.format(val1, val2)
    
    elif hand.handenum == Hand.FOUROFAKIND:
        val = status_vals[0]
        return FOUR_OF_A_KIND_DESCRIPTOR.format(val)
    
    elif hand.handenum == Hand.STRAIGHTFLUSH:
        val1, val2 = status_vals[-1], status_vals[0]
        return STRAIGHT_FLUSH_DESCRIPTOR.format(
            status_suit, val1, val2
        )
