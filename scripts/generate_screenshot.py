#!/usr/bin/env python3
import sys
import os
from PIL import Image, ImageDraw, ImageFont

def render_terminal(output_text, output_image_path):
    os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
    
    font_path = "/System/Library/Fonts/Menlo.ttc"
    font_size = 14
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        font = ImageFont.load_default()

    lines = output_text.strip().split("\n")
    
    line_height = 20
    padding_x = 25
    title_bar_height = 36
    padding_bottom = 25
    
    max_line_len = max(len(l) for l in lines) if lines else 80
    img_width = max(1000, max_line_len * 9 + padding_x * 2)
    img_height = title_bar_height + len(lines) * line_height + padding_bottom

    # Background
    bg_color = (24, 24, 32)
    img = Image.new("RGBA", (img_width, img_height), bg_color)
    draw = ImageDraw.Draw(img)

    # Title Bar
    title_bar_color = (32, 33, 44)
    draw.rectangle([(0, 0), (img_width, title_bar_height)], fill=title_bar_color)

    # Window buttons
    button_radius = 6
    btn_y = 18
    # Close (Red)
    draw.ellipse([(20 - button_radius, btn_y - button_radius), (20 + button_radius, btn_y + button_radius)], fill=(255, 95, 86))
    # Minimize (Yellow)
    draw.ellipse([(40 - button_radius, btn_y - button_radius), (40 + button_radius, btn_y + button_radius)], fill=(255, 189, 46))
    # Maximize (Green)
    draw.ellipse([(60 - button_radius, btn_y - button_radius), (60 + button_radius, btn_y + button_radius)], fill=(39, 201, 63))

    # Title text
    title_text = "sourabh@mac: ~/flask-mongodb-app (minikube) — kubectl get hpa,pods -w"
    draw.text((img_width // 2 - 200, 10), title_text, fill=(160, 160, 175), font=font)

    # Render terminal lines with syntax coloring
    curr_y = title_bar_height + 15
    for line in lines:
        if line.startswith("$") or line.startswith(">>>"):
            color = (80, 220, 120)  # Light Green for commands / headers
        elif "cpu:" in line or "TARGETS" in line:
            color = (255, 215, 0)   # Yellow/Gold for HPA metrics
        elif "Running" in line:
            color = (130, 200, 255) # Light Blue for running pods
        elif "===" in line or "---" in line:
            color = (180, 140, 255) # Purple for separators
        elif "Complete" in line or "Requests" in line:
            color = (100, 240, 180) # Mint for stats
        else:
            color = (220, 225, 235) # Light grayish white
            
        draw.text((padding_x, curr_y), line, fill=color, font=font)
        curr_y += line_height

    img.save(output_image_path, "PNG")
    print(f"Screenshot successfully created at: {output_image_path}")

if __name__ == "__main__":
    log_file = sys.argv[1] if len(sys.argv) > 1 else "/tmp/hpa_test.log"
    out_file = sys.argv[2] if len(sys.argv) > 2 else "/Users/sourabh/Desktop/Projects/Flask App/flask-mongodb-app/screenshots/autoscaling_results.png"
    
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            content = f.read()
    else:
        content = "No log found"
        
    render_terminal(content, out_file)

