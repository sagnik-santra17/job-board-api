import pytest
from httpx import AsyncClient


from tests.test_helper import get_token_from_logged_user


# ----------------------------------------------------------------------------
# HAPPY TESTS (Everything works as expected)
# ----------------------------------------------------------------------------

# ------ User registration (201 Created) ------
@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):

    user_data = {
    "username": "test_user",
    "full_name": "Test User",
    "email": "test_user@email.com",
    "password": "test_password123",
    "confirm_password": "test_password123",
    "role": "employee",           
    "is_active": True,             
}

    response = await client.post("/users/", json=user_data)
    assert response.status_code == 201

    data = response.json()
    assert data["username"] == "test_user"
    assert data["email"] == "test_user@email.com"
    assert data["is_active"] is True
    assert "user_id" in data
    assert "password" not in data


# ------ User login (200 OK) ------
@pytest.mark.asyncio
async def test_user_login_success(client: AsyncClient):

    user_data = {
        "username": "test_user",
        "full_name": "Test User",
        "email": "test_user@email.com",
        "password": "test_password123",
        "confirm_password": "test_password123",
        "role": "employee",           
        "is_active": True,             
    }

    await client.post("/users/", json=user_data)

    login_credentials = {
        "username": "test_user", 
        "password": "test_password123"
    }

    response = await client.post("/users/login", data=login_credentials)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data


# ------ Get own profile (200 OK) ------
@pytest.mark.asyncio
async def test_get_profile_success(client: AsyncClient):
    
    header = await get_token_from_logged_user(client)

    response = await client.get("/users/me", headers=header)
    assert response.status_code == 200

    data = response.json()
    assert data["username"] == "test_user"
    assert data["email"] == "test_user@email.com"
    assert "user_id" in data


# ------ Update own profile (200 OK) ------
@pytest.mark.asyncio
async def test_update_profile_success(client: AsyncClient):
    
    header = await get_token_from_logged_user(client)
    
    update_data = {
        "username": "test_user1",
        "email": "test_user1@email.com",
        "password": "new_test_password123",
        "confirm_password": "new_test_password123",
        "current_password": "test_password123",
    }

    response = await client.patch(
        "/users/me", 
        json=update_data, 
        headers=header
    )

    assert response.status_code == 200

    data = response.json()
    assert data["username"] == "test_user1"
    assert data["email"] == "test_user1@email.com"
    assert "password" not in data


# ------ Delete own account (200 OK) ------
@pytest.mark.asyncio
async def test_user_delete_user_success(client):

    headers = await get_token_from_logged_user(client)

    delete_data = {"password": "test_password123"}

    response = await client.request(
        "DELETE",
        "/users/me", 
        headers=headers, 
        json=delete_data
    )

    assert response.status_code == 200
    assert response.json() == {"detail": "User account deleted successfully"}


# ------ Login after profile update (still works) ------
@pytest.mark.asyncio
async def test_login_after_update_success(client: AsyncClient):
    
    header = await get_token_from_logged_user(client)
    
    update_data = {
        "username": "test_user1",
        "email": "test_user1@email.com",
        "password": "new_test_password123",
        "confirm_password": "new_test_password123",
        "current_password": "test_password123",
    }

    await client.patch(
        "/users/me", 
        json=update_data, 
        headers=header
    )

    login_credentials = {
        "username": "test_user1", 
        "password": "new_test_password123"
    }

    response = await client.post("/users/login", data=login_credentials)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data



# ----------------------------------------------------------------------------
# SAD TESTS (Failures and edge cases)
# ----------------------------------------------------------------------------

# ------ Registration failures (Sad: Username already taken -> 409 Conflict) ------
@pytest.mark.asyncio
async def test_username_exists_fail(client):

    await get_token_from_logged_user(client)

    user_data = {
        "username": "test_user",
        "full_name": "Test User",
        "email": "test_user@email.com",
        "password": "test_password123",
        "confirm_password": "test_password123",
        "role": "employee",           
        "is_active": True,             
    }

    response = await client.post("/users/", json=user_data)
    assert response.status_code == 409

    error_message = response.json()["detail"]
    assert "User with username test_user already exists" in error_message


# ------- Sad: Email already taken -> 409 Conflict ------
@pytest.mark.asyncio
async def test_register_duplicate_email_fail(client: AsyncClient):
    
    await get_token_from_logged_user(client)  

    user_data = {
        "username": "test_user_email_dup",  
        "full_name": "Test User",
        "email": "test_user@email.com",     
        "password": "test_password123",
        "confirm_password": "test_password123",
        "role": "employee",
        "is_active": True,
    }

    response = await client.post("/users/", json=user_data)
    assert response.status_code == 409

    assert response.json()["detail"] == "User with email test_user@email.com already exists"
     

# -------- Sad: Password and confirm_password differ -> 422 Unprocessable Entity ------
@pytest.mark.asyncio
async def test_register_password_mismatch_fail(client: AsyncClient):
    
    user_data = {
        "username": "test_user",
        "full_name": "Test User",
        "email": "test_user@email.com",
        "password": "test_password123",
        "confirm_password": "test_password456",
        "role": "employee",           
        "is_active": True,             
    }

    response = await client.post("/users/", json=user_data)
    assert response.status_code == 422

    error_message = response.json()["detail"][0]["msg"]
    assert "Passwords don't match" in error_message


