#!/usr/bin/env python3
"""
Extract DDI (Data Documentation Initiative) metadata from setup files.
DDI files contain detailed question text and documentation.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import zipfile
import tempfile

def extract_ddi_metadata(year):
    """Extract question text from DDI XML files.

    Args:
        year: Year to extract metadata for

    Returns:
        Dictionary mapping variable_name -> question_text
        Returns empty dict if no DDI file found
    """
    setup_dir = Path("data/setup_files")
    setup_files = list(setup_dir.glob(f"*{year}*.zip"))

    if not setup_files:
        return {}

    setup_zip = setup_files[0]
    variable_questions = {}

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(setup_zip, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)

            # Find DDI XML files (usually named *DS0001*.xml or *codebook*.xml)
            xml_files = list(Path(tmpdir).rglob("*.xml"))

            # Filter to likely DDI files (containing DS0001 or being the longest filename)
            ddi_files = [f for f in xml_files if 'DS0001' in f.name.upper()]
            if not ddi_files and xml_files:
                # Use longest filename as heuristic
                ddi_files = [max(xml_files, key=lambda f: len(f.name))]

            if not ddi_files:
                return {}

            ddi_file = ddi_files[0]

            # Parse DDI XML
            tree = ET.parse(ddi_file)
            root = tree.getroot()

            # DDI namespace handling
            ns = {}
            if root.tag.startswith('{'):
                ns_url = root.tag.split('}')[0].strip('{')
                ns = {'ddi': ns_url}

            # Extract variable information
            # DDI structure: dataDscr/var elements contain variable info
            for var in root.findall('.//ddi:var', ns) if ns else root.findall('.//var'):
                var_name = var.get('name', '').upper()

                # Get question text from qstn/qstnLit or labl elements
                question_text = ''

                # Try qstn/qstnLit first (most detailed)
                qstn = var.find('.//ddi:qstn/ddi:qstnLit', ns) if ns else var.find('.//qstn/qstnLit')
                if qstn is not None and qstn.text:
                    question_text = qstn.text.strip()
                else:
                    # Try labl as fallback
                    labl = var.find('.//ddi:labl', ns) if ns else var.find('.//labl')
                    if labl is not None and labl.text:
                        question_text = labl.text.strip()

                if var_name and question_text:
                    variable_questions[var_name] = question_text

            print(f"✓ {year}: Extracted DDI for {len(variable_questions)} variables")

    except Exception as e:
        print(f"⚠️  {year}: Could not parse DDI - {str(e)}")

    return variable_questions

def extract_all_ddi_metadata(years):
    """Extract DDI metadata for all years.

    Args:
        years: List of years to process

    Returns:
        Dictionary: {year: {variable_name: question_text}}
    """
    all_ddi = {}

    for year in years:
        ddi_dict = extract_ddi_metadata(year)
        if ddi_dict:
            all_ddi[year] = ddi_dict

    return all_ddi

if __name__ == "__main__":
    # Test with a few years
    years = list(range(2002, 2025))
    ddi_data = extract_all_ddi_metadata(years)

    print(f"\nYears with DDI data: {len(ddi_data)}")
    for year in sorted(ddi_data.keys())[:5]:
        print(f"{year}: {len(ddi_data[year])} variables")
        # Show example
        first_var = list(ddi_data[year].items())[0]
        print(f"  Example: {first_var[0]} = {first_var[1][:80]}...")
