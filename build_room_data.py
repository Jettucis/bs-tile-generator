import config
from PIL import Image, ImageFont, ImageDraw, ImageColor, ImageFilter
import json
import math
import re
import os

SCALE = config.TILE_WIDTH  # 48
multiplier = SCALE/48

title = {
    'font': 'fonts/RobotoSlab-SemiBold.ttf',
    # 'font_size': 37*multiplier,
    'font_size': 52*multiplier,  # empirically tested for a character height of 37 pixels at a SCALE of 48
    'height': 64*multiplier,
    'margin_side': 20*multiplier,
    'margin_vert': 14*multiplier,  # Reference from capital letter
    'multiline_margin_vert': 15*1.25*multiplier,
    'shadow_offset': 4*multiplier,
}
entity = {
    'font': 'fonts/SourceSans3-SemiBold.ttf',
    # 'font_size': 37*multiplier,
    'font_size': 52*multiplier,  # empirically tested for a character height of 37 pixels at a SCALE of 48
    # Slightly reduced kerning
    'icon-text_margin': 12*multiplier,
    'icon_shiftdown': 8*multiplier,
    'text_shiftdown': 14*multiplier,
    'margin_side': 12*multiplier,
    'margin_top': 14*multiplier,
    'margin_bottom': 20*multiplier,
    'height': 68*multiplier,
    'shadow_offset': 4*multiplier,
    'distance_between': 4*multiplier,
}
icon = {
    'base_height': 64,
}
background = {
    'margin': 18*multiplier,
    'top_border_space': 30*multiplier,
    'shadow_offset': 0*multiplier,
    'radius': 24*multiplier,
}
shadows = {
    'margin': 11*multiplier,
    'color': (0, 0, 0, 255),
    'blur_factor': 6*multiplier,  # TODO varies based on zoom?
}


class RoomData:
    def __init__(self, room):
        self.coordinates = [(coord + 0.5)*SCALE for coord in room['coordinates']]
        self.fill = ImageColor.getrgb(room['color'])
        self.titles = RoomTitles(self, room)
        self.height = self.titles.background_height + shadows['margin']*2
        self.entities = RoomEntities(self, room)
        if len(self.entities.entities) == 0:
            self.background_height = 0
            self.background_width = 0
        else:
            self.background_height = len(self.entities.entities)*entity['height'] + (len(self.entities.entities) - 1)*entity['distance_between'] + \
                background['margin']*2 + self.titles.background_height - background['top_border_space']
            self.background_width = max(self.titles.background_width, self.entities.background_width) + background['margin']*2

    def get_background_coordinates(self):
        coordinates = self.coordinates
        x0 = coordinates[0] - self.background_width/2
        x1 = x0 + self.background_width
        y0 = coordinates[1] - self.background_height/2
        y1 = y0 + self.background_height
        return x0, y0, x1, y1

    def render_background(self, canvas: ImageDraw.ImageDraw):
        if len(self.entities.entities) == 0:
            return
        coordinates = self.get_background_coordinates()
        canvas.rounded_rectangle(coordinates, radius=background['radius'], fill=self.fill)

    def render_shadow(self, image: Image.Image):
        if len(self.entities.entities) == 0:
            return
        coordinates = self.get_background_coordinates()
        margin = shadows['margin']
        x0 = round(coordinates[0] + background['shadow_offset'] - margin)
        y0 = round(coordinates[1] + background['shadow_offset'] - margin)
        width = math.ceil(self.background_width + margin*2)
        height = math.ceil(self.background_height + margin*2)
        shadow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        shadow_canvas = ImageDraw.Draw(shadow)
        shadow_canvas.rounded_rectangle((margin, margin, self.background_width + margin, self.background_height + margin),
                                        radius=background['radius'], fill=shadows['color'])
        # while shadow.getpixel((width//2, 0)) == (0, 0, 0, 0):
        #    shadow = shadow.filter(ImageFilter.BoxBlur(1))
        shadow = shadow.filter(ImageFilter.GaussianBlur(shadows['blur_factor']))
        image.alpha_composite(shadow, (x0, y0))

    def get_link(self):
        return self.titles.get_link() + self.entities.get_link()


class RoomEntities:
    def __init__(self, parent: RoomData, room):
        self.parent = parent
        self.entities = [RoomEntity(self, entity, color) for entity, color in zip(room['entities'], room['entity_colors'])]
        if len(self.entities) == 0:
            self.background_width = 0
        else:
            self.background_width = max(entity.width for entity in self.entities) + entity['margin_side']*2

    def get_background_coordinates(self):
        coordinates = self.parent.coordinates
        x0 = coordinates[0] - self.background_width/2
        x1 = x0 + self.background_width
        y0 = coordinates[1] - self.parent.background_height/2 + background['margin'] + self.parent.titles.background_height - background['top_border_space']
        y1 = y0 + entity['height']
        return x0, y0, x1, y1

    def render_shadow(self, image: Image.Image):
        coordinates = self.get_background_coordinates()
        for i, roomentity in enumerate(self.entities):
            roomentity.render_shadow(image, coordinates, i)

    def render_background(self, canvas: ImageDraw.ImageDraw):
        coordinates = self.get_background_coordinates()
        for i, roomentity in enumerate(self.entities):
            roomentity.render_background(canvas, coordinates, i)

    def render_text(self, image: Image.Image, canvas: ImageDraw.ImageDraw):
        coordinates = self.get_background_coordinates()
        for i, roomentity in enumerate(self.entities):
            roomentity.render_text(image, canvas, coordinates, i)

    def get_link(self):
        coordinates = self.get_background_coordinates()
        return [entity.get_link(coordinates, i) for i, entity in enumerate(self.entities)]


