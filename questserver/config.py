from configparser import ConfigParser
from collections import namedtuple
from sys import exit


CatalogueSpecifier = namedtuple(
    'CatalogueSpecifier', ['command', 'path', 'mediadir', 'description']
)

config = ConfigParser()
config.read('./config.ini')

BOTTOKEN = config.get('config', 'bottoken', fallback=None)
if not BOTTOKEN:
    print('Please give "bottoken" in your config.ini')
    exit(1)

WELCOME = config.get('config', 'welcome', fallback=None)
if not WELCOME:
    print('Please give "welcome" in your config.ini')
    exit(1)

catalogue_section = config['catalogues']

CATALOGUESPECIFIERS = []

for key, value in catalogue_section.items():
    path_json, mediadir, description = value.split(':')
    CATALOGUESPECIFIERS.append(
        CatalogueSpecifier(
            command=key,
            path=path_json.strip(),
            mediadir=mediadir.strip(),
            description=description.strip()
        )
    )
