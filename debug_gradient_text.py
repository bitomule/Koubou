#!/usr/bin/env python3
"""Debug gradient text rendering to identify black border issue."""

from PIL import Image, ImageDraw, ImageFont
import os
import sys

# Add src to path
sys.path.insert(0, 'src')

from koubou.config import TextGradientConfig
from koubou.renderers.text_gradient import TextGradientRenderer

def test_gradient_text():
    """Test gradient text rendering in isolation."""
    
    # Create a simple canvas
    canvas = Image.new("RGB", (800, 400), (240, 240, 250))  # Light purple background
    
    # Create gradient config
    gradient_config = TextGradientConfig(
        type="linear",
        colors=["#4F46E5", "#EC4899", "#F59E0B"],  # Blue to pink to orange
        direction=45,
        stops=[0.0, 0.5, 1.0]
    )
    
    # Create text mask manually
    text_mask = Image.new("L", canvas.size, 0)  # Black background
    mask_draw = ImageDraw.Draw(text_mask)
    
    # Load a font
    try:
        font = ImageFont.truetype("Arial", 72)
    except:
        font = ImageFont.load_default()
    
    # Draw text on mask (white text = show gradient)
    text = "Test Gradient"
    mask_draw.text((50, 150), text, font=font, fill=255)
    
    # Save the mask for inspection
    text_mask.save("/tmp/debug_simple_mask.png")
    print("Saved mask to /tmp/debug_simple_mask.png")
    
    # Generate gradient
    gradient_renderer = TextGradientRenderer()
    text_bounds = (50, 150, 600, 100)  # x, y, width, height
    gradient_image = gradient_renderer.create_gradient_for_text(text_bounds, gradient_config)
    
    # Save gradient for inspection  
    gradient_image.save("/tmp/debug_gradient.png")
    print("Saved gradient to /tmp/debug_gradient.png")
    
    # Create full-canvas gradient
    canvas_gradient = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    canvas_gradient.paste(gradient_image, (50, 150))
    
    # Method 1: Using Image.composite (old way)
    transparent_bg = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gradient_text_composite = Image.composite(canvas_gradient, transparent_bg, text_mask)
    
    canvas_composite = canvas.copy().convert("RGBA")
    canvas_composite.paste(gradient_text_composite, (0, 0), gradient_text_composite)
    canvas_composite.save("/tmp/debug_composite_method.png")
    print("Saved composite method to /tmp/debug_composite_method.png")
    
    # Method 2: Using putalpha (new way)
    canvas_gradient_alpha = canvas_gradient.copy()
    canvas_gradient_alpha.putalpha(text_mask)
    
    canvas_alpha = canvas.copy().convert("RGBA")
    canvas_alpha.paste(canvas_gradient_alpha, (0, 0), canvas_gradient_alpha)
    canvas_alpha.save("/tmp/debug_alpha_method.png")
    print("Saved alpha method to /tmp/debug_alpha_method.png")
    
    # Method 3: Using high-resolution approach
    scale_factor = 4
    hr_canvas = Image.new("RGB", (canvas.width * scale_factor, canvas.height * scale_factor), (240, 240, 250))
    hr_mask = Image.new("L", hr_canvas.size, 0)
    hr_draw = ImageDraw.Draw(hr_mask)
    
    try:
        hr_font = ImageFont.truetype("Arial", 72 * scale_factor)
    except:
        hr_font = ImageFont.load_default()
    
    hr_draw.text((50 * scale_factor, 150 * scale_factor), text, font=hr_font, fill=255)
    
    # Downsample mask
    downsampled_mask = hr_mask.resize(canvas.size, Image.Resampling.LANCZOS)
    downsampled_mask.save("/tmp/debug_hr_mask.png")
    print("Saved high-res downsampled mask to /tmp/debug_hr_mask.png")
    
    # Apply to gradient
    canvas_gradient_hr = canvas_gradient.copy()
    canvas_gradient_hr.putalpha(downsampled_mask)
    
    canvas_hr = canvas.copy().convert("RGBA")
    canvas_hr.paste(canvas_gradient_hr, (0, 0), canvas_gradient_hr)
    canvas_hr.save("/tmp/debug_hr_method.png")
    print("Saved high-res method to /tmp/debug_hr_method.png")

if __name__ == "__main__":
    test_gradient_text()