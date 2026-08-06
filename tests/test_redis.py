import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock

import redis


from app.modules.jobs.job_router import get_cache, set_cache
from app.modules.jobs.job_schema import JobResponse
from tests.test_helper import create_test_company, create_test_job


# ----------------------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------
# HAPPY TESTS
# ----------------------------------------------------------------------------

# ------ Job detail caching – first request stores, second request uses cache ------
@pytest.mark.asyncio
async def test_job_detail_caching_uses_cache(client: AsyncClient, monkeypatch):

    # 1. Create a company and a job (manager needed)
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # Prepare a mock cached response (dict of job data)
    cached_job_dict = JobResponse.model_validate(job["job"]).model_dump(mode="json")

    # Mock get_cache to return None on first call, then the cached dict on subsequent calls
    mock_get = AsyncMock()
    mock_get.side_effect = [None, cached_job_dict]

    # Mock set_cache to do nothing (we don't care about the store, but we can capture it)
    mock_set = AsyncMock()

    # Patch the get_cache and set_cache functions in the router module
    monkeypatch.setattr("app.modules.jobs.job_router.get_cache", mock_get)
    monkeypatch.setattr("app.modules.jobs.job_router.set_cache", mock_set)

    # 2. First request – should fetch from DB (cache miss)
    response1 = await client.get(
        f"/companies/{company_id}/jobs/{job_id}",
        headers=manager_headers
    )
    assert response1.status_code == 200
    data1 = response1.json()

    # On cache miss, the service should be called and the result cached.
    assert data1["job_id"] == job_id
    assert data1["title"] == job["job"]["title"]

    # Ensure set_cache was called with the correct key and data
    mock_set.assert_called_once()

    # The key should be "job:{job_id}"
    call_args = mock_set.call_args[0]
    assert call_args[0] == f"job:{job_id}"

    # 3. Second request – should return cached data (cache hit)
    response2 = await client.get(
        f"/companies/{company_id}/jobs/{job_id}",
        headers=manager_headers
    )
    assert response2.status_code == 200
    data2 = response2.json()

    # Data should match cached dict
    assert data2 == cached_job_dict

    # Verify get_cache was called twice (first miss, second hit)
    assert mock_get.call_count == 2

    # Verify set_cache was called only once (only on first request)
    assert mock_set.call_count == 1


