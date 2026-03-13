"""Tests for StorageService."""

import tempfile
import shutil
from pathlib import Path

import pytest

from app.services.harvest.storage import StorageService
from app.services.harvest.storage.storage_service import (
    LocalStorageBackend,
    StorageBackend,
)


class TestLocalStorageBackend:
    """Test suite for LocalStorageBackend."""

    @pytest.fixture
    def temp_dir(self) -> str:
        """Create a temporary directory for testing."""
        path = tempfile.mkdtemp()
        yield path
        shutil.rmtree(path)

    @pytest.fixture
    def backend(self, temp_dir: str) -> LocalStorageBackend:
        """Create a backend instance."""
        return LocalStorageBackend(base_path=temp_dir)

    def test_upload_and_download(self, backend: LocalStorageBackend) -> None:
        """Test uploading and downloading a file."""
        key = "test/file.txt"
        data = b"Hello, World!"
        content_type = "text/plain"

        # Upload
        url = backend.upload(key, data, content_type)
        assert url is not None

        # Download
        downloaded = backend.download(key)
        assert downloaded == data

    def test_upload_creates_directories(self, backend: LocalStorageBackend) -> None:
        """Test that upload creates necessary directories."""
        key = "deep/nested/path/file.txt"
        data = b"Content"

        backend.upload(key, data, "text/plain")

        # Should not raise
        downloaded = backend.download(key)
        assert downloaded == data

    def test_download_nonexistent_raises(self, backend: LocalStorageBackend) -> None:
        """Test that downloading nonexistent file raises."""
        with pytest.raises(FileNotFoundError):
            backend.download("nonexistent.txt")

    def test_delete(self, backend: LocalStorageBackend) -> None:
        """Test deleting a file."""
        key = "to_delete.txt"
        backend.upload(key, b"Delete me", "text/plain")

        # Verify exists
        assert backend.download(key) == b"Delete me"

        # Delete
        backend.delete(key)

        # Verify gone
        with pytest.raises(FileNotFoundError):
            backend.download(key)

    def test_delete_nonexistent_no_error(self, backend: LocalStorageBackend) -> None:
        """Test that deleting nonexistent file doesn't raise."""
        # Should not raise
        backend.delete("nonexistent.txt")

    def test_get_signed_url(self, backend: LocalStorageBackend) -> None:
        """Test getting a signed URL."""
        key = "signed.txt"
        backend.upload(key, b"Sign this", "text/plain")

        url = backend.get_signed_url(key, 3600)

        assert url.startswith("file://")
        assert key in url

    def test_get_signed_url_nonexistent_raises(
        self, backend: LocalStorageBackend
    ) -> None:
        """Test that signed URL for nonexistent file raises."""
        with pytest.raises(FileNotFoundError):
            backend.get_signed_url("nonexistent.txt", 3600)

    def test_list_keys(self, backend: LocalStorageBackend) -> None:
        """Test listing keys with prefix."""
        # Upload some files
        backend.upload("prefix/a.txt", b"A", "text/plain")
        backend.upload("prefix/b.txt", b"B", "text/plain")
        backend.upload("other/c.txt", b"C", "text/plain")

        # List with prefix
        keys = backend.list_keys("prefix/")

        assert len(keys) == 2
        assert "prefix/a.txt" in keys
        assert "prefix/b.txt" in keys
        assert "other/c.txt" not in keys

    def test_list_keys_empty(self, backend: LocalStorageBackend) -> None:
        """Test listing keys with no matches."""
        keys = backend.list_keys("nonexistent/")
        assert keys == []


