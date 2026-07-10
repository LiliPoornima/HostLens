import pandas as pd

from config import FILES


def load_dataset(file_path):

    try:

        df = pd.read_csv(file_path)

        print(
            f"Loaded {file_path} "
            f"({df.shape[0]} rows, {df.shape[1]} columns)"
        )

        return df

    except Exception as e:

        print(
            f"Error loading {file_path}: {e}"
        )

        return None


listings = load_dataset(FILES["listings"])
calendar = load_dataset(FILES["calendar"])
reviews = load_dataset(FILES["reviews"])
neighbourhoods = load_dataset(
    FILES["neighbourhoods"]
)