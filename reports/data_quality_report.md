# Data Quality Report

## Dataset Summary

| Dataset | Rows | Columns |
|----------|----------|----------|
| Listings | 30259 | 90 |
| Calendar | 11152576 | 5 |
| Reviews | 990170 | 6 |
| Neighbourhoods | 230 | 2 |

## Missing Values

The following columns exhibit substantial missingness:

- neighborhood_overview
- host_since
- host_neighbourhood
- host_response_time
- bedrooms
- bathrooms
- beds
- license

## Completeness Implications

- Missing host information limits host tenure analysis.
- Missing bedroom and bathroom information affects pricing models.
- Missing license data limits regulatory analysis.

## Duplicate Detection

Duplicate detection was performed using:

1. Deterministic matching.
2. Fuzzy matching with RapidFuzz.

## Domain Validation

Validation rules applied:

- Price must be non-negative.
- Latitude must be within [-90, 90].
- Longitude must be within [-180, 180].