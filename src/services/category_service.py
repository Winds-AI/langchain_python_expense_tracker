"""
Business logic layer for category and subcategory management.
Provides high-level operations with validation, conflict resolution, and error handling.
"""

from __future__ import annotations

from typing import List, Optional

from src.db.mongo import get_database
from src.models.category import (
    CategoryModel, CategoryCreate, CategoryUpdate,
    SubcategoryCreate, SubcategoryUpdate
)
from src.repositories.categories_repo import CategoriesRepository
from src.utils.exceptions import (
    CategoryNotFoundError, CategoryAlreadyExistsError,
    SubcategoryNotFoundError, SubcategoryAlreadyExistsError,
    InvalidInputError, BusinessLogicError
)
from src.utils.logger import logger, log_execution_time


class CategoryService:
    """
    Service class for managing expense categories and subcategories.

    Provides business logic operations including validation, conflict resolution,
    and high-level category management functions.
    """

    def __init__(self, db=None):
        """Initialize service with database connection."""
        if db is None:
            db = get_database()
        self._repo = CategoriesRepository(db)
        self._db = db

    @log_execution_time
    def get_all_categories(self, include_inactive: bool = False) -> List[CategoryModel]:
        """
        Retrieve all categories with optional filtering.

        Args:
            include_inactive: Whether to include inactive categories

        Returns:
            List of CategoryModel instances ordered by sort_order
        """
        try:
            categories = self._repo.find_all(include_inactive=include_inactive)
            logger.info("Retrieved categories", {
                "count": len(categories),
                "include_inactive": include_inactive
            })
            return categories
        except Exception as e:
            logger.error("Failed to retrieve categories", {
                "include_inactive": include_inactive,
                "error": str(e)
            })
            raise

    @log_execution_time
    def get_category_by_id(self, category_id: str) -> CategoryModel:
        """
        Retrieve a specific category by ID.

        Args:
            category_id: The category ID to retrieve

        Returns:
            CategoryModel instance

        Raises:
            CategoryNotFoundError: If category doesn't exist
            InvalidInputError: If category_id is invalid
        """
        if not category_id or not category_id.strip():
            raise InvalidInputError("category_id", category_id, "Category ID cannot be empty")

        try:
            category = self._repo.find_by_id(category_id)
            logger.info("Retrieved category by ID", {"category_id": category_id, "name": category.name})
            return category
        except CategoryNotFoundError:
            logger.warning("Category not found", {"category_id": category_id})
            raise
        except Exception as e:
            logger.error("Failed to retrieve category by ID", {
                "category_id": category_id,
                "error": str(e)
            })
            raise

    @log_execution_time
    def get_category_by_name(self, name: str) -> Optional[CategoryModel]:
        """
        Retrieve a category by name (case-insensitive).

        Args:
            name: The category name to search for

        Returns:
            CategoryModel instance or None if not found

        Raises:
            InvalidInputError: If name is invalid
        """
        if not name or not name.strip():
            raise InvalidInputError("name", name, "Category name cannot be empty")

        try:
            category = self._repo.find_by_name(name.strip())
            if category:
                logger.info("Retrieved category by name", {"name": name, "category_id": str(category.id)})
            else:
                logger.info("Category not found by name", {"name": name})
            return category
        except Exception as e:
            logger.error("Failed to retrieve category by name", {
                "name": name,
                "error": str(e)
            })
            raise

    @log_execution_time
    def create_category(self, category_data: CategoryCreate) -> CategoryModel:
        """
        Create a new category with validation and conflict resolution.

        Args:
            category_data: The category creation data

        Returns:
            Created CategoryModel instance

        Raises:
            CategoryAlreadyExistsError: If category with same name exists
            InvalidInputError: If input data is invalid
        """
        try:
            # Additional business logic validation
            self._validate_category_data(category_data)

            # Check for existing category with same name
            existing = self.get_category_by_name(category_data.name)
            if existing:
                raise CategoryAlreadyExistsError(category_data.name)

            # Create the category
            category = self._repo.create(category_data)

            logger.info("Category created successfully", {
                "category_id": str(category.id),
                "name": category.name,
                "subcategories_count": len(category.subcategories)
            })

            return category

        except (CategoryAlreadyExistsError, InvalidInputError):
            raise
        except Exception as e:
            logger.error("Failed to create category", {
                "name": category_data.name,
                "error": str(e)
            })
            raise BusinessLogicError(f"Failed to create category '{category_data.name}': {str(e)}")

    @log_execution_time
    def update_category(self, category_id: str, update_data: CategoryUpdate) -> CategoryModel:
        """
        Update an existing category with validation and conflict resolution.

        Args:
            category_id: The ID of the category to update
            update_data: The update data

        Returns:
            Updated CategoryModel instance

        Raises:
            CategoryNotFoundError: If category doesn't exist
            CategoryAlreadyExistsError: If updating to existing name
            InvalidInputError: If input data is invalid
        """
        try:
            # Validate update data
            self._validate_update_data(update_data)

            # Get current category for validation
            current_category = self.get_category_by_id(category_id)

            # Check for name conflicts if name is being updated
            if update_data.name and update_data.name != current_category.name:
                existing = self.get_category_by_name(update_data.name)
                if existing and str(existing.id) != category_id:
                    raise CategoryAlreadyExistsError(update_data.name)

            # Update the category
            updated_category = self._repo.update(category_id, update_data)

            logger.info("Category updated successfully", {
                "category_id": category_id,
                "old_name": current_category.name,
                "new_name": updated_category.name if update_data.name else current_category.name
            })

            return updated_category

        except (CategoryNotFoundError, CategoryAlreadyExistsError, InvalidInputError):
            raise
        except Exception as e:
            logger.error("Failed to update category", {
                "category_id": category_id,
                "error": str(e)
            })
            raise BusinessLogicError(f"Failed to update category '{category_id}': {str(e)}")

    @log_execution_time
    def delete_category(self, category_id: str, hard_delete: bool = False) -> bool:
        """
        Delete a category with safety checks.

        Args:
            category_id: The ID of the category to delete
            hard_delete: Whether to perform hard delete (permanent)

        Returns:
            True if deletion was successful

        Raises:
            CategoryNotFoundError: If category doesn't exist
            BusinessLogicError: If category has dependencies preventing deletion
        """
        try:
            # Get category to check dependencies
            category = self.get_category_by_id(category_id)

            # Business rule: Don't allow deletion of categories with subcategories
            if category.subcategories and not hard_delete:
                raise BusinessLogicError(
                    f"Cannot delete category '{category.name}' because it contains {len(category.subcategories)} subcategories. "
                    "Remove all subcategories first or use hard_delete=True."
                )

            # Perform deletion
            if hard_delete:
                success = self._repo.hard_delete(category_id)
                logger.warning("Category hard deleted", {
                    "category_id": category_id,
                    "name": category.name
                })
            else:
                success = self._repo.delete(category_id)
                logger.info("Category soft deleted", {
                    "category_id": category_id,
                    "name": category.name
                })

            return success

        except (CategoryNotFoundError, BusinessLogicError):
            raise
        except Exception as e:
            logger.error("Failed to delete category", {
                "category_id": category_id,
                "hard_delete": hard_delete,
                "error": str(e)
            })
            raise BusinessLogicError(f"Failed to delete category '{category_id}': {str(e)}")

    @log_execution_time
    def add_subcategory(self, category_id: str, subcategory_data: SubcategoryCreate) -> CategoryModel:
        """
        Add a subcategory to an existing category.

        Args:
            category_id: The ID of the category
            subcategory_data: The subcategory creation data

        Returns:
            Updated CategoryModel instance

        Raises:
            CategoryNotFoundError: If category doesn't exist
            SubcategoryAlreadyExistsError: If subcategory already exists
            InvalidInputError: If input data is invalid
        """
        try:
            # Validate subcategory data
            self._validate_subcategory_data(subcategory_data)

            # Get category to check current state
            category = self.get_category_by_id(category_id)

            # Check if subcategory already exists (case-insensitive)
            existing_names = [sub.name.lower() for sub in category.subcategories]
            if subcategory_data.name.lower() in existing_names:
                raise SubcategoryAlreadyExistsError(category_id, subcategory_data.name)

            # Add subcategory
            updated_category = self._repo.add_subcategory(category_id, subcategory_data)

            logger.info("Subcategory added successfully", {
                "category_id": category_id,
                "category_name": category.name,
                "subcategory_name": subcategory_data.name
            })

            return updated_category

        except (CategoryNotFoundError, SubcategoryAlreadyExistsError, InvalidInputError):
            raise
        except Exception as e:
            logger.error("Failed to add subcategory", {
                "category_id": category_id,
                "subcategory_name": subcategory_data.name,
                "error": str(e)
            })
            raise BusinessLogicError(f"Failed to add subcategory to category '{category_id}': {str(e)}")

    @log_execution_time
    def update_subcategory(self, category_id: str, old_name: str, update_data: SubcategoryUpdate) -> CategoryModel:
        """
        Update a subcategory within a category.

        Args:
            category_id: The ID of the category
            old_name: The current name of the subcategory
            update_data: The update data

        Returns:
            Updated CategoryModel instance

        Raises:
            CategoryNotFoundError: If category doesn't exist
            SubcategoryNotFoundError: If subcategory doesn't exist
            SubcategoryAlreadyExistsError: If updating to existing name
            InvalidInputError: If input data is invalid
        """
        try:
            # Validate update data
            self._validate_subcategory_update_data(update_data)

            # Get category to validate current state
            category = self.get_category_by_id(category_id)

            # Find the subcategory
            sub_exists = any(sub.name.lower() == old_name.lower() for sub in category.subcategories)
            if not sub_exists:
                raise SubcategoryNotFoundError(category_id, old_name)

            # Check for name conflicts if name is being updated
            if update_data.name:
                existing_names = [sub.name.lower() for sub in category.subcategories if sub.name.lower() != old_name.lower()]
                if update_data.name.lower() in existing_names:
                    raise SubcategoryAlreadyExistsError(category_id, update_data.name)

            # Update subcategory
            updated_category = self._repo.update_subcategory(category_id, old_name, update_data)

            logger.info("Subcategory updated successfully", {
                "category_id": category_id,
                "old_name": old_name,
                "new_name": update_data.name
            })

            return updated_category

        except (CategoryNotFoundError, SubcategoryNotFoundError, SubcategoryAlreadyExistsError, InvalidInputError):
            raise
        except Exception as e:
            logger.error("Failed to update subcategory", {
                "category_id": category_id,
                "old_name": old_name,
                "error": str(e)
            })
            raise BusinessLogicError(f"Failed to update subcategory '{old_name}' in category '{category_id}': {str(e)}")

    @log_execution_time
    def remove_subcategory(self, category_id: str, subcategory_name: str) -> bool:
        """
        Remove a subcategory from a category.

        Args:
            category_id: The ID of the category
            subcategory_name: The name of the subcategory to remove

        Returns:
            True if removal was successful

        Raises:
            CategoryNotFoundError: If category doesn't exist
            SubcategoryNotFoundError: If subcategory doesn't exist
        """
        try:
            # Get category to validate current state
            category = self.get_category_by_id(category_id)

            # Find the subcategory
            sub_exists = any(sub.name.lower() == subcategory_name.lower() for sub in category.subcategories)
            if not sub_exists:
                raise SubcategoryNotFoundError(category_id, subcategory_name)

            # Remove subcategory
            success = self._repo.remove_subcategory(category_id, subcategory_name)

            if success:
                logger.info("Subcategory removed successfully", {
                    "category_id": category_id,
                    "category_name": category.name,
                    "subcategory_name": subcategory_name
                })

            return success

        except (CategoryNotFoundError, SubcategoryNotFoundError):
            raise
        except Exception as e:
            logger.error("Failed to remove subcategory", {
                "category_id": category_id,
                "subcategory_name": subcategory_name,
                "error": str(e)
            })
            raise BusinessLogicError(f"Failed to remove subcategory '{subcategory_name}' from category '{category_id}': {str(e)}")

    @log_execution_time
    def seed_default_categories(self) -> List[CategoryModel]:
        """
        Seed the database with default categories if none exist.

        Returns:
            List of created CategoryModel instances
        """
        try:
            created_categories = self._repo.seed_defaults()

            if created_categories:
                logger.info("Default categories seeded successfully", {
                    "count": len(created_categories)
                })
            else:
                logger.info("Default categories already exist, skipping seed")

            return created_categories

        except Exception as e:
            logger.error("Failed to seed default categories", {"error": str(e)})
            raise BusinessLogicError(f"Failed to seed default categories: {str(e)}")

    def _validate_category_data(self, data: CategoryCreate) -> None:
        """
        Validate category creation data with business rules.

        Args:
            data: The category creation data to validate

        Raises:
            InvalidInputError: If validation fails
        """
        if not data.name or not data.name.strip():
            raise InvalidInputError("name", data.name, "Category name is required")

        if len(data.name.strip()) < 2:
            raise InvalidInputError("name", data.name, "Category name must be at least 2 characters")

        if len(data.name.strip()) > 50:
            raise InvalidInputError("name", data.name, "Category name cannot exceed 50 characters")

        # Check for reserved names
        reserved_names = ["uncategorized", "other", "miscellaneous"]
        if data.name.lower().strip() in reserved_names:
            raise InvalidInputError("name", data.name, f"'{data.name}' is a reserved category name")

    def _validate_update_data(self, data: CategoryUpdate) -> None:
        """
        Validate category update data.

        Args:
            data: The category update data to validate

        Raises:
            InvalidInputError: If validation fails
        """
        if data.name is not None:
            if not data.name or not data.name.strip():
                raise InvalidInputError("name", data.name, "Category name cannot be empty")

            if len(data.name.strip()) < 2:
                raise InvalidInputError("name", data.name, "Category name must be at least 2 characters")

            if len(data.name.strip()) > 50:
                raise InvalidInputError("name", data.name, "Category name cannot exceed 50 characters")

    def _validate_subcategory_data(self, data: SubcategoryCreate) -> None:
        """
        Validate subcategory creation data.

        Args:
            data: The subcategory creation data to validate

        Raises:
            InvalidInputError: If validation fails
        """
        if not data.name or not data.name.strip():
            raise InvalidInputError("name", data.name, "Subcategory name is required")

        if len(data.name.strip()) < 1:
            raise InvalidInputError("name", data.name, "Subcategory name must be at least 1 character")

        if len(data.name.strip()) > 50:
            raise InvalidInputError("name", data.name, "Subcategory name cannot exceed 50 characters")

    def _validate_subcategory_update_data(self, data: SubcategoryUpdate) -> None:
        """
        Validate subcategory update data.

        Args:
            data: The subcategory update data to validate

        Raises:
            InvalidInputError: If validation fails
        """
        if data.name is not None:
            if not data.name or not data.name.strip():
                raise InvalidInputError("name", data.name, "Subcategory name cannot be empty")

            if len(data.name.strip()) < 1:
                raise InvalidInputError("name", data.name, "Subcategory name must be at least 1 character")

            if len(data.name.strip()) > 50:
                raise InvalidInputError("name", data.name, "Subcategory name cannot exceed 50 characters")
