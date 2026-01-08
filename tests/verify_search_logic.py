from PIL import Image
import imagehash
import numpy as np

# Mock implementation to verify logic
HASH_SIZE = 16
MAX_HASH_DIST = 256

def test_hash_logic():
    print(f"Testing Hash Logic with HASH_SIZE={HASH_SIZE}")
    
    # Create a random image
    img1 = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
    img2 = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
    
    h1 = imagehash.whash(img1, hash_size=HASH_SIZE)
    h2 = imagehash.whash(img2, hash_size=HASH_SIZE)
    
    print(f"Hash 1: {h1}")
    print(f"Hash 2: {h2}")
    print(f"Hash Length (bits): {len(h1.hash) ** 2}") # imagehash stores as boolean array
    
    dist = h1 - h2
    print(f"Distance: {dist}")
    
    # Calculate percentage
    percentage = max(0, 1.0 - (dist / MAX_HASH_DIST)) * 100
    print(f"Match Percentage: {percentage:.2f}%")
    
    assert 0 <= dist <= MAX_HASH_DIST
    assert 0 <= percentage <= 100
    
    # Test identical
    dist_same = h1 - h1
    percentage_same = max(0, 1.0 - (dist_same / MAX_HASH_DIST)) * 100
    print(f"Identical Distance: {dist_same}")
    print(f"Identical Percentage: {percentage_same:.2f}%")
    assert dist_same == 0
    assert percentage_same == 100.0

if __name__ == "__main__":
    try:
        test_hash_logic()
        print("Verification Successful")
    except Exception as e:
        print(f"Verification Failed: {e}")
