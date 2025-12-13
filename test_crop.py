
from PIL import Image, ImageDraw
import imagehash
import os

# Create a base image
img = Image.new('RGB', (400, 400), color='white')
d = ImageDraw.Draw(img)
d.rectangle([50, 50, 150, 150], fill='red')
d.rectangle([200, 200, 300, 300], fill='blue')
img.save('base.png')

# Create a crop (the red square)
crop = img.crop((40, 40, 160, 160))
crop.save('crop.png')

# Calculate hashes
h_base = imagehash.crop_resistant_hash(img)
h_crop = imagehash.crop_resistant_hash(crop)

print(f"Base hash type: {type(h_base)}")
print(f"Base hash string: {str(h_base)}")
print(f"Crop hash string: {str(h_crop)}")

# Test matching behavior of ImageMultiHash subtraction
# We want to know if (h1 - h2) returns the minimum distance between any segments

# Test symmetry
m1, d1 = h_base.hash_diff(h_crop)
m2, d2 = h_crop.hash_diff(h_base)
print(f"Base vs Crop: matches={m1}, dist={d1}")
print(f"Crop vs Base: matches={m2}, dist={d2}")





# Test serialization
h_str = str(h_base)
h_restored = imagehash.hex_to_multihash(h_str)
print(f"Restored segments: {len(h_restored.segment_hashes)}")
