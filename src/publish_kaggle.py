"""Publish the Polaris v2 dataset to Kaggle (mirror of the Hugging Face dataset).

Auth: reads the new-style Kaggle token from env var `KAGGLE_API_TOKEN` (set it in
`.env`). kagglehub recognizes it — no legacy kaggle.json needed.

Uploads a clean staging dir (parquet + csv). The dataset title/subtitle/description
are set on the Kaggle web page after the first upload (paste from the dataset card).

Run:  python -m src.publish_kaggle --dry   # stage + show, no upload
      python -m src.publish_kaggle         # upload
"""

from __future__ import annotations

import argparse
import os
import shutil

from dotenv import load_dotenv

load_dotenv()

HANDLE = "vladislavmarinovich1/polaris-support-tickets-v2"
STAGE = "data/kaggle_upload"
FILES = ["data/polaris_tickets_v2.parquet", "data/polaris_tickets_v2.csv"]


def _stage() -> None:
    """Copy the dataset files into a clean upload dir (nothing else)."""
    if os.path.exists(STAGE):
        shutil.rmtree(STAGE)
    os.makedirs(STAGE)
    for f in FILES:
        shutil.copy(f, STAGE)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="stage + list, no upload")
    args = ap.parse_args()

    missing = [f for f in FILES if not os.path.exists(f)]
    if missing:
        raise SystemExit(f"missing files (run the export step first): {missing}")

    _stage()
    if args.dry:
        print(f"would upload {os.listdir(STAGE)}  ->  {HANDLE}")
        return

    if not os.environ.get("KAGGLE_API_TOKEN"):
        raise SystemExit("KAGGLE_API_TOKEN not set — add it to .env (the new-style token)")

    import kagglehub

    kagglehub.dataset_upload(HANDLE, STAGE, version_notes="initial upload — Polaris v2")
    print("done ->", f"https://www.kaggle.com/datasets/{HANDLE}")


if __name__ == "__main__":
    main()
