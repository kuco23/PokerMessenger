from datetime import datetime

def formatted_timestamp() -> str:
    timestamp = datetime.now()
    timevals = ['year', 'month', 'day', 'hour', 'minute', 'second']
    return '/'.join(str(timestamp.__getattribute__(val)) for val in timevals)
def deformatted_timestamp(timestamp) -> list:
    return map(int, timestamp.split('/'))

def get_time_diff(timestamp1, timestamp2):
    timestamp1 = deformatted_timestamp(timestamp1)
    timestamp2 = deformatted_timestamp(timestamp2)
    diff = datetime(*timestamp1) - datetime(*timestamp2)
    days = diff.days
    seconds = diff.seconds
    hours, seconds = seconds // 3600, seconds % 3600
    minutes, seconds = seconds // 60, seconds % 60
    return {'days': days, 'hours': hours,
            'minutes': minutes, 'seconds': seconds}

def get_time_remainder(timestamp1, timestamp2, waiting_period=4):
    timestamp1 = deformatted_timestamp(timestamp1)
    timestamp2 = deformatted_timestamp(timestamp2)
    diff = datetime(*timestamp1) - datetime(*timestamp2)
    seconds = (waiting_period - diff.days * 24) * 3600 - diff.seconds
    seconds = seconds if seconds >= 0 else 0
    days, seconds = seconds // (3600 * 24), seconds % (3600 * 24)
    hours, seconds = seconds // 3600, seconds % 3600
    minutes, seconds = seconds // 60, seconds % 60
    return {'days': days, 'hours': hours,
            'minutes': minutes, 'seconds': seconds}
