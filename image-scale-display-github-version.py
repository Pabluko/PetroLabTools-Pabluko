import streamlit as st
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import tempfile
import zipfile
import re
from pathlib import Path
import io

# Magnification settings lookup
magnification_settings = {
    2_5: (0.001245, 200),
    10: (0.0003215, 100),
    20: (0.0001608, 50),
    40: (0.00008051, 20),
}

# Font setup
try:
    font = ImageFont.truetype("fonts/arial.ttf", 75)  # Load bundled Arial font
except OSError:
    font = ImageFont.load_default()  # fallback if font not found

# Padding parameters
padding_h = 20
padding_v = 20
line_text_gap = 10
margin = 20
line_thickness = 10

st.title("Microscope Image Scale Bar Tool - Lab Petrografía UACh")
st.write("Sube tus fotos en el microscopio con el siguiente formato de nombre (e.g., `codigo_de_muestra_40x.jpg`).")

uploaded_files = st.file_uploader("Upload microscope images", type=["jpg","jpeg","png","tif","tiff","bmp"], accept_multiple_files=True)

if st.button("Process Images") and uploaded_files:
    temp_dir = Path(tempfile.mkdtemp())
    output_dir = temp_dir / "processed"
    output_dir.mkdir(exist_ok=True)

    for uploaded_file in uploaded_files:
        #Opening with Pillow
        image = Image.open(uploaded_file).convert("RGB")
        width, height = image.size

        # Detect magnification from filename
        match = re.search(r'(\d{1,3})x', uploaded_file.name.lower())
        if not match:
            st.warning(f"{uploaded_file.name}: Magnification not found in filename.")
            continue

        mag_value = int(match.group(1))
        if mag_value not in magnification_settings:
            st.warning(f"{uploaded_file.name}: Magnification {mag_value}x not in settings.")
            continue

        mm_per_pixel, scale_length_um = magnification_settings[mag_value]
        scale_length_mm = scale_length_um / 1000.0
        scale_length_px = int(scale_length_mm / mm_per_pixel)

        # Prepare text
        text = f"{scale_length_um} µm"
        dummy_img = Image.new("RGB", (1, 1))
        draw_dummy = ImageDraw.Draw(dummy_img)
        bbox = draw_dummy.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Dynamic box size
        box_width = max(scale_length_px, text_width) + 2 * padding_h
        box_height = text_height + line_text_gap + line_thickness + 2 * padding_v

        # Box position
        x_start = width - margin - box_width
        y_start = height - margin - box_height
        x_end = width - margin
        y_end = height - margin

        # PIL for text/line
        draw = ImageDraw.Draw(image)

        #White rectangle background for the scale
        draw.rectangle([x_start, y_start, x_end, y_end], fill=(255,255,255))

        # Line
        line_x1 = x_start + (box_width - scale_length_px) // 2
        line_x2 = line_x1 + scale_length_px
        line_y = y_start + padding_v
        draw.line((line_x1, line_y, line_x2, line_y), fill=(0, 0, 0), width=line_thickness)

        # Text
        text_x = x_start + (box_width - text_width) // 2
        text_y = line_y + line_text_gap
        draw.text((text_x, text_y), text, font=font, fill=(0, 0, 0))

        # Save
        output_path = output_dir / uploaded_file.name
        image.save(output_path)

    # Create ZIP for download
    zip_path = temp_dir / "processed_images.zip"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in output_dir.iterdir():
            zipf.write(file, file.name)

    st.success("Processing complete!")
    with open(zip_path, "rb") as f:

        st.download_button("Download All Processed Images", f, file_name="processed_images.zip")
