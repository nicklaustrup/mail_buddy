"""
Create a simple bear icon for the Mail Buddy application.
This script creates a text-based bear icon and saves it to icon.txt.
"""

# Simple ASCII bear icon
bear_icon = """
   ʕ•ᴥ•ʔ
MAIL BUDDY
"""

# Save to file
with open('icon.txt', 'w') as f:
    f.write(bear_icon)

print("Bear icon created successfully!")
print("To use this icon, you'll need to convert it to a PNG file.")
print("For now, we'll use a placeholder icon in the application.") 