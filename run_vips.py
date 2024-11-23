import math
import pyvips
import os
import shutil

def sanitize_directory(directory):
    shutil.rmtree(directory, ignore_errors=True)
    os.makedirs(directory)


def parse_map_file(file):
    map = pyvips.Image.new_from_file(file, access='sequential')
    map = map.flatten(background=[0, 0, 0])
    map.dzsave(
        "out/tiles",
        layout="google",
        suffix=".png[compression=9]",
        background=[0, 0, 0]
    )


sanitize_directory('out/')
parse_map_file('all-map-mini-test.png')