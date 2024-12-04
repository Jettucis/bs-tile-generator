
This repo is used to generate Leaflet tiles for the Brighter Shores Wiki
You input an image of the Brighter Shores map, and the program will cut up the images into tiles, and then upload the tiles automatically to the wiki

# Setup
* Install Python: https://www.python.org/downloads/release/python-3130/
* Install Vips: https://github.com/libvips/build-win64-mxe/releases/tag/v8.16.0
* If needed, copy the updated icon color data from https://brightershoreswiki.org/w/MediaWiki:Common.less/leaflet.less to map_data/icon_data.less.txt
* `pip install requirements.txt`
* `python download_small_icons.py`
* If needed, update config.py
* Create a file called "creds.file" and fill in the information to log into an admin bot wiki account. Write 3 lines in the file:
```
Username
Password
Blank (2-FA, not needed)
```
# Updating the Map

`python build_room_data.py` for the map overlay
`python run_vips.py` to break up the maps into tiles
Verify that you are satisfied with the generated tiles
`python upload.py`
