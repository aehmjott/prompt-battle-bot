from PIL import Image, ImageDraw, ImageFont
import textwrap
from math import sqrt

def add_text(image, text, text_height=100, text_padding=5, footer=False):
    width, height = image.size
    
    image_with_text = Image.new("RGB", (width, height + text_height), color="white")
    if not footer:
        image_with_text.paste(image, (0, text_height))
    else:
        image_with_text.paste(image, (0, 0))
    
    characters_per_line = int(sqrt(width)) * 2
    wrapped_text = "\n".join(textwrap.wrap(text, width=characters_per_line, break_long_words=False))
    
    draw = ImageDraw.Draw(image_with_text)
    font_size = 100
    while font_size > 0:
        font = ImageFont.truetype(r"C:\Windows\Fonts\Comic.ttf", font_size)
        size = draw.multiline_textbbox((text_padding, text_padding), wrapped_text, font, align="center")
        if size[2] < (width - 2 * text_padding) and size[3] < text_height - 2 * text_padding:
            break
        font_size -= 1
        
    text_x = (width - size[2]) / 2
    text_y = (text_height - size[3]) / 2
    
    if footer:
        text_y += height
        
    draw.multiline_text((text_x, text_y), wrapped_text, "#000", font, align="center")
    return image_with_text
    
    
def combine_images(images, gap=5, cols=2):
    rows = min((len(images) + 1) // cols, len(images))
    
    size = images[0].size

    collage_width = size[0] * cols + (cols - 1) * gap
    collage_height = size[1] * rows + (rows - 1) * gap
    collage = Image.new("RGB", (collage_width, collage_height), color="white")
    
    for r in range(rows):
        for c in range(cols):
            if not len(images):
                continue
            img = images.pop()
            img.resize(size)
            collage.paste(img, (c * (size[0] + gap), r * (size[1] + gap)))

    return collage
    
    
def get_image_from_grid(image, col, row, width, height, gap=5):
    left = col * (width + gap)
    top = row * (height + gap)
    right = left + width
    bottom = top + height
    
    return image.crop((left, top, right, bottom))
    
    
def create_collage (images, text):
    images_with_text = []
    for image, image_text in images:
        image_with_heading = add_text(image, image_text, footer=True)
        images_with_text.append(image_with_heading)
    
    collage = combine_images(images_with_text, cols=len(images_with_text))
    collage = add_text(collage, text, text_padding=10)
    return collage
    
