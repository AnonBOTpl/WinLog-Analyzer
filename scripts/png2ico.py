import struct, os, sys

def png_to_ico(png_path, ico_path):
    with open(png_path, "rb") as f:
        png_data = f.read()

    # PNG stores width/height at bytes 16-23
    w, h = struct.unpack(">II", png_data[16:24])

    # ICO: dimensions > 255 are stored as 0
    icow = min(w, 255)
    icoh = min(h, 255)

    header = struct.pack("<HHH", 0, 1, 1)
    dir_entry = struct.pack("<BBBBHHII", icow, icoh, 0, 0, 1, 32, len(png_data), 22)
    with open(ico_path, "wb") as f:
        f.write(header)
        f.write(dir_entry)
        f.write(png_data)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input.png> <output.ico>")
        sys.exit(1)
    png_to_ico(sys.argv[1], sys.argv[2])
    print(f"Created {sys.argv[2]}")
