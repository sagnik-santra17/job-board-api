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

# ------ Registration failures ------
@pytest.mark.asyncio
async def test_register_duplicate_username_fail(client: AsyncClient):
    """Sad: Username already taken -> 409 Conflict."""
    pass  # TODO: create user, register again with same username, assert 409

@pytest.mark.asyncio
async def test_register_duplicate_email_fail(client: AsyncClient):
    """Sad: Email already taken -> 409 Conflict."""
    pass  # TODO: create user, register again with same email, assert 409

@pytest.mark.asyncio
async def test_register_password_mismatch_fail(client: AsyncClient):
    """Sad: Password and confirm_password differ -> 422 Unprocessable Entity."""
    pass  # TODO: send mismatched passwords, assert 422

@pytest.mark.asyncio
async def test_register_short_password_fail(client: AsyncClient):
    """Sad: Password < 8 characters -> 422."""
    pass  # TODO: send password length 6, assert 422

@pytest.mark.asyncio
async def test_register_missing_required_fields_fail(client: AsyncClient):
    """Sad: Missing username/email/password -> 422."""
    pass  # TODO: omit a required field, assert 422

@pytest.mark.asyncio
async def test_register_invalid_email_fail(client: AsyncClient):
    """Sad: Invalid email format -> 422."""
    pass  # TODO: send "notanemail", assert 422

# ------ Login failures ------
@pytest.mark.asyncio
async def test_login_wrong_username_fail(client: AsyncClient):
    """Sad: Non-existent username -> 401 Unauthorized."""
    pass  # TODO: login with wrong username, assert 401

@pytest.mark.asyncio
async def test_login_wrong_password_fail(client: AsyncClient):
    """Sad: Incorrect password -> 401."""
    pass  # TODO: create user, login with wrong password, assert 401

@pytest.mark.asyncio
async def test_login_empty_credentials_fail(client: AsyncClient):
    """Sad: Empty username or password -> 422 (OAuth2 form validation)."""
    pass  # TODO: send empty fields, assert 422

# ------ Protected route failures (authentication required) ------
@pytest.mark.asyncio
async def test_get_profile_unauthenticated_fail(client: AsyncClient):
    """Sad: No token -> 401."""
    pass  # TODO: GET /users/me without token, assert 401

@pytest.mark.asyncio
async def test_update_profile_unauthenticated_fail(client: AsyncClient):
    """Sad: No token -> 401."""
    pass  # TODO: PATCH /users/me without token, assert 401

@pytest.mark.asyncio
async def test_delete_account_unauthenticated_fail(client: AsyncClient):
    """Sad: No token -> 401."""
    pass  # TODO: DELETE /users/me without token, assert 401

@pytest.mark.asyncio
async def test_update_profile_wrong_current_password_fail(client: AsyncClient):
    """Sad: Valid token but wrong current_password -> 401."""
    pass  # TODO: create user, login, PATCH with wrong current_password, assert 401

@pytest.mark.asyncio
async def test_delete_account_wrong_password_fail(client: AsyncClient):
    """Sad: Valid token but wrong password -> 401."""
    pass  # TODO: create user, login, DELETE with wrong password, assert 401

@pytest.mark.asyncio
async def test_update_profile_duplicate_username_fail(client: AsyncClient):
    """Sad: Changing username to one already taken by another user -> 409."""
    pass  # TODO: create user A and B, login as B, try to update to A's username, assert 409

@pytest.mark.asyncio
async def test_update_profile_duplicate_email_fail(client: AsyncClient):
    """Sad: Changing email to one already taken -> 409."""
    pass  # TODO: similar to above, assert 409

# ------ Edge cases for role validation (not enforced yet) ------
# If you add role validation in the future, test invalid role values.

# ------ Inactive user (if you later implement is_active logic) ------
# Test login with inactive user should fail (401).