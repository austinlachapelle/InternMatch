from pydantic import BaseModel, EmailStr, Field


class ProfileCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    target_role: str = Field(min_length=2, max_length=120)
    gpa: float = Field(ge=0.0, le=4.0)
    metro_slug: str = Field(min_length=2, max_length=64)
