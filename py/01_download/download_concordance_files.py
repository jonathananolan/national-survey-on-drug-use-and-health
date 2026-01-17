#!/usr/bin/env python3
"""
Download NSDUH concordance (crosswalk) Excel files from SAMHSA.
"""

from pathlib import Path
import requests

CONCORDANCE_DIR = Path("metadata/concordance")
CONCORDANCE_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "ConcatPUFComparability_2019.xlsx": (
        "https://www.samhsa.gov/data/sites/default/files/variable-crosswalk/"
        "ConcatPUFComparability_2019.xlsx"
    ),
    "PUFComparability_2024.xlsx": (
        "https://www.samhsa.gov/data/sites/default/files/2025-12/"
        "PUFComparability_2024.xlsx"
    ),
}


def download_file(filename, url):
    output_path = CONCORDANCE_DIR / filename
    if output_path.exists():
        print(f"✓ {filename}: Already downloaded")
        return

    print(f"⬇ {filename}: ", end="", flush=True)
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"✓ ({file_size_mb:.1f} MB)")


def main():
    print(f"Concordance files → {CONCORDANCE_DIR.absolute()}\n")
    for filename, url in FILES.items():
        download_file(filename, url)


if __name__ == "__main__":
    main()
