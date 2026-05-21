import zipfile
import os

zip_path = "trainingData/archive(5)New.zip"  # path to your zip
output_dir = "trainingData/NewDataset1_5"     # where to extract

MAX_PATH = 200  # adjust if needed

with zipfile.ZipFile(zip_path, 'r') as z:
    for member in z.infolist():
        # Split into directory and filename
        dir_part = os.path.dirname(member.filename)
        file_part = os.path.basename(member.filename)

        # Shorten filename if the full path would be too long
        full_out = os.path.join(output_dir, dir_part, file_part)
        if len(full_out) > MAX_PATH:
            ext = os.path.splitext(file_part)[1]
            file_part = file_part[:10] + ext  # shorten to 10 chars + extension

        out_path = os.path.join(output_dir, dir_part, file_part)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        with z.open(member) as src, open(out_path, 'wb') as dst:
            dst.write(src.read())

print("Done!")