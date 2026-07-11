# Statistical Hypothesis Testing Results for BOSTON

This file summarizes the results of the 5 key business hypotheses tested on the BOSTON Airbnb dataset.

| Hypothesis | Test Type | Metric / Mean Comparison | Test Statistic | P-Value | Effect Size | Result |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **H1: Room Type Price Impact** | Welch's Two-Sample t-test | Entire Home: $391.41 vs Private Room: $177.11 | t = 30.979 | 7.88e-190 | Cohen's d = 0.809 | REJECT H0 (Significant) |
| **H2: Superhost Ratings Impact** | Welch's Two-Sample t-test | Superhost Rating: 4.852 vs Non-Superhost: 4.719 | t = 15.114 | 2.47e-50 | Cohen's d = 0.413 | REJECT H0 (Significant) |
| **H3: Review Volume Price Impact** | Welch's Two-Sample t-test | >10 Reviews: $347.26 vs <=10 Reviews: $328.90 | t = 1.971 | 4.88e-02 | Cohen's d = 0.060 | REJECT H0 (Significant) |
| **H4: Borough Pricing Variation** | One-Way ANOVA | Multi-group mean comparison | F = 14.777 | 5.83e-58 | Eta-squared = 0.0753 | REJECT H0 (Significant) |
| **H5: Weekend Occupancy Rate** | Chi-Square Test of Independence (Occupancy Proxy) | Weekend Occupancy: 41.5% vs Weekday: 40.1% | Chi2 = 264.461 | 1.83e-59 | Cramer's V = 0.0128 | REJECT H0 (Significant) |

Note: Bonferroni correction adjusted significance threshold is α/5 = 0.01.
