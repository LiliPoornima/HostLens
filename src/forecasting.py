import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import Holt

def run_forecasting(city="nyc"):
    print(f"Starting Occupancy Forecasting for {city.upper()}...")
    os.makedirs("reports/figures", exist_ok=True)
    
    # 1. Load Calendar data
    raw_path = "data/raw" if city == "nyc" else f"data/raw/{city}"
    print(f"Loading {raw_path}/calendar.csv...")
    calendar = pd.read_csv(f"{raw_path}/calendar.csv")
    calendar["date"] = pd.to_datetime(calendar["date"])
    calendar["is_booked"] = calendar["available"].map({"f": 1, "t": 0})
    
    # Group by Year-Month
    monthly_data = calendar.groupby(calendar["date"].dt.to_period("M"))["is_booked"].mean().reset_index()
    monthly_data["date"] = monthly_data["date"].dt.to_timestamp()
    monthly_data.rename(columns={"is_booked": "occupancy_rate"}, inplace=True)
    
    # Sort by date
    monthly_data = monthly_data.sort_values(by="date").reset_index(drop=True)
    
    # 2. Fit Holt's Exponential Smoothing
    ts = monthly_data.set_index("date")["occupancy_rate"]
    
    print("Fitting Exponential Smoothing model...")
    model = Holt(ts, initialization_method="estimated").fit()
    forecast_steps = 6
    forecast = model.forecast(forecast_steps)
    
    # Generate future dates
    last_date = ts.index[-1]
    future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=forecast_steps, freq="MS")
    
    forecast_df = pd.DataFrame({
        "date": future_dates,
        "forecast_occupancy": forecast.values
    })
    
    # Export forecast CSV
    forecast_df.to_csv(f"reports/occupancy_forecast_{city}.csv", index=False)
    if city == "nyc":
        forecast_df.to_csv("reports/occupancy_forecast.csv", index=False)
    print(f"Saved reports/occupancy_forecast_{city}.csv")
    
    # 3. Plot history & forecast
    plt.figure(figsize=(10, 5))
    plt.plot(ts.index, ts.values, marker="o", color="#00A699", label="Historical Occupancy Rate")
    plt.plot(future_dates, forecast.values, marker="s", linestyle="--", color="#FF5A5F", label="Holt Forecast (Next 6 Months)")
    
    plt.title(f"{city.upper()} Airbnb Monthly Occupancy Rate: History & 6-Month Forecast", fontsize=14, pad=15)
    plt.xlabel("Month", fontsize=12)
    plt.ylabel("Occupancy Rate", fontsize=12)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.ylim(0, 1.0)
    plt.legend(fontsize=11)
    
    # Save chart
    plt.tight_layout()
    plt.savefig(f"reports/figures/07_occupancy_forecast_{city}.png", dpi=150)
    if city == "nyc":
        plt.savefig("reports/figures/07_occupancy_forecast.png", dpi=150)
    plt.close()
    print(f"Saved occupancy forecast visualization to reports/figures/07_occupancy_forecast_{city}.png")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run forecasting for a specific city.")
    parser.add_argument("--city", type=str, default="nyc", choices=["nyc", "boston", "sf"])
    args = parser.parse_args()
    run_forecasting(args.city)
