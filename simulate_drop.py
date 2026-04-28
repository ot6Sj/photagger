import time
import os

dummy_file = "Drop_Zone/test_photo.raw"

print("Starting to write file...")
with open(dummy_file, "wb") as f:
    for i in range(5):
        f.write(os.urandom(1024 * 1024))  # Write 1MB chunk
        f.flush()
        print(f"Wrote chunk {i+1}/5")
        time.sleep(1) # wait 1 second between chunks to simulate slow copy

print("Finished writing file.")
