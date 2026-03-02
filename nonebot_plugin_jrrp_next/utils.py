import pathlib
import random
import time
from io import BytesIO
from typing import Tuple, Union

from httpx import AsyncClient, ConnectError, Response
from PIL import Image, ImageDraw, ImageFile, ImageFont

ImageFile.LOAD_TRUNCATED_IMAGES = True


def average(Itr):
    return sum(Itr) / len(Itr)


rand = random.Random()


def get_average_color(image: Image.Image) -> Tuple[int, int, int, int]:
    pix = image.load()
    R_list = []
    G_list = []
    B_list = []
    width, height = image.size
    for x in range(int(width)):
        for y in range(height):
            R_list.append(pix[x, y][0])  # type: ignore
            G_list.append(pix[x, y][1])  # type: ignore
            B_list.append(pix[x, y][2])  # type: ignore
    R_average = int(average(R_list))
    G_average = int(average(G_list))
    B_average = int(average(B_list))
    return R_average, G_average, B_average, 255


def get_jrrp(string: str):
    now = time.localtime()
    seed = f"h&%tkH+cck>#+{string}+t/sHz2t^6nr+{now.tm_year}+Ba`;05gz4x@5+{now.tm_mday}+2NB>9|0A^gz:+{now.tm_mon}+UtH4vfhh^)q^"
    rand.seed(seed)
    return rand.randint(0, 100)


async def open_img(image_path: str, is_url: bool = True) -> Image.Image:
    if is_url:
        for i in range(3):
            origin_data: Response | None = None
            try:
                origin_data = await AsyncClient().get(image_path, follow_redirects=True)
                return Image.open(BytesIO(origin_data.content)).convert("RGBA")
            except Exception as e:
                print(f"Warn: {e}, {type(e)}")
                if origin_data:
                    print(
                        f"origin_data: {origin_data}, {origin_data.content}, {origin_data.headers}, {origin_data.url}"
                    )
        raise Exception
    with open(image_path, "rb") as f:
        return Image.open(f).convert("RGBA")


class DataText:
    def __init__(
        self, left: float, top: float, size: int, text, path, anchor: str = "lt"
    ) -> None:
        self.left = left
        self.top = top
        self.text = str(text)
        self.path = path
        self.font = ImageFont.truetype(str(self.path), size)
        self.anchor = anchor


def write_text(
    image: Image.Image,
    font: ImageFont.ImageFont | ImageFont.FreeTypeFont | ImageFont.TransposedFont,
    text: str = "sample_text",
    pos: tuple[float, float] = (0, 0),
    color: tuple[int, int, int, int] = (255, 255, 255, 255),
    anchor: str = "lt",
    stroke_width: int = 0,
    stroke_fill: Union[str, tuple[int, int, int]] = "Black",
) -> Image.Image:
    rgba_image = image
    text_overlay = Image.new("RGBA", rgba_image.size, (255, 255, 255, 0))
    image_draw = ImageDraw.Draw(text_overlay)
    image_draw.text(
        pos,
        text,
        font=font,
        fill=color,
        anchor=anchor,
        stroke_width=stroke_width,
        stroke_fill=stroke_fill,
    )
    return Image.alpha_composite(rgba_image, text_overlay)


def draw_text(
    image: Image.Image,
    class_text: DataText,
    color: Tuple[int, int, int, int] = (255, 255, 255, 255),
    stroke_width: int = 0,
    stroke_fill: Union[str, tuple[int, int, int]] = "Black",
) -> Image.Image:
    font = class_text.font
    text = class_text.text
    anchor = class_text.anchor
    color = color
    return write_text(
        image,
        font,
        text,
        (class_text.left, class_text.top),
        color,
        anchor,
        stroke_width=stroke_width,
        stroke_fill=stroke_fill,
    )


def drawer_draw_shadowed_text(
    draw: ImageDraw.ImageDraw,
    pos: Tuple[float, float],
    text: str,
    font: pathlib.Path | str,
    font_size: float,
    shadow_size: float,
    color: Tuple[int, int, int, int],
    shadow_color: Tuple[int, int, int, int],
    anchor: str,
):
    draw.text(
        (pos[0] + shadow_size, pos[1] + shadow_size),
        text,
        font=ImageFont.truetype(font, font_size),
        fill=shadow_color,
        anchor=anchor,
        stroke_width=int(shadow_size),
        stroke_fill=shadow_color,
    )
    draw.text(
        pos,
        text,
        font=ImageFont.truetype(font, font_size),
        fill=color,
        anchor=anchor,
    )


def avatar_handler(image: Image.Image) -> Image.Image:
    scale = 3
    w, h = image.size
    r = w * scale
    alpha_layer = Image.new("L", (r, r), 0)
    draw = ImageDraw.Draw(alpha_layer)
    draw.ellipse((0, 0, r, r), fill=255)
    alpha_layer = alpha_layer.resize((w, w), Image.Resampling.LANCZOS)
    image.putalpha(alpha_layer)
    return image
