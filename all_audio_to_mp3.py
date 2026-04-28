import pandas as pd
import os
import subprocess
from pathlib import Path

# Load your Rekordbox export CSV
df = pd.read_csv("smp.csv", encoding="utf-16", sep="\t")

# Clean up column names
df.columns = [col.strip() for col in df.columns]

# Define audio formats to convert (anything that's not already MP3)
non_mp3_formats = (".flac", ".aif", ".aiff", ".wav", ".m4a", ".ogg", ".opus", ".wma", ".alac")

# Create single output folder
output_dir = Path("smp_converted")
output_dir.mkdir(exist_ok=True)

# Track stats
converted = 0
already_mp3 = 0
not_found = 0
errors = 0

for _, row in df.iterrows():
    file_path = row.get("Location")
    if pd.isna(file_path):
        continue

    src = Path(str(file_path).strip())
    suffix = src.suffix.lower()

    # Skip non-audio or unsupported files
    if not suffix:
        continue

    if suffix == ".mp3":
        # Already MP3 — copy to output folder as-is
        dst = output_dir / src.name
        if not src.exists():
            print(f"⚠️  File not found: {src}")
            not_found += 1
            continue
        # Avoid overwriting if duplicate filename
        if dst.exists():
            dst = output_dir / (src.stem + "_dupe.mp3")
        import shutil
        shutil.copy2(src, dst)
        print(f"📋 Copied MP3:   {src.name}")
        already_mp3 += 1

    elif suffix in non_mp3_formats:
        dst = output_dir / (src.stem + ".mp3")
        if not src.exists():
            print(f"⚠️  File not found: {src}")
            not_found += 1
            continue
        # Handle duplicate filenames
        if dst.exists():
            dst = output_dir / (src.stem + "_dupe.mp3")
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(src),
            "-ab", "320k",
            "-map_metadata", "0",   # preserve metadata/tags
            str(dst)
        ]
        try:
            result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            if result.returncode == 0:
                print(f"✅ Converted:    {src.name} → {dst.name}")
                converted += 1
            else:
                print(f"❌ FFmpeg error: {src.name}")
                print(result.stderr.decode()[-300:])  # last 300 chars of error
                errors += 1
        except Exception as e:
            print(f"❌ Error: {src}: {e}")
            errors += 1
    else:
        print(f"⏭️  Skipped (unknown format): {src.name}")

print(f"""
🎧 Done!
   ✅ Converted:    {converted}
   📋 Copied MP3s:  {already_mp3}
   ⚠️  Not found:   {not_found}
   ❌ Errors:       {errors}
   📁 Output folder: {output_dir.resolve()}
""")
