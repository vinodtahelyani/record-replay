import json
import base64
from PIL import Image, ImageDraw, ImageFont
import os
from io import BytesIO

def annotate_images_from_jsonl(jsonl_file, output_dir):
    """
    Annotate images based on JSONL file and save them as PNG files.
    
    :param jsonl_file: Path to the input JSONL file containing logs.
    :param output_dir: Directory where annotated images will be saved.
    :param font_path: Path to a TrueType font file for annotations (optional).
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    with open(jsonl_file, 'r') as file:
        for i, line in enumerate(file):
            try:
                # Parse JSON line
                data = json.loads(line.strip())
                
                # Decode base64 screenshot to an image
                screenshot_data = base64.b64decode(data["screenshot"])
                image = Image.open(BytesIO(screenshot_data))
                draw = ImageDraw.Draw(image)

                # Parse bounds and draw bounding box
                bounds = data["bounds"]
                x1, y1, x2, y2 = map(int, bounds.replace("][", ",").replace("[", "").replace("]", "").split(","))
                draw.rectangle([x1, y1, x2, y2], outline="red", width=3)

                # Draw prompt text on the image
                # font = ImageFont.truetype(font_path, 20) if font_path else None
                # prompt_text = data["prompt"]
                # draw.text((10, 10), prompt_text, fill="yellow", font=font)

                # Save the annotated image as PNG
                output_path = os.path.join(output_dir, f"annotated_image_{i + 1}.png")
                image.save(output_path, "PNG")
                print(f"Saved annotated image to: {output_path}")
            except Exception as e:
                print(f"Error processing line {i + 1}: {e}")

annotate_images_from_jsonl('data-9bbbe631-48e1-43d7-be2e-7b8aaa2f65b3.jsonl', 'annotated_images')