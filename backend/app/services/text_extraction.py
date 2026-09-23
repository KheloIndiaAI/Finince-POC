"""Extract text from a PDF.

Digital PDFs (with a text layer) are read locally with pdfplumber. Scanned PDFs
(little or no extractable text) go to AWS Textract's async API, which reads the
file already stored in S3. Returns (text, method) with method 'TEXT' or 'TEXTRACT'.
"""
import io
import time
from collections import Counter

import boto3
import pdfplumber

from app.config import settings

# Body characters per page, counted after running headers are removed. A scan from
# eOffice carries a stamp on every page (~200 chars/page) that would otherwise pass
# as a text layer; a real text layer runs several hundred body characters per page.
_MIN_BODY_CHARS_PER_PAGE = 200
_textract = boto3.client("textract", region_name=settings.aws_region)


def extract_text(pdf_bytes: bytes, s3_bucket: str, s3_key: str) -> tuple[str, str]:
    """Read a digital text layer if present, else OCR the scan via Textract."""
    pages = _extract_digital(pdf_bytes)
    if pages and len(_body_text(pages)) >= _MIN_BODY_CHARS_PER_PAGE * len(pages):
        return "\n".join(pages), "TEXT"
    return _extract_textract(s3_bucket, s3_key), "TEXTRACT"


def _extract_digital(pdf_bytes: bytes) -> list[str]:
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return [page.extract_text() or "" for page in pdf.pages]


def _body_text(pages: list[str]) -> str:
    """The text minus lines repeated across pages (running headers and footers).

    A scanned eOffice file has no body at all - only the stamp - so this is what
    separates "has a text layer" from "only looks like it has one".
    """
    lines = [line.strip() for page in pages for line in page.splitlines() if line.strip()]
    repeated = {
        line for line, count in Counter(lines).items() if count >= max(2, len(pages) * 0.6)
    }
    return "\n".join(line for line in lines if line not in repeated)


def _extract_textract(bucket: str, key: str) -> str:
    job_id = _textract.start_document_text_detection(
        DocumentLocation={"S3Object": {"Bucket": bucket, "Name": key}}
    )["JobId"]
    _wait_for_job(job_id)
    return _read_all_lines(job_id)


def _wait_for_job(job_id: str, tries: int = 60, delay: int = 2) -> None:
    for _ in range(tries):
        status = _textract.get_document_text_detection(JobId=job_id)["JobStatus"]
        if status == "SUCCEEDED":
            return
        if status == "FAILED":
            raise RuntimeError(f"Textract job {job_id} failed")
        time.sleep(delay)
    raise TimeoutError(f"Textract job {job_id} timed out")


def _read_all_lines(job_id: str) -> str:
    lines: list[str] = []
    token = None
    while True:
        kwargs = {"JobId": job_id}
        if token:
            kwargs["NextToken"] = token
        resp = _textract.get_document_text_detection(**kwargs)
        lines += [b["Text"] for b in resp["Blocks"] if b["BlockType"] == "LINE"]
        token = resp.get("NextToken")
        if not token:
            return "\n".join(lines)
