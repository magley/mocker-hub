import base64
import os
import random
from PIL import Image, ImageDraw, ImageFont
import hashlib
import base64
from io import BytesIO


def save_image(inline_image_base64: str, filename_without_path_or_extension: str) -> str:
    header, encoded = inline_image_base64.split(",", 1)
    file_format = header.split("/")[1].split(";")[0]

    image_bytes = base64.b64decode(encoded)

    filename = f"{filename_without_path_or_extension}.{file_format}"
    filepath = f"./images/{filename}"

    if os.getenv('mocker_hub_TEST_ENV') is None:
        with open(filepath, "wb") as f:
            f.write(image_bytes)

    return filepath


def generate_inline_image(text: str, size: int=128, block_size=16) -> str:
    image = Image.new('RGB', (size, size), 'white')
    draw = ImageDraw.Draw(image)

    hash_object = hashlib.md5(text.encode())
    hash_hex = hash_object.hexdigest()
    color = '#' + hash_hex[:6]
    num_blocks = size // block_size
    for y in range(num_blocks):
        for x in range(num_blocks // 2):
            if int(hash_hex[(x + y * num_blocks) % len(hash_hex)], 16) % 2 == 0:
                draw.rectangle(
                    [x * block_size, y * block_size, (x + 1) * block_size, (y + 1) * block_size],
                    fill=color
                )
                draw.rectangle(
                    [(num_blocks - x - 1) * block_size, y * block_size, (num_blocks - x) * block_size, (y + 1) * block_size],
                    fill=color
                )
                
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"