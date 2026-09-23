"""Routing logic of extract_text (digital vs Textract), without AWS or real PDFs."""
from app.services import text_extraction as te

def _body_page(n: int) -> str:
    """A page of a real text layer: body lines, and different on every page."""
    return "\n".join(f"Page {n} line {i}: utilization certificate detail text." for i in range(8))

# What a scanned eOffice page carries: the same stamp on every page, nothing else.
_STAMP_PAGE = (
    "308018/2024/RC-Zirakpur-Khelo India Division\n"
    "File No. 17-04003/3/2022-RC Zirakpur Khelo India Division (Computer No. 29937)\n"
    "Generated from eOffice by Sidharth Singh, YP-SS, YOUNG PROFESSIONAL, "
    "O/o DG SAI on 12/02/2025 01:09 PM"
)


def test_uses_digital_when_text_present(monkeypatch):
    monkeypatch.setattr(te, "_extract_digital", lambda b: [_body_page(1), _body_page(2)])
    monkeypatch.setattr(te, "_extract_textract", lambda bk, k: "OCR")
    text, method = te.extract_text(b"", "bucket", "key")
    assert method == "TEXT"
    assert "utilization certificate detail text" in text


def test_single_page_scan_uses_synchronous_textract(monkeypatch):
    """One small page: answer directly instead of queuing an async job."""
    monkeypatch.setattr(te, "_extract_digital", lambda b: ["  "])
    monkeypatch.setattr(te, "_extract_textract_sync", lambda data: "SYNC OCR")
    monkeypatch.setattr(te, "_extract_textract", lambda bk, k: "ASYNC OCR")
    text, method = te.extract_text(b"%PDF small", "bucket", "key")
    assert (text, method) == ("SYNC OCR", "TEXTRACT")


def test_multi_page_scan_uses_async_textract(monkeypatch):
    """More than one page cannot use the synchronous API."""
    monkeypatch.setattr(te, "_extract_digital", lambda b: ["  ", "  ", "  "])
    monkeypatch.setattr(te, "_extract_textract_sync", lambda data: "SYNC OCR")
    monkeypatch.setattr(te, "_extract_textract", lambda bk, k: "ASYNC OCR")
    text, method = te.extract_text(b"%PDF", "bucket", "key")
    assert (text, method) == ("ASYNC OCR", "TEXTRACT")


def test_sync_failure_falls_back_to_async(monkeypatch):
    """If Textract rejects the sync call, the job route must still run."""
    from botocore.exceptions import ClientError

    def boom(data):
        raise ClientError({"Error": {"Code": "UnsupportedDocumentException"}}, "DetectDocumentText")

    monkeypatch.setattr(te, "_extract_digital", lambda b: ["  "])
    monkeypatch.setattr(te, "_extract_textract_sync", boom)
    monkeypatch.setattr(te, "_extract_textract", lambda bk, k: "ASYNC OCR")
    text, method = te.extract_text(b"%PDF", "bucket", "key")
    assert (text, method) == ("ASYNC OCR", "TEXTRACT")


def test_scan_with_repeated_stamp_goes_to_textract(monkeypatch):
    """A scan whose only text layer is a per-page eOffice stamp must still be OCR'd.

    The stamp is long enough to look like a text layer by character count, but it
    holds no document content - the amounts are in the page image.
    """
    monkeypatch.setattr(te, "_extract_digital", lambda b: [_STAMP_PAGE] * 5)
    monkeypatch.setattr(te, "_extract_textract", lambda bk, k: "OCR TEXT")
    text, method = te.extract_text(b"", "bucket", "key")
    assert method == "TEXTRACT"
    assert text == "OCR TEXT"


def test_body_text_drops_only_the_repeated_lines():
    pages = [f"{_STAMP_PAGE}\nSanctioned amount Rs. 5,00,000/-", f"{_STAMP_PAGE}\nUtilized Rs. 4,20,000/-"]
    body = te._body_text(pages)
    assert "Sanctioned amount Rs. 5,00,000/-" in body
    assert "Utilized Rs. 4,20,000/-" in body
    assert "Generated from eOffice" not in body
