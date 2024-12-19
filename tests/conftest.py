import pytest
from fastapi.testclient import TestClient
from config.database import get_db, Base
from app.main import app
from config.models import User,File
from Users.auth import create_jwt_token
from tests.database import TestingSessionLocal, engine
from datetime import datetime

UPLOAD_DIRECTORY='static/documents'

@pytest.fixture()
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture()
def client(session):
    def override_get_db():
        try:
            yield session
        finally:
            session.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)

@pytest.fixture()
def test_client_user(client):
    user_data = {"email": "client@test.com", "password": "password", "role": "CLIENT"}
    res = client.post("/signup", json=user_data)
    new_user = res.json()
    assert res.status_code == 201


    user_id = new_user['id']
    verify_res = client.get(f"/verify-email/{user_id}")
    assert verify_res.status_code == 200
    assert verify_res.json()["email_verified"] is True

    return new_user
@pytest.fixture()
def test_unverified_client_user(client):
    user_data = {"email": "client@test.com", "password": "password", "role": "CLIENT"}
    res = client.post("/signup", json=user_data)
    new_user = res.json()
    assert res.status_code == 201
    return new_user

@pytest.fixture()
def test_ops_user(client):
    user_data = {"email": "ops@test.com", "password": "password", "role": "OPS"}
    res = client.post("/signup/", json=user_data)
    new_user = res.json()
    assert res.status_code == 201

    # Verify the user's email automatically
    user_id = new_user['id']
    verify_res = client.get(f"/verify-email/{user_id}")
    assert verify_res.status_code == 200
    assert verify_res.json()["email_verified"] is True

    return new_user

@pytest.fixture()
def client_token(test_client_user):
    token = create_jwt_token({"sub": str(test_client_user['id'])})

    return token

@pytest.fixture()
def ops_token(test_ops_user):
    token = create_jwt_token({"sub": str(test_ops_user['id'])})
    return token

@pytest.fixture()
def authorized_client(client, client_token):
    client.headers.update({
        "Authorization": f"Bearer {client_token['access_token']}"
    })
    return client

@pytest.fixture()
def authorized_ops(client, ops_token):
    client.headers.update({
        "Authorization": f"Bearer {ops_token['access_token']}"
    })
    return client

@pytest.fixture()
def test_file(test_ops_user,session):
    test_file = File(
        filename="test.xlsx",
        file_path=f"{UPLOAD_DIRECTORY}/test.xlsx",
        uploaded_by=test_ops_user['id'],
        uploaded_at=datetime.utcnow(),
    )
    session.add(test_file)
    session.commit()
    session.refresh(test_file)
    session.close()
    print(test_file)
    return test_file

@pytest.fixture()
def test_secure_link(authorized_client,test_file):
    res = authorized_client.get(f'files/{test_file.id}/generate-secure-link')
    generated_url = res.json()
    assert res.status_code ==200
    assert generated_url['message']=="success"
    return generated_url
