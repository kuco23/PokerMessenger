from pathlib import Path
import configparser

strToList = lambda s: list(map(
    str.strip,
    s[1:-1].split(',')
))

base = 'config/'
config_files = [
    'config_implementation.ini',
    'config_interface.ini',
    'config_account.ini'
]

config_paths = list(map(
    lambda file: Path(base) / Path(file),
    config_files
))

cfg = configparser.ConfigParser()
cfg.read(config_paths, encoding='utf-8-sig')

section = 'sqlite'
keys = cfg.options(section)
locals().update(dict(zip(
    map(lambda key: key.upper(), keys),
    map(lambda key: cfg.get(section, key), keys)
)))

section = 'game-table'
keys = cfg.options(section)
locals().update(dict(zip(
    map(lambda key: key.upper(), keys),
    map(lambda key: cfg.getint(section, key), keys)
)))

section = 'game-user'
keys = cfg.options(section)
locals().update(dict(zip(
    map(lambda key: key.upper(), keys),
    map(lambda key: cfg.getint(section, key), keys)
)))

section = 'data_repr'
keys = cfg.options(section)
locals().update(dict(zip(
    map(lambda key: key.upper(), keys),
    map(lambda key: strToList(cfg.get(section, key)), keys)
)))

section = 'statements-round'
keys = cfg.options(section)
locals().update(dict(zip(
    map(lambda key: key.upper(), keys),
    map(lambda key: cfg.get(section, key), keys)
)))

section = 'statements-table'
keys = cfg.options(section)
locals().update(dict(zip(
    map(lambda key: key.upper(), keys),
    map(lambda key: cfg.get(section, key), keys)
)))

section = 'statements-user'
keys = cfg.options(section)
locals().update(dict(zip(
    map(lambda key: key.upper(), keys),
    map(lambda key: cfg.get(section, key), keys)
)))


section = 'statements-replies-table'
keys = cfg.options(section)
locals().update(dict(zip(
    map(lambda key: key.upper(), keys),
    map(lambda key: cfg.get(section, key), keys)
)))

section = 'statements-replies-user'
keys = cfg.options(section)
locals().update(dict(zip(
    map(lambda key: key.upper(), keys),
    map(lambda key: cfg.get(section, key), keys)
)))

section = 'privateout-descriptors'
keys = cfg.options(section)
locals().update(dict(zip(
    map(lambda key: key.upper(), keys),
    map(lambda key: cfg.get(section, key), keys)
)))

section = 'publicout-descriptors'
keys = cfg.options(section)
locals().update(dict(zip(
    map(lambda key: key.upper(), keys),
    map(lambda key: cfg.get(section, key), keys)
)))

section = 'hand-descriptors'
keys = cfg.options(section)
locals().update(dict(zip(
    map(lambda key: key.upper(), keys),
    map(lambda key: cfg.get(section, key), keys)
)))

section = 'facebook-dealer_account'
keys = cfg.options(section)
locals().update(dict(zip(
    map(lambda key: key.upper(), keys),
    map(lambda key: cfg.get(section, key), keys)
)))
