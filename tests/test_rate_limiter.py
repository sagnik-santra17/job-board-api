import pytest
from httpx import AsyncClient
import time
import asyncio


from app.modules.applications.application_router import application_limiter
from app.api.dependencies import RateLimiter
from tests.test_helper import create_test_company, create_test_employee_user, create_test_job


# -------------------------------------------------------------------------------------------------- #

# This fixture overrides the mocked limiter with a real one for these tests.
# It uses a short window (2 seconds) so you don't have to wait 60 seconds.

@pytest.fixture(autouse=True)
def use_real_rate_limiter(monkeypatch):

    # Create a limiter with 2 requests per 2 seconds for fast testing
    test_limiter = RateLimiter(max_requests=2, window_seconds=2)
    # Replace the application_limiter's method with the real one
    monkeypatch.setattr(application_limiter, "check_rate_limit", test_limiter.check_rate_limit)
    yield

# -------------------------------------------------------------------------------------------------- #

# Happy: First two applications succeed (201), third returns 429
@pytest.mark.asyncio
async def test_rate_limiter_two_requests_succeed_third_fails(client: AsyncClient):

    # Create a company
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    # Create three different jobs under the same company
    job1 = await create_test_job(client, company_id, headers=manager_headers)
    job2 = await create_test_job(client, company_id, headers=manager_headers)
    job3 = await create_test_job(client, company_id, headers=manager_headers)

    # Create an employee user
    employee_headers = await create_test_employee_user(client)

    # First application – to job1 (succeeds)
    response1 = await client.post(
        f"/jobs/{job1['job_id']}/applications/",
        json={"cover_letter": "First application"},
        headers=employee_headers
    )
    assert response1.status_code == 201

    # Second application – to job2 (succeeds)
    response2 = await client.post(
        f"/jobs/{job2['job_id']}/applications/",
        json={"cover_letter": "Second application"},
        headers=employee_headers
    )
    assert response2.status_code == 201

    # Third application – to job3 (should be blocked by rate limiter)
    response3 = await client.post(
        f"/jobs/{job3['job_id']}/applications/",
        json={"cover_letter": "Third application"},
        headers=employee_headers
    )
    assert response3.status_code == 429
    assert "Too many applications" in response3.json()["detail"]


# Happy: After the window expires (2 seconds), a new request is allowed (201).
@pytest.mark.asyncio
async def test_rate_limiter_resets_after_window(client: AsyncClient):

    # Create a company
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    # Create three different jobs
    job1 = await create_test_job(client, company_id, headers=manager_headers)
    job2 = await create_test_job(client, company_id, headers=manager_headers)
    job3 = await create_test_job(client, company_id, headers=manager_headers)

    # Create an employee user
    employee_headers = await create_test_employee_user(client)

    # First request – to job1 (succeeds)
    response1 = await client.post(
        f"/jobs/{job1['job_id']}/applications/",
        json={"cover_letter": "First request"},
        headers=employee_headers
    )
    assert response1.status_code == 201

    # Second request – to job2 (succeeds)
    response2 = await client.post(
        f"/jobs/{job2['job_id']}/applications/",
        json={"cover_letter": "Second request"},
        headers=employee_headers
    )
    assert response2.status_code == 201

    # Wait for the window to expire (2 seconds + small margin)
    await asyncio.sleep(2.5)

    # Third request – to job3 (should succeed after reset)
    response3 = await client.post(
        f"/jobs/{job3['job_id']}/applications/",
        json={"cover_letter": "Third request after reset"},
        headers=employee_headers
    )
    assert response3.status_code == 201