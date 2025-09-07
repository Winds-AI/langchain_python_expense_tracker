"""
Pydantic models for expense categories and subcategories.
Provides type-safe data structures with validation for category management.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
import re


class SubcategoryModel(BaseModel):
    """Model for expense subcategories."""
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate subcategory name format."""
        if not v or not v.strip():
            raise ValueError("Subcategory name cannot be empty")
        if len(v.strip()) < 1:
            raise ValueError("Subcategory name must be at least 1 character")
        if len(v.strip()) > 50:
            raise ValueError("Subcategory name cannot exceed 50 characters")
        # Allow alphanumeric, spaces, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v):
            raise ValueError("Subcategory name can only contain letters, numbers, spaces, hyphens, and underscores")
        return v.strip()

    model_config = {
        "json_encoders": {datetime: lambda v: v.isoformat()}
    }

class CategoryModel(BaseModel):
    """Complete model for expense categories with subcategories."""
    id: Optional[str] = Field(None, alias="_id")
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    subcategories: List[SubcategoryModel] = Field(default_factory=list)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')  # Hex color
    icon: Optional[str] = Field(None, max_length=50)
    is_active: bool = Field(default=True)
    sort_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('id', mode='before')
    @classmethod
    def convert_object_id(cls, v):
        """Convert MongoDB ObjectId to string."""
        if v is None:
            return None
        # Handle ObjectId from MongoDB
        if hasattr(v, '__class__') and 'ObjectId' in str(type(v)):
            return str(v)
        # If it's already a string, return as is
        if isinstance(v, str):
            return v
        # Convert any other type to string
        return str(v)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate category name format and uniqueness considerations."""
        if not v or not v.strip():
            raise ValueError("Category name cannot be empty")
        if len(v.strip()) < 2:
            raise ValueError("Category name must be at least 2 characters")
        if len(v.strip()) > 50:
            raise ValueError("Category name cannot exceed 50 characters")
        # Allow alphanumeric, spaces, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9\s\-_&]+$', v):
            raise ValueError("Category name can only contain letters, numbers, spaces, hyphens, underscores, and ampersands")
        return v.strip()

    def dict_for_db(self) -> Dict[str, Any]:
        """Convert to dict format suitable for MongoDB storage."""
        data = self.model_dump(by_alias=True, exclude_unset=True)
        if 'id' in data and data['id'] is None:
            del data['id']  # Remove None _id for new documents
        return data

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        },
        "validate_by_name": True
    }


class CategoryCreate(BaseModel):
    """Model for creating new categories."""
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    """Model for updating existing categories."""
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class SubcategoryCreate(BaseModel):
    """Model for creating new subcategories."""
    name: str
    description: Optional[str] = None


class SubcategoryUpdate(BaseModel):
    """Model for updating existing subcategories."""
    name: Optional[str] = None
    description: Optional[str] = None
