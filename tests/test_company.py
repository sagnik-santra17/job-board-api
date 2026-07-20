import uuid
from dns import update
import pytest
from httpx import AsyncClient


from tests.test_helper import create_test_company, get_token_from_logged_user



# ----------------------------------------------------------------------------
# HAPPY TESTS (Successful flows)
# ----------------------------------------------------------------------------

# ------ Create Company – manager creates a company with valid data ------
@pytest.mark.asyncio
async def test_create_company_success(client: AsyncClient):
    
    header = await get_token_from_logged_user(client, role="manager") # -> Adding role="manager" in the header

    company_data = {
        "company_name": "Test Company",
        "company_email": "test_company@email.com",
        "company_phone": "+14155552671",         
        "company_address": "123 Main St",
        "company_website": "https://example.com",
        "company_description": "This is a test company with at least fifty characters. More text here to reach the minimum length."
    }

    response = await client.post("/companies/", json=company_data, headers=header)
    assert response.status_code == 201

    data = response.json()
    assert data["company_name"] == "Test Company"
    assert data["company_email"] == "test_company@email.com"
    assert data["company_phone"] == "+14155552671"
    assert data["company_address"] == "123 Main St"
    assert data["company_website"].startswith("https://example.com")
    assert data["company_description"] == company_data["company_description"]
    assert "company_id" in data
        
    

# ------ List All Companies – manager retrieves their own companies ------
@pytest.mark.asyncio
async def test_list_companies_success(client: AsyncClient):

    result = await create_test_company(client, company_name="Test Company List")
    header = result["headers"]

    response = await client.get("/companies/", headers=header)
    data = response.json()
    
    assert any(c["company_name"] == result["company"]["company_name"] for c in data)
    


# ------ Get Single Company – manager fetches own company ------
@pytest.mark.asyncio
async def test_get_company_success(client: AsyncClient):
    
    result = await create_test_company(client, company_name="Test Company List")
    header = result["headers"]
    
    response = await client.get("/companies/", headers=header)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


# ------ Update Company – manager updates own company ------
@pytest.mark.asyncio
async def test_update_company_success(client: AsyncClient):
    
    result = await create_test_company(client, company_name="Test Company")
    header = result["headers"]

    new_email = f"test_{uuid.uuid4().hex[:8]}@email.com" # -> Unique email
    
    update_data = {
        "company_name": "Test Company Updated",
        "company_email": new_email, 
        "company_phone": "+14155552671",
        "company_address": "123 Main St",
        "company_website": str("https://example.com"),
        "company_description": "This is a test company with at least fifty characters. More text here to reach the minimum length."
    }

    response = await client.patch(f"/companies/{result['company_id']}", json=update_data, headers=header)
    data = response.json()

    assert response.status_code == 200
    assert data["company_name"] == "Test Company Updated"
    assert data["company_email"] == new_email 
    assert data["company_phone"] == "+14155552671"
    assert data["company_address"] == "123 Main St"
    assert data["company_website"].startswith("https://example.com")
    assert data["company_description"] == update_data["company_description"]
    assert "company_id" in data



# ------ Delete Company – manager deletes own company ------
@pytest.mark.asyncio
async def test_delete_company_success(client: AsyncClient):
    
    result = await create_test_company(client, company_name="Test Company")
    header = result["headers"]
    
    response = await client.delete(f"/companies/{result['company_id']}", headers=header)

    assert response.status_code == 200
    assert response.json() == {"message": "company deleted successfully"}



# ----------------------------------------------------------------------------
# SAD TESTS (Failure flows)
# ----------------------------------------------------------------------------

# ------ Authentication & Authorization ------

# ------ Create company without token ------
@pytest.mark.asyncio
async def test_create_company_without_token_fail(client: AsyncClient):
    
    company_data = {
        "company_name": "Test Company",
        "company_email": "test_company@email.com",
        "company_phone": "+14155552671",         
        "company_address": "123 Main St",
        "company_website": "https://example.com",
        "company_description": "This is a test company with at least fifty characters. More text here to reach the minimum length."
    }

    response = await client.post("/companies/", json=company_data)
    assert response.status_code == 401

    assert response.json()["detail"] == "Not authenticated"


