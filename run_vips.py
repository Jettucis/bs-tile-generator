import pyvips
import os
import shutil
import config


def sanitize_directory(directory):
    shutil.rmtree(directory, ignore_errors=True)
    os.makedirs(directory)


def parse_map_file(file, background_color):
    map = pyvips.Image.new_from_file(file, access='sequential')
    map = map.flatten(background=background_color)
    map.dzsave(
        "out/tiles",
        layout="google",
        suffix=".png[compression=9]",
        background=background_color
    )
    # In dzsave, the background parameter properly tints tiles, but appears to be somehow bugged for blank.png when a non-monochrome parameter is provided
    # Therefore, we manually recreate the blank.png file
    background_color_image = pyvips.Image.new_from_memory(bytes(background_color*256*256), 256, 256, 3, 'uchar')
    background_color_image.pngsave('out/tiles/blank.png', compression=9)


def parse_room_file(file):
    map = pyvips.Image.new_from_file(file, access='sequential')
    map.dzsave(
        "out/rooms",
        layout="google",
        suffix=".png[compression=9]",
        background=(0, 0, 0, 0)
    )


sanitize_directory('out/tiles/')
parse_map_file(config.MAP_FILE, [0, 0, 0])
sanitize_directory('out/rooms/')
parse_room_file('out/room_layer.png')
