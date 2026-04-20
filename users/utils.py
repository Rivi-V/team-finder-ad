import io
import random
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont


def generate_avatar_file(letter: str):
    size = 256
    palette = [
        '#8AAAE5', '#7FC8A9', '#9C89B8', '#A1C181', '#84A59D', '#B8B8FF',
        '#8E9AAF', '#90BE6D', '#A3B18A', '#A68A64'
    ]
    background = random.choice(palette)
    image = Image.new('RGB', (size, size), background)
    draw = ImageDraw.Draw(image)

    font = None
    possible_fonts = [
        Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
        Path('/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf'),
    ]
    for font_path in possible_fonts:
        if font_path.exists():
            font = ImageFont.truetype(str(font_path), size=128)
            break
    if font is None:
        font = ImageFont.load_default()

    letter = (letter or '?')[0].upper()
    bbox = draw.textbbox((0, 0), letter, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) / 2
    y = (size - text_height) / 2 - 10
    draw.text((x, y), letter, fill='white', font=font)

    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return ContentFile(buffer.getvalue(), name=f'avatar_{random.randint(100000, 999999)}.png')