# ------ Create company as employee ------
@pytest.mark.asyncio
async def test_create_company_as_employee_fail(client: AsyncClient):
    
    unique = uuid.uuid4().hex[:8]
    
    header = await get_token_from_logged_user(client, role="employee") # -> Adding role="employee" in the header

    company_data = {
        "company_name": f"Test Company {unique}",
        "company_email": f"test_company_{unique}@email.com",
        "company_phone": "+14155552671",         
        "company_address": "123 Main St",
        "company_website": "https://example.com",
        "company_description": "This is a test company with at least fifty characters. More text here to reach the minimum length."
    }

    response = await client.post("/companies/", json=company_data, headers=header)
    assert response.status_code == 403

    assert response.json()["detail"] == "Only managers can create companies"


# ------ Create company with invalid token ------
@pytest.mark.asyncio
async def test_create_company_invalid_token_fail(client: AsyncClient):
    
    company_data = {
        "company_name": "Test Company",
        "company_email": "test_company@email.com",
        "company_phone": "+14155552671",         
        "company_address": "123 Main St",
        "company_website": "https://example.com",
        "company_description": "This is a test company with at least fifty characters. More text here to reach the minimum length."
    }

    response = await client.post("/companies/", json=company_data, headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401

    assert response.json()["detail"] == "Incorrect username or password"



# ------ Creation failures ------

# ------ Duplicate company name ------
@pytest.mark.asyncio
async def test_create_company_duplicate_name_fail(client: AsyncClient):
    
    unique = uuid.uuid4().hex[:8]
    company_name = f"Test Company {unique}"

    # Creating the first company
    header = await get_token_from_logged_user(client, role="manager") # -> Adding role="manager" in the header

    company_data = {
        "company_name": company_name,
        "company_email": f"test_{unique}@email.com",
        "company_phone": "+14155552671",
        "company_address": "123 Main St",
        "company_website": "https://example.com",
        "company_description": "This is a test company with at least fifty characters. More text here to reach the minimum length."
    }

    await client.post("/companies/", json=company_data, headers=header)
    
    # Second attempt with same name (different email to avoid duplicate email conflict)
    duplicate_data = company_data.copy()
    duplicate_data["company_email"] = f"test_{unique}@email.com"

    response = await client.post("/companies/", json=duplicate_data, headers=header)
    assert response.status_code == 409

    assert "Company name" in response.json()["detail"]



# ------ Duplicate company email ------
@pytest.mark.asyncio
async def test_create_company_duplicate_email_fail(client: AsyncClient):
    
    unique = uuid.uuid4().hex[:8]
    company_email = f"test_{unique}@email.com"

    # Creating the first company
    header = await get_token_from_logged_user(client, role="manager") # -> Adding role="manager" in the header

    company_data = {
        "company_name": f"Test Company {unique}",
        "company_email": company_email,
        "company_phone": "+14155552671",
        "company_address": "123 Main St",
        "company_website": "https://example.com",
        "company_description": "This is a test company with at least fifty characters. More text here to reach the minimum length."
    }

    await client.post("/companies/", json=company_data, headers=header)
    
    # Second attempt with same email (different name to avoid duplicate name conflict)
    duplicate_data = company_data.copy()
    duplicate_data["company_name"] = f"Test Company {unique}_duplicate"

    response = await client.post("/companies/", json=duplicate_data, headers=header)
    assert response.status_code == 409

    assert "Company email" in response.json()["detail"]



# ------ Invalid phone number ------
@pytest.mark.asyncio
async def test_create_company_invalid_phone_fail(client: AsyncClient):
    
    header = await get_token_from_logged_user(client, role="manager") # -> Adding role="manager" in the header

    company_data = {
        "company_name": "Test Company",
        "company_email": "test_company@email.com",
        "company_phone": "invalid_phone_number",         
        "company_address": "123 Main St",
        "company_website": "https://example.com",
        "company_description": "This is a test company with at least fifty characters. More text here to reach the minimum length."
    }

    response = await client.post("/companies/", json=company_data, headers=header)
    assert response.status_code == 422

    assert "Invalid phone number" in response.json()["detail"][0]["msg"]


# ------ Missing required fields ------
@pytest.mark.asyncio
async def test_create_company_missing_fields_fail(client: AsyncClient):
    
    header = await get_token_from_logged_user(client, role="manager") # -> Adding role="manager" in the header

    company_data = {
        "company_name": "Test Company",
        "company_email": "test_company@email.com",
        "company_address": "123 Main St",
        "company_website": "https://example.com",
        "company_description": "This is a test company with at least fifty characters. More text here to reach the minimum length."
    }

    response = await client.post("/companies/", json=company_data, headers=header)
    assert response.status_code == 422

    assert response.json()["detail"][0]["msg"] == "Field required"



# ------ Read/List failures ------

# ------ Get non-existent company ------
@pytest.mark.asyncio
async def test_get_non_existent_company_fail(client: AsyncClient):
    
    header = await get_token_from_logged_user(client, role="manager") # -> Adding role="manager" in the header

    response = await client.get("/companies/999", headers=header)
    assert response.status_code == 404

    assert response.json()["detail"] == "Company not found with that company id"


# ------ Get company owned by another manager ------
@pytest.mark.asyncio
async def test_get_company_other_manager_fail(client: AsyncClient):
    
    # Creating a company with manager 1
    result_1 = await create_test_company(client, company_name="Test Company A")
    company_id_of_manager_1 = result_1["company_id"]

    # Get a token for Manager B (a different manager)
    # Using a unique username for each manager to avoid duplicate username conflict
    unique_username = f"manager_{uuid.uuid4().hex[:8]}"
    header_2 = await get_token_from_logged_user(client, role="manager", username=unique_username)

    # Try to get the company with Manager B's token
    response = await client.get(f"/companies/{company_id_of_manager_1}", headers=header_2)
    assert response.status_code == 401

    assert response.json()["detail"] == "You are not authorized to access this company."


# ------ Update failures ------

# ------ Update non-existent company ------
@pytest.mark.asyncio
async def test_update_non_existent_company_fail(client: AsyncClient):
    
    header = await get_token_from_logged_user(client, role="manager") # -> Adding role="manager" in the header

    response = await client.patch("/companies/999", json={}, headers=header)
    assert response.status_code == 404

    assert response.json()["detail"] == "Company not found with that company id"


# ------ Update company owned by another manager ------
@pytest.mark.asyncio
async def test_update_company_other_manager_fail(client: AsyncClient):
    
    # Creating a company with manager 1
    result_1 = await create_test_company(client, company_name="Test Company A")
    company_id_of_manager_1 = result_1["company_id"]

    # Get a token for Manager B (a different manager)
    # Using a unique username for each manager to avoid duplicate username conflict
    unique_username = f"manager_{uuid.uuid4().hex[:8]}"
    header_2 = await get_token_from_logged_user(client, role="manager", username=unique_username)

    # Try to update the company with Manager B's token
    update_data = {
        "company_name": "Updated Company Name"
    }

    response = await client.patch(f"/companies/{company_id_of_manager_1}", json=update_data, headers=header_2)
    assert response.status_code == 401

    assert response.json()["detail"] == "You are not authorized to access this company."


# ------ Update with duplicate name (other company) ------
@pytest.mark.asyncio
async def test_update_company_duplicate_name_fail(client: AsyncClient):
    
    # Create first company with Manager A
    result_a = await create_test_company(client, company_name="Test Company A")
    header_a = result_a["headers"]

    # Create second company with the same manager (different name)
    # Use a unique email and name for second company
    unique = uuid.uuid4().hex[:8]
    company_b_data = {
        "company_name": "Test Company B",
        "company_email": f"test_b_{unique}@email.com",
        "company_phone": "+14155552671",
        "company_address": "456 Oak St",
        "company_website": "https://example.com/",
        "company_description": "This is a test company with at least fifty characters. More text here to reach the minimum length."
    }

    await client.post("/companies/", json=company_b_data, headers=header_a)

    # Try to update Company A to use the same name as Company B
    update_data = {"company_name": "Test Company B"}

    response = await client.patch(
        f"/companies/{result_a['company_id']}", 
        json=update_data, 
        headers=header_a
    )
    
    assert response.status_code == 409
    assert "Company already exists with name" in response.json()["detail"]


# ------ Update with duplicate email (other company) ------
@pytest.mark.asyncio
async def test_update_company_duplicate_email_fail(client: AsyncClient):
    
    # Create first company with Manager A
    result_a = await create_test_company(client, company_name="Test Company A")
    header_a = result_a["headers"]

    # Create second company with the same manager (different name)
    # Use a unique email and name for second company
    unique = uuid.uuid4().hex[:8]

    company_b_data = {
        "company_name": f"Test Company B {unique}",
        "company_email": f"test_b_{unique}@email.com",
        "company_phone": "+14155552671",
        "company_address": "456 Oak St",
        "company_website": "https://example.com/",
        "company_description": "This is a test company with at least fifty characters. More text here to reach the minimum length."
    }

    await client.post("/companies/", json=company_b_data, headers=header_a)

    # Try to update Company A to use the same email as Company B
    update_data = {"company_email": f"test_b_{unique}@email.com"}

    response = await client.patch(
        f"/companies/{result_a['company_id']}", 
        json=update_data, 
        headers=header_a
    )
    
    assert response.status_code == 409
    assert "Company already exists with email" in response.json()["detail"]



# ------ Update with invalid phone number ------
@pytest.mark.asyncio
async def test_update_company_invalid_phone_fail(client: AsyncClient):
    
    result = await create_test_company(client, company_name="Test Company")
    header = result["headers"]

    update_data = {"company_phone": "invalid_phone_number"}

    response = await client.patch(
        f"/companies/{result['company_id']}", 
        json=update_data, 
        headers=header
    )
    
    assert response.status_code == 422
    assert "Invalid phone number" in response.json()["detail"][0]["msg"]

# ------ Update without token ------
@pytest.mark.asyncio
async def test_update_company_without_token_fail(client: AsyncClient):
    
    update_data = {
        "company_name": "Updated Company Name"
    }

    response = await client.patch(
        "/companies/1", 
        json=update_data, 
        headers={"Authorization": "InvalidToken"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"



# ------ Delete failures ------

# ------ Delete non-existent company ------
@pytest.mark.asyncio
async def test_delete_non_existent_company_fail(client: AsyncClient):
    
    header = await get_token_from_logged_user(client, role="manager") # -> Adding role="manager" in the header

    response = await client.delete("/companies/999", headers=header)
    assert response.status_code == 404

    assert response.json()["detail"] == "Company not found with that company id"


# ------ Delete company owned by another manager ------
@pytest.mark.asyncio
async def test_delete_company_other_manager_fail(client: AsyncClient):
    
    # Creating a company with manager 1
    result_1 = await create_test_company(client, company_name="Test Company A")
    company_id_of_manager_1 = result_1["company_id"]

    # Get a token for Manager B (a different manager)
    # Using a unique username for each manager to avoid duplicate username conflict
    unique_username = f"manager_{uuid.uuid4().hex[:8]}"
    header_2 = await get_token_from_logged_user(client, role="manager", username=unique_username)

    # Try to delete the company with Manager B's token
    response = await client.delete(f"/companies/{company_id_of_manager_1}", headers=header_2)
    assert response.status_code == 401

    assert response.json()["detail"] == "You are not authorized to access this company."

# ------ Delete without token ------
@pytest.mark.asyncio
async def test_delete_company_without_token_fail(client: AsyncClient):
    
    response = await client.delete(
        "/companies/1", 
        headers={"Authorization": "InvalidToken"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"