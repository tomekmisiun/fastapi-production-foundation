def test_register(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["is_active"] is True


def test_register_duplicate_email(client):
    payload = {
        "email": "test@example.com",
        "password": "password123",
    }

    client.post("/auth/register", json=payload)
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 400


def test_login(client):
    client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_me(client):
    client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["is_active"] is True


def test_me_unauthorized(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_refresh_token(client):
    register_data = {
        "email": "test@example.com",
        "password": "password123",
    }

    client.post("/auth/register", json=register_data)

    login_response = client.post(
        "/auth/login",
        json=register_data,
    )

    refresh_token = login_response.json()["refresh_token"]

    response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_refresh_with_access_token(client):
    register_data = {
        "email": "test2@example.com",
        "password": "password123",
    }

    client.post("/auth/register", json=register_data)

    login_response = client.post(
        "/auth/login",
        json=register_data,
    )

    access_token = login_response.json()["access_token"]

    response = client.post(
        "/auth/refresh",
        json={"refresh_token": access_token},
    )

    assert response.status_code == 401


def test_refresh_with_invalid_token(client):
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "invalid-token"},
    )

    assert response.status_code == 401