# ------ Job list caching – paginated queries are cached separately ------
@pytest.mark.asyncio
async def test_jobs_list_caching_uses_cache(client: AsyncClient, monkeypatch):

    # 1. Create a company and several jobs
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    # Create 3 jobs
    job1 = await create_test_job(client, company_id, headers=manager_headers)
    job2 = await create_test_job(client, company_id, headers=manager_headers)
    job3 = await create_test_job(client, company_id, headers=manager_headers)

    jobs = [job1, job2, job3]

    # Convert jobs to dicts for cached responses
    cached_page1 = [JobResponse.model_validate(j["job"]).model_dump(mode="json") for j in jobs[:2]]
    cached_page2 = [JobResponse.model_validate(jobs[2]["job"]).model_dump(mode="json")]

    # 2. Mock get_cache and set_cache
    mock_get = AsyncMock()
    mock_get.side_effect = [
        None, # -> First request (skip=0, limit=2) – cache miss
        cached_page1, # -> Second request (same pagination) – cache hit
        None, # -> Third request (skip=2, limit=2) – cache miss
        cached_page2, # -> Fourth request (same pagination) – cache hit
    ]

    mock_set = AsyncMock()

    monkeypatch.setattr("app.modules.jobs.job_router.get_cache", mock_get)
    monkeypatch.setattr("app.modules.jobs.job_router.set_cache", mock_set)

    # 3. Make two requests with same skip/limit
    # First request – cache miss
    response1 = await client.get(
        f"/companies/{company_id}/jobs/",
        headers=manager_headers,
        params={"skip": 0, "limit": 2}
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1) == 2
    assert data1[0]["job_id"] == job1["job_id"]
    assert data1[1]["job_id"] == job2["job_id"]

    # verify set_cache called with correct key
    mock_set.assert_called_once()
    call_args1 = mock_set.call_args[0]
    assert call_args1[0] == f"jobs:all:{company_id}:skip:0:limit:2"

    # Second request – same pagination – should be cache hit
    response2 = await client.get(
        f"/companies/{company_id}/jobs/",
        headers=manager_headers,
        params={"skip": 0, "limit": 2}
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2 == cached_page1

    # 4. Test different skip/limit values produce different cache keys
    # Third request – skip=2, limit=2 – cache miss
    response3 = await client.get(
        f"/companies/{company_id}/jobs/",
        headers=manager_headers,
        params={"skip": 2, "limit": 2}
    )
    assert response3.status_code == 200
    data3 = response3.json()
    assert len(data3) == 1
    assert data3[0]["job_id"] == job3["job_id"]

    # verify set_cache called second time
    assert mock_set.call_count == 2
    call_args2 = mock_set.call_args[0]
    assert call_args2[0] == f"jobs:all:{company_id}:skip:2:limit:2"

    # Fourth request – skip=2, limit=2 – cache hit
    response4 = await client.get(
        f"/companies/{company_id}/jobs/",
        headers=manager_headers,
        params={"skip": 2, "limit": 2}
    )
    assert response4.status_code == 200
    data4 = response4.json()
    assert data4 == cached_page2

    # Verify get_cache was called 4 times (for each request)
    assert mock_get.call_count == 4

    # Verify set_cache was called exactly 2 times (once for each unique pagination)
    assert mock_set.call_count == 2


# ----------------------------------------------------------------------------
# SAD TESTS (or edge cases)
# ----------------------------------------------------------------------------

# ------ Cache returns stale data? Not applicable if TTL is short.
# Instead, test that cache is bypassed when data changes (if we implement invalidation).
# For now, we test that cache is not used when Redis is down (error handling).

# ------ Redis failure – caching is skipped, request still succeeds ------
@pytest.mark.asyncio
async def test_cache_handles_redis_failure_gracefully(client: AsyncClient, monkeypatch):

    # 1. Create a company and a job (manager needed)
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # 2. Mock get_cache and set_cache to raise an exception (simulate Redis down)
    async def mock_get_raise(*args, **kwargs):
        raise redis.ConnectionError("Redis is down")

    async def mock_set_raise(*args, **kwargs):
        raise redis.ConnectionError("Redis is down")

    monkeypatch.setattr("app.modules.jobs.job_router.get_cache", mock_get_raise)
    monkeypatch.setattr("app.modules.jobs.job_router.set_cache", mock_set_raise)

    # 3. Make a GET request – should still succeed (fall back to DB)
    response = await client.get(
        f"/companies/{company_id}/jobs/{job_id}",
        headers=manager_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Verify the data is correct (from DB, not cache)
    assert data["job_id"] == job_id
    assert data["title"] == job["job"]["title"]
    assert data["company_id"] == company_id


# ------ TTL expiration (optional) – can mock time or just test that after expiry, new data fetched ------
@pytest.mark.asyncio
async def test_cache_expires_after_ttl(client: AsyncClient, monkeypatch):

    # 1. Create a company and a job
    company = await create_test_company(client)
    company_id = company["company_id"]
    manager_headers = company["headers"]

    job = await create_test_job(client, company_id, headers=manager_headers)
    job_id = job["job_id"]

    # 2. Mock get_cache to return None on first call (cache miss),
    cached_job_dict = JobResponse.model_validate(job["job"]).model_dump(mode="json")

    mock_get = AsyncMock()
    mock_get.side_effect = [
        None, # -> first request – miss
        cached_job_dict, # -> second request – hit
        None, # _> third request – TTL expired, miss
    ]

    mock_set = AsyncMock()

    monkeypatch.setattr("app.modules.jobs.job_router.get_cache", mock_get)
    monkeypatch.setattr("app.modules.jobs.job_router.set_cache", mock_set)

    # 3. First request – cache miss, fetch from DB, store cache
    response1 = await client.get(
        f"/companies/{company_id}/jobs/{job_id}",
        headers=manager_headers
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["job_id"] == job_id

    # verify set_cache was called (caching happened)
    mock_set.assert_called_once()

    # 4. Second request – cache hit (returns cached data)
    response2 = await client.get(
        f"/companies/{company_id}/jobs/{job_id}",
        headers=manager_headers
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2 == cached_job_dict  # matches cached data

    # 5. Third request – TTL expired (simulate by get_cache returning None)
    response3 = await client.get(
        f"/companies/{company_id}/jobs/{job_id}",
        headers=manager_headers
    )
    assert response3.status_code == 200
    data3 = response3.json()

    # Should be fresh data (from DB), which matches original job data
    assert data3["job_id"] == job_id