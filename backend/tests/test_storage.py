import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
from fastapi import UploadFile
from app.services.storage import is_blob_url, get_file_target, save_upload, remove
from app.core.config import settings

def test_is_blob_url():
    assert is_blob_url('https://store.public.blob.vercel-storage.com/test.pdf') is True
    assert is_blob_url('http://store.public.blob.vercel-storage.com/test.pdf') is True
    assert is_blob_url('local_file_key.pdf') is False
    assert is_blob_url('') is False
    assert is_blob_url(None) is False

def test_get_file_target():
    url = 'https://store.public.blob.vercel-storage.com/sample.png'
    target, is_remote = get_file_target(url)
    assert is_remote is True
    assert target == url

    local_key = 'sample_local.png'
    target, is_remote = get_file_target(local_key)
    assert is_remote is False
    assert target.endswith('sample_local.png')

@pytest.mark.anyio
async def test_save_upload_local_fallback(tmp_path):
    with patch.object(settings, 'BLOB_READ_WRITE_TOKEN', ''):
        with patch('app.services.storage.root', tmp_path):
            file_data = b'Hello CloudDrive Local'
            upload = UploadFile(filename='test.txt', file=BytesIO(file_data))
            
            key, size = await save_upload(upload)
            assert size == len(file_data)
            assert not is_blob_url(key)
            assert (tmp_path / key).exists()
            assert (tmp_path / key).read_bytes() == file_data

@pytest.mark.anyio
async def test_save_upload_vercel_blob():
    with patch.object(settings, 'BLOB_READ_WRITE_TOKEN', 'vercel_blob_rw_dummy_token'):
        with patch('vercel_blob.put') as mock_put:
            mock_put.return_value = {
                'url': 'https://store.public.blob.vercel-storage.com/sample_key.txt',
                'downloadUrl': 'https://store.public.blob.vercel-storage.com/sample_key.txt?download=1',
                'pathname': 'sample_key.txt'
            }
            
            file_data = b'Hello Vercel Blob'
            upload = UploadFile(filename='sample.txt', file=BytesIO(file_data))
            
            key, size = await save_upload(upload)
            assert size == len(file_data)
            assert is_blob_url(key)
            assert key == 'https://store.public.blob.vercel-storage.com/sample_key.txt'
            mock_put.assert_called_once()

def test_remove_blob():
    with patch.object(settings, 'BLOB_READ_WRITE_TOKEN', 'vercel_blob_rw_dummy_token'):
        with patch('vercel_blob.delete') as mock_delete:
            blob_url = 'https://store.public.blob.vercel-storage.com/file_to_delete.txt'
            remove(blob_url)
            mock_delete.assert_called_once_with(
                blob_url,
                options={'token': 'vercel_blob_rw_dummy_token'}
            )
