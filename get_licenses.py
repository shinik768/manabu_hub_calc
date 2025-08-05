import os
import json

input_file = "licenses.json"
output_dir = "individual_licenses"
os.makedirs(output_dir, exist_ok=True)

with open(input_file, "r", encoding="utf-8") as f:
    licenses = json.load(f)

for entry in licenses:
    name = entry["Name"]
    license_text = entry.get("LicenseText", "").strip()
    if license_text:
        # ライブラリ名をファイル名として安全に変換
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '.', '_')).rstrip()
        file_path = os.path.join(output_dir, f"{safe_name}_LICENSE.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(license_text)
