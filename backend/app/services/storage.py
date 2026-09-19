import hashlib
import os
import re
import uuid
from pathlib import Path
from typing import BinaryIO, Tuple
from fastapi import UploadFile

from app.core.config import settings
from app.core.errors import FileValidationError


class StorageService:
    """Manages secure file validation, streaming persistence, and deduplication hashing."""

    # Allowed MIME types and their canonical magic byte signatures
    ALLOWED_MAGIC_BYTES = {
        b"%PDF": "application/pdf",
        b"\x89PNG\r\n\x1a\n": "image/png",
        b"\xff\xd8\xff": "image/jpeg",
    }

    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

    def __init__(self, upload_dir: str = settings.UPLOAD_DIR):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Strips path traversal sequences, null bytes, and dangerous characters."""
        # Extract basename only to prevent directory traversal
        base_name = os.path.basename(filename or "unnamed_document")
        # Remove null bytes
        base_name = base_name.replace("\x00", "")
        # Remove special characters except alphanumeric, hyphen, underscore, and dot
        clean_name = re.sub(r"[^a-zA-Z0-9._-]", "_", base_name)
        # Limit length
        if len(clean_name) > 100:
            name_part, ext = os.path.splitext(clean_name)
            clean_name = name_part[: 100 - len(ext)] + ext
        return clean_name or "document"

    @classmethod
    def detect_mime_type(cls, file_header: bytes, filename: str) -> str:
        """Sniffs magic bytes to determine real file type, rejecting spoofed extensions."""
        ext = os.path.splitext(filename.lower())[1]
        if ext not in cls.ALLOWED_EXTENSIONS:
            raise FileValidationError(
                f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(cls.ALLOWED_EXTENSIONS)}"
            )

        # Check magic bytes
        for magic, mime in cls.ALLOWED_MAGIC_BYTES.items():
            if file_header.startswith(magic):
                return mime

        raise FileValidationError(
            "Corrupt or invalid file format: header magic bytes do not match a supported PDF, PNG, or JPEG format"
        )

    async def save_upload_file(
        self, upload_file: UploadFile
    ) -> Tuple[str, str, str, int, str]:
        """
        Streams uploaded file to disk while validating size, magic bytes, and SHA-256 hash.
        
        Returns:
            Tuple of (sanitized_original_name, stored_filename, absolute_file_path, file_size_bytes, mime_type)
        """
        original_name = self.sanitize_filename(upload_file.filename or "upload.bin")
        ext = os.path.splitext(original_name)[1].lower()

        # Read first 16 bytes for magic byte verification
        header = await upload_file.read(16)
        if not header:
            raise FileValidationError("Uploaded file is empty (0 bytes)")

        mime_type = self.detect_mime_type(header, original_name)

        # Generate unique storage name: <uuid>_<timestamp><ext>
        stored_filename = f"{uuid.uuid4().hex}{ext}"
        destination_path = self.upload_dir / stored_filename

        # Rewind to start
        await upload_file.seek(0)

        hasher = hashlib.sha256()
        total_size = 0
        chunk_size = 1024 * 1024  # 1MB chunks

        with open(destination_path, "wb") as out_file:
            while chunk := await upload_file.read(chunk_size):
                total_size += len(chunk)
                if total_size > settings.max_upload_size_bytes:
                    # Clean up partial file on violation
                    out_file.close()
                    destination_path.unlink(missing_ok=True)
                    raise FileValidationError(
                        f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB"
                    )
                hasher.update(chunk)
                out_file.write(chunk)

        file_hash = hasher.hexdigest()
        return (
            original_name,
            stored_filename,
            str(destination_path.resolve()),
            total_size,
            mime_type,
        )


storage_service = StorageService()
