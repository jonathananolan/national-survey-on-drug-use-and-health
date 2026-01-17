#!/usr/bin/env python3
"""
Master pipeline script to run complete NSDUH analysis
Runs all steps in correct order with proper error handling
"""
import sys
import subprocess
from pathlib import Path

def run_step(script_name, description):
    """Run a Python script and handle errors"""
    print(f"\n{'='*70}")
    print(f"STEP: {description}")
    print(f"Running: {script_name}")
    print(f"{'='*70}\n")

    script_path = Path('py') / script_name
    if not script_path.exists():
        print(f"❌ ERROR: Script not found: {script_path}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=False  # Show output in real-time
        )
        print(f"\n✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR: {description} failed with exit code {e.returncode}")
        return False

def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║           NSDUH Drug Use Trends Analysis Pipeline                   ║
║                      1979-2024 Data Processing                       ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    steps = [
        ('01_download/download_nsduh_data.py', 'Download Stata data and setup files'),
        ('01_download/download_concordance_files.py', 'Download concordance (crosswalk) files'),
        ('02_build_metadata/build_metadata.py', 'Build comprehensive metadata'),
        ('03_build_database/build_database.py', 'Build SQLite database (15-30 minutes)'),
        ('04_analysis/plot_trends.py', 'Generate trend visualizations'),
    ]

    for i, (script, description) in enumerate(steps, 1):
        print(f"\n[Step {i}/{len(steps)}]")
        success = run_step(script, description)

        if not success:
            print(f"\n❌ Pipeline failed at step {i}: {description}")
            print("Fix the error and run again, or run individual scripts manually.")
            sys.exit(1)

    print(f"\n{'='*70}")
    print("✅ PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"{'='*70}\n")
    print("Output files created:")
    print("  • data/processed/nsduh_data.db - SQLite database (survey_data + variable_metadata)")
    print("  • metadata/variable_metadata.csv - Comprehensive variable metadata")
    print("  • plots/drug_trends_18_25_*.png - Visualizations")
    print("  • reports/*.html - HTML summary reports for each step")
    print("\nSee README.md for details on outputs and methodology.")

if __name__ == '__main__':
    main()