# ------ Sad: Password < 8 characters -> 422 -------
@pytest.mark.asyncio
async def test_register_short_password_fail(client: AsyncClient):
    
    user_data = {
        "username": "test_user",
        "full_name": "Test User",
        "email": "test_user@email.com",
        "password": "test123",
        "confirm_password": "test123",
        "role": "employee",           
        "is_active": True,             
    }

    response = await client.post("/users/", json=user_data)
    assert response.status_code == 422

    error_message = response.json()["detail"][0]["msg"]
    assert "String should have at least 8 characters" in error_message


# ------ Sad: Missing username/email/password -> 422 ------
@pytest.mark.asyncio
async def test_register_missing_required_fields_fail(client: AsyncClient):
    
    user_data = {
        "full_name": "Test User",
        "email": "test_user@email.com",
        "password": "test_password123",
        "confirm_password": "test_password123",
        "role": "employee",           
        "is_active": True,             
    }

    response = await client.post("/users/", json=user_data)
    assert response.status_code == 422

    error_message = response.json()["detail"][0]["msg"]
    assert "Field required" in error_message


# ------ Sad: Invalid email format -> 422 ----
@pytest.mark.asyncio
async def test_register_invalid_email_fail(client: AsyncClient):
    
    user_data = {
        "username": "test_user",
        "full_name": "Test User",
        "email": "invalid email",
        "password": "test_password123",
        "confirm_password": "test_password123",
        "role": "employee",           
        "is_active": True,             
    }

    response = await client.post("/users/", json=user_data)
    assert response.status_code == 422

    error_message = response.json()["detail"][0]["msg"]
    assert "An email address must have an @-sign." in error_message


# ------ Login failures - Sad: Non-existent username -> 401 Unauthorized ------
@pytest.mark.asyncio
async def test_login_wrong_username_fail(client: AsyncClient):
    
    login_credentials = {
        "username": "wrong_username",
        "password": "test_password123"
    }

    response = await client.post("/users/login", data=login_credentials)
    assert response.status_code == 401

    assert response.json()["detail"] == "Incorrect username or password"


# ------- Sad: Incorrect password -> 401 ----------
@pytest.mark.asyncio
async def test_login_wrong_password_fail(client: AsyncClient):
    
    login_credentials = {
        "username": "test_user",
        "password": "wrong_password"
    }

    response = await client.post("/users/login", data=login_credentials)
    assert response.status_code == 401

    assert response.json()["detail"] == "Incorrect username or password"


# ----- Sad: Empty username or password -> 422 (OAuth2 form validation) ----
@pytest.mark.asyncio
async def test_login_empty_credentials_fail(client: AsyncClient):
    
    login_credentials = {
        "username": "",
        "password": ""
    }

    response = await client.post("/users/login", data=login_credentials)
    assert response.status_code == 422

    error_message = response.json()["detail"][0]["msg"]
    assert "Field required" in error_message


# ------ Protected route failures (authentication required) - Sad: No token -> 401 ------
@pytest.mark.asyncio
async def test_get_profile_unauthenticated_fail(client: AsyncClient):
    
    response = await client.get("/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


# ------ Sad: No token -> 401 -----
@pytest.mark.asyncio
async def test_update_profile_unauthenticated_fail(client: AsyncClient):
    
    response = await client.patch("/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


# ---- Sad: No token -> 401 ----
@pytest.mark.asyncio
async def test_delete_account_unauthenticated_fail(client: AsyncClient):
    
    response = await client.delete("/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


# ------ Sad: Valid token but wrong current_password -> 401 ------
@pytest.mark.asyncio
async def test_update_profile_wrong_current_password_fail(client: AsyncClient):
    
    header = await get_token_from_logged_user(client)
    
    update_data = {
        "username": "test_user1",
        "email": "test_user1@email.com",
        "password": "new_test_password123",
        "confirm_password": "new_test_password123",
        "current_password": "wrong_password",
    }

    response = await client.patch(
        "/users/me", 
        json=update_data, 
        headers=header
    )

    assert response.status_code == 401

    assert response.json()["detail"] == "Incorrect current password."


# -------- Sad: Valid token but wrong password -> 401 -------
@pytest.mark.asyncio
async def test_delete_account_wrong_password_fail(client: AsyncClient):
    
    header = await get_token_from_logged_user(client)
    
    delete_data = {
        "password": "wrong_password",
    }

    response = await client.request(
        "DELETE",
        "/users/me",
        json=delete_data,
        headers=header
    )

    assert response.status_code == 401

    assert "Incorrect password" in response.json()["detail"]


# -------- Sad: Changing username to one already taken by another user -> 409 -------
@pytest.mark.asyncio
async def test_update_profile_duplicate_username_fail(client: AsyncClient):
    
    await get_token_from_logged_user(client, username="test_user_a")

    header_b = await get_token_from_logged_user(client, username="test_user_b")

    update_data = {
        "username": "test_user_a",
        "current_password": "test_password123",
    }

    response = await client.patch(
        "/users/me", 
        json=update_data, 
        headers=header_b
    )

    assert response.status_code == 409

    assert "User already exists with username" in response.json()["detail"]


# --------- Sad: Changing email to one already taken -> 409 -----------
@pytest.mark.asyncio
async def test_update_profile_duplicate_email_fail(client: AsyncClient):
    
    await get_token_from_logged_user(client)

    header_b = await get_token_from_logged_user(client, username="test_user_b")

    update_data = {
        "email": "test_user@email.com",
        "current_password": "test_password123",
    }

    response = await client.patch(
        "/users/me", 
        json=update_data, 
        headers=header_b
    )

    assert response.status_code == 409

    assert "User already exists with email" in response.json()["detail"]