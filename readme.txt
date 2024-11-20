This repo is used to generate Leaflet tiles for the Brighter Shores Wiki
You input an image of the Brighter Shores map, and the program will cut up the images into tiles, and then upload the tiles automatically to the wiki

Install Python: https://www.python.org/downloads/release/python-3130/
Install Vips: https://github.com/libvips/build-win64-mxe/releases/tag/v8.16.0

In the console:
pip install requirements

Ask an admin on the wiki to help get a bot account for the wiki
Create a file called "creds.file"
Write 3 lines in the file:
```
Username
Password
Blank (2-FA, not needed)
```

To update the maps:
make tiles
Verify that you are satisfied with the tiles
python upload.py
