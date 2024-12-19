def test_signup(client):
    response = client.post(
        "/signup",
        json={
            "email": "newuser@example.com",
            "password": "securepassword",
            "role": "CLIENT"
        },
    )
    assert response.status_code == 201
    assert response.json()["email"] == "newuser@example.com"

def test_verify_email(client,test_unverified_client_user):
    response = client.get(f"/verify-email/{test_unverified_client_user['id']}")
    assert response.status_code == 200
    assert response.json()["email_verified"] is True

# Test login endpoint
def test_login(client,test_client_user):
    response = client.post(
        "/login",
        json={"email": test_client_user['email'], "password": 'password'},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_unverified_user(client,test_unverified_client_user):
    response = client.post(
        "/login",
        json={"email": test_unverified_client_user['email'], "password": "password"},
    )
    print(f" UNVERIFIED USER LOGIN RES : {response.json()}")
    assert response.status_code == 400
    assert response.json()["detail"] == "User account is not verified"

def test_login_invalid_credentials(client):
    response = client.post(
        "/login",
        json={"email": "nonexistent@example.com", "password": "wrongpassword"},
    )
    print(f"INVALID CREDS RESPONSE : {response.json()}")
    # assert response.status_code == 400
    assert response.json()["detail"] == "Invalid credentials"