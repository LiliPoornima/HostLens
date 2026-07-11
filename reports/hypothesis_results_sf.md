# Statistical Hypothesis Testing Results for SF

This file summarizes the results of the 5 key business hypotheses tested on the SF Airbnb dataset.

| Hypothesis | Test Type | Metric / Mean Comparison | Test Statistic | P-Value | Effect Size | Result |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **H1: Room Type Price Impact** | Welch's Two-Sample t-test | Entire Home: $413.00 vs Private Room: $318.04 | t = 2.317 | 2.06e-02 | Cohen's d = 0.072 | REJECT H0 (Significant) |
| **H2: Superhost Ratings Impact** | Welch's Two-Sample t-test | Superhost Rating: 4.895 vs Non-Superhost: 4.773 | t = 17.059 | 1.71e-63 | Cohen's d = 0.386 | REJECT H0 (Significant) |
| **H3: Review Volume Price Impact** | Welch's Two-Sample t-test | >10 Reviews: $336.82 vs <=10 Reviews: $424.72 | t = -3.056 | 2.25e-03 | Cohen's d = -0.068 | REJECT H0 (Significant) |
| **H4: Borough Pricing Variation** | One-Way ANOVA | Multi-group mean comparison | F = 2.829 | 5.83e-08 | Eta-squared = 0.0134 | REJECT H0 (Significant) |
| **H5: Weekend Occupancy Rate** | Chi-Square Test of Independence (Occupancy Proxy) | Weekend Occupancy: 50.2% vs Weekday: 49.7% | Chi2 = 52.702 | 3.88e-13 | Cramer's V = 0.0044 | REJECT H0 (Significant) |

Note: Bonferroni correction adjusted significance threshold is α/5 = 0.01.
