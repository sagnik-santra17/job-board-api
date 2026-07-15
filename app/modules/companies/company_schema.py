from datetime import datetime
import phonenumbers
from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator


# ---------------------------------------------------------------------------------------------------------------- #


# Company Schema for creating a new company
class CompanyCreate(BaseModel):
    company_name: str = Field(..., min_length=3, max_length=100)
    company_address: str = Field(..., min_length=3, max_length=100)
    company_email: EmailStr = Field(...)
    company_phone: str = Field(...)
    company_website: HttpUrl = Field(...)
    company_description: str = Field(..., min_length=50, max_length=1000)


    # Validate and format phone number
    @field_validator("company_phone")
    @classmethod
    def validate_and_format_phone(cls, value: str) -> str:
        try:
            # Parse assuming the input contains a country code prefix (e.g., +1, +44)
            parsed = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("The phone number provided is not valid.")

            # Standardize and save in international E.164 format (+14155552671)
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
        except Exception:
            raise ValueError(
                "Invalid phone number. Ensure it includes a valid country code (e.g., +1)."
            )
        

# Company Schema for updating an existing company
class CompanyUpdate(BaseModel):
    company_name: str | None = Field(default=None, min_length=3, max_length=100)
    company_address: str | None = Field(default=None, min_length=3, max_length=100)
    company_email: EmailStr | None = Field(default=None)
    company_phone: str | None = Field(default=None)
    company_website: HttpUrl | None = Field(default=None)
    company_description: str | None = Field(default=None, min_length=50, max_length=1000)


    # Validate and format phone number
    @field_validator("company_phone")
    @classmethod
    def validate_and_format_phone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:

            parsed = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("The phone number provided is not valid.")
            
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        
        except Exception:
            raise ValueError("Invalid phone number. Ensure it includes a valid country code (e.g., +1).")


# Company Schema for company details (read-only)/response
class Company(BaseModel):
    model_config = ConfigDict(from_attributes=True)  
    company_id: int
    company_name: str
    company_address: str
    company_email: EmailStr
    company_phone: str
    company_website: HttpUrl
    company_description: str
    created_at: datetime


