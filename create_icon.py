from PIL import Image, ImageDraw, ImageFont
import os

# Create a new image with a transparent background
size = 256
image = Image.new('RGBA', (size, size), (255, 255, 255, 0))
draw = ImageDraw.Draw(image)

# Try to use a system font that supports emojis
try:
    # Try to find a font that supports emojis
    font = ImageFont.truetype("seguiemj.ttf", size=200)  # Windows Segoe UI Emoji font
except:
    try:
        font = ImageFont.truetype("Apple Color Emoji.ttc", size=200)  # macOS emoji font
    except:
        # Fallback to default font
        font = ImageFont.load_default()

# Draw the bear emoji in the center
emoji = "🐻"
text_width, text_height = draw.textsize(emoji, font=font) if hasattr(draw, 'textsize') else font.getsize(emoji)
position = ((size - text_width) // 2, (size - text_height) // 2)

# Draw the emoji
draw.text(position, emoji, fill=(101, 67, 33, 255), font=font)  # Brown color

# Save the image
image.save("icon.png")
print("Bear emoji icon created successfully!") 