import mwbot
import pathlib
import json
import time
import os

TILE_PATHS = 'out/tiles/'
ATTEMPTS = 3


def try_upload(bot, title, filename):
    with open(filename, 'rb') as f:
        file_data = f.read()
    posted = 0
    while posted < ATTEMPTS:
        query = bot.upload(summary='', title=title, fullfile=file_data)
        querytext = json.loads(query.text)
        if query.ok and 'error' in querytext and 'code' in querytext['error'] and querytext['error']['code'] == 'fileexists-no-change':
            # Rejected by file has not changed - ok
            return
        if query.ok and 'error' not in querytext and 'upload' in querytext and 'result' in querytext['upload'] and querytext['upload']['result'] == 'Success':
            # Successfully uploaded
            return
        else:
            print('FAILED TO POST TO '+title)
            print(query.headers)
            print(query.status_code)
            print(query.reason)
            print(querytext)
            posted += 1
            time.sleep(30)
    raise ConnectionError


def try_delete(bot, title, reason):
    posted = 0
    while posted < ATTEMPTS:
        query = bot.delete(title=title, reason=reason)
        querytext = json.loads(query.text)
        if query.ok and 'error' in querytext and 'code' in querytext['error'] and querytext['error']['code'] == 'missingtitle':
            # File does not exist - pass
            return
        if query.ok and 'error' not in querytext and 'delete' in querytext and 'logid' in querytext['delete']:
            # Successfully deleted
            return
        else:
            print('FAILED TO POST TO '+title)
            print(query.headers)
            print(query.status_code)
            print(query.reason)
            print(querytext)
            posted += 1
            time.sleep(30)
    raise ConnectionError


def try_edit(bot, summary, title, text):
    posted = 0
    while posted < ATTEMPTS:
        query = bot.post(summary, title, text)
        querytext = json.loads(query.text)
        #if query.ok and 'error' in querytext and 'code' in querytext['error'] and querytext['error']['code'] == 'missingtitle':
        #    # File does not exist - pass
        #    return
        if query.ok and 'error' not in querytext and 'edit' in querytext and 'result' in querytext['edit'] and 'Success' in querytext['edit']['result']:
            # Successfully deleted
            return
        else:
            print('FAILED TO POST TO '+title)
            print(query.headers)
            print(query.status_code)
            print(query.reason)
            print(querytext)
            posted += 1
            time.sleep(30)
    raise ConnectionError


def tile_paths(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            yield os.path.join(root, file)


def count_zoom_levels(directory):
    folders = os.listdir(directory)
    levels = 0
    while str(levels) in folders:
        levels += 1
    return levels


def tile_paths(directory, zooms):
    for zoom in range(zooms):
        for y in range(2**zoom):
            for x in range(2**zoom):
                file_path = pathlib.Path(directory, str(zoom), str(y), f'{x}.png')
                wiki_path = f'Brighter_Shores_World_Map_Tile_{zoom}_{y}_{x}.png'
                yield [file_path, wiki_path]


bot = mwbot.Mwbot('creds.file')
zooms = count_zoom_levels(TILE_PATHS)
gallery = []
# Normal tiles:
for file_path, wiki_path in tile_paths(TILE_PATHS, zooms):
    print(file_path, wiki_path)
    if file_path.exists():
        print(f'\033[92m{wiki_path}')
        gallery.append(wiki_path)
        try_upload(bot, wiki_path, file_path)
    else:
        print(f'\033[91m{wiki_path}')
        try_delete(bot, f'File:{wiki_path}', 'Unused map file')
# Blank tile:
wiki_path = 'Brighter_Shores_World_Map_Tile_blank.png'
file_path = pathlib.Path(TILE_PATHS, 'blank.png')
print(f'\033[92m{wiki_path}')
gallery.append(wiki_path)
try_upload(bot, wiki_path, file_path)

# Orphanage
orphanage_page = 'Brighter Shores:Orphanage/Map'
print(orphanage_page)
orphanage_text = f'''These map tiles are used in the Brighter Shores wiki map:
<gallery>
{'\n'.join(gallery)}
</gallery>'''
try_edit(bot, 'Updating map tiles', orphanage_page, orphanage_text)
