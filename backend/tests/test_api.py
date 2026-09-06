import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.core.db import Base, engine, SessionLocal
from app.models.models import User, File, Folder, LinkShare

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture
def client():
    return TestClient(app)

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok', 'service': 'clouddrive-api'}

def test_auth_and_files_workflow(client):
    # 1. Register a user
    import uuid
    random_email = f'user_{uuid.uuid4().hex[:8]}@example.com'
    register_res = client.post('/auth/register', json={
        'name': 'Test User',
        'email': random_email,
        'password': 'password123'
    })
    assert register_res.status_code == 200
    assert register_res.json()['email'] == random_email

    # Verify cookies set
    assert 'access_token' in client.cookies

    # 2. Check /auth/me
    me_res = client.get('/auth/me')
    assert me_res.status_code == 200
    assert me_res.json()['email'] == random_email

    # 3. Create folder
    folder_res = client.post('/folders', json={'name': 'Documents', 'parent_id': None})
    assert folder_res.status_code == 200
    folder_id = folder_res.json()['id']

    # 4. Upload file with Vercel Blob mock
    with patch('app.services.storage.settings.BLOB_READ_WRITE_TOKEN', 'dummy_token'):
        with patch('vercel_blob.put') as mock_put:
            mock_put.return_value = {
                'url': 'https://mockstore.public.blob.vercel-storage.com/uploaded_file.txt',
                'downloadUrl': 'https://mockstore.public.blob.vercel-storage.com/uploaded_file.txt?download=1',
                'pathname': 'uploaded_file.txt'
            }

            upload_res = client.post(
                '/files/upload',
                params={'folder_id': folder_id},
                files={'file': ('document.txt', b'Hello CloudDrive Blob!', 'text/plain')}
            )
            assert upload_res.status_code == 200
            file_data = upload_res.json()
            assert file_data['name'] == 'document.txt'
            file_id = file_data['id']

    # 5. List files
    list_res = client.get('/files', params={'folder_id': folder_id})
    assert list_res.status_code == 200
    files = list_res.json()
    assert len(files) >= 1
    assert any(f['id'] == file_id for f in files)

    # 6. Download file (streamed via backend)
    with patch("httpx.AsyncClient") as mock_httpx_cls:
        mock_client = MagicMock()
        mock_httpx_cls.return_value.__aenter__.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        async def mock_aiter_bytes(chunk_size=65536):
            yield b"Hello CloudDrive Blob!"
        mock_resp.aiter_bytes = mock_aiter_bytes
        mock_client.stream.return_value.__aenter__.return_value = mock_resp

        download_res = client.get(f'/files/{file_id}/download')
        assert download_res.status_code == 200
        assert download_res.content == b'Hello CloudDrive Blob!'

    # 7. Rename & Move File/Folder
    rename_f_res = client.patch(f'/files/{file_id}', json={'name': 'renamed_doc.txt'})
    assert rename_f_res.status_code == 200
    assert rename_f_res.json()['name'] == 'renamed_doc.txt'

    rename_folder_res = client.patch(f'/folders/{folder_id}', json={'name': 'Renamed Folder'})
    assert rename_folder_res.status_code == 200
    assert rename_folder_res.json()['name'] == 'Renamed Folder'

    # 8. Check Activities API
    act_res = client.get('/activities')
    assert act_res.status_code == 200
    activities = act_res.json()
    assert len(activities) >= 1

    # 9. Create public share link
    link_res = client.post('/public-link', json={'file_id': file_id})
    assert link_res.status_code == 200
    token = link_res.json()['token']

    # 10. Access public share link (unauthenticated client)
    unauth_client = TestClient(app)
    with patch("httpx.AsyncClient") as mock_httpx_cls:
        mock_client = MagicMock()
        mock_httpx_cls.return_value.__aenter__.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        async def mock_aiter_bytes(chunk_size=65536):
            yield b"Hello CloudDrive Blob!"
        mock_resp.aiter_bytes = mock_aiter_bytes
        mock_client.stream.return_value.__aenter__.return_value = mock_resp

        pub_res = unauth_client.get(f'/public/{token}')
        assert pub_res.status_code == 200

    # 11. Star file
    star_res = client.post(f'/files/{file_id}/star')
    assert star_res.status_code == 200
    assert star_res.json()['starred'] is True

    # 12. Soft delete / Trash file
    del_res = client.delete(f'/files/{file_id}')
    assert del_res.status_code == 200

    # 13. Permanent delete
    with patch('app.services.storage.settings.BLOB_READ_WRITE_TOKEN', 'dummy_token'):
        with patch('vercel_blob.delete') as mock_delete:
            perm_del = client.delete(f'/files/{file_id}', params={'permanent': True})
            assert perm_del.status_code == 200
            mock_delete.assert_called_once()

def test_user_to_user_sharing(client):
    import uuid
    email_a = f'user_a_{uuid.uuid4().hex[:8]}@example.com'
    email_b = f'user_b_{uuid.uuid4().hex[:8]}@example.com'

    client_a = TestClient(app)
    client_b = TestClient(app)

    reg_a = client_a.post('/auth/register', json={'name': 'User A', 'email': email_a, 'password': 'password123'})
    assert reg_a.status_code == 200

    reg_b = client_b.post('/auth/register', json={'name': 'User B', 'email': email_b, 'password': 'password123'})
    assert reg_b.status_code == 200

    # 2. User A uploads a file
    upload_res = client_a.post('/files/upload', files={'file': ('shared_doc.pdf', b'PDF Content', 'application/pdf')})
    assert upload_res.status_code == 200
    file_id = upload_res.json()['id']

    # 3. User A shares file with User B as viewer
    share_res = client_a.post('/shares', json={'file_id': file_id, 'email': email_b, 'role': 'viewer'})
    assert share_res.status_code == 200
    assert share_res.json()['ok'] is True

    # 4. User B checks shared view
    shared_res = client_b.get('/files', params={'view': 'shared'})
    assert shared_res.status_code == 200
    shared_files = shared_res.json()
    assert len(shared_files) == 1
    assert shared_files[0]['id'] == file_id
    assert shared_files[0]['name'] == 'shared_doc.pdf'

    # 5. User B downloads the shared file
    dl_res = client_b.get(f'/files/{file_id}/download')
    assert dl_res.status_code == 200
    assert dl_res.content == b'PDF Content'
