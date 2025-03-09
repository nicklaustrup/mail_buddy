"""
Create a simple placeholder icon for the Mail Buddy application.
This script creates a colored square with the text "MB" as a placeholder icon.
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    
    # Create a new image with a blue background
    size = 64
    image = Image.new('RGB', (size, size), (0, 120, 212))  # Blue color
    draw = ImageDraw.Draw(image)
    
    # Try to use a system font
    try:
        font = ImageFont.truetype("arial.ttf", size=30)
    except Exception:
        font = ImageFont.load_default()
    
    # Draw "MB" text in the center
    text = "MB"
    
    # Get text size - handle different PIL versions
    try:
        # For newer PIL versions
        left, top, right, bottom = font.getbbox(text)
        text_width = right - left
        text_height = bottom - top
    except AttributeError:
        try:
            # For older PIL versions
            text_width, text_height = draw.textsize(text, font=font)
        except AttributeError:
            # Fallback
            text_width, text_height = 30, 30
    
    position = ((size - text_width) // 2, (size - text_height) // 2)
    
    # Draw the text
    draw.text(position, text, fill=(255, 255, 255), font=font)  # White text
    
    # Save the image
    image.save("icon.png")
    print("Icon created successfully!")
    
except ImportError:
    print("PIL library not found. Creating a text file instead.")
    with open('icon.txt', 'w') as f:
        f.write("MB")
    print("Created icon.txt as a placeholder.") 