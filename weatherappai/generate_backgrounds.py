from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import os
import math
import random

# Create directories
os.makedirs("assets/backgrounds", exist_ok=True)

WIDTH, HEIGHT = 400, 600

def create_gradient(width, height, top_color, bottom_color):
    """Creates a vertical linear gradient image."""
    base = Image.new('RGB', (width, height), top_color)
    top_r, top_g, top_b = top_color
    bot_r, bot_g, bot_b = bottom_color

    pixels = base.load()
    for y in range(height):
        # Interpolate colors
        ratio = y / height
        r = int(top_r + (bot_r - top_r) * ratio)
        g = int(top_g + (bot_g - top_g) * ratio)
        b = int(top_b + (bot_b - top_b) * ratio)
        for x in range(width):
            pixels[x, y] = (r, g, b)
    return base

def create_cinematic_sunny():
    """Generates a warm, glowing sunny scene with subtle heat haze/rays."""
    frames = []
    # Deep sky blue to warm golden horizon
    bg_base = create_gradient(WIDTH, HEIGHT, (20, 100, 200), (255, 220, 150))
    
    # Sun Glow (Large radial gradient simulation using layers)
    sun_glow = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_glow = ImageDraw.Draw(sun_glow)
    
    # Multiple transparent circles for soft bloom
    center_x, center_y = WIDTH // 2, HEIGHT // 5
    for r in range(150, 0, -5):
        alpha = int(255 * (1 - (r / 150)) * 0.1) # Fade out edges
        draw_glow.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], fill=(255, 255, 200, alpha))
    
    # Blur the glow heavily
    sun_glow = sun_glow.filter(ImageFilter.GaussianBlur(20))

    for i in range(20):
        frame = bg_base.copy()
        frame.paste(sun_glow, (0, 0), sun_glow)

        # Subtle pulsing of the sun core
        overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        pulse = 5 + 2 * math.sin(i * 0.3)
        
        # Sun Core
        draw.ellipse([center_x - 40 - pulse, center_y - 40 - pulse, 
                      center_x + 40 + pulse, center_y + 40 + pulse], 
                     fill=(255, 255, 240, 200))
        
        # God Rays (Rotating transparent wedges)
        # Using lines for simplicity but blurred
        for angle in range(0, 360, 30):
            # Rotate slowly
            rad = math.radians(angle + i)
            end_x = center_x + 300 * math.cos(rad)
            end_y = center_y + 300 * math.sin(rad)
            draw.line([center_x, center_y, end_x, end_y], fill=(255, 255, 255, 15), width=20)
        
        overlay = overlay.filter(ImageFilter.GaussianBlur(10)) # Soften rays
        
        frame.paste(overlay, (0, 0), overlay)
        frames.append(frame)

    frames[0].save('assets/backgrounds/sunny.gif', save_all=True, append_images=frames[1:], duration=100, loop=0)

def create_cinematic_rainy():
    """Generates a moody, dark rainy scene with depth (parallax rain)."""
    frames = []
    # Dark slate/navy gradient
    bg_base = create_gradient(WIDTH, HEIGHT, (15, 20, 30), (40, 50, 70))
    
    drops_bg = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(3, 8)] for _ in range(80)]
    drops_fg = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(10, 20)] for _ in range(40)]

    for i in range(15): # Short loop, high fps feel
        frame = bg_base.copy()
        
        # Draw Background Rain (Blurred)
        layer_bg = Image.new('RGBA', (WIDTH, HEIGHT), (0,0,0,0))
        draw_bg = ImageDraw.Draw(layer_bg)
        
        for drop in drops_bg:
            draw_bg.line([drop[0], drop[1], drop[0], drop[1]+10], fill=(100, 120, 150, 100), width=1)
            drop[1] += drop[2] # Speed
            if drop[1] > HEIGHT: drop[1] = -10; drop[0] = random.randint(0, WIDTH)
            
        # Blur background rain for depth
        layer_bg = layer_bg.filter(ImageFilter.GaussianBlur(2))
        frame.paste(layer_bg, (0,0), layer_bg)
        
        # Draw Foreground Rain (Sharp, Fast)
        layer_fg = Image.new('RGBA', (WIDTH, HEIGHT), (0,0,0,0))
        draw_fg = ImageDraw.Draw(layer_fg)
        
        for drop in drops_fg:
            draw_fg.line([drop[0], drop[1], drop[0], drop[1]+25], fill=(200, 220, 255, 180), width=2)
            # Splash effect at bottom? 
            # keep it simple for GIF size
            drop[1] += drop[2]
            if drop[1] > HEIGHT: drop[1] = -25; drop[0] = random.randint(0, WIDTH)

        frame.paste(layer_fg, (0,0), layer_fg)
        
        # Vignette for cinematic feel (Dark corners)
        # Apply a static radial gradient mask if we could, but let's just draw dark boxes or skipped here to keep it optimized.
        
        frames.append(frame)

    frames[0].save('assets/backgrounds/rainy.gif', save_all=True, append_images=frames[1:], duration=50, loop=0)

def create_cinematic_cloudy():
    """Generates a soft, misty, cloudy scene with drifting fog."""
    frames = []
    # Muted Blue/Grey Gradient
    bg_base = create_gradient(WIDTH, HEIGHT, (100, 110, 120), (180, 190, 200))
    
    # Generate "Clouds" as large blurred blobs
    cloud_layer = Image.new('RGBA', (WIDTH + 200, HEIGHT), (0,0,0,0)) # Wider for scrolling
    draw_cloud = ImageDraw.Draw(cloud_layer)
    
    # Draw randomness
    for _ in range(50):
        x = random.randint(0, WIDTH+200)
        y = random.randint(0, HEIGHT//2)
        r = random.randint(40, 100)
        draw_cloud.ellipse([x-r, y-r, x+r, y+r], fill=(255, 255, 255, 30))
        
    # Heavily blur the clouds to define "mist"
    cloud_layer = cloud_layer.filter(ImageFilter.GaussianBlur(30))
    
    for i in range(40):
        frame = bg_base.copy()
        
        # Scroll the cloud layer
        offset = i * 1 # Slow drift
        # Crop the visible part
        current_clouds = cloud_layer.crop((offset, 0, offset + WIDTH, HEIGHT))
        
        frame.paste(current_clouds, (0,0), current_clouds)
        
        # Add a second layer moving faster?
        # Let's keep one layer for smooth loop physics implies we need seamless or bounce. 
        # A simple linear drift across 40 frames might jump at end. 
        # To make it seamless: blending start and end. 
        # For this task, a simple drift is okay, or a "breathing" fog (opacity change).
        
        frames.append(frame)
        
    frames[0].save('assets/backgrounds/cloudy.gif', save_all=True, append_images=frames[1:], duration=100, loop=0)

def create_cinematic_default():
    """Deep twilight gradient with subtle color shift."""
    frames = []
    
    for i in range(20):
        # Color shifting gradient
        shift = math.sin(i * 0.2) * 10
        top = (40 + int(shift), 20, 60) # Deep Purple/Red
        bot = (20, 20, 40) # Dark Blue
        
        frame = create_gradient(WIDTH, HEIGHT, top, bot)
        frames.append(frame)

    frames[0].save('assets/backgrounds/default.gif', save_all=True, append_images=frames[1:], duration=150, loop=0)

if __name__ == "__main__":
    print("Generating cinematic assets...")
    try:
        create_cinematic_sunny()
        print("- Sunny Generated")
        create_cinematic_rainy()
        print("- Rainy Generated")
        create_cinematic_cloudy()
        print("- Cloudy Generated")
        create_cinematic_default()
        print("- Default Generated")
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