class RoomEntity:
    def __init__(self, parent: RoomEntities, text, color):
        self.parent = parent
        self.color = color
        self.parse_text(text)
        self.bbox = ENTITY_FONT.getbbox(self.text)
        self.text_width = self.bbox[2] - self.bbox[0]
        self.text_offset = sum([icon.size[0] for icon in self.icons]) + entity['icon-text_margin'] if len(self.icons) > 0 else 0
        self.width = self.text_width + self.text_offset

    def parse_text(self, text):
        data = text.split(';')
        self.text = data.pop(-1)
        self.icons = []
        for icon in data:
            self.icons.append(IMAGES[icon])

    def render_shadow(self, image: Image.Image, coordinates, i):
        margin = shadows['margin']
        x0 = round(coordinates[0] + title['shadow_offset'] - margin)
        y0 = round(coordinates[1] + title['shadow_offset'] - margin + i*(entity['height'] + entity['distance_between']))
        x1 = round(coordinates[2] + title['shadow_offset'] - margin)
        y1 = round(coordinates[3] + title['shadow_offset'] - margin + i*(entity['height'] + entity['distance_between']))
        width = math.ceil(x1 - x0 + margin*2)
        height = math.ceil(y1 - y0 + margin*2)
        shadow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        shadow_canvas = ImageDraw.Draw(shadow)
        shadow_canvas.rectangle((margin, margin, (x1 - x0) + margin, (y1 - y0) + margin), fill=shadows['color'])
        # while shadow.getpixel((width//2, 0)) == (0, 0, 0, 0):
        #    shadow = shadow.filter(ImageFilter.BoxBlur(1))
        shadow = shadow.filter(ImageFilter.GaussianBlur(shadows['blur_factor']))
        image.alpha_composite(shadow, (x0, y0))

    def render_background(self, canvas: ImageDraw.ImageDraw, coordinates, i):
        x0 = coordinates[0]
        y0 = coordinates[1] + i*(entity['height'] + entity['distance_between'])
        x1 = coordinates[2]
        y1 = coordinates[3] + i*(entity['height'] + entity['distance_between'])
        canvas.rectangle((x0, y0, x1, y1), fill=COLORS[self.color])

    def render_text(self, image: Image.Image, canvas: ImageDraw.ImageDraw, coordinates, i):
        x = coordinates[0] + entity['margin_side']
        y = coordinates[1] + i*(entity['height'] + entity['distance_between'])
        x_icon = x
        y_icon = y + entity['icon_shiftdown']
        for icon in self.icons:
            image.alpha_composite(icon, dest=(round(x_icon), round(y_icon)))
            x_icon += icon.size[0]
        x_text = x + self.text_offset
        y_text = y + entity['text_shiftdown']
        canvas.text((x_text, y_text), self.text, fill=(0, 0, 0), anchor='lt', font=ENTITY_FONT)

    def get_link(self, coordinates, i):
        x0 = coordinates[0]
        y0 = coordinates[1] + i*(entity['height'] + entity['distance_between'])
        x1 = coordinates[2]
        y1 = coordinates[3] + i*(entity['height'] + entity['distance_between'])
        return {'coordinates': [[y0, x0], [y1, x1]], 'link': self.text}


