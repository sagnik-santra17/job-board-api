import uuid
from httpx import AsyncClient


# ---------------------------------------------------------------------------------------------------------------- #


#------------------Test helpers for user module-----------------#

#----helper function for user login-------#
async def get_token_from_logged_user(
    client: AsyncClient, 
    username: str=None,
    role: str="employee"
) -> dict:
    
    # ALWAYS generate unique usernames
    if username is None:
        unique = uuid.uuid4().hex[:8]
        username = f"test_user_{unique}"

    user_data = {
        "username": username,
        "full_name": "Test User",
        "email": f"{username}@email.com",
        "password": "test_password123",
        "confirm_password": "test_password123",
        "role": role,
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
    
    return {
        "Authorization": f"Bearer {access_token}",
        "username": username # -> returns a unique username
    } 


#------------------ Test helpers for user id -----------------#
async def get_user_id(
    client: AsyncClient, 
    username: str="test_user",
    role: str="employee"
) -> dict:
    
    user_data = {
        "username": username,
        "full_name": "Test User",
        "email": f"{username}@email.com",
        "password": "test_password123",
        "confirm_password": "test_password123",
        "role": role,
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



# --------- Create a company helper function --------------- #
async def create_test_company(
    client: AsyncClient, 
    manager_username: str = "manager_user",
    company_name: str = "Test Company",
    company_email: str = None
) -> dict:
    
     # ALWAYS generate unique values – don't use what's passed
    unique_id = uuid.uuid4().hex[:8]
    manager_username = f"manager_{unique_id}"
    company_name = f"Test Company {uuid.uuid4().hex[:6]}"
    company_email = f"test_{uuid.uuid4().hex[:8]}@email.com"
    
    # Get manager token
    header = await get_token_from_logged_user(client, username=manager_username, role="manager")

    # Add company data (passing the default values)
    company_data = {
        "company_name": company_name,
        "company_email": company_email,
        "company_phone": "+14155552671",
        "company_address": "456 Oak St",
        "company_website": "https://example.com/",
        "company_description": "This is a test company with at least fifty characters. More text here to reach the minimum length."
    }

    # Create company    
    response = await client.post("/companies/", json=company_data, headers=header)
    company = response.json()
    
    return {
        "headers": header,
        "company": company,
        "company_id": company["company_id"]
    }
