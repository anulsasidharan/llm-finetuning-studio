from datetime import timedelta
from io import BytesIO
from unittest.mock import MagicMock, patch

from core.storage import delete_file, download_file, get_presigned_url, upload_file


def test_upload_file_calls_put_object() -> None:
    with patch("core.storage.minio_client") as mock_client:
        file_data = BytesIO(b"hello")
        upload_file("fts-datasets", "foo.txt", file_data, 5, "text/plain")
        mock_client.put_object.assert_called_once_with(
            "fts-datasets", "foo.txt", file_data, 5, content_type="text/plain"
        )


def test_download_file_reads_and_releases_response() -> None:
    with patch("core.storage.minio_client") as mock_client:
        mock_response = MagicMock()
        mock_response.read.return_value = b"hello"
        mock_client.get_object.return_value = mock_response

        result = download_file("fts-datasets", "foo.txt")

        mock_client.get_object.assert_called_once_with("fts-datasets", "foo.txt")
        assert result == b"hello"
        mock_response.close.assert_called_once()
        mock_response.release_conn.assert_called_once()


def test_get_presigned_url_converts_seconds_to_timedelta() -> None:
    with patch("core.storage.minio_client") as mock_client:
        mock_client.presigned_get_object.return_value = "https://example.com/foo.txt"

        result = get_presigned_url("fts-datasets", "foo.txt", expires_seconds=120)

        mock_client.presigned_get_object.assert_called_once_with(
            "fts-datasets", "foo.txt", expires=timedelta(seconds=120)
        )
        assert result == "https://example.com/foo.txt"


def test_delete_file_calls_remove_object() -> None:
    with patch("core.storage.minio_client") as mock_client:
        delete_file("fts-datasets", "foo.txt")
        mock_client.remove_object.assert_called_once_with("fts-datasets", "foo.txt")
