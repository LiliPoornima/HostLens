import pandas as pd
from rapidfuzz import fuzz


def detect_similar_names(
    df,
    column,
    threshold=90,
    sample_size=100
):

    duplicates = []

    values = (
        df[column]
        .dropna()
        .astype(str)
        .head(sample_size)
        .tolist()
    )

    for i in range(len(values)):

        for j in range(i + 1, len(values)):

            score = fuzz.ratio(
                values[i].lower(),
                values[j].lower()
            )

            if score >= threshold:

                duplicates.append({

                    "value_1": values[i],
                    "value_2": values[j],
                    "similarity": score

                })

    return pd.DataFrame(
        duplicates
    )


if __name__ == "__main__":

    listings = pd.read_csv(
        "data/raw/listings.csv"
    )

    print("Starting fuzzy duplicate detection...")

    similar_listings = detect_similar_names(
        listings,
        "name",
        sample_size=100
    )

    print("Detection complete!")

    print(similar_listings.head())

    print(
        f"Found {len(similar_listings)} possible duplicates."
    )