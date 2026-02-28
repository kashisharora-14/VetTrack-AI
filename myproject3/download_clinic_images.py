import requests
import os
from pathlib import Path

# Create static folder if it doesn't exist
static_dir = Path(__file__).parent / 'static' / 'uploads'
static_dir.mkdir(parents=True, exist_ok=True)

# Unsplash API - free images (no API key needed for direct URLs)
clinic_images = {
    'clinic1.jpg': 'https://images.unsplash.com/photo-1576091160550-112173e7f5b0?w=400&h=300&fit=crop',  # Dog at vet
    'clinic2.jpg': 'https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400&h=300&fit=crop',  # Vet clinic
    'clinic3.jpg': 'https://images.unsplash.com/photo-1628009368871-b37404b43869?w=400&h=300&fit=crop',  # Vet with pet
    'clinic4.jpg': 'https://images.unsplash.com/photo-1551717743-49959800b1f6?w=400&h=300&fit=crop',   # Cat at vet
}

print("Downloading clinic images from Unsplash...")

for filename, url in clinic_images.items():
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            filepath = static_dir / filename
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"✓ Downloaded {filename}")
        else:
            print(f"✗ Failed to download {filename} (Status: {response.status_code})")
    except Exception as e:
        print(f"✗ Error downloading {filename}: {str(e)}")

print(f"\nImages saved to: {static_dir}")
print("Done!")
