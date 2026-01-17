# NSDUH Drug Use Survey (USA)

This repository works with the National Survey on Drug Use and Health (NSDUH), a U.S. federal survey that measures substance use, mental health, and related outcomes among the civilian, non-institutionalized population. It is designed for researchers, analysts, and policymakers who want consistent, documented cross-year estimates.

## Why This Repo Exists

The NSDUH public-use files are not provided in a format to enable quick download and year-to-year comparison. Comparing across years can be problematic, because:

- Methodology shifts (sampling frames, weights, and survey design) introduce breaks.
- Questionnaire wording and variable definitions change across time.
- Some variables are discontinued or replaced.

Those constraints are real and important. Still, cross-year analysis is useful when you are careful about documenting breaks. This project builds a traceable metadata layer to make those comparisons as transparent as possible.

For a concise summary of comparability breaks and reasons, see [metadata/METHODOLOGY_NOTES.md](metadata/METHODOLOGY_NOTES.md).

## What You Get

The pipeline produces:

- `metadata/variable_metadata.csv`: cross-year variable metadata with confirmed and narrow harmonization keys.
- `data/processed/nsduh_data.csv`: the full survey_data table as a flat file.
- `plots/drug_trends_core.png`: core trends (alcohol, any illicit, tobacco).
- `plots/drug_trends_illicit_facets.png`: illicit drug facets (shared y-axis).
- A SQLite database (`data/processed/nsduh_data.db`) that contains:
  `survey_data`: the same data as nsduh_data.csv
  `variable_metadata`: the same data as variable_metadata.csv

The pipeline also standardizes a few derived fields for analysis:

- `age_category` and `age_group` from the NSDUH CATAGE codes
- `analysis_weight` unified across years (ANALWT_C / ANALWT2_C / ANALWT / ANALWT2)
- Created variables (e.g., `ecstasy`, `any_illicit`, `hallucinogen`, `methamphetamine`) group closely related measures that underwent small wording or naming changes; they are convenient rollups, but not perfect substitutes for the original items.

## Quick Start

1. Download and process data:

This repo downloads all the files you need from the NSDUH website. To run it, install python and then run:

```bash
python run.py
```

## Example Plots

![Core Trends (Age 18–25)](plots/drug_trends_core.png)

![Illicit Drug Trends (Age 18–25)](plots/drug_trends_illicit_facets.png)

These charts show separate line segments for periods that are methodologically comparable. When a line breaks, it indicates a known methodology change or wording change that makes cross-period comparisons unreliable. Sudden step changes at those breaks are likely artifacts of the survey redesign, not real shifts in behavior. Trends are best interpreted within each continuous segment.

## Notes

This project was vibe-coded for personal use without any QA. Please use with caution and doubel check any results!
