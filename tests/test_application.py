import uuid
import pytest
from httpx import AsyncClient


from tests.test_helper import create_test_application, create_test_company, create_test_employee_user, create_test_job, get_token_from_logged_user

# ---------------------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------
# HAPPY TESTS
# ----------------------------------------------------------------------------


# ------ Create application (employee applies to job) ------
@pytest.mark.asyncio
async def test_create_application_success(client: AsyncClient):

    # Create a company and a job (manager needed)
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Get an employee token (creates a new employee user)
    employee_headers = await create_test_employee_user(client)

    # POST the application
    cover_letter = "I am very interested in this position. Please consider my application."
    response = await client.post(
        f"/jobs/{job_id}/applications/",
        json={"cover_letter": cover_letter},
        headers=employee_headers
    )
    assert response.status_code == 201

    # Verify the response
    data = response.json()
    assert data["cover_letter"] == cover_letter
    assert data["status"] == "pending" # -> Default status          
    assert data["job_id"] == job_id
    assert "application_id" in data
    assert "employee_id" in data                
    assert "applied_at" in data
    assert "updated_at" in data


# ------ Get application by ID (employee) ------
@pytest.mark.asyncio
async def test_get_application_by_id_employee_success(client: AsyncClient):

    # Creating a company and a job with a manager
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Creating an application with an employee
    employee_headers = await create_test_employee_user(client)
    application_result = await create_test_application(client, job_id, employee_headers)
    application_id = application_result["application_id"]

    # Getting the application with the same employee token
    response = await client.get(
        f"/jobs/{job_id}/applications/{application_id}",
        headers=employee_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verifying that employee sees only allowed fields (no status, no employee_id)
    assert data["application_id"] == application_id
    assert data["cover_letter"] == application_result["application"]["cover_letter"]
    assert data["job_id"] == job_id
    assert "status" not in data
    assert "employee_id" not in data
    assert "applied_at" in data
    assert "updated_at" in data


# ------ Get application by ID (manager) ------
@pytest.mark.asyncio
async def test_get_application_by_id_manager_success(client: AsyncClient):
    
    # Creating a company and a job with a manager
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Creating an application with an employee
    employee_headers = await create_test_employee_user(client)
    application_result = await create_test_application(client, job_id, employee_headers)
    application_id = application_result["application_id"]

    # Getting the application with the manager token
    response = await client.get(
        f"/jobs/{job_id}/applications/{application_id}",
        headers=manager_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Verifying that manager sees all fields (including status and employee_id)
    assert data["application_id"] == application_id
    assert data["cover_letter"] == application_result["application"]["cover_letter"]
    assert data["job_id"] == job_id
    assert data["status"] == "pending"
    assert data["employee_id"] == application_result["application"]["employee_id"]
    assert "applied_at" in data
    assert "updated_at" in data


# ------ List applications (employee) ------
@pytest.mark.asyncio
async def test_list_applications_employee_success(client: AsyncClient):
    
    # Creating a company and two jobs with a manager
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    # Create first job
    job1 = await create_test_job(client, company_id, headers=manager_headers)
    job1_id = job1["job_id"]

    # Create second job
    job2 = await create_test_job(client, company_id, headers=manager_headers)
    job2_id = job2["job_id"]

    # Creating an employee user and applying to both jobs
    employee_headers = await create_test_employee_user(client)
    app1 = await create_test_application(client, job1_id, employee_headers)
    app2 = await create_test_application(client, job2_id, employee_headers)

    # Listing applications using the GET /jobs/{job_id}/applications/ endpoint
    response = await client.get(
        f"/jobs/{job1_id}/applications/",
        headers=employee_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Assert that the list contains both applications
    assert len(data) == 2
    app_ids = [app["application_id"] for app in data]
    assert app1["application_id"] in app_ids
    assert app2["application_id"] in app_ids

    # Verify that each application has the required fields and no status
    for app in data:
        assert "application_id" in app
        assert "cover_letter" in app
        assert "job_id" in app
        assert "status" not in app
        assert "employee_id" not in app


# ------ List applications (manager) ------
@pytest.mark.asyncio
async def test_list_applications_manager_success(client: AsyncClient):
    
    # Creating a company and two jobs with a manager
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    # Create first job
    job1 = await create_test_job(client, company_id, headers=manager_headers)
    job1_id = job1["job_id"]

    # Create second job
    job2 = await create_test_job(client, company_id, headers=manager_headers)
    job2_id = job2["job_id"]

    # Creating an employee user and applying to both jobs
    employee_headers = await create_test_employee_user(client)
    app1 = await create_test_application(client, job1_id, employee_headers)
    app2 = await create_test_application(client, job2_id, employee_headers)

    # Listing applications using the GET /jobs/{job_id}/applications/ endpoint
    # Using job1_id (the endpoint should return all applications for the manager's jobs, not just for job1)
    response = await client.get(
        f"/jobs/{job1_id}/applications/",
        headers=manager_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Assert that the list contains both applications (since both jobs belong to the same manager)
    assert len(data) == 2
    app_ids = [app["application_id"] for app in data]
    assert app1["application_id"] in app_ids
    assert app2["application_id"] in app_ids

    # Verify that manager sees all fields (status, employee_id present)
    for app in data:
        assert "application_id" in app
        assert "cover_letter" in app
        assert "job_id" in app
        assert "status" in app
        assert "employee_id" in app
        assert "applied_at" in app
        assert "updated_at" in app


# ------ Update application (employee updates cover_letter) ------
@pytest.mark.asyncio
async def test_update_application_employee_success(client: AsyncClient):
    
    # Creating a company and a job with a manager
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Creating an application with an employee
    employee_headers = await create_test_employee_user(client)
    application_result = await create_test_application(client, job_id, employee_headers)
    application_id = application_result["application_id"]

    # New cover_letter
    new_cover_letter = "Updated cover letter with more details about my interest."

    # Patching the application with the new cover_letter
    response = await client.patch(
        f"/jobs/{job_id}/applications/{application_id}",
        json={"cover_letter": new_cover_letter},
        headers=employee_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Verifying that cover_letter was updated
    assert data["cover_letter"] == new_cover_letter
    assert data["application_id"] == application_id
    assert data["job_id"] == job_id
    # Employee response should not contain status or employee_id
    assert "status" not in data
    assert "employee_id" not in data
    assert "applied_at" in data
    assert "updated_at" in data


# ------ Update application (manager updates status) ------
@pytest.mark.asyncio
async def test_update_application_manager_success(client: AsyncClient):
    """Happy: Manager updates only the status (e.g., to accepted) -> 200 OK."""
    
    # Creating a company and a job with a manager
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Creating an application with an employee (cover_letter will be the default)
    employee_headers = await create_test_employee_user(client)
    application_result = await create_test_application(client, job_id, employee_headers)
    application_id = application_result["application_id"]
    original_cover_letter = application_result["application"]["cover_letter"]

    # Manager updates the status to "accepted"
    response = await client.patch(
        f"/jobs/{job_id}/applications/{application_id}",
        json={"status": "accepted"},
        headers=manager_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Verifying that status updated and cover_letter unchanged
    assert data["status"] == "accepted"
    assert data["cover_letter"] == original_cover_letter
    assert data["application_id"] == application_id
    assert data["job_id"] == job_id
    assert data["employee_id"] == application_result["application"]["employee_id"]
    assert "applied_at" in data
    assert "updated_at" in data


# ------ Delete application (employee) ------
@pytest.mark.asyncio
async def test_delete_application_employee_success(client: AsyncClient):
    
    # Creating a company and a job with a manager
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Creating an application with an employee
    employee_headers = await create_test_employee_user(client)
    application_result = await create_test_application(client, job_id, employee_headers)
    application_id = application_result["application_id"]

    # Deleting the application with the employee token
    response = await client.delete(
        f"/jobs/{job_id}/applications/{application_id}",
        headers=employee_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "Application deleted successfully"

    # Optional: verify the application is actually gone
    get_response = await client.get(
        f"/jobs/{job_id}/applications/{application_id}",
        headers=employee_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "Application deleted successfully"


# ------ Filter applications by status (manager) ------
@pytest.mark.asyncio
async def test_get_applications_by_status_manager_success(client: AsyncClient):
    """Happy: Manager filters applications by pending status -> 200 OK."""
    
    # Creating a company with a manager
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    # Creating three jobs under the same company
    job1 = await create_test_job(client, company_id, headers=manager_headers)
    job1_id = job1["job_id"]

    job2 = await create_test_job(client, company_id, headers=manager_headers)
    job2_id = job2["job_id"]

    job3 = await create_test_job(client, company_id, headers=manager_headers)
    job3_id = job3["job_id"]

    # Creating a single employee user
    employee_headers = await create_test_employee_user(client)

    # Create one application for each job (all pending by default)
    pending_app = await create_test_application(client, job1_id, employee_headers)
    pending_id = pending_app["application_id"]

    # For job2, update status to "accepted"
    accepted_app = await create_test_application(client, job2_id, employee_headers)
    accepted_id = accepted_app["application_id"]
    await client.patch(
        f"/jobs/{job2_id}/applications/{accepted_id}",
        json={"status": "accepted"},
        headers=manager_headers
    )

    # For job3, update status to "rejected"
    rejected_app = await create_test_application(client, job3_id, employee_headers)
    rejected_id = rejected_app["application_id"]
    await client.patch(
        f"/jobs/{job3_id}/applications/{rejected_id}",
        json={"status": "rejected"},
        headers=manager_headers
    )

    # Manager filters by status "pending"
    response = await client.get(
        f"/jobs/{job1_id}/applications/status/pending",
        headers=manager_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify that only the pending application is returned
    assert len(data) == 1
    assert data[0]["application_id"] == pending_id
    assert data[0]["status"] == "pending"

    # Verify accepted and rejected are not in the list
    returned_ids = [app["application_id"] for app in data]
    assert accepted_id not in returned_ids
    assert rejected_id not in returned_ids


# ------ Get applications for a specific job (manager) ------
@pytest.mark.asyncio
async def test_get_applications_by_job_manager_success(client: AsyncClient):
    """Happy: Manager gets all applicants for a specific job they own -> 200 OK."""
    
    # Creating a company and a job with a manager
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Creating two different employee users
    employee1_headers = await create_test_employee_user(client)
    employee2_headers = await create_test_employee_user(client)

    # Creating two applications for the same job (different employees)
    app1 = await create_test_application(client, job_id, employee1_headers)
    app2 = await create_test_application(client, job_id, employee2_headers)

    # Manager gets all applications for this job
    response = await client.get(
        f"/jobs/{job_id}/applications/job/",
        headers=manager_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Verify both applications are returned and belong to the job
    assert len(data) == 2
    for app in data:
        assert app["job_id"] == job_id

    app_ids = [app["application_id"] for app in data]
    assert app1["application_id"] in app_ids
    assert app2["application_id"] in app_ids

    # Verify manager sees full details (status, employee_id)
    for app in data:
        assert "status" in app
        assert "employee_id" in app
        assert "cover_letter" in app
        assert "applied_at" in app
        assert "updated_at" in app


# ----------------------------------------------------------------------------
# SAD TESTS
# ----------------------------------------------------------------------------

# ------ Authentication & Authorization ------

# ------ Create application without token ------
@pytest.mark.asyncio
async def test_create_application_without_token_fail(client: AsyncClient):
    
    # Creating a company and a job with a manager
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Attempting to apply without any Authorization header
    application_data = {"cover_letter": "I am interested in this position."}
    response = await client.post(
        f"/jobs/{job_id}/applications/",
        json=application_data
        # no headers
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


# ------ Create application as manager ------
@pytest.mark.asyncio
async def test_create_application_as_manager_fail(client: AsyncClient):
    
    # Creating a company and a job with a manager
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Attempting to apply using the manager token (should fail)
    application_data = {"cover_letter": "I am interested in this position."}
    response = await client.post(
        f"/jobs/{job_id}/applications/",
        json=application_data,
        headers=manager_headers
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Only employees can apply for jobs"


# ------ Delete application as manager ------
@pytest.mark.asyncio
async def test_delete_application_as_manager_fail(client: AsyncClient):
    
    # Creating a company and a job with a manager
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Creating an application with an employee
    employee_headers = await create_test_employee_user(client)
    application_result = await create_test_application(client, job_id, employee_headers)
    application_id = application_result["application_id"]

    # Manager tries to delete the application
    response = await client.delete(
        f"/jobs/{job_id}/applications/{application_id}",
        headers=manager_headers
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Only employees can delete their own applications"


# ------ Update application (employee tries to update another employee's app) ------
@pytest.mark.asyncio
async def test_update_application_employee_other_owner_fail(client: AsyncClient):
    
    # Creating a company and a job with a manager
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Creating two different employee users
    employee_a_headers = await create_test_employee_user(client, username="employee_a")
    employee_b_headers = await create_test_employee_user(client, username="employee_b")

    # Employee A creates an application
    application_result = await create_test_application(client, job_id, employee_a_headers)
    application_id = application_result["application_id"]

    # Employee B tries to update the cover letter
    response = await client.patch(
        f"/jobs/{job_id}/applications/{application_id}",
        json={"cover_letter": "Trying to hijack this application"},
        headers=employee_b_headers
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "You are not authorized to update this application"


# ------ Update application (employee tries to change status) ------
@pytest.mark.asyncio
async def test_update_application_employee_change_status_fail(client: AsyncClient):
    
    # Creating a company and a job with a manager
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Creating an application with an employee
    employee_headers = await create_test_employee_user(client)
    application_result = await create_test_application(client, job_id, employee_headers)
    application_id = application_result["application_id"]

    # Employee tries to update status (not allowed)
    response = await client.patch(
        f"/jobs/{job_id}/applications/{application_id}",
        json={"status": "accepted"},
        headers=employee_headers
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Employee can only update the cover letter"


# ------ Update application (manager tries to change cover_letter) ------
@pytest.mark.asyncio
async def test_update_application_manager_change_cover_letter_fail(client: AsyncClient):
    
    # Creating a company and a job with a manager
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Creating an application with an employee
    employee_headers = await create_test_employee_user(client)
    application_result = await create_test_application(client, job_id, employee_headers)
    application_id = application_result["application_id"]

    # Manager tries to update cover_letter (not allowed)
    response = await client.patch(
        f"/jobs/{job_id}/applications/{application_id}",
        json={"cover_letter": "Trying to change this as manager"},
        headers=manager_headers
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Manager can only update the status"


# ------ Filter by status as employee ------
@pytest.mark.asyncio
async def test_get_applications_by_status_as_employee_fail(client: AsyncClient):
    
    # Creating a company and a job with a manager (needed to get a valid job_id)
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Getting an employee token
    employee_headers = await create_test_employee_user(client)

    # Employee tries to filter applications by status (only managers allowed)
    response = await client.get(
        f"/jobs/{job_id}/applications/status/pending",
        headers=employee_headers
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Only managers can filter by status"


# ------ Ownership & Existence ------

# ------ Create application for non-existent job ------
@pytest.mark.asyncio
async def test_create_application_job_not_exist_fail(client: AsyncClient):
    
    # Creating an employee user to get a token
    employee_headers = await create_test_employee_user(client)

    # Attempting to apply to a non-existent job ID (e.g., 999)
    application_data = {"cover_letter": "I am interested."}
    response = await client.post(
        "/jobs/999/applications/",
        json=application_data,
        headers=employee_headers
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


# ------ Get non-existent application ------
@pytest.mark.asyncio
async def test_get_application_not_exist_fail(client: AsyncClient):
    
    # Creating a company and a job to get a valid job_id
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Creating an employee token
    employee_headers = await create_test_employee_user(client)

    # Attempting to fetch an application with a non-existent ID (e.g., 999)
    response = await client.get(
        f"/jobs/{job_id}/applications/999",
        headers=employee_headers
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"


# ------ Update non-existent application ------
@pytest.mark.asyncio
async def test_update_application_not_exist_fail(client: AsyncClient):
    
    # Creating a company and a job to get a valid job_id
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Creating an employee token
    employee_headers = await create_test_employee_user(client)

    # Attempting to update an application with non-existent ID (999)
    response = await client.patch(
        f"/jobs/{job_id}/applications/999",
        json={"cover_letter": "Updated text"},
        headers=employee_headers
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"


# ------ Delete non-existent application ------
@pytest.mark.asyncio
async def test_delete_application_not_exist_fail(client: AsyncClient):
    
    # Creating a company and a job to get a valid job_id
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Creating an employee token
    employee_headers = await create_test_employee_user(client)

    # Attempting to delete an application with non-existent ID (999)
    response = await client.delete(
        f"/jobs/{job_id}/applications/999",
        headers=employee_headers
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"


# ------ Manager tries to update application for a job they don't own ------
@pytest.mark.asyncio
async def test_update_application_manager_other_company_fail(client: AsyncClient):
    
    # Creating a company and a job with Manager A
    company_a = await create_test_company(client)
    company_id = company_a["company_id"]
    manager_a_headers = company_a["headers"]

    job = await create_test_job(client, company_id, headers=manager_a_headers)
    job_id = job["job_id"]

    # Creating an application with an employee
    employee_headers = await create_test_employee_user(client)
    application_result = await create_test_application(client, job_id, employee_headers)
    application_id = application_result["application_id"]

    # Creating Manager B (different manager)
    manager_b_headers = await get_token_from_logged_user(
        client,
        username=f"manager_b_{uuid.uuid4().hex[:8]}",
        role="manager"
    )

    # Manager B tries to update the application status
    response = await client.patch(
        f"/jobs/{job_id}/applications/{application_id}",
        json={"status": "accepted"},
        headers=manager_b_headers
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "You are not authorized to access this company."


# ------ Manager tries to update application for a job they don't own ------
@pytest.mark.asyncio
async def test_update_application_manager_other_company_fail(client: AsyncClient):
    
    # Creating a company and a job with Manager A
    company_a = await create_test_company(client)
    company_id = company_a["company_id"]
    manager_a_headers = company_a["headers"]

    job = await create_test_job(client, company_id, headers=manager_a_headers)
    job_id = job["job_id"]

    # Creating an application with an employee
    employee_headers = await create_test_employee_user(client)
    application_result = await create_test_application(client, job_id, employee_headers)
    application_id = application_result["application_id"]

    # Creating Manager B (different manager)
    manager_b_headers = await get_token_from_logged_user(
        client,
        username=f"manager_b_{uuid.uuid4().hex[:8]}",
        role="manager"
    )

    # Manager B tries to update the application status
    response = await client.patch(
        f"/jobs/{job_id}/applications/{application_id}",
        json={"status": "accepted"},
        headers=manager_b_headers
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "You are not authorized to access this company."


# ------ Business Logic & Validation ------

# ------ Duplicate application (same employee, same job) ------
@pytest.mark.asyncio
async def test_create_application_duplicate_fail(client: AsyncClient):
    
    # Creating a company and a job with a manager
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Creating an employee user
    employee_headers = await create_test_employee_user(client)

    # Creating the first application
    application_data = {"cover_letter": "First application"}
    response1 = await client.post(
        f"/jobs/{job_id}/applications/",
        json=application_data,
        headers=employee_headers
    )
    assert response1.status_code == 201

    # Trying to apply again with the same employee and job
    response2 = await client.post(
        f"/jobs/{job_id}/applications/",
        json=application_data,
        headers=employee_headers
    )
    assert response2.status_code == 409
    assert response2.json()["detail"] == "You have already applied for this job"


# ------ Missing cover_letter ------
@pytest.mark.asyncio
async def test_create_application_missing_fields_fail(client: AsyncClient):
    
    # Creating a company and a job with a manager
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Creating an employee token
    employee_headers = await create_test_employee_user(client)

    # Sending a request without the cover_letter field
    response = await client.post(
        f"/jobs/{job_id}/applications/",
        json={},  # empty body
        headers=employee_headers
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("cover_letter" in err["loc"] for err in errors)
    assert any(err["msg"] == "Field required" for err in errors)


# ------ Cover_letter too short ------
@pytest.mark.asyncio
async def test_create_application_short_cover_letter_fail(client: AsyncClient):
    """Sad: cover_letter too short (e.g., 2 chars) -> 422."""
    
    # Creating a company and a job with a manager
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Creating an employee token
    employee_headers = await create_test_employee_user(client)

    # Sending a cover_letter that is too short (< min_length=3)
    application_data = {"cover_letter": "ab"}  # length 2
    response = await client.post(
        f"/jobs/{job_id}/applications/",
        json=application_data,
        headers=employee_headers
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("cover_letter" in err["loc"] for err in errors)
    assert any(err["type"] == "string_too_short" for err in errors)


# ------ Invalid status value ------
@pytest.mark.asyncio
async def test_update_application_invalid_status_fail(client: AsyncClient):
    """Sad: Send invalid status (e.g., "maybe") -> 422."""
    
    # Creating a company and a job with a manager
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Creating an application with an employee
    employee_headers = await create_test_employee_user(client)
    application_result = await create_test_application(client, job_id, employee_headers)
    application_id = application_result["application_id"]

    # Manager tries to update with invalid status
    response = await client.patch(
        f"/jobs/{job_id}/applications/{application_id}",
        json={"status": "maybe"},
        headers=manager_headers
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("status" in err["loc"] for err in errors)
    # Pydantic enum validation error type is "enum"
    assert any(err["type"] == "enum" for err in errors)