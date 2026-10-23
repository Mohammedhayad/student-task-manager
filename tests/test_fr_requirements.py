"""
test_fr_requirements.py - Comprehensive Unit & Integration Tests for FR-1 through FR-7.
"""

import os
import shutil
import tempfile
import pytest
from models import ValidationError, TaskNotFoundError
from task_storage import JsonTaskStorage
from task_service import TaskService
from app import create_app


@pytest.fixture
def temp_storage():
    """Provides an isolated temporary JSON storage file for each test."""
    temp_dir = tempfile.mkdtemp()
    json_path = os.path.join(temp_dir, "test_tasks.json")
    storage = JsonTaskStorage(file_path=json_path)
    service = TaskService(storage=storage)
    yield service, json_path
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_client(temp_storage):
    """Provides a Flask test client with an isolated temporary storage."""
    _, json_path = temp_storage
    app = create_app(storage_path=json_path)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# =====================================================================
# FR-1 — Create: Students can create an academic task.
# =====================================================================
def test_fr1_create_academic_task(temp_storage):
    service, _ = temp_storage
    payload = {
        "title": "CS101 Lab Report",
        "description": "Analyze binary search tree performance",
        "due_date": "2026-11-15",
        "priority": "High",
        "status": "Pending"
    }
    task = service.create_task(payload)

    assert task["id"] == 1
    assert task["title"] == "CS101 Lab Report"
    assert task["description"] == "Analyze binary search tree performance"
    assert task["due_date"] == "2026-11-15"
    assert task["priority"] == "High"
    assert task["status"] == "Pending"
    assert "created_at" in task
    assert "updated_at" in task


# =====================================================================
# FR-2 — Task details: Unique ID, title, description, due date, priority, status.
# =====================================================================
def test_fr2_task_details_fields(temp_storage):
    service, _ = temp_storage
    payload = {
        "title": "Linear Algebra Homework 4",
        "description": "Problems 12 through 20 on eigenvalues",
        "due_date": "2026-12-01",
        "priority": "Medium",
        "status": "In Progress"
    }
    task = service.create_task(payload)

    # Verify all FR-2 mandated fields are present and properly typed
    assert isinstance(task["id"], int)
    assert isinstance(task["title"], str) and task["title"] == "Linear Algebra Homework 4"
    assert isinstance(task["description"], str) and "eigenvalues" in task["description"]
    assert task["due_date"] == "2026-12-01"
    assert task["priority"] in ["Low", "Medium", "High"]
    assert task["status"] in ["Pending", "In Progress", "Completed"]


# =====================================================================
# FR-3 — View: Students can view task list and see each task's details.
# =====================================================================
def test_fr3_view_task_list_and_details(temp_storage):
    service, _ = temp_storage
    t1 = service.create_task({"title": "Essay 1", "due_date": "2026-11-10", "priority": "Low"})
    t2 = service.create_task({"title": "Chemistry Quiz", "due_date": "2026-11-05", "priority": "High"})

    all_tasks = service.list_tasks()
    assert len(all_tasks) == 2

    # Verify viewing single task details by ID
    fetched_t1 = service.get_task(t1["id"])
    assert fetched_t1["title"] == "Essay 1"
    assert fetched_t1["id"] == t1["id"]

    fetched_t2 = service.get_task(t2["id"])
    assert fetched_t2["title"] == "Chemistry Quiz"
    assert fetched_t2["id"] == t2["id"]


# =====================================================================
# FR-4 — Update: Students can update an existing task by its ID.
# =====================================================================
def test_fr4_update_task_by_id(temp_storage):
    service, _ = temp_storage
    task = service.create_task({
        "title": "History Reading",
        "description": "Chapter 4",
        "due_date": "2026-11-20",
        "priority": "Low",
        "status": "Pending"
    })

    # Update title and status
    updated = service.update_task(task["id"], {
        "title": "History Reading - Chapters 4 & 5",
        "status": "In Progress"
    })

    assert updated["id"] == task["id"]
    assert updated["title"] == "History Reading - Chapters 4 & 5"
    assert updated["status"] == "In Progress"
    assert updated["description"] == "Chapter 4"  # Retained unmodified field


# =====================================================================
# FR-5 — Delete: Students can delete an existing task by its ID.
# =====================================================================
def test_fr5_delete_task_by_id(temp_storage):
    service, _ = temp_storage
    task = service.create_task({"title": "Delete Me", "due_date": "2026-11-01"})
    task_id = task["id"]

    # Delete the task
    assert service.delete_task(task_id) is True

    # Subsequent view should no longer include the deleted task
    all_tasks = service.list_tasks()
    assert all(t["id"] != task_id for t in all_tasks)

    # Direct query should fail
    with pytest.raises(TaskNotFoundError):
        service.get_task(task_id)