class RoomTitles:
    def __init__(self, parent: RoomData, room):
        self.parent = parent
        self.titles = [RoomTitle(title) for title in room['name'].split('\n')]
        self.background_width = title['margin_side']*2 + max([title.width for title in self.titles])
        if len(self.titles) == 1:
            self.background_height = title['height']
        else:
            self.background_height = len(self.titles)*title['font_size'] + (len(self.titles) + 1)*title['multiline_margin_vert']

    def get_background_coordinates(self):
        coordinates = self.parent.coordinates
        x0 = coordinates[0] - self.background_width/2
        x1 = x0 + self.background_width
        if self.parent.background_height != 0:
            y0 = coordinates[1] - self.parent.background_height/2 - background['top_border_space']
        else:
            y0 = coordinates[1] - self.background_height/2
        y1 = y0 + self.background_height
        return x0, y0, x1, y1

    def render_background(self, canvas: ImageDraw.ImageDraw):
        coordinates = self.get_background_coordinates()
        canvas.rectangle(coordinates, fill=self.parent.fill)

    def render_text(self, canvas: ImageDraw.ImageDraw):
        coordinates = self.parent.coordinates
        offset = title['multiline_margin_vert'] if len(self.titles) > 1 else title['margin_vert']
        x = coordinates[0]
        if self.parent.background_height != 0:
            y = coordinates[1] - self.parent.background_height/2 - background['top_border_space']
        else:
            y = coordinates[1] - self.background_height/2
        for roomtitle in self.titles:
            y += offset
            roomtitle.render_text(canvas, x, y)
            y += title['font_size']

    def render_shadow(self, image: Image.Image):
        coordinates = self.get_background_coordinates()
        margin = shadows['margin']
        x0 = round(coordinates[0] + title['shadow_offset'] - margin)
        y0 = round(coordinates[1] + title['shadow_offset'] - margin)
        width = math.ceil(self.background_width + margin*2)
        height = math.ceil(self.background_height + margin*2)
        shadow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        shadow_canvas = ImageDraw.Draw(shadow)
        shadow_canvas.rectangle((margin, margin, self.background_width + margin, self.background_height + margin), fill=shadows['color'])
        # while shadow.getpixel((width//2, 0)) == (0, 0, 0, 0):
        #    shadow = shadow.filter(ImageFilter.BoxBlur(1))
        shadow = shadow.filter(ImageFilter.GaussianBlur(shadows['blur_factor']))
        image.alpha_composite(shadow, (x0, y0))

    def get_link(self):
        coordinates = self.get_background_coordinates()
        lat_lng_bounds = [[coordinates[1], coordinates[0]], [coordinates[3], coordinates[2]]]
        return [{'coordinates': lat_lng_bounds, 'link': ' '.join([title.text for title in self.titles])}]


class RoomTitle:
    def __init__(self, text):
        self.text = text
        self.bbox = TITLE_FONT.getbbox(self.text)
        self.width = self.bbox[2] - self.bbox[0]

    def render_text(self, canvas: ImageDraw.ImageDraw, x, y):
        canvas.text((x, y), self.text, fill=(255, 255, 255), anchor='mt', font=TITLE_FONT)


def build_room(image: Image.Image, canvas: ImageDraw.ImageDraw, room):
    room_data = RoomData(room)
    room_data.render_shadow(image)
    room_data.render_background(canvas)
    room_data.entities.render_shadow(image)
    room_data.entities.render_background(canvas)
    room_data.entities.render_text(image, canvas)
    room_data.titles.render_shadow(image)
    room_data.titles.render_background(canvas)
    room_data.titles.render_text(canvas)
    return room_data.get_link()


def convert_json_pixels_to_coordinates(links):
    hopeport_portal_stone_x = math.floor(config.HOPEPORT_PORTAL_STONE_IMAGE_X/config.TILE_WIDTH)
    hopeport_portal_stone_y = math.floor(config.HOPEPORT_PORTAL_STONE_IMAGE_Y/config.TILE_WIDTH)
    border_left = config.HOPEPORT_PORTAL_STONE_COORD_X - hopeport_portal_stone_x
    border_up = config.HOPEPORT_PORTAL_STONE_COORD_Y - hopeport_portal_stone_y

    def pixel_to_coordinate(latlng, round_func):
        lat = border_up + round_func(latlng[0])/config.TILE_WIDTH
        lng = border_left + round_func(latlng[1])/config.TILE_WIDTH
        return [lat, lng]

    for link in links:
        link['coordinates'][0] = pixel_to_coordinate(link['coordinates'][0], math.floor)
        link['coordinates'][1] = pixel_to_coordinate(link['coordinates'][1], math.ceil)


def build_image(filepath, room_data):
    map = Image.open(filepath)
    image = Image.new('RGBA', map.size, (0, 0, 0, 0))
    canvas = ImageDraw.Draw(image)
    links = []
    with open(room_data, 'r') as f:
        rooms = json.load(f)
    for room in rooms:
        links.extend(build_room(image, canvas, room))
    #convert_json_pixels_to_coordinates(links)
    image.save('out/room_layer.png')
    map.alpha_composite(image)
    map.save('out/composition.png')
    with open('out/room_data.json', 'w') as f:
        json.dump(links, f)


TITLE_FONT = ImageFont.truetype(font=title['font'], size=title['font_size'])
ENTITY_FONT = ImageFont.truetype(font=entity['font'], size=entity['font_size'])

COLORS = {}
with open('map_data/icon_data.less.txt', 'r') as f:
    pattern = r"@(\w+): (#\w+);"
    matches = re.findall(pattern, f.read())
    for name, color in matches:
        COLORS[name] = ImageColor.getrgb(color)

IMAGES = {}
IMAGE_PATH = 'map_data/images/'
for filename in os.listdir(IMAGE_PATH):
    if filename.lower().endswith('.png'):
        with Image.open(os.path.join(IMAGE_PATH, filename)) as image:
            width, height = image.size
            assert height <= 64
            assert width <= 64
            resized_image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            x_offset = (64 - width)//2
            y_offset = (64 - height)//2
            resized_image.paste(image, (x_offset, y_offset))
            resized_image.thumbnail((SCALE, SCALE), Image.Resampling.LANCZOS)
            IMAGES[filename.split('.')[0]] = resized_image

if __name__ == '__main__':
    build_image(config.MAP_FILE, 'map_data/room_data.json')
