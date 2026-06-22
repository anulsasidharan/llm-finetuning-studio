import contextlib
from unittest.mock import MagicMock, patch

from utils.storage import download_dataset_file


def test_download_dataset_file_reads_and_releases_response() -> None:
    fake_response = MagicMock()
    fake_response.read.return_value = b'{"prompt": "hi"}'
    fake_client = MagicMock()
    fake_client.get_object.return_value = fake_response

    with patch("utils.storage._get_minio_client", return_value=fake_client):
        result = download_dataset_file("fts-datasets", "user/file.jsonl")

    assert result == b'{"prompt": "hi"}'
    fake_client.get_object.assert_called_once_with("fts-datasets", "user/file.jsonl")
    fake_response.close.assert_called_once()
    fake_response.release_conn.assert_called_once()


def test_download_dataset_file_releases_response_even_on_read_error() -> None:
    fake_response = MagicMock()
    fake_response.read.side_effect = RuntimeError("boom")
    fake_client = MagicMock()
    fake_client.get_object.return_value = fake_response

    with (
        patch("utils.storage._get_minio_client", return_value=fake_client),
        contextlib.suppress(RuntimeError),
    ):
        download_dataset_file("fts-datasets", "user/file.jsonl")

    fake_response.close.assert_called_once()
    fake_response.release_conn.assert_called_once()
