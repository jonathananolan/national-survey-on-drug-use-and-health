#!/usr/bin/env python3
"""
Download NSDUH (National Survey on Drug Use and Health) public use files.
Downloads both Stata data files and setup files (which contain DDI metadata).
"""

import requests
from pathlib import Path

# Create data directories
DATA_DIR = Path("data")
SETUP_DIR = Path("data/setup_files")
DATA_DIR.mkdir(exist_ok=True)
SETUP_DIR.mkdir(exist_ok=True)

# Base URL pattern for NSDUH files
BASE_URL = "https://www.samhsa.gov/data/system/files/media-puf-file/"

# Years to download (1979-2024)
YEARS = list(range(1979, 2025))

def generate_data_filename_variants(year):
    """Generate possible filename variants for Stata data files."""
    prefix = "NHSDA" if year < 2002 else "NSDUH"

    variants = [
        # Try v4 first (newer releases)
        f"{prefix}-{year}-DS0001-bndl-data-stata_v4.zip",
        f"{prefix.lower()}-{year}-ds0001-bndl-data-stata_v4.zip",
        # Then v2
        f"{prefix}-{year}-DS0001-bndl-data-stata_v2.zip",
        f"{prefix.lower()}-{year}-ds0001-bndl-data-stata_v2.zip",
        # Then v1
        f"{prefix}-{year}-DS0001-bndl-data-stata_v1.zip",
        f"{prefix.lower()}-{year}-ds0001-bndl-data-stata_v1.zip",
        # Finally no version suffix
        f"{prefix}-{year}-DS0001-bndl-data-stata.zip",
        f"{prefix.lower()}-{year}-ds0001-bndl-data-stata.zip",
    ]
    return variants

def generate_setup_filename_variants(year):
    """Generate possible filename variants for setup files with DDI metadata."""
    prefix = "NHSDA" if year < 2002 else "NSDUH"

    variants = [
        # ASCII setup to Stata variants
        f"{prefix}-{year}-DS0001-bndl-data-ASCII-setup-to-stata_v4.zip",
        f"{prefix.lower()}-{year}-ds0001-bndl-data-ASCII-setup-to-stata_v4.zip",
        f"{prefix}-{year}-DS0001-bndl-data-ascii-setup-to-stata_v4.zip",
        f"{prefix.lower()}-{year}-ds0001-bndl-data-ascii-setup-to-stata_v4.zip",
        f"{prefix}-{year}-DS0001-bndl-data-ascii-setup-to-stata_v2.zip",
        f"{prefix.lower()}-{year}-ds0001-bndl-data-ascii-setup-to-stata_v2.zip",
        f"{prefix}-{year}-DS0001-bndl-data-ascii-setup-to-stata_v1.zip",
        f"{prefix.lower()}-{year}-ds0001-bndl-data-ascii-setup-to-stata_v1.zip",
        f"{prefix}-{year}-DS0001-bndl-data-ascii-setup-to-stata.zip",
        f"{prefix.lower()}-{year}-ds0001-bndl-data-ascii-setup-to-stata.zip",
        # Also try general setup variants
        f"{prefix}-{year}-DS0001-setup_v2.zip",
        f"{prefix.lower()}-{year}-ds0001-setup_v2.zip",
        f"{prefix}-{year}-DS0001-setup_v1.zip",
        f"{prefix.lower()}-{year}-ds0001-setup_v1.zip",
    ]
    return variants

def try_download_file(year, file_type='data'):
    """Try downloading a file by testing multiple filename variants.

    Args:
        year: Year to download
        file_type: 'data' for Stata files or 'setup' for setup/DDI files
    """
    if file_type == 'data':
        target_dir = DATA_DIR
        variants = generate_data_filename_variants(year)
        pattern = f"*{year}*stata.zip"
    else:  # setup
        target_dir = SETUP_DIR
        variants = generate_setup_filename_variants(year)
        pattern = f"*{year}*setup*.zip"

    # Check if we already have a file for this year
    existing_files = list(target_dir.glob(pattern))
    if existing_files:
        print(f"✓ {year} {file_type}: Already downloaded ({existing_files[0].name})")
        return True

    print(f"⬇ {year} {file_type}: ", end="", flush=True)

    # Try each filename variant
    for filename in variants:
        url = BASE_URL + filename

        try:
            # Use HEAD request first to check if file exists
            response = requests.head(url, timeout=10, allow_redirects=True)

            if response.status_code == 200:
                # File exists, now download it
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()

                output_path = target_dir / filename
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                file_size_mb = output_path.stat().st_size / (1024 * 1024)
                print(f"✓ ({file_size_mb:.1f} MB) [{filename}]")
                return True

        except requests.exceptions.RequestException:
            # Try next variant
            continue

    print(f"✗ Not found")
    return False

def main():
    print(f"Downloading NSDUH files\n")
    print(f"Data files → {DATA_DIR.absolute()}")
    print(f"Setup files → {SETUP_DIR.absolute()}\n")

    data_success = 0
    data_failed = 0
    setup_success = 0
    setup_failed = 0

    for year in YEARS:
        # Download data file
        if try_download_file(year, 'data'):
            data_success += 1
        else:
            data_failed += 1

        # Download setup file (these may not exist for all years)
        if try_download_file(year, 'setup'):
            setup_success += 1
        else:
            setup_failed += 1

    print(f"\n{'='*60}")
    print(f"Download complete!")
    print(f"Data files:  {data_success} successful, {data_failed} failed")
    print(f"Setup files: {setup_success} successful, {setup_failed} failed")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
