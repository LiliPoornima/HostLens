import os
import json
import pandas as pd
import numpy as np
import scipy.stats as stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.outliers_influence import variance_inflation_factor

def run_statistical_analysis():
    print("Starting statistical analysis...")
    os.makedirs("reports", exist_ok=True)
    
    # Load enriched data
    df = pd.read_csv("data/processed/enriched_listings.csv")
    calendar = pd.read_csv("data/raw/calendar.csv")
    calendar["date"] = pd.to_datetime(calendar["date"])
    
    findings = {}

    # H1: Entire-home listings command statistically significantly higher prices than private rooms
    entire_homes = df[df["room_type"] == "Entire Home/Apt"]["price"].dropna()
    private_rooms = df[df["room_type"] == "Private Room"]["price"].dropna()
    
    t_stat_h1, p_val_h1 = stats.ttest_ind(entire_homes, private_rooms, equal_var=False)
    
    # Cohen's d
    n1, n2 = len(entire_homes), len(private_rooms)
    v1, v2 = entire_homes.var(), private_rooms.var()
    pooled_se = np.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
    cohens_d_h1 = (entire_homes.mean() - private_rooms.mean()) / pooled_se
    
    findings["H1"] = {
        "test": "Welch's Two-Sample t-test",
        "entire_home_mean": float(entire_homes.mean()),
        "private_room_mean": float(private_rooms.mean()),
        "t_statistic": float(t_stat_h1),
        "p_value": float(p_val_h1),
        "cohens_d": float(cohens_d_h1),
        "significant": bool(p_val_h1 < 0.05)
    }

    # H2: Superhost listings achieve higher review scores than non-superhost listings
    superhosts = df[df["host_is_superhost"] == "t"]["review_scores_rating"].dropna()
    non_superhosts = df[df["host_is_superhost"] == "f"]["review_scores_rating"].dropna()
    
    t_stat_h2, p_val_h2 = stats.ttest_ind(superhosts, non_superhosts, equal_var=False)
    
    n1, n2 = len(superhosts), len(non_superhosts)
    v1, v2 = superhosts.var(), non_superhosts.var()
    pooled_se = np.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
    cohens_d_h2 = (superhosts.mean() - non_superhosts.mean()) / pooled_se
    
    findings["H2"] = {
        "test": "Welch's Two-Sample t-test",
        "superhost_mean_rating": float(superhosts.mean()),
        "non_superhost_mean_rating": float(non_superhosts.mean()),
        "t_statistic": float(t_stat_h2),
        "p_value": float(p_val_h2),
        "cohens_d": float(cohens_d_h2),
        "significant": bool(p_val_h2 < 0.05)
    }

    # H3: Listings with more than 10 reviews have significantly different prices than listings with fewer
    more_reviews = df[df["number_of_reviews"] > 10]["price"].dropna()
    fewer_reviews = df[df["number_of_reviews"] <= 10]["price"].dropna()
    
    t_stat_h3, p_val_h3 = stats.ttest_ind(more_reviews, fewer_reviews, equal_var=False)
    
    n1, n2 = len(more_reviews), len(fewer_reviews)
    v1, v2 = more_reviews.var(), fewer_reviews.var()
    pooled_se = np.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
    cohens_d_h3 = (more_reviews.mean() - fewer_reviews.mean()) / pooled_se
    
    findings["H3"] = {
        "test": "Welch's Two-Sample t-test",
        "more_reviews_mean_price": float(more_reviews.mean()),
        "fewer_reviews_mean_price": float(fewer_reviews.mean()),
        "t_statistic": float(t_stat_h3),
        "p_value": float(p_val_h3),
        "cohens_d": float(cohens_d_h3),
        "significant": bool(p_val_h3 < 0.05)
    }

    # H4: Neighbourhood average prices differ significantly (ANOVA across neighbourhood groups)
    groups = df.groupby("neighbourhood_group_cleansed")["price"].apply(list)
    f_stat, p_val_h4 = stats.f_oneway(*groups)
    
    # Calculate eta-squared (effect size)
    overall_mean = df["price"].mean()
    ss_between = sum(len(group) * (np.mean(group) - overall_mean)**2 for group in groups)
    ss_total = sum(sum((val - overall_mean)**2 for val in group) for group in groups)
    eta_squared = ss_between / ss_total if ss_total > 0 else 0
    
    findings["H4"] = {
        "test": "One-Way ANOVA",
        "f_statistic": float(f_stat),
        "p_value": float(p_val_h4),
        "eta_squared": float(eta_squared),
        "significant": bool(p_val_h4 < 0.05)
    }

    # H5: Weekend vs. weekday occupancy differences (Proxy for missing pricing data in calendar)
    # We define weekend as Friday/Saturday and weekday as Sunday-Thursday
    calendar["day_of_week"] = calendar["date"].dt.dayofweek
    calendar["is_weekend"] = calendar["day_of_week"].isin([4, 5]).astype(int)
    calendar["is_booked"] = calendar["available"].map({"f": 1, "t": 0})
    
    # Perform a chi-square test on total booked vs available
    contingency_table = pd.crosstab(calendar["is_weekend"], calendar["is_booked"])
    chi2, p_val_h5, dof, expected = stats.chi2_contingency(contingency_table)
    
    # Calculate Cramér's V (effect size)
    n = contingency_table.sum().sum()
    cramers_v = np.sqrt(chi2 / (n * min(contingency_table.shape - np.array([1, 1]))))
    
    findings["H5"] = {
        "test": "Chi-Square Test of Independence (Occupancy Proxy)",
        "weekend_occupancy_rate": float(calendar[calendar["is_weekend"] == 1]["is_booked"].mean()),
        "weekday_occupancy_rate": float(calendar[calendar["is_weekend"] == 0]["is_booked"].mean()),
        "chi2_statistic": float(chi2),
        "p_value": float(p_val_h5),
        "cramers_v": float(cramers_v),
        "significant": bool(p_val_h5 < 0.05)
    }

    # 2. Driver & Correlation Analysis
    # Select numerical columns for correlation matrix
    num_cols = ["price", "bedrooms", "beds", "number_of_reviews", "review_scores_rating", 
                "reviews_per_month", "host_tenure_years", "occupancy_rate", "estimated_annual_revenue"]
    corr_matrix = df[num_cols].corr()
    corr_matrix.to_csv("reports/correlation_matrix.csv")
    
    # Regression analysis (OLS) to identify price drivers
    # Prepare categories and dummy variables
    reg_df = df[["price", "bedrooms", "beds", "room_type", "neighbourhood_group_cleansed", 
                 "review_scores_rating", "host_is_superhost"]].dropna()
    reg_df["log_price"] = np.log1p(reg_df["price"])
    reg_df["host_is_superhost"] = reg_df["host_is_superhost"].map({"t": 1, "f": 0}).fillna(0)
    
    # Define OLS model
    formula = "log_price ~ bedrooms + beds + C(room_type) + C(neighbourhood_group_cleansed) + review_scores_rating + host_is_superhost"
    model = ols(formula, data=reg_df).fit()
    
    # Save regression summary as text file
    with open("reports/ols_regression_summary.txt", "w") as f:
        f.write(model.summary().as_text())
    
    # Compute VIF to check multicollinearity
    # Select variables from regression design matrix
    X_variables = reg_df[["bedrooms", "beds", "review_scores_rating", "host_is_superhost"]].copy()
    # Add constant
    X_variables = sm.add_constant(X_variables)
    
    vif_data = pd.DataFrame()
    vif_data["feature"] = X_variables.columns
    vif_data["VIF"] = [variance_inflation_factor(X_variables.values, i) for i in range(len(X_variables.columns))]
    vif_data.to_csv("reports/vif_report.csv", index=False)

    # Save JSON findings
    with open("reports/statistical_findings.json", "w") as f:
        json.dump(findings, f, indent=4)
        
    print("Statistical analysis complete. Reports saved under reports/")

if __name__ == "__main__":
    run_statistical_analysis()
