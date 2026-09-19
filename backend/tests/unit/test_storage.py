import pytest
from app.core.errors import FileValidationError
from app.services.storage import StorageService


def test_sanitize_filename_traversal():
    # Attempt directory traversal
    unsafe_name = "../../../etc/passwd.pdf"
    clean = StorageService.sanitize_filename(unsafe_name)
    assert "/" not in clean
    assert "\\" not in clean
    assert ".." not in clean
    assert clean == "passwd.pdf"


def test_sanitize_filename_special_chars():
    unsafe_name = "test <file> | with * invalid ? chars!.pdf"
    clean = StorageService.sanitize_filename(unsafe_name)
    assert "<" not in clean
    assert ">" not in clean
    assert "*" not in clean
    assert "?" not in clean
    assert clean.endswith(".pdf")


def test_detect_mime_type_valid():
    # Valid PDF magic bytes
    pdf_header = b"%PDF-1.7\r\n\x00\x01\x02\x03\x04\x05"
    assert StorageService.detect_mime_type(pdf_header, "exam.pdf") == "application/pdf"

    # Valid PNG magic bytes
    png_header = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    assert StorageService.detect_mime_type(png_header, "figure.png") == "image/png"

    # Valid JPEG magic bytes
    jpeg_header = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00"
    assert StorageService.detect_mime_type(jpeg_header, "scan.jpg") == "image/jpeg"


def test_detect_mime_type_spoofed_or_invalid():
    # Executable disguised as PDF
    fake_header = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00"
    with pytest.raises(FileValidationError):
        StorageService.detect_mime_type(fake_header, "malicious.pdf")

    # Unsupported extension
    with pytest.raises(FileValidationError):
        StorageService.detect_mime_type(b"%PDF-1.4", "document.exe")
