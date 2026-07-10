import pandas as pd


def profile_dataset(df, name):

    report = pd.DataFrame({

        "column": df.columns,

        "dtype": df.dtypes.astype(str),

        "missing_values": df.isnull().sum(),

        "missing_percent": (
            df.isnull().mean() * 100
        ),

        "unique_values": [
            df[col].nunique()
            for col in df.columns
        ]
    })

    report.to_csv(

        f"../reports/{name}_profile.csv",

        index=False
    )

    print(

        f"{name} profile saved."

    )