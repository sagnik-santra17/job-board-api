from httpx import AsyncClient


# ---------------------------------------------------------------------------------------------------------------- #


#------------------Test helpers for user module-----------------#

#----helper function for user login-------#
async def get_token_from_logged_user(client: AsyncClient, username: str="test_user") -> dict:
    
    user_data = {
        "username": username,
        "full_name": "Test User",
        "email": f"{username}@email.com",
        "password": "test_password123",
        "confirm_password": "test_password123",
        "role": "employee",
        "is_active": True
    }

    await client.post("/users/", json=user_data)

    login_credentials = {
        "username": username,
        "password": "test_password123"
    }

    login_response = await client.post("/users/login", data=login_credentials)
    token_data = login_response.json()

    access_token = token_data["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


#------------------ Test helpers for user id -----------------#
async def get_user_id(client: AsyncClient, username: str="test_user") -> dict:
    
    user_data = {
        "username": username,
        "full_name": "Test User",
        "email": f"{username}@email.com",
        "password": "test_password123",
        "confirm_password": "test_password123",
        "role": "employee",
        "is_active": True
    }

    signup_response = await client.post("/users/", json=user_data)
    signup_data = signup_response.json()
    user_id = signup_data["user_id"]

    login_credentials = {
        "username": username,
        "password": "test_password123"
    }

    login_response = await client.post("/users/login", data=login_credentials)
    token_data = login_response.json()
    access_token = token_data["access_token"]

    return {
        "Authorization": f"Bearer {access_token}",
        "user_id": user_id
    }