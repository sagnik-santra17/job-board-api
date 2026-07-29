import uuid
import pytest
from httpx import AsyncClient


from tests.test_helper import create_test_company, create_test_job, get_token_from_logged_user

# ----------------------------------------------------------------------------
# HAPPY TESTS (Successful flows)
# ----------------------------------------------------------------------------

# ------ Create Job – manager creates a job under their company ------
@pytest.mark.asyncio
async def test_create_job_success(client: AsyncClient):

    company = await create_test_company(client, company_name="Test Company")
    company_id = company["company_id"]
    header = company["headers"]

    job_data = {
        "title": f"Software Engineer {uuid.uuid4().hex[:6]}",
        "description": "This is a test job with at least fifty characters. More text here to reach the minimum length.",
        "location": "San Francisco, CA",
        "salary_range": "100000-200000"
    }

    response = await client.post(
        f"/companies/{company_id}/jobs/", 
        json=job_data,
        headers=header
    )

    assert response.status_code == 201
    data = response.json()

    assert data["title"] == job_data["title"]
    assert data["description"] == job_data["description"]
    assert data["location"] == job_data["location"]
    assert data["salary_range"] == job_data["salary_range"]
    assert data["company_id"] == company_id


# ------ List All Jobs – manager lists jobs of their company ------
@pytest.mark.asyncio
async def test_list_jobs_success(client: AsyncClient):

    # Create company and a job 
    company = await create_test_company(client, company_name="Test Company")
    company_header = company["headers"]
    company_id = company["company_id"]

    job = await create_test_job(client, company_id, company_header)
    job_id = job["job_id"]

    # GET /companies/{company_id}/jobs/
    response = await client.get(f"/companies/{company_id}/jobs/", headers=company_header)
    data = response.json()
    assert response.status_code == 200

    # Loop through jobs and check if job_id is in data
    assert any(j["job_id"] == job_id for j in data)


# ------ Get Single Job – manager fetches a job they own ------
@pytest.mark.asyncio
async def test_get_job_success(client: AsyncClient):
    
    # Create company and a job 
    company = await create_test_company(client, company_name="Test Company")
    company_header = company["headers"]
    company_id = company["company_id"]
    
    job = await create_test_job(client, company_id, company_header)
    job_id = job["job_id"]

    # GET /companies/{company_id}/jobs/
    response = await client.get(f"/companies/{company_id}/jobs/{job_id}", headers=company_header)
    assert response.status_code == 200
    data = response.json()
    
    # Verify the correct job was returned
    assert data["job_id"] == job_id
    assert data["company_id"] == company_id


# ------ Update Job – manager updates own job ------
@pytest.mark.asyncio
async def test_update_job_success(client: AsyncClient):
    
    # Create company and a job (Get the job title because we are updating it)
    company = await create_test_company(client, company_name="Test Company")
    company_header = company["headers"]
    company_id = company["company_id"]
    
    job = await create_test_job(client, company_id, company_header)
    job_id = job["job_id"]
    original_title = job["job"]["title"] # -> Get the original title
    
    # Prepare update data (new title, description, etc.)
    update_data = {
        "title": f"Updated {original_title}", # -> Update the title
        "description": "This is an updated job description with at least fifty characters. More text to reach the minimum.",
        "location": "New York, NY",
        "salary_range": "120000-180000"
    }
    
    # PATCH /companies/{company_id}/jobs/{job_id} with new data
    response = await client.patch(
        f"/companies/{company_id}/jobs/{job_id}",
        json=update_data,
        headers=company_header
    )
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify the updated fields
    assert data["job_id"] == job_id
    assert data["company_id"] == company_id
    assert data["title"] == update_data["title"]
    assert data["description"] == update_data["description"]
    assert data["location"] == update_data["location"]
    assert data["salary_range"] == update_data["salary_range"]


# ------ Delete Job – manager deletes own job ------
@pytest.mark.asyncio
async def test_delete_job_success(client: AsyncClient):
    
    # Create company and a job
    company = await create_test_company(client, company_name="Test Company")
    company_header = company["headers"]
    company_id = company["company_id"]
    
    job = await create_test_job(client, company_id, company_header)
    job_id = job["job_id"]
    
    # DELETE /companies/{company_id}/jobs/{job_id}
    response = await client.delete(
        f"/companies/{company_id}/jobs/{job_id}",
        headers=company_header
    )

    assert response.status_code == 200
    
    # Verify the success message
    data = response.json()
    assert data["message"] == "job deleted successfully"
    

# ----------------------------------------------------------------------------
# SAD TESTS (Failure flows)
# ----------------------------------------------------------------------------

# ------ Authentication & Authorization ------