# =====================================================================
# FR-6 — Error handling: Distinguishes unknown IDs, reports invalid input,
# does not report failed operation as successful.
# =====================================================================
def test_fr6_unknown_task_id(temp_storage):
    service, _ = temp_storage
    # Trying to get an unknown task ID
    with pytest.raises(TaskNotFoundError) as exc_info:
        service.get_task(9999)
    assert "Task with ID 9999 does not exist" in str(exc_info.value)

    # Trying to update an unknown task ID
    with pytest.raises(TaskNotFoundError):
        service.update_task(9999, {"title": "Ghost Task"})

    # Trying to delete an unknown task ID
    with pytest.raises(TaskNotFoundError):
        service.delete_task(9999)


def test_fr6_invalid_input_validation(temp_storage):
    service, _ = temp_storage

    # Empty title
    with pytest.raises(ValidationError) as exc:
        service.create_task({"title": "", "due_date": "2026-11-01"})
    assert "title" in exc.value.errors

    # Whitespace only title
    with pytest.raises(ValidationError) as exc:
        service.create_task({"title": "   ", "due_date": "2026-11-01"})
    assert "title" in exc.value.errors

    # Invalid date format
    with pytest.raises(ValidationError) as exc:
        service.create_task({"title": "Math Quiz", "due_date": "not-a-date"})
    assert "due_date" in exc.value.errors

    # Invalid calendar date (e.g. month 13)
    with pytest.raises(ValidationError) as exc:
        service.create_task({"title": "Math Quiz", "due_date": "2026-13-45"})
    assert "due_date" in exc.value.errors

    # Invalid priority
    with pytest.raises(ValidationError) as exc:
        service.create_task({"title": "Math Quiz", "due_date": "2026-11-01", "priority": "Urgent"})
    assert "priority" in exc.value.errors

    # Invalid status
    with pytest.raises(ValidationError) as exc:
        service.create_task({"title": "Math Quiz", "due_date": "2026-11-01", "status": "Finished"})
    assert "status" in exc.value.errors


# =====================================================================
# FR-7 — ID integrity:
# ID identifies at most one task.
# Updating a task retains its ID.
# Deleting a task removes it from subsequent views.
# =====================================================================
def test_fr7_id_integrity(temp_storage):
    service, _ = temp_storage
    t1 = service.create_task({"title": "Task 1", "due_date": "2026-11-01"})
    t2 = service.create_task({"title": "Task 2", "due_date": "2026-11-02"})

    assert t1["id"] != t2["id"]

    # Updating task retains its ID even if payload attempts to change it
    updated_t1 = service.update_task(t1["id"], {"id": 999, "title": "Updated Task 1"})
    assert updated_t1["id"] == t1["id"]
    assert updated_t1["id"] != 999

    # Delete task 1
    service.delete_task(t1["id"])
    views_after_delete = service.list_tasks()
    assert all(t["id"] != t1["id"] for t in views_after_delete)
    assert len(views_after_delete) == 1
    assert views_after_delete[0]["id"] == t2["id"]

    # Creating a new task does NOT collide with previous IDs
    t3 = service.create_task({"title": "Task 3", "due_date": "2026-11-03"})
    assert t3["id"] > t2["id"]
    assert t3["id"] != t1["id"]


# =====================================================================
# REST API Client Tests for FR-1 through FR-7
# =====================================================================
def test_api_crud_workflow(test_client):
    # 1. Create (FR-1, FR-2)
    resp = test_client.post("/api/tasks", json={
        "title": "Bio 101 Midterm Prep",
        "description": "Cellular respiration & photosynthesis",
        "due_date": "2026-11-25",
        "priority": "High",
        "status": "In Progress"
    })
    assert resp.status_code == 201
    res_data = resp.get_json()
    assert res_data["success"] is True
    task_id = res_data["data"]["id"]

    # 2. View (FR-3)
    resp_list = test_client.get("/api/tasks")
    assert resp_list.status_code == 200
    assert len(resp_list.get_json()["data"]) == 1

    resp_single = test_client.get(f"/api/tasks/{task_id}")
    assert resp_single.status_code == 200
    assert resp_single.get_json()["data"]["title"] == "Bio 101 Midterm Prep"

    # 3. Update (FR-4, FR-7)
    resp_update = test_client.put(f"/api/tasks/{task_id}", json={
        "status": "Completed"
    })
    assert resp_update.status_code == 200
    assert resp_update.get_json()["data"]["status"] == "Completed"
    assert resp_update.get_json()["data"]["id"] == task_id  # ID retained

    # 4. Delete (FR-5, FR-7)
    resp_delete = test_client.delete(f"/api/tasks/{task_id}")
    assert resp_delete.status_code == 200
    assert resp_delete.get_json()["success"] is True

    # 5. Subsequent View (FR-7)
    resp_after = test_client.get(f"/api/tasks/{task_id}")
    assert resp_after.status_code == 404
    assert resp_after.get_json()["success"] is False
    assert "does not exist" in resp_after.get_json()["error"]
