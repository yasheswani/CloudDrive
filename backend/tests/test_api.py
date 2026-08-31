import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
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

    # 6. Download file (redirect to Vercel Blob CDN)
    download_res = client.get(f'/files/{file_id}/download', follow_redirects=False)
    assert download_res.status_code == 307
    assert 'mockstore.public.blob.vercel-storage.com' in download_res.headers['location']

    # 7. Create public share link
    link_res = client.post('/public-link', json={'file_id': file_id})
    assert link_res.status_code == 200
    token = link_res.json()['token']

    # 8. Access public share link (unauthenticated client)
    unauth_client = TestClient(app)
    pub_res = unauth_client.get(f'/public/{token}', follow_redirects=False)
    assert pub_res.status_code == 307
    assert 'mockstore.public.blob.vercel-storage.com' in pub_res.headers['location']

    # 9. Star file
    star_res = client.post(f'/files/{file_id}/star')
    assert star_res.status_code == 200
    assert star_res.json()['starred'] is True

    # 10. Soft delete / Trash file
    del_res = client.delete(f'/files/{file_id}')
    assert del_res.status_code == 200

    # 11. Permanent delete
    with patch('app.services.storage.settings.BLOB_READ_WRITE_TOKEN', 'dummy_token'):
        with patch('vercel_blob.delete') as mock_delete:
            perm_del = client.delete(f'/files/{file_id}', params={'permanent': True})
            assert perm_del.status_code == 200
            mock_delete.assert_called_once()
