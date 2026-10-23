"""
task_service.py - Core Business Logic and Operations for Academic Tasks.
Implements FR-1 through FR-7 and enforces NFR-1, NFR-2, and NFR-4.
"""

from datetime import datetime, date
from typing import List, Dict, Any, Optional
from models import (
    Task,
    validate_task_payload,
    ValidationError,
    TaskNotFoundError,
    VALID_PRIORITIES,
    VALID_STATUSES
)
from task_storage import JsonTaskStorage, StorageError


class TaskService:
    """
    Service layer providing CRUD operations and business rule enforcement.
    """

    def __init__(self, storage: Optional[JsonTaskStorage] = None):
        self.storage = storage or JsonTaskStorage()

    def _parse_task_id(self, task_id: Any) -> int:
        """
        Parses and validates a task ID to an integer.
        Raises ValidationError if invalid.
        """
        if task_id is None:
            raise ValidationError("Task ID cannot be None.")
        try:
            val = int(task_id)
            if val <= 0:
                raise ValueError()
            return val
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid task ID '{task_id}'. Task ID must be a positive integer.")

    def create_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        FR-1: Students can create an academic task.
        FR-2: Validates all details (title, description, due date, priority, status).
        FR-6: Reports invalid input and failed operations.
        FR-7: Assigns a strictly unique ID.
        """
        cleaned = validate_task_payload(data, is_update=False)

        # Thread-safe persistent allocation of next ID
        raw = self.storage.load_raw_data()
        metadata = raw.setdefault("metadata", {})
        next_id = metadata.get("next_id", 1)

        # Check existing IDs to enforce ID integrity (FR-7: ID identifies at most one task)
        existing_ids = {t["id"] for t in raw.get("tasks", [])}
        while next_id in existing_ids:
            next_id += 1

        now_str = datetime.now().isoformat()
        new_task = Task(
            id=next_id,
            title=cleaned["title"],
            description=cleaned.get("description", ""),
            due_date=cleaned["due_date"],
            priority=cleaned.get("priority", "Medium"),
            status=cleaned.get("status", "Pending"),
            created_at=now_str,
            updated_at=now_str
        )

        raw.setdefault("tasks", []).append(new_task.to_dict())
        metadata["next_id"] = next_id + 1
        self.storage.save_raw_data(raw)

        return new_task.to_dict()

    def get_task(self, task_id: Any) -> Dict[str, Any]:
        """
        FR-3: Students can see task details by ID.
        FR-6: Distinguishes unknown task IDs from existing tasks.
        """
        parsed_id = self._parse_task_id(task_id)
        raw = self.storage.load_raw_data()
        tasks = raw.get("tasks", [])

        for task in tasks:
            if task.get("id") == parsed_id:
                return dict(task)

        raise TaskNotFoundError(parsed_id)

    def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = "due_date",
        sort_order: Optional[str] = "asc"
    ) -> List[Dict[str, Any]]:
        """
        FR-3: Students can view their task list and see each task's ID and details.
        Supports filtering, searching, and sorting for high usability (NFR-1, NFR-4).
        """
        raw = self.storage.load_raw_data()
        tasks = raw.get("tasks", [])

        results = list(tasks)

        # Filter by status
        if status and status.strip() and status.lower() != "all":
            norm_status = status.strip().lower()
            results = [t for t in results if t.get("status", "").lower() == norm_status]

        # Filter by priority
        if priority and priority.strip() and priority.lower() != "all":
            norm_priority = priority.strip().lower()
            results = [t for t in results if t.get("priority", "").lower() == norm_priority]

        # Search query (matches title or description)
        if search and search.strip():
            q = search.strip().lower()
            results = [
                t for t in results
                if q in t.get("title", "").lower() or q in t.get("description", "").lower()
            ]

        # Sorting logic
        priority_order = {"High": 1, "Medium": 2, "Low": 3}

        def get_sort_key(task: Dict[str, Any]):
            if sort_by == "priority":
                return priority_order.get(task.get("priority", "Medium"), 4)
            elif sort_by == "title":
                return task.get("title", "").lower()
            elif sort_by == "id":
                return task.get("id", 0)
            elif sort_by == "status":
                return task.get("status", "").lower()
            else:  # default to due_date
                return task.get("due_date", "9999-99-99")

        reverse = (sort_order.lower() == "desc") if sort_order else False
        results.sort(key=get_sort_key, reverse=reverse)

        return results

    def update_task(self, task_id: Any, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        FR-4: Students can update an existing task by its ID.
        FR-6: Distinguishes unknown task IDs from existing tasks; reports invalid input.
        FR-7: ID integrity: Updating a task retains its ID.
        """
        parsed_id = self._parse_task_id(task_id)
        cleaned = validate_task_payload(updates, is_update=True)

        raw = self.storage.load_raw_data()
        tasks = raw.get("tasks", [])

        target_index = -1
        for i, t in enumerate(tasks):
            if t.get("id") == parsed_id:
                target_index = i
                break

        if target_index == -1:
            raise TaskNotFoundError(parsed_id)

        current_task = tasks[target_index]

        # FR-7: Updating a task retains its ID unconditionally
        for field, value in cleaned.items():
            if field != "id":
                current_task[field] = value

        current_task["updated_at"] = datetime.now().isoformat()
        tasks[target_index] = current_task

        self.storage.save_raw_data(raw)
        return dict(current_task)

    def delete_task(self, task_id: Any) -> bool:
        """
        FR-5: Students can delete an existing task by its ID.
        FR-6: Distinguishes unknown task IDs from existing tasks.
        FR-7: Deleting a task removes it from subsequent views.
        """
        parsed_id = self._parse_task_id(task_id)

        raw = self.storage.load_raw_data()
        tasks = raw.get("tasks", [])

        initial_len = len(tasks)
        filtered = [t for t in tasks if t.get("id") != parsed_id]

        if len(filtered) == initial_len:
            # Task was not found (FR-6)
            raise TaskNotFoundError(parsed_id)

        raw["tasks"] = filtered
        self.storage.save_raw_data(raw)
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Calculates summary statistics for student dashboard (NFR-1 Usability)."""
        tasks = self.list_tasks()
        total = len(tasks)
        completed = sum(1 for t in tasks if t.get("status") == "Completed")
        in_progress = sum(1 for t in tasks if t.get("status") == "In Progress")
        pending = sum(1 for t in tasks if t.get("status") == "Pending")

        today_str = date.today().strftime("%Y-%m-%d")
        overdue = sum(
            1 for t in tasks
            if t.get("status") != "Completed" and t.get("due_date", "") < today_str
        )
        due_today = sum(
            1 for t in tasks
            if t.get("status") != "Completed" and t.get("due_date", "") == today_str
        )

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "overdue": overdue,
            "due_today": due_today
        }
