from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, model_validator, ConfigDict


# ------------------------------------------------------------------------------------------------------------------ #


# Schema for user registration (signup)
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    full_name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    role: str = Field(..., description="Must be 'employee' or 'manager'")  # Added role
    is_active: bool = Field(default=True)  

    # Validate that password and confirm_password match
    @model_validator(mode="after")
    def check_password_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords don't match")
        return self


# Schema for updating user details (partial update)
class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=20)
    full_name: str | None = Field(default=None, min_length=3, max_length=100)
    email: EmailStr | None = Field(default=None)
    password: str | None = Field(default=None, min_length=8, max_length=100)
    confirm_password: str | None = Field(default=None, min_length=8, max_length=100)

    # Required to confirm identity for any update (secure approach)
    current_password: str = Field(..., description="Enter your current password to update your account")

    # Validate password fields consistency
    @model_validator(mode="after")
    def check_password_update(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords don't match")
        if self.password is None and self.confirm_password is not None:
            raise ValueError("You have entered confirm password but not password")
        if self.password is not None and self.confirm_password is None:
            raise ValueError("You have entered password but not confirm password")
        return self


# Schema for returning user data in API responses (read-only)
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  
    user_id: int
    username: str
    full_name: str
    email: EmailStr
    role: str                 
    is_active: bool
    created_at: datetime


# Schema for user login
class UserLogin(BaseModel):
    username: str
    password: str


# Schema for account deletion (requires password confirmation)
class UserDelete(BaseModel):
    password: str = Field(..., description="Enter your current password to delete this account")


# Schema for JWT token response
class Token(BaseModel):
    access_token: str
    token_type: str