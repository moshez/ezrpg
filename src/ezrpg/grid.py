from __future__ import annotations
import math
import dataclasses

from PIL import Image, ImageDraw

HEXAGON_ANGLE = math.tau * (30 / 360)

@dataclasses.dataclass(frozen=True)
class Point:
    x: float
    y: float
    
    def dx(self, diff):
        return Point(self.x + diff, self.y)
    def dy(self, diff):
        return Point(self.x, self.y + diff)
    
    def coords(self):
        return self.x, self.y
    

@dataclasses.dataclass(frozen=True)
class HexParams:
    side: float
    
    @property
    def height(self):
        return math.sin(HEXAGON_ANGLE) * self.side
    
    @property
    def radius(self):
        return math.sin(HEXAGON_ANGLE) * self.side

    @property
    def rect_height(self):
        return self.side + 2 * self.height
    
    @property
    def rect_width(self):
        return 2 * self.radius

def hexagon_points(center: Point, side: float):
    params = HexParams(side)
    yield center.dy(params.radius)
    yield center.dy(params.rect_width).dx(params.height)
    yield center.dy(params.rect_width).dx(params.height + params.side)
    yield center.dy(params.radius).dx(params.rect_height)
    yield center.dx(params.side + params.height)
    yield center.dx(params.height)

def hex_center_from_grid(pt, side):
    params = HexParams(side)
    radius = params.radius
    return Point(3 * pt.x * radius, (2 * pt.y + pt.x%2) * radius)

def hex_coords(here, side):
    center = hex_center_from_grid(here, side)
    return [pt.coords() for pt in hexagon_points(center, side)]
    

def square_coords(here, size):
    return [(side * (here.x + x), side * (here.y + y))
                       for (x, y) in [(0, 0), (0, 1), (1, 1), (1, 0)]]

    
def grid(size, color_by_point, coords_by_point):
    side = 20
    physical_size = side * size * 3
    im = Image.new("RGB", (600, 600), (255,255,255))
    draw = ImageDraw.Draw(im)

    for i in range(1, size+1):
        for j in range(1, size+1):
            here = Point(i, j)
            fill = color_by_point(here)
            coords = coords_by_point(here, side)
            draw.polygon(coords, width=2, outline=(0,0,0), fill=fill)
    return im
