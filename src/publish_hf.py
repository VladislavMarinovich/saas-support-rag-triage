"""Publish the Polaris v2 dataset to the Hugging Face Hub.

Auth: reads HF_TOKEN from the environment (a `write` token) — set it via `.env`
(HF_TOKEN=...) or `huggingface-cli login`. The token is NEVER hard-coded here.

Uploads the dataset files (parquet + csv) and the dataset card as the repo README.

Run:  python -m src.publish_hf          # publish
      python -m src.publish_hf --dry    # show what would upload, no network
"""

from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv

load_dotenv()

REPO_ID = "VladislavMarinovich/polaris-support-tickets-v2"

# (local path, path inside the HF repo)
FILES = [
    ("docs/hf-dataset-card.md", "README.md"),                # becomes the dataset card
    ("data/polaris_tickets_v2.parquet", "polaris_tickets_v2.parquet"),
    ("data/polaris_tickets_v2.csv", "polaris_tickets_v2.csv"),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="list files, no upload")
    args = ap.parse_args()

    missing = [local for local, _ in FILES if not os.path.exists(local)]
    if missing:
        raise SystemExit(f"missing files (run the export step first): {missing}")

    if args.dry:
        print(f"would create dataset repo: {REPO_ID}")
        for local, dest in FILES:
            print(f"  {local}  ->  {dest}  ({os.path.getsize(local)//1024} KB)")
        return

    from huggingface_hub import HfApi

    # token=None falls back to the cached `huggingface-cli login` credential
    api = HfApi(token=os.environ.get("HF_TOKEN"))
    who = api.whoami()  # fails early with a clear error if not authenticated
    print("authenticated as:", who.get("name"))

    api.create_repo(REPO_ID, repo_type="dataset", exist_ok=True)
    for local, dest in FILES:
        api.upload_file(path_or_fileobj=local, path_in_repo=dest,
                        repo_id=REPO_ID, repo_type="dataset")
        print("uploaded:", dest)
    print("done ->", f"https://huggingface.co/datasets/{REPO_ID}")


if __name__ == "__main__":
    main()
