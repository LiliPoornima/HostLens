# Statistical Hypothesis Testing Results

This file summarizes the results of the 5 key business hypotheses tested on the NYC Airbnb dataset.

| Hypothesis | Test Type | Metric / Mean Comparison | Test Statistic | P-Value | Effect Size | Result |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **H1: Room Type Price Impact** | Welch's Two-Sample t-test | Entire Home: $282.26 vs Private Room: $187.20 | t = 19.575 | 8.84e-85 | Cohen's d = 0.225 | REJECT H0 (Significant) |
| **H2: Superhost Ratings Impact** | Welch's Two-Sample t-test | Superhost Rating: 4.859 vs Non-Superhost: 4.743 | t = 32.426 | 3.17e-226 | Cohen's d = 0.306 | REJECT H0 (Significant) |
| **H3: Review Volume Price Impact** | Welch's Two-Sample t-test | >10 Reviews: $234.71 vs <=10 Reviews: $256.85 | t = -4.705 | 2.55e-06 | Cohen's d = -0.049 | REJECT H0 (Significant) |
| **H4: Borough Pricing Variation** | One-Way ANOVA | Multi-group mean comparison | F = 161.623 | 3.95e-137 | Eta-squared = 0.0209 | REJECT H0 (Significant) |
| **H5: Weekend Occupancy Rate** | Chi-Square Test of Independence (Occupancy Proxy) | Weekend Occupancy: 49.1% vs Weekday: 48.7% | Chi2 = 157.847 | 3.34e-36 | Cramer's V = 0.0038 | REJECT H0 (Significant) |

Note: Bonferroni correction adjusted significance threshold is α/5 = 0.01.
