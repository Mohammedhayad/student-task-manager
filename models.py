"""
models.py - Data structures and validation rules for Academic Tasks.
Supports FR-2, FR-6, FR-7, and NFR-2.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, date
from typing import Optional, Dict, Any, List

VALID_PRIORITIES: List[str] = ["Low", "Medium", "High"]
VALID_STATUSES: List[str] = ["Pending", "In Progress", "Completed"]


class ValidationError(Exception):
    """Raised when task input data fails validation."""
    def __init__(self, message: str, errors: Optional[Dict[str, str]] = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or {}


class TaskNotFoundError(Exception):
    """Raised when a task with the specified ID is not found (FR-6)."""
    def __init__(self, task_id: Any):
        super().__init__(f"Task with ID {task_id} does not exist.")
        self.task_id = task_id


@dataclass
class Task:
    """
    Academic Task data model.
    FR-2: Each task has a unique ID, title, description, due date, priority, and completion status.
    """
    id: int
    title: str
    description: str
    due_date: str          # YYYY-MM-DD
    priority: str          # Low, Medium, High
    status: str            # Pending, In Progress, Completed
    created_at: str        # ISO format
    updated_at: str        # ISO format

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        return cls(
            id=int(data["id"]),
            title=str(data["title"]),
            description=str(data.get("description", "")),
            due_date=str(data["due_date"]),
            priority=str(data["priority"]),
            status=str(data.get("status", "Pending")),
            created_at=str(data.get("created_at", datetime.now().isoformat())),
            updated_at=str(data.get("updated_at", datetime.now().isoformat())),
        )


def validate_date_string(date_str: str) -> str:
    """
    Validates that date_str is a valid YYYY-MM-DD calendar date.
    Returns the normalized date string or raises ValueError.
    """
    if not isinstance(date_str, str):
        raise ValueError("Due date must be a string in YYYY-MM-DD format.")
    
    date_str = date_str.strip()
    if not date_str:
        raise ValueError("Due date is required.")
        
    try:
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format: '{date_str}'. Expected format is YYYY-MM-DD (e.g., 2026-10-31).")
        
    # Standardize to YYYY-MM-DD string
    return parsed_date.strftime("%Y-%m-%d")


def validate_task_payload(data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
    """
    Validates and cleans input data for creating or updating a task.
    Enforces FR-2, FR-6, and NFR-2 (input validation).
    
    :param data: The raw dictionary of user input.
    :param is_update: If True, partial updates are allowed unless fields are explicitly provided.
    :return: Cleaned and normalized dictionary.
    :raises ValidationError: If any field fails validation.
    """
    if not isinstance(data, dict):
        raise ValidationError("Request payload must be a JSON object.")

    errors: Dict[str, str] = {}
    cleaned: Dict[str, Any] = {}

    # Check for ID tampering on update (FR-7)
    if is_update and "id" in data:
        # We do not allow changing ID in the payload. Note: The service layer protects the original ID.
        pass

    # Title validation
    if "title" in data or not is_update:
        title = data.get("title")
        if title is None:
            errors["title"] = "Title is required."
        elif not isinstance(title, str) or not title.strip():
            errors["title"] = "Title cannot be empty or blank."
        elif len(title.strip()) > 200:
            errors["title"] = "Title must not exceed 200 characters."
        else:
            cleaned["title"] = title.strip()

    # Description validation
    if "description" in data or not is_update:
        desc = data.get("description", "")
        if desc is None:
            cleaned["description"] = ""
        elif not isinstance(desc, str):
            errors["description"] = "Description must be text."
        elif len(desc) > 3000:
            errors["description"] = "Description must not exceed 3000 characters."
        else:
            cleaned["description"] = desc.strip()

    # Due date validation
    if "due_date" in data or not is_update:
        due_date = data.get("due_date")
        if not due_date:
            errors["due_date"] = "Due date is required."
        else:
            try:
                cleaned["due_date"] = validate_date_string(str(due_date))
            except ValueError as ve:
                errors["due_date"] = str(ve)

    # Priority validation
    if "priority" in data or not is_update:
        priority = data.get("priority")
        if not priority:
            # Default to Medium if not specified during creation
            if not is_update:
                cleaned["priority"] = "Medium"
            else:
                errors["priority"] = f"Priority is required. Allowed values: {', '.join(VALID_PRIORITIES)}."
        elif not isinstance(priority, str):
            errors["priority"] = f"Priority must be text. Allowed values: {', '.join(VALID_PRIORITIES)}."
        else:
            norm_priority = priority.strip().title()
            if norm_priority not in VALID_PRIORITIES:
                errors["priority"] = f"Invalid priority '{priority}'. Allowed values: {', '.join(VALID_PRIORITIES)}."
            else:
                cleaned["priority"] = norm_priority

    # Status validation
    if "status" in data or not is_update:
        status = data.get("status")
        if not status:
            # Default to Pending during creation
            if not is_update:
                cleaned["status"] = "Pending"
            else:
                errors["status"] = f"Status is required. Allowed values: {', '.join(VALID_STATUSES)}."
        elif not isinstance(status, str):
            errors["status"] = f"Status must be text. Allowed values: {', '.join(VALID_STATUSES)}."
        else:
            norm_status = status.strip().title()
            # Handle special casing like "In Progress"
            if norm_status.lower() == "in progress":
                norm_status = "In Progress"
            if norm_status not in VALID_STATUSES:
                errors["status"] = f"Invalid status '{status}'. Allowed values: {', '.join(VALID_STATUSES)}."
            else:
                cleaned["status"] = norm_status

    if errors:
        raise ValidationError("Input validation failed.", errors=errors)

    return cleaned
