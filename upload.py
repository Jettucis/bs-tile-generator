import mwbot
import json
import time
import os

TILE_PATHS = 'out/tiles/'


def tryUpload(bot, title, filename):
    with open(filename, 'rb') as f:
        file_data = f.read()
    posted = 0
    while posted < 2:
        query = bot.upload(summary='', title=title, fullfile=file_data)
        querytext = json.loads(query.text)
        if query.ok and 'error' in querytext and 'code' in querytext['error'] and querytext['error']['code'] == 'fileexists-no-change':
            return
        if query.ok and 'error' not in querytext and 'upload' in querytext and 'result' in querytext['upload'] and querytext['upload']['result'] == 'Success':
            return
        else:
            print('FAILED TO POST TO '+title)
            print(query.headers)
            print(query.status_code)
            print(query.reason)
            print(querytext)
            posted += 1
            time.sleep(30)


def tile_paths(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            yield os.path.join(root, file)


bot = mwbot.Mwbot('creds.file')
for tile_path in tile_paths(TILE_PATHS):
    filename = 'Brighter_Shores_World_Map_Tile_' + tile_path[len(TILE_PATHS):].replace('/', '_').replace('\\', '_')
    print(filename)
    tryUpload(bot, filename, tile_path)