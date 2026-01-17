# NSDUH Drug Use Survey (USA)

This repository works with the National Survey on Drug Use and Health (NSDUH), a U.S. federal survey that measures substance use, mental health, and related outcomes among the civilian, non-institutionalized population. It is designed for researchers, analysts, and policymakers who want consistent, documented cross-year estimates.

## Why This Repo Exists

The NSDUH public-use files are not provided in a format to enable quick download and year-to-year comparisons because:

- Methodology shifts (sampling frames, weights, and survey design) introduce breaks.
- Questionnaire wording and variable definitions change across time.
- Some variables are discontinued or replaced.

Those constraints are real and important. Still, cross-year analysis is useful when you are careful about documenting breaks. This project builds a traceable metadata layer to make those comparisons as transparent as possible.

For a concise summary of comparability breaks and reasons, see `metadata/METHODOLOGY_NOTES.md`.

## What You Get

The pipeline produces:

- `metadata/variable_metadata.csv`: cross-year variable metadata with confirmed and narrow harmonization keys.
- `data/processed/nsduh_data.db`: a SQLite database with the survey data and metadata tables.
- `data/processed/nsduh_data.csv`: the full survey_data table as a flat file.
- `plots/drug_trends_18_25_combined.png`: a simple example plot of lifetime use trends (ages 18–25).

The pipeline also standardizes a few derived fields for analysis:

- `age_category` and `age_group` from the NSDUH CATAGE codes
- `analysis_weight` unified across years (ANALWT_C / ANALWT2_C / ANALWT / ANALWT2)
- Created variables (e.g., `ecstasy_ever`, `any_illicit_ever`) group closely related measures that underwent small wording or naming changes; they are convenient rollups, but not perfect substitutes for the original items.

## Quick Start

1. Download and process data:

This repo downloads all the files you need from the NSDUH website. To run it, install python and then run:

```bash
python run.py
```

2. Expected outputs:

- `metadata/variable_metadata.csv`
- `data/processed/nsduh_data.db`
- `data/processed/nsduh_data.csv`
- `plots/drug_trends_18_25_combined.png`

## SQLite Tables

The SQLite database (`data/processed/nsduh_data.db`) contains:

- `survey_data`: respondent-level records with harmonized age and drug flags.
- `variable_metadata`: cross-year variable metadata and harmonization keys.

## Example Plot

The plot is checked into the repo and will render on GitHub:

![NSDUH Drug Trends (18–25) Facets](plots/drug_trends_18_25_facets.png)

## How To Read The Graph

This chart shows separate line segments for periods that are methodologically comparable. When a line breaks, it indicates a known methodology change or wording change that makes cross-period comparisons unreliable. Sudden step changes at those breaks are likely artifacts of the survey redesign, not real shifts in behavior. Trends are best interpreted within each continuous segment.

## Notes

This project was vibe-coded for personal use without any QA. Please use with caution and doubel check any results!
