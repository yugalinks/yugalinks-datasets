"""Download the complete corridor HS6 dataset from Hugging Face."""

from __future__ import annotations

import argparse
from pathlib import Path

from huggingface_hub import hf_hub_download


REPO_ID = "yugalinks/import-export-corridor-product-year-v1"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data"),
        help="Directory for the downloaded Parquet file.",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    path = hf_hub_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        filename="data.parquet",
        local_dir=args.output_dir,
    )
    print(f"Downloaded: {path}")


if __name__ == "__main__":
    main()
