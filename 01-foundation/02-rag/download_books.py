import argparse
import csv
import io
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


BOOKS_CSV_URL = (
    "https://raw.githubusercontent.com/alexeygrigorev/"
    "ai-engineering-buildcamp-code/main/01-foundation/homework/books.csv"
)


def download(url: str, destination: Path) -> None:
    request = Request(url, headers={"User-Agent": "book-downloader/1.0"})
    with urlopen(request, timeout=60) as response:
        destination.write_bytes(response.read())


def filename_for(title: str, pdf_url: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_").lower()
    url_name = Path(urlparse(pdf_url).path).name
    extension = Path(url_name).suffix or ".pdf"
    return f"{slug}{extension}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download the books listed in the Buildcamp books CSV."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("books"),
        help="Directory for downloaded PDFs (default: books)",
    )
    args = parser.parse_args()

    try:
        request = Request(BOOKS_CSV_URL, headers={"User-Agent": "book-downloader/1.0"})
        with urlopen(request, timeout=30) as response:
            csv_text = response.read().decode("utf-8-sig")
            rows = list(csv.DictReader(io.StringIO(csv_text)))

        if not rows:
            raise ValueError("The CSV contains no book records.")

        args.output_dir.mkdir(parents=True, exist_ok=True)
        failures = []

        for row in rows:
            title = row.get("title", "").strip()
            pdf_url = row.get("pdf_url", "").strip()
            if not title or not pdf_url:
                failures.append(f"Skipping invalid CSV row: {row!r}")
                continue

            destination = args.output_dir / filename_for(title, pdf_url)
            try:
                print(f"Downloading {title} -> {destination}")
                download(pdf_url, destination)
            except (HTTPError, URLError, TimeoutError, OSError) as error:
                failures.append(f"Failed to download {title} ({pdf_url}): {error}")

        if failures:
            print("\nSome downloads did not complete:", file=sys.stderr)
            for failure in failures:
                print(f"- {failure}", file=sys.stderr)
            return 1

        print(f"\nDownloaded {len(rows)} PDF files to {args.output_dir}.")
        return 0
    except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"Download failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
