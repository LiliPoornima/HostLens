import os
import requests
import gzip
import shutil


def download_file(url, output_path):

    response = requests.get(url)

    response.raise_for_status()

    with open(output_path, "wb") as file:

        file.write(response.content)

    print(f"Downloaded: {output_path}")


def extract_gzip(input_path, output_path):

    with gzip.open(input_path, "rb") as f_in:

        with open(output_path, "wb") as f_out:

            shutil.copyfileobj(f_in, f_out)

    print(f"Extracted: {output_path}")