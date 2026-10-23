"""
test_nfr_requirements.py - Tests for Non-Functional Requirements NFR-1 through NFR-5.
"""

import os
import time
import shutil
import tempfile
import pytest
from models import ValidationError
from task_storage import JsonTaskStorage, StorageError
from task_service import TaskService


@pytest.fixture
def temp_storage():
    temp_dir = tempfile.mkdtemp()
    json_path = os.path.join(temp_dir, "test_tasks.json")
    storage = JsonTaskStorage(file_path=json_path)
    service = TaskService(storage=storage)
    yield service, json_path
    shutil.rmtree(temp_dir, ignore_errors=True)


# =====================================================================
# NFR-1 — Usability: Clear labels and understandable feedback
# =====================================================================
def test_nfr1_understandable_error_feedback(temp_storage):
    service, _ = temp_storage
    try:
        service.create_task({"title": "", "due_date": "invalid-date", "priority": "Unknown"})
    except ValidationError as ve:
        # Check that error feedback is specific, field-by-field, and understandable
        assert "title" in ve.errors
        assert "Title cannot be empty" in ve.errors["title"]
        assert "due_date" in ve.errors
        assert "YYYY-MM-DD" in ve.errors["due_date"]
        assert "priority" in ve.errors
        assert "Allowed values" in ve.errors["priority"]


# =====================================================================
# NFR-2 — Data integrity:
# Operations do not silently corrupt or misidentify tasks.
# Invalid input does not corrupt storage.
# =====================================================================
def test_nfr2_data_integrity_on_invalid_input(temp_storage):
    service, json_path = temp_storage
    t1 = service.create_task({"title": "Initial Task", "due_date": "2026-11-10"})

    # Attempt an invalid update
    with pytest.raises(ValidationError):
        service.update_task(t1["id"], {"title": ""})

    # Storage must remain uncorrupted and intact
    fetched = service.get_task(t1["id"])
    assert fetched["title"] == "Initial Task"


def test_nfr2_corrupted_file_detection_and_backup(temp_storage):
    service, json_path = temp_storage
    service.create_task({"title": "Existing", "due_date": "2026-11-10"})

    # Simulate catastrophic file corruption (e.g., power failure during external edit)
    with open(json_path, "w", encoding="utf-8") as f:
        f.write("{invalid-json-content-here")

    # Accessing storage must detect corruption, save a backup, and report error
    with pytest.raises(StorageError) as exc_info:
        service.list_tasks()

    assert "Corrupted task storage file detected" in str(exc_info.value)
    # Verify backup exists
    dir_files = os.listdir(os.path.dirname(json_path))
    corrupt_backups = [f for f in dir_files if "corrupt" in f]
    assert len(corrupt_backups) > 0


# =====================================================================
# NFR-3 — Reliability:
# Successfully saved tasks remain available after restart.
# =====================================================================
def test_nfr3_persistence_across_restart(temp_storage):
    service1, json_path = temp_storage

    # Student creates tasks in session 1
    t1 = service1.create_task({"title": "Physics Lab", "due_date": "2026-11-12", "priority": "High"})
    t2 = service1.create_task({"title": "English Paper", "due_date": "2026-11-20", "priority": "Medium"})

    # Simulate restart by instantiating a brand-new service and storage pointing to the same file
    service2 = TaskService(storage=JsonTaskStorage(file_path=json_path))
    reloaded_tasks = service2.list_tasks()

    assert len(reloaded_tasks) == 2
    assert reloaded_tasks[0]["title"] in ["Physics Lab", "English Paper"]
    assert reloaded_tasks[1]["title"] in ["Physics Lab", "English Paper"]
    assert service2.get_task(t1["id"])["title"] == "Physics Lab"


# =====================================================================
# NFR-4 — Performance:
# Viewing and updating normal student-sized lists feels responsive.
# =====================================================================
def test_nfr4_performance_student_sized_list(temp_storage):
    service, _ = temp_storage

    # Create 100 typical student tasks
    start_time = time.perf_counter()
    created_ids = []
    for i in range(100):
        t = service.create_task({
            "title": f"Assignment #{i+1} for Semester",
            "description": f"Detailed notes and requirements for unit {i+1}",
            "due_date": f"2026-11-{(i % 28) + 1:02d}",
            "priority": "Medium" if i % 2 == 0 else "High"
        })
        created_ids.append(t["id"])
    creation_time = time.perf_counter() - start_time

    # Viewing all tasks
    start_view = time.perf_counter()
    all_tasks = service.list_tasks()
    view_time = time.perf_counter() - start_view

    # Updating 20 tasks
    start_update = time.perf_counter()
    for task_id in created_ids[:20]:
        service.update_task(task_id, {"status": "Completed"})
    update_time = time.perf_counter() - start_update

    assert len(all_tasks) == 100
    # Reading a 100-item list from disk should take well under 50ms
    assert view_time < 0.05, f"View time took {view_time:.4f}s, expected < 0.05s"
    # Updating 20 items with atomic fsync writes should finish comfortably fast
    assert update_time < 0.5, f"Update time took {update_time:.4f}s, expected < 0.5s"


# =====================================================================
# NFR-5 — Privacy:
# Task data is not exposed beyond intended audience; stored locally.
# =====================================================================
def test_nfr5_privacy_local_storage_path(temp_storage):
    service, json_path = temp_storage
    service.create_task({"title": "Private Exam Prep Notes", "due_date": "2026-11-15"})

    # Ensure data is written exclusively to the student's designated local file path
    assert os.path.exists(json_path)
    with open(json_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Private Exam Prep Notes" in content