# ------ Create job without token ------
@pytest.mark.asyncio
async def test_create_job_without_token_fail(client: AsyncClient):
    
    # Create a company to get a valid company_id
    company = await create_test_company(client, company_name="Test Company")
    company_id = company["company_id"]
    
    # Prepare job data (doesn't matter what, as it won't reach validation)
    job_data = {
        "title": "Software Engineer",
        "description": "This is a test job with at least fifty characters. More text here to reach the minimum length.",
        "location": "San Francisco, CA",
        "salary_range": "100000-200000"
    }
    
    # POST without any Authorization header
    response = await client.post(
        f"/companies/{company_id}/jobs/",
        json=job_data
        # heeaders=no headers -> No authentication header
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


# ------ Create job as employee ------
@pytest.mark.asyncio
async def test_create_job_as_employee_fail(client: AsyncClient):
    
    # Create a company using a manager (we need a valid company_id)
    company = await create_test_company(client, company_name="Test Company")
    company_id = company["company_id"]
    
    # Get a token for an employee (different user, role="employee")
    employee_header = await get_token_from_logged_user(
        client, 
        username=f"employee_{uuid.uuid4().hex[:8]}", 
        role="employee"
    )
    
    # Prepare job data
    job_data = {
        "title": "Software Engineer",
        "description": "This is a test job with at least fifty characters. More text here to reach the minimum length.",
        "location": "San Francisco, CA",
        "salary_range": "100000-200000"
    }
    
    # Attempt to create job with employee token
    response = await client.post(
        f"/companies/{company_id}/jobs/",
        json=job_data,
        headers=employee_header # -> Using the employee's token/header
    )
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Only managers can create jobs"
    

# ------ Create job with invalid token ------
@pytest.mark.asyncio
async def test_create_job_invalid_token_fail(client: AsyncClient):
    
    # Create a company to get a valid company_id (but we won't use its token)
    company = await create_test_company(client, company_name="Test Company")
    company_id = company["company_id"]
    
    # Prepare job data (doesn't matter, as validation will fail before reaching data)
    job_data = {
        "title": "Software Engineer",
        "description": "This is a test job with at least fifty characters. More text here to reach the minimum length.",
        "location": "San Francisco, CA",
        "salary_range": "100000-200000"
    }
    
    # Use a completely malformed token
    invalid_headers = {"Authorization": "Bearer invalid_token_123"}
    
    # Attempt to create job with invalid token
    response = await client.post(
        f"/companies/{company_id}/jobs/",
        json=job_data,
        headers=invalid_headers # -> Usiing an invalid token
    )
    
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


# ------ Ownership & existence failures ------

# ------ Create job for a company that doesn't exist ------
@pytest.mark.asyncio
async def test_create_job_company_not_exist_fail(client: AsyncClient):
    
    # Get a valid manager token
    manager_header = await get_token_from_logged_user(
        client, 
        username=f"manager_{uuid.uuid4().hex[:8]}", 
        role="manager"
    )
    
    # Prepare job data (doesn't matter, as it will fail before validation)
    job_data = {
        "title": "Software Engineer",
        "description": "This is a test job with at least fifty characters. More text here to reach the minimum length.",
        "location": "San Francisco, CA",
        "salary_range": "100000-200000"
    }
    
    # Attempt to create job under a non-existent company ID
    response = await client.post(
        "/companies/999/jobs/", # -> Using a non-existent company ID
        json=job_data,
        headers=manager_header
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Company not found with that company id"


# ------ Create job for a company owned by another manager ------
@pytest.mark.asyncio
async def test_create_job_company_other_manager_fail(client: AsyncClient):
    
    # Create a company with Manager A (using create_test_company)
    company = await create_test_company(client, company_name="Test Company")
    company_id = company["company_id"]
    
    # Get a token for Manager B (a different manager)
    manager_b_username = f"manager_b_{uuid.uuid4().hex[:8]}"
    manager_b_header = await get_token_from_logged_user(
        client,
        username=manager_b_username,
        role="manager"
    )
    
    # Prepare job data
    job_data = {
        "title": "Software Engineer",
        "description": "This is a test job with at least fifty characters. More text here to reach the minimum length.",
        "location": "San Francisco, CA",
        "salary_range": "100000-200000"
    }
    
    # Attempt to create job with Manager B's token
    response = await client.post(
        f"/companies/{company_id}/jobs/",
        json=job_data,
        headers=manager_b_header
    )
    
    # Assert 401 Unauthorized
    assert response.status_code == 401
    assert response.json()["detail"] == "You are not authorized to access this company."


# ------ Duplicate job title within same company ------
@pytest.mark.asyncio
async def test_create_job_duplicate_title_fail(client: AsyncClient):
    
    # Create a company
    company = await create_test_company(client, company_name="Test Company")
    company_header = company["headers"]
    company_id = company["company_id"]
    
    # Create first job with a specific title
    unique_title = f"Software Engineer {uuid.uuid4().hex[:6]}"

    await create_test_job(
        client, 
        company_id, 
        company_header, 
        title=unique_title
    )
    
    # Attempt to create a second job with the SAME title
    job_data = {
        "title": unique_title,  # same title as first job
        "description": "This is a duplicate job with at least fifty characters. More text here to reach the minimum length.",
        "location": "San Francisco, CA",
        "salary_range": "100000-200000"
    }
    
    response = await client.post(
        f"/companies/{company_id}/jobs/",
        json=job_data,
        headers=company_header
    )
    
    assert response.status_code == 409
    assert response.json()["detail"] == "Job already exists with title."


# ------ Invalid data for job creation ------
@pytest.mark.asyncio
async def test_create_job_missing_fields_fail(client: AsyncClient):
    
    # Create a company to get a valid company_id and manager token
    company = await create_test_company(client, company_name="Test Company")
    company_header = company["headers"]
    company_id = company["company_id"]
    
    # Prepare job data WITHOUT the title field
    job_data = {
        "description": "This is a test job with at least fifty characters. More text here to reach the minimum length.",
        "location": "San Francisco, CA",
        "salary_range": "100000-200000"
        # title is intentionally not included
    }
    
    # Attempt to create job with missing title
    response = await client.post(
        f"/companies/{company_id}/jobs/",
        json=job_data,
        headers=company_header
    )
    
    assert response.status_code == 422
    errors = response.json()["detail"]

    # Check that the error list contains a missing field error for "title"
    assert any("title" in err["loc"] for err in errors)


# ------ List jobs for a company not owned by manager ------
@pytest.mark.asyncio
async def test_list_jobs_other_company_fail(client: AsyncClient):
    
    # Create a company with Manager A
    company = await create_test_company(client, company_name="Test Company")
    company_id = company["company_id"]
    
    # Get a token for Manager B (a different manager)
    manager_b_username = f"manager_b_{uuid.uuid4().hex[:8]}"
    manager_b_header = await get_token_from_logged_user(
        client,
        username=manager_b_username,
        role="manager"
    )
    
    # Attempt to list jobs with Manager B's token
    response = await client.get(
        f"/companies/{company_id}/jobs/",
        headers=manager_b_header
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "You are not authorized to access this company."


# ------ Get non-existent job ------
@pytest.mark.asyncio
async def test_get_job_not_exist_fail(client: AsyncClient):
    
    # Create a company to get a valid company_id and manager token
    company = await create_test_company(client, company_name="Test Company")
    company_header = company["headers"]
    company_id = company["company_id"]
    
    # Attempt to fetch a job with a non-existent ID (999)
    response = await client.get(
        f"/companies/{company_id}/jobs/999",
        headers=company_header
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found with that job id"


# ------ Get job from a company not owned by manager ------
@pytest.mark.asyncio
async def test_get_job_other_company_fail(client: AsyncClient):
    
    # Create a company and a job with Manager A
    company = await create_test_company(client, company_name="Test Company")
    company_header = company["headers"]
    company_id = company["company_id"]
    
    job = await create_test_job(client, company_id, company_header)
    job_id = job["job_id"]
    
    # Get a token for Manager B (a different manager)
    manager_b_username = f"manager_b_{uuid.uuid4().hex[:8]}"
    manager_b_header = await get_token_from_logged_user(
        client,
        username=manager_b_username,
        role="manager"
    )
    
    # Attempt to fetch the job with Manager B's token
    response = await client.get(
        f"/companies/{company_id}/jobs/{job_id}",
        headers=manager_b_header
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "You are not authorized to access this company."


# ------ Update non-existent job ------
@pytest.mark.asyncio
async def test_update_job_not_exist_fail(client: AsyncClient):
    
    # Create a company to get a valid company_id and manager token
    company = await create_test_company(client, company_name="Test Company")
    company_header = company["headers"]
    company_id = company["company_id"]
    
    # Prepare update data (doesn't matter, as it will fail before validation)
    update_data = {
        "title": "Updated Title",
        "description": "This is an updated job description with at least fifty characters. More text to reach the minimum.",
        "location": "New York, NY",
        "salary_range": "120000-180000"
    }
    
    # Attempt to update a job with non-existent ID (999)
    response = await client.patch(
        f"/companies/{company_id}/jobs/999",
        json=update_data,
        headers=company_header
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found with that job id"


# ------ Update job from a company not owned ------
@pytest.mark.asyncio
async def test_update_job_other_company_fail(client: AsyncClient):
    
    # Create a company and a job with Manager A
    company = await create_test_company(client, company_name="Test Company")
    company_header = company["headers"]
    company_id = company["company_id"]
    
    job = await create_test_job(client, company_id, company_header)
    job_id = job["job_id"]
    
    # Get a token for Manager B (a different manager)
    manager_b_username = f"manager_b_{uuid.uuid4().hex[:8]}"
    manager_b_header = await get_token_from_logged_user(
        client,
        username=manager_b_username,
        role="manager"
    )
    
    # Prepare update data
    update_data = {
        "title": "Updated Title",
        "description": "This is an updated job description with at least fifty characters. More text to reach the minimum.",
        "location": "New York, NY",
        "salary_range": "120000-180000"
    }
    
    # Attempt to update the job with Manager B's token
    response = await client.patch(
        f"/companies/{company_id}/jobs/{job_id}",
        json=update_data,
        headers=manager_b_header
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "You are not authorized to access this company."


# ------ Update job with duplicate title (within same company) ------
@pytest.mark.asyncio
async def test_update_job_duplicate_title_fail(client: AsyncClient):
    
    # Create a company
    company = await create_test_company(client, company_name="Test Company")
    company_header = company["headers"]
    company_id = company["company_id"]
    
    # Create Job A with a unique title
    title_a = f"Software Engineer {uuid.uuid4().hex[:6]}"
    job_a = await create_test_job(client, company_id, company_header, title=title_a)
    job_a_id = job_a["job_id"]
    
    # Create Job B with a different unique title
    title_b = f"Data Scientist {uuid.uuid4().hex[:6]}"
    await create_test_job(client, company_id, company_header, title=title_b)
    
    # Attempt to update Job A to use Job B's title
    update_data = {"title": title_b}
    response = await client.patch(
        f"/companies/{company_id}/jobs/{job_a_id}",
        json=update_data,
        headers=company_header
    )
    
    assert response.status_code == 409
    assert response.json()["detail"] == "Job already exists with title."


# ------ Update job with invalid data ------
@pytest.mark.asyncio
async def test_update_job_invalid_data_fail(client: AsyncClient):
    """Sad: Send invalid field (e.g., title too short) -> 422."""
    
    # Create a company and a job
    company = await create_test_company(client, company_name="Test Company")
    company_header = company["headers"]
    company_id = company["company_id"]
    
    job = await create_test_job(client, company_id, company_header)
    job_id = job["job_id"]
    
    # Attempt to update with title that is too short (min length is 3)
    update_data = {"title": "ab"}  # less than 3 characters
    response = await client.patch(
        f"/companies/{company_id}/jobs/{job_id}",
        json=update_data,
        headers=company_header
    )
    
    assert response.status_code == 422
    errors = response.json()["detail"]
    # Check that the error relates to the title field and is about string too short
    assert any("title" in err["loc"] for err in errors)
    assert any(err["type"] == "string_too_short" for err in errors)


# ------ Delete non-existent job ------
@pytest.mark.asyncio
async def test_delete_job_not_exist_fail(client: AsyncClient):
    
    # Create a company to get a valid company_id and manager token
    company = await create_test_company(client, company_name="Test Company")
    company_header = company["headers"]
    company_id = company["company_id"]
    
    # Attempt to delete a job with non-existent ID (999)
    response = await client.delete(
        f"/companies/{company_id}/jobs/999",
        headers=company_header
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found with that job id"


# ------ Delete job from a company not owned ------
@pytest.mark.asyncio
async def test_delete_job_other_company_fail(client: AsyncClient):
    
    # Create a company and a job with Manager A
    company = await create_test_company(client, company_name="Test Company")
    company_header = company["headers"]
    company_id = company["company_id"]
    
    job = await create_test_job(client, company_id, company_header)
    job_id = job["job_id"]
    
    # Get a token for Manager B (a different manager)
    manager_b_username = f"manager_b_{uuid.uuid4().hex[:8]}"
    manager_b_header = await get_token_from_logged_user(
        client,
        username=manager_b_username,
        role="manager"
    )
    
    # Attempt to delete the job with Manager B's token
    response = await client.delete(
        f"/companies/{company_id}/jobs/{job_id}",
        headers=manager_b_header
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "You are not authorized to access this company."


# ------ Delete job without token ------
@pytest.mark.asyncio
async def test_delete_job_without_token_fail(client: AsyncClient):
    
    # Create a company and a job (requires authentication)
    company = await create_test_company(client, company_name="Test Company")
    company_header = company["headers"]
    company_id = company["company_id"]
    
    job = await create_test_job(client, company_id, company_header)
    job_id = job["job_id"]
    
    # Attempt to delete the job without sending any Authorization header
    response = await client.delete(
        f"/companies/{company_id}/jobs/{job_id}"
        # no headers
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"