class TestStorageService:
    """Test suite for StorageService."""

    @pytest.fixture
    def temp_dir(self) -> str:
        """Create a temporary directory for testing."""
        path = tempfile.mkdtemp()
        yield path
        shutil.rmtree(path)

    @pytest.fixture
    def service(self, temp_dir: str) -> StorageService:
        """Create a storage service instance."""
        backend = LocalStorageBackend(base_path=temp_dir)
        return StorageService(backend=backend)

    def test_upload_plan_export_csv(self, service: StorageService) -> None:
        """Test uploading a CSV export."""
        url = service.upload_plan_export(
            plan_id="plan-123",
            cycle_id="2025-1",
            file_bytes=b"col1,col2\n1,2\n3,4",
            format="csv",
        )

        assert url is not None
        assert "plan-123" in url

    def test_upload_plan_export_json(self, service: StorageService) -> None:
        """Test uploading a JSON export."""
        url = service.upload_plan_export(
            plan_id="plan-456",
            cycle_id="2025-2",
            file_bytes=b'{"key": "value"}',
            format="json",
        )

        assert url is not None
        assert "plan-456" in url

    def test_upload_plan_export_custom_filename(
        self, service: StorageService
    ) -> None:
        """Test uploading with custom filename."""
        url = service.upload_plan_export(
            plan_id="plan-789",
            cycle_id="2025-1",
            file_bytes=b"data",
            format="csv",
            filename="custom_export.csv",
        )

        assert "custom_export.csv" in url

    def test_download_export(self, service: StorageService) -> None:
        """Test downloading an export."""
        # Upload first
        content = b"Download test content"
        service.upload_plan_export(
            plan_id="plan-dl",
            cycle_id="2025-1",
            file_bytes=content,
            format="csv",
            filename="download_test.csv",
        )

        # Download
        downloaded = service.download_export(
            plan_id="plan-dl",
            cycle_id="2025-1",
            filename="download_test.csv",
        )

        assert downloaded == content

    def test_get_signed_url(self, service: StorageService) -> None:
        """Test getting a signed URL."""
        # Upload first
        service.upload_plan_export(
            plan_id="plan-url",
            cycle_id="2025-1",
            file_bytes=b"Signed content",
            format="json",
            filename="signed.json",
        )

        # Get URL
        url = service.get_signed_url(
            plan_id="plan-url",
            cycle_id="2025-1",
            filename="signed.json",
        )

        assert url is not None

    def test_delete_plan_exports(self, service: StorageService) -> None:
        """Test deleting all exports for a plan."""
        # Upload multiple files
        for i in range(3):
            service.upload_plan_export(
                plan_id="plan-delete",
                cycle_id="2025-1",
                file_bytes=f"File {i}".encode(),
                format="csv",
                filename=f"file_{i}.csv",
            )

        # Delete all
        count = service.delete_plan_exports(
            plan_id="plan-delete",
            cycle_id="2025-1",
        )

        assert count == 3

        # Verify deleted
        exports = service.list_plan_exports(
            plan_id="plan-delete",
            cycle_id="2025-1",
        )
        assert len(exports) == 0

    def test_list_plan_exports(self, service: StorageService) -> None:
        """Test listing exports for a plan."""
        # Upload files
        service.upload_plan_export(
            plan_id="plan-list",
            cycle_id="2025-1",
            file_bytes=b"A",
            format="csv",
            filename="a.csv",
        )
        service.upload_plan_export(
            plan_id="plan-list",
            cycle_id="2025-1",
            file_bytes=b"B",
            format="json",
            filename="b.json",
        )

        # List
        exports = service.list_plan_exports(
            plan_id="plan-list",
            cycle_id="2025-1",
        )

        assert len(exports) == 2
        filenames = [e["filename"] for e in exports]
        assert "a.csv" in filenames
        assert "b.json" in filenames

    def test_upload_audit_export(self, service: StorageService) -> None:
        """Test uploading an audit trail export."""
        audit_json = '{"entries": []}'

        url = service.upload_audit_export(
            optimization_id="opt-123",
            cycle_id="2025-1",
            audit_json=audit_json,
        )

        assert url is not None
        assert "audits" in url

    def test_key_structure(self, service: StorageService) -> None:
        """Test that keys follow the expected structure."""
        key = service._build_key(
            cycle_id="2025-1",
            plan_id="plan-123",
            filename="export.csv",
        )

        assert key == "harvest-plans/2025-1/plan-123/export.csv"
