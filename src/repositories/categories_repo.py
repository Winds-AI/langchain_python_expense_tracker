"""
MongoDB CRUD operations for categories and subcategories.
Provides comprehensive data access layer with error handling and logging.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any

from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError as MongoDuplicateKeyError
from bson import ObjectId

from src.models.category import (
    CategoryModel, CategoryCreate, CategoryUpdate,
    SubcategoryCreate, SubcategoryUpdate, SubcategoryModel
)
from src.utils.exceptions import (
    handle_database_error, CategoryNotFoundError, CategoryAlreadyExistsError,
    SubcategoryNotFoundError, SubcategoryAlreadyExistsError, DuplicateKeyError
)
from src.utils.logger import logger, log_database_operation


class CategoriesRepository:
    """
    Repository for managing categories and subcategories in MongoDB.

    Handles all CRUD operations with proper error handling, validation,
    and logging for category management.
    """

    def __init__(self, db: Database):
        self._db = db
        self._categories: Collection = db["categories"]
        self._ensure_indexes()

    @staticmethod
    def _to_object_id(category_id: str) -> ObjectId:
        """Normalize a category id (string/ObjectId) to ObjectId for queries."""
        if isinstance(category_id, ObjectId):
            return category_id
        try:
            return ObjectId(str(category_id))
        except Exception:
            # Raise explicit error instead of returning an empty ObjectId
            raise ValueError(f"Invalid ObjectId: {category_id}")

    def _ensure_indexes(self):
        """Create necessary indexes for optimal query performance."""
        try:
            # Unique index on category name (case-insensitive)
            self._categories.create_index(
                [("name", 1)],
                unique=True,
                collation={"locale": "en", "strength": 2}  # Case-insensitive
            )
            # Ensure subcategories array index for efficient operations
            self._categories.create_index("subcategories.name")
            # Index on is_active for filtering
            self._categories.create_index("is_active")
            # Index on sort_order for ordering
            self._categories.create_index("sort_order")
            # Index on created_at for sorting
            self._categories.create_index("created_at")
            logger.info("Categories indexes ensured")
        except Exception as e:
            logger.error("Failed to create categories indexes", {"error": str(e)})
            raise

    @log_database_operation("categories", "find_all")
    def find_all(self, include_inactive: bool = False) -> List[CategoryModel]:
        """
        Find all categories with optional filtering.

        Args:
            include_inactive: Whether to include inactive categories

        Returns:
            List of CategoryModel instances
        """
        try:
            query = {}
            if not include_inactive:
                query["is_active"] = True

            categories = list(self._categories.find(query).sort("sort_order"))
            return [CategoryModel(**cat) for cat in categories]
        except Exception as e:
            logger.error("Failed to find categories", {"include_inactive": include_inactive, "error": str(e)})
            raise handle_database_error(e, "find_all", "categories")

    @log_database_operation("categories", "find_by_id")
    def find_by_id(self, category_id: str) -> CategoryModel:
        """
        Find a category by its ID.

        Args:
            category_id: The category ID to find

        Returns:
            CategoryModel instance

        Raises:
            CategoryNotFoundError: If category doesn't exist
        """
        try:
            category = self._categories.find_one({"_id": self._to_object_id(category_id)})
            if not category:
                raise CategoryNotFoundError(category_id)
            return CategoryModel(**category)
        except CategoryNotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to find category by ID", {"category_id": category_id, "error": str(e)})
            raise handle_database_error(e, "find_by_id", "categories")

    @log_database_operation("categories", "find_by_name")
    def find_by_name(self, name: str) -> Optional[CategoryModel]:
        """
        Find a category by name (case-insensitive).

        Args:
            name: The category name to search for

        Returns:
            CategoryModel instance or None if not found
        """
        try:
            # Use collation for case-insensitive search
            category = self._categories.find_one(
                {"name": name},
                collation={"locale": "en", "strength": 2}
            )
            return CategoryModel(**category) if category else None
        except Exception as e:
            logger.error("Failed to find category by name", {"name": name, "error": str(e)})
            raise handle_database_error(e, "find_by_name", "categories")

    @log_database_operation("categories", "create")
    def create(self, category_data: CategoryCreate) -> CategoryModel:
        """
        Create a new category.

        Args:
            category_data: The category data to create

        Returns:
            Created CategoryModel instance

        Raises:
            CategoryAlreadyExistsError: If category with same name exists
        """
        try:
            # Check if category already exists
            existing = self.find_by_name(category_data.name)
            if existing:
                raise CategoryAlreadyExistsError(category_data.name)

            # Create new category
            category_dict = category_data.model_dump()
            category_dict.update({
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })

            result = self._categories.insert_one(category_dict)
            category_dict["_id"] = result.inserted_id

            logger.info("Category created successfully", {"category_id": str(result.inserted_id), "name": category_data.name})
            return CategoryModel(**category_dict)

        except CategoryAlreadyExistsError:
            raise
        except MongoDuplicateKeyError:
            raise CategoryAlreadyExistsError(category_data.name)
        except Exception as e:
            logger.error("Failed to create category", {"name": category_data.name, "error": str(e)})
            raise handle_database_error(e, "create", "categories")

    @log_database_operation("categories", "update")
    def update(self, category_id: str, update_data: CategoryUpdate) -> CategoryModel:
        """
        Update an existing category.

        Args:
            category_id: The ID of the category to update
            update_data: The update data

        Returns:
            Updated CategoryModel instance

        Raises:
            CategoryNotFoundError: If category doesn't exist
            CategoryAlreadyExistsError: If updating to existing name
        """
        try:
            # Check if category exists
            existing = self.find_by_id(category_id)

            # Prepare update data
            update_dict = update_data.model_dump(exclude_unset=True)
            if update_dict:
                update_dict["updated_at"] = datetime.utcnow()

                # Check name conflict if name is being updated
                if "name" in update_dict:
                    name_conflict = self.find_by_name(update_dict["name"])
                    if name_conflict and str(name_conflict.id) != category_id:
                        raise CategoryAlreadyExistsError(update_dict["name"])

                # Perform update
                result = self._categories.update_one(
                    {"_id": self._to_object_id(category_id)},
                    {"$set": update_dict}
                )

                if result.modified_count == 0:
                    logger.warning("Category update resulted in no changes", {"category_id": category_id})

            # Return updated category
            return self.find_by_id(category_id)

        except (CategoryNotFoundError, CategoryAlreadyExistsError):
            raise
        except MongoDuplicateKeyError:
            if "name" in update_data.model_dump(exclude_unset=True):
                raise CategoryAlreadyExistsError(update_data.name)
            raise
        except Exception as e:
            logger.error("Failed to update category", {"category_id": category_id, "error": str(e)})
            raise handle_database_error(e, "update", "categories")

    @log_database_operation("categories", "delete")
    def delete(self, category_id: str) -> bool:
        """
        Delete a category (soft delete by setting is_active=False).

        Args:
            category_id: The ID of the category to delete

        Returns:
            True if deletion was successful

        Raises:
            CategoryNotFoundError: If category doesn't exist
        """
        try:
            # Check if category exists
            self.find_by_id(category_id)

            # Soft delete by setting is_active=False
            result = self._categories.update_one(
                {"_id": self._to_object_id(category_id)},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )

            success = result.modified_count > 0
            logger.info("Category deleted (soft)", {"category_id": category_id, "success": success})
            return success

        except CategoryNotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to delete category", {"category_id": category_id, "error": str(e)})
            raise handle_database_error(e, "delete", "categories")

    @log_database_operation("categories", "hard_delete")
    def hard_delete(self, category_id: str) -> bool:
        """
        Permanently delete a category.

        Args:
            category_id: The ID of the category to delete

        Returns:
            True if deletion was successful

        Raises:
            CategoryNotFoundError: If category doesn't exist
        """
        try:
            # Check if category exists
            self.find_by_id(category_id)

            result = self._categories.delete_one({"_id": self._to_object_id(category_id)})
            success = result.deleted_count > 0

            logger.warning("Category hard deleted", {"category_id": category_id, "success": success})
            return success

        except CategoryNotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to hard delete category", {"category_id": category_id, "error": str(e)})
            raise handle_database_error(e, "hard_delete", "categories")

    @log_database_operation("categories", "add_subcategory")
    def add_subcategory(self, category_id: str, subcategory_data: SubcategoryCreate) -> CategoryModel:
        """
        Add a subcategory to a category.

        Args:
            category_id: The ID of the category
            subcategory_data: The subcategory data to add

        Returns:
            Updated CategoryModel instance

        Raises:
            CategoryNotFoundError: If category doesn't exist
            SubcategoryAlreadyExistsError: If subcategory already exists
        """
        try:
            # Get current category
            category = self.find_by_id(category_id)

            # Check if subcategory already exists
            existing_names = [sub.name.lower() for sub in category.subcategories]
            if subcategory_data.name.lower() in existing_names:
                raise SubcategoryAlreadyExistsError(category_id, subcategory_data.name)

            # Create new subcategory
            new_subcategory = SubcategoryModel(
                name=subcategory_data.name,
                description=subcategory_data.description
            )

            # Add to category
            update_result = self._categories.update_one(
                {"_id": self._to_object_id(category_id)},
                {
                    "$push": {"subcategories": new_subcategory.model_dump()},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )

            if update_result.modified_count == 0:
                raise Exception("Failed to add subcategory")

            logger.info("Subcategory added", {
                "category_id": category_id,
                "subcategory_name": subcategory_data.name
            })

            # Return updated category
            return self.find_by_id(category_id)

        except (CategoryNotFoundError, SubcategoryAlreadyExistsError):
            raise
        except Exception as e:
            logger.error("Failed to add subcategory", {
                "category_id": category_id,
                "subcategory_name": subcategory_data.name,
                "error": str(e)
            })
            raise handle_database_error(e, "add_subcategory", "categories")

    @log_database_operation("categories", "update_subcategory")
    def update_subcategory(self, category_id: str, old_name: str, update_data: SubcategoryUpdate) -> CategoryModel:
        """
        Update a subcategory in a category.

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
        """
        try:
            # Get current category
            category = self.find_by_id(category_id)

            # Find subcategory index
            sub_index = None
            for i, sub in enumerate(category.subcategories):
                if sub.name.lower() == old_name.lower():
                    sub_index = i
                    break

            if sub_index is None:
                raise SubcategoryNotFoundError(category_id, old_name)

            # Check name conflict if name is being updated
            if update_data.name:
                existing_names = [sub.name.lower() for i, sub in enumerate(category.subcategories) if i != sub_index]
                if update_data.name.lower() in existing_names:
                    raise SubcategoryAlreadyExistsError(category_id, update_data.name)

            # Prepare update
            update_dict = update_data.model_dump(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()

            # Update subcategory in array
            result = self._categories.update_one(
                {"_id": self._to_object_id(category_id), "subcategories.name": old_name},
                {
                    "$set": {
                        f"subcategories.{sub_index}.name": update_data.name or category.subcategories[sub_index].name,
                        f"subcategories.{sub_index}.description": update_data.description,
                        f"subcategories.{sub_index}.updated_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                },
                collation={"locale": "en", "strength": 2}
            )

            if result.modified_count == 0:
                raise Exception("Failed to update subcategory")

            logger.info("Subcategory updated", {
                "category_id": category_id,
                "old_name": old_name,
                "new_name": update_data.name
            })

            return self.find_by_id(category_id)

        except (CategoryNotFoundError, SubcategoryNotFoundError, SubcategoryAlreadyExistsError):
            raise
        except Exception as e:
            logger.error("Failed to update subcategory", {
                "category_id": category_id,
                "old_name": old_name,
                "error": str(e)
            })
            raise handle_database_error(e, "update_subcategory", "categories")

    @log_database_operation("categories", "remove_subcategory")
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
            # Get current category
            category = self.find_by_id(category_id)

            # Check if subcategory exists
            sub_exists = any(sub.name.lower() == subcategory_name.lower() for sub in category.subcategories)
            if not sub_exists:
                raise SubcategoryNotFoundError(category_id, subcategory_name)

            # Remove subcategory
            result = self._categories.update_one(
                {"_id": self._to_object_id(category_id)},
                {
                    "$pull": {"subcategories": {"name": subcategory_name}},
                    "$set": {"updated_at": datetime.utcnow()}
                },
                collation={"locale": "en", "strength": 2}
            )

            success = result.modified_count > 0
            logger.info("Subcategory removed", {
                "category_id": category_id,
                "subcategory_name": subcategory_name,
                "success": success
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
            raise handle_database_error(e, "remove_subcategory", "categories")

    @log_database_operation("categories", "seed_defaults")
    def seed_defaults(self) -> List[CategoryModel]:
        """
        Seed the database with default categories if none exist.

        Returns:
            List of created CategoryModel instances
        """
        try:
            # Check if categories already exist
            existing_count = self._categories.count_documents({})
            if existing_count > 0:
                logger.info("Categories already seeded", {"count": existing_count})
                return []

            # Default categories with subcategories
            default_categories = [
                {
                    "name": "Food & Dining",
                    "description": "Expenses related to food and dining",
                    "color": "#FF6B6B",
                    "icon": "🍽️",
                    "sort_order": 1,
                    "subcategories": [
                        {"name": "Breakfast", "description": "Morning meals"},
                        {"name": "Lunch", "description": "Midday meals"},
                        {"name": "Dinner", "description": "Evening meals"},
                        {"name": "Snacks", "description": "Light snacks and beverages"},
                        {"name": "Restaurant", "description": "Restaurant dining"},
                        {"name": "Delivery", "description": "Food delivery services"}
                    ]
                },
                {
                    "name": "Transportation",
                    "description": "Travel and commuting expenses",
                    "color": "#4ECDC4",
                    "icon": "🚗",
                    "sort_order": 2,
                    "subcategories": [
                        {"name": "Bus", "description": "Public bus transportation"},
                        {"name": "Taxi", "description": "Taxi and ride-sharing services"},
                        {"name": "Train", "description": "Train and metro services"},
                        {"name": "Fuel", "description": "Vehicle fuel expenses"},
                        {"name": "Parking", "description": "Parking fees"},
                        {"name": "Maintenance", "description": "Vehicle maintenance"}
                    ]
                },
                {
                    "name": "Entertainment",
                    "description": "Leisure and entertainment expenses",
                    "color": "#45B7D1",
                    "icon": "🎬",
                    "sort_order": 3,
                    "subcategories": [
                        {"name": "Movies", "description": "Cinema and movie tickets"},
                        {"name": "Games", "description": "Video games and gaming"},
                        {"name": "Music", "description": "Music and concerts"},
                        {"name": "Events", "description": "Live events and shows"},
                        {"name": "Books", "description": "Books and publications"},
                        {"name": "Streaming", "description": "Streaming services"}
                    ]
                },
                {
                    "name": "Utilities",
                    "description": "Household and utility bills",
                    "color": "#96CEB4",
                    "icon": "💡",
                    "sort_order": 4,
                    "subcategories": [
                        {"name": "Electricity", "description": "Electricity bills"},
                        {"name": "Water", "description": "Water supply bills"},
                        {"name": "Internet", "description": "Internet service"},
                        {"name": "Phone", "description": "Mobile and landline"},
                        {"name": "Gas", "description": "Gas supply bills"},
                        {"name": "Other", "description": "Other utility services"}
                    ]
                },
                {
                    "name": "Healthcare",
                    "description": "Medical and health-related expenses",
                    "color": "#FECA57",
                    "icon": "🏥",
                    "sort_order": 5,
                    "subcategories": [
                        {"name": "Doctor", "description": "Doctor consultations"},
                        {"name": "Medicine", "description": "Medicines and pharmaceuticals"},
                        {"name": "Hospital", "description": "Hospital visits and treatments"},
                        {"name": "Insurance", "description": "Health insurance premiums"},
                        {"name": "Dental", "description": "Dental care"},
                        {"name": "Optical", "description": "Eye care and glasses"}
                    ]
                }
            ]

            created_categories = []
            for cat_data in default_categories:
                try:
                    # Convert subcategory dicts to SubcategoryModel
                    subcategories = []
                    for sub_data in cat_data.pop("subcategories", []):
                        subcategories.append(SubcategoryModel(**sub_data))

                    # Create category
                    category_data = CategoryCreate(**cat_data)
                    category = self.create(category_data)

                    # Add subcategories
                    for subcategory in subcategories:
                        self.add_subcategory(str(category.id), SubcategoryCreate(
                            name=subcategory.name,
                            description=subcategory.description
                        ))

                    created_categories.append(category)

                except Exception as e:
                    logger.error("Failed to create default category", {
                        "category_name": cat_data["name"],
                        "error": str(e)
                    })

            logger.info("Default categories seeded", {"count": len(created_categories)})
            return created_categories

        except Exception as e:
            logger.error("Failed to seed default categories", {"error": str(e)})
            raise handle_database_error(e, "seed_defaults", "categories")
