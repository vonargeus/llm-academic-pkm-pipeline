import os
from PIL import Image

def main():
    image_path = r"C:\Users\jubam\Downloads\ChatGPT Image Jul 2, 2026, 01_48_23 PM.png"
    pdf_path = r"C:\Users\jubam\Downloads\thesis_poster.pdf"
    
    if not os.path.exists(image_path):
        print(f"Error: Source image not found at {image_path}")
        return
        
    print(f"Opening image: {image_path}...")
    image = Image.open(image_path)
    
    # Standard A2 dimensions at 300 DPI:
    # 420mm (16.535 inches) -> 4960 pixels
    # 594mm (23.386 inches) -> 7016 pixels
    target_width = 4960
    target_height = 7016
    
    print(f"Original size: {image.size[0]}x{image.size[1]} pixels")
    print(f"Resizing to exact A2 format at 300 DPI: {target_width}x{target_height} pixels (using Lanczos filter)...")
    
    # Use Lanczos filter for high-quality downsampling/upsampling of text and tables
    resized_image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    # Convert RGBA to RGB for PDF export compatibility
    print("Converting to RGB color space...")
    rgb_image = resized_image.convert('RGB')
    
    # Save as PDF with explicit 300 DPI metadata to enforce physical A2 page dimensions
    print(f"Saving A2 print-ready PDF to: {pdf_path}...")
    rgb_image.save(pdf_path, "PDF", resolution=300.0, quality=100)
    print("A2 PDF conversion completed successfully!")

if __name__ == '__main__':
    main()
