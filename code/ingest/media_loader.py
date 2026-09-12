"""
Dynamic Media Loader.
Discovers and manages local images (receipts, statements, invoices) dynamically at runtime.
Zero hardcoding of image filenames or directories.
"""

from __future__ import annotations
import os
import hashlib
import logging
from pathlib import Path
from typing import Dict, Optional, List
from PIL import Image

logger = logging.getLogger(__name__)


class MediaItem:
    """Represents a dynamically discovered media file."""
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.filename = file_path.name
        self.media_id = file_path.stem.lower()
        self._hash: Optional[str] = None

    @property
    def sha256(self) -> str:
        if self._hash is None:
            hasher = hashlib.sha256()
            with open(self.file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            self._hash = hasher.hexdigest()
        return self._hash

    def open_image(self) -> Optional[Image.Image]:
        try:
            return Image.open(self.file_path)
        except Exception as e:
            logger.error(f"Failed to open image at {self.file_path}: {e}")
            return None


class DynamicMediaLoader:
    """
    Discovers all image files dynamically in a given directory hierarchy.
    Enables resolution by ID or filename without hardcoding.
    """

    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}

    def __init__(self):
        self.media_index: Dict[str, MediaItem] = {}

    def discover_media(self, root_dir: str | Path) -> Dict[str, MediaItem]:
        """
        Scans root directory recursively for supported image files.
        """
        path = Path(root_dir)
        if not path.exists():
            return {}

        count = 0
        for item in path.rglob("*"):
            if item.is_file() and item.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                media_item = MediaItem(item)
                # Map by stem (e.g., 'receipt_01') and full name ('receipt_01.png')
                self.media_index[media_item.media_id] = media_item
                self.media_index[item.name.lower()] = media_item
                count += 1

        logger.info(f"Dynamically discovered {count} media items in '{path}'.")
        return self.media_index

    def get_media(self, identifier: str) -> Optional[MediaItem]:
        """
        Retrieves a media item by image_id or filename dynamically.
        """
        if not identifier:
            return None
        clean_id = str(identifier).strip().lower()
        # Remove common extension if present
        for ext in self.SUPPORTED_EXTENSIONS:
            if clean_id.endswith(ext):
                clean_id = clean_id[:-len(ext)]
                break
        return self.media_index.get(clean_id) or self.media_index.get(str(identifier).strip().lower())
