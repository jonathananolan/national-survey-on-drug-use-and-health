# NSDUH Methodology Changes and Series Breaks

## Critical Finding: Multiple Series Breaks

**Comparability periods for analysis:**

- Pre-1999 (1979-1998) - NOT comparable to later years
- 1999-2001 - NOT comparable to other periods
- **2002-2019 - COMPARABLE** (SAMHSA-adjusted, see note below)
- 2020 (**DO NOT USE** - incomplete/unreliable data)
- 2021-2023+ (multimode era) - NOT comparable to prior years

**Important Note on 2002-2019 Comparability:**
While there were methodology changes in 2002 and 2015, SAMHSA has confirmed that the drug use variables in the Public Use Files (PUFs) for 2002-2019 ARE comparable due to statistical adjustments and careful harmonization. This is documented in `ConcatPUFComparability_2019.xlsx` where flag variables maintain the same comparability code across all years 2002-2019.

## Major Methodology Changes

### 1999 Redesign (NHSDA)

**Changes:**

- **ACASI Implementation**: Shifted from paper-and-pencil interviewing (PAPI) to:
  - Computer-Assisted Personal Interviewing (CAPI)
  - Audio Computer-Assisted Self-Interviewing (ACASI)
- **Sampling**: Changed to 50-state design with independent, multistage area probability sample for each state + DC
- **Purpose**: ACASI designed to provide highly private and confidential means of responding, increasing honest reporting of illicit drug use and other sensitive behaviors

**Impact:** Complete break in comparability with pre-1999 data

### 2002 Improvements (Renamed to NSDUH)

**Changes:**

- **Survey Renamed**: National Household Survey on Drug Abuse (NHSDA) → National Survey on Drug Use and Health (NSDUH)
- **Respondent Incentives**: Introduced $30 payment to all respondents
  - Initially improved response rates significantly
  - Increased participation
- **Additional methodological refinements** from lessons learned during 1999-2001 period

**Impact:**

- Prevalence rates for 2002 were **substantially higher** than 2001
- 2002 data constitutes a **new baseline** for tracking trends
- **NOT appropriate** to compare 2002+ estimates with 2001 and earlier

### 2015 Redesign

**Changes:**

- Partial redesign questionnaire
- Variables prefixed with "RC-" (Recoded)

**Impact:** Despite questionnaire changes, drug use variables remain comparable to 2002-2014 per SAMHSA harmonization\*

### 2020 COVID-19 Disruption

**Changes:**

- **Almost no data collection** from mid-March through September 2020
- **Web data collection introduced** in October 2020
- Very limited in-person data collection
- New questionnaire elements added in October 2020

**Impact:**

- **2020 data should NOT be used** - missing 2 quarters of data
- Estimates based on Q1 and Q4 only are NOT comparable to full-year estimates
- **Cannot separate true behavioral changes from methodology changes**

### 2021+ Multimode Era

**Changes:**

- **Multimode data collection**: Both in-person and web interviews
- Mode adjustment weighting: Targets 70% in-person, 30% web
- Gradual increase in in-person interviews as COVID restrictions lifted

**Impact:**

- 2021, 2022, 2023 are comparable to **each other** (with updated weights)
- **NOT comparable** to 2020 or any prior years
- Web vs. in-person responses differ in ways that cannot be fully corrected statistically

## What This Means for Drug Use Trends

The large increases in reported drug use between:

- 1998 → 2002
- 1999 → 2002

are **NOT real increases in drug use** but rather **methodological artifacts** from:

1. ACASI increasing honest reporting (1999)
2. $30 incentive improving response rates and possibly changing respondent composition (2002)

## Recommendations

1. **Analyze trends within these comparable periods:**
   - 1979-1998 (pre-ACASI)
   - 1999-2001 (ACASI, no incentive)
   - **2002-2019 (continuous comparable period)**
   - **SKIP 2020** (unreliable data)
   - 2021-2023+ (multimode: web + in-person)

2. **Plotting guidance:**
   - Use different colors for incomparable periods (pre-1999, 1999-2001, 2002-2019, 2021+)
   - DO NOT connect lines between incomparable periods
   - 2002-2019 can be plotted as a continuous line (variables are harmonized)

3. **Visual markers for context (informational only):**
   - 1999: ACASI introduced (creates break)
   - 2002: $30 incentive + renamed to NSDUH (creates break, but 2002-2019 harmonized)
   - 2015: Questionnaire redesign (but comparable within 2002-2019 period)\*
   - 2020: COVID disruption (EXCLUDE DATA)
   - 2021: Multimode era begins (creates break)

4. **Exclude 2020 data entirely** from analysis - it is neither comparable to prior years nor to subsequent years

\*Per SAMHSA PUF Comparability documentation

## Sources

- NCBI Bookshelf: "2002 - National Survey on Drug Use and Health"
- SAMHSA: NSDUH Combined Public-use Files documentation
- SAMHSA FAQ: "Why does SAMHSA caution against comparing 2020 estimates with estimates from other years?"
- 2021, 2022, 2023 NSDUH Methodological Summary and Definitions reports
