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



# --------- Create a job helper function --------------- #
import uuid
from httpx import AsyncClient

async def create_test_job(
    client: AsyncClient,
    company_id: int,
    headers: dict = None, # -> Optional: use existing token
    title: str = "Software Engineer",
    description: str = "This is a test job with at least fifty characters. More text here to reach the minimum length.",
    location: str = "San Francisco, CA",
    salary_range: str = "100000-200000"
) -> dict:
    
    """
    Create a test job under a given company.

    Args:
        client: The HTTP client.
        company_id: The ID of the company to attach the job to.
        headers: Optional dict with Authorization header. If not provided, a new manager is created.
        title: Job title (default: "Software Engineer").
        description: Job description (must be at least 50 chars).
        location: Job location.
        salary_range: Salary range (e.g., "100000-200000").

    Returns:
        dict: Contains 'headers' (used for the request), 'job' (the created job data), and 'job_id'.
    """
    # If no headers were provided, create a new manager user and get its token
    if headers is None:
        unique = uuid.uuid4().hex[:8]
        manager_username = f"manager_{unique}"
        headers = await get_token_from_logged_user(client, username=manager_username, role="manager")
    
    # Generate a unique title if it's the default (to avoid conflicts across tests)
    if title == "Software Engineer":
        title = f"Software Engineer {uuid.uuid4().hex[:6]}"

    # Prepare the job data (matches the JobCreate schema)
    job_data = {
        "title": title,
        "description": description,
        "location": location,
        "salary_range": salary_range
    }

    # Send the request
    response = await client.post(
        f"/companies/{company_id}/jobs/",
        json=job_data,
        headers=headers
    )
    # Raise an error if creation failed, so the test fails early
    assert response.status_code == 201, f"Job creation failed: {response.text}"

    job = response.json()
    return {
        "headers": headers,          # the headers used (either provided or new)
        "job": job,
        "job_id": job["job_id"]
    }



# --------- Create an employee user helper --------------- #
async def create_test_employee_user(
    client: AsyncClient,
    username: str = None
) -> dict:
    """Create an employee user and return the Authorization header."""
    if username is None:
        username = f"employee_{uuid.uuid4().hex[:8]}"

    header = await get_token_from_logged_user(client, username=username, role="employee")
    return header


# --------- Create an application helper --------------- #
async def create_test_application(
    client: AsyncClient,
    job_id: int,
    employee_headers: dict = None,
    cover_letter: str = "I am very interested in this position. Please consider my application."
) -> dict:
    
    if employee_headers is None:
        employee_headers = await create_test_employee_user(client)
    
    application_data = {"cover_letter": cover_letter}

    response = await client.post(
        f"/jobs/{job_id}/applications/",
        json=application_data,
        headers=employee_headers
    )

    assert response.status_code == 201  
    application = response.json()

    return {
        "headers": employee_headers,
        "application": application,
        "application_id": application["application_id"]
    }