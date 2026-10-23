# 📚 Student Academic Task Manager

A web-based Academic Task Management Application specifically built to meet all Functional Requirements (**FR-1 through FR-7**) and Non-Functional Requirements (**NFR-1 through NFR-5**).

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.8+ (Tested on Python 3.11)
- Flask 2.2+ (Already installed)

### 2. Start the Web Application
```bash
python app.py
```
Open your browser and navigate to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

### 3. Run Automated Tests
```bash
python -m pytest tests -v
```

### 4. (Optional) Reset / Re-seed Sample Tasks
```bash
python seed_data.py
```

---

## 📋 Requirements Compliance Matrix

### Functional Requirements

| ID | Requirement | Implementation Details |
|---|---|---|
| **FR-1** | **Create** | Students can create academic tasks with Title, Description, Due Date, Priority, and Completion Status via the web UI modal or `POST /api/tasks`. |
| **FR-2** | **Task Details** | Every task enforces 6 standard attributes: unique `id`, `title`, `description`, `due_date` (YYYY-MM-DD), `priority` (`High`, `Medium`, `Low`), and `status` (`Pending`, `In Progress`, `Completed`). |
| **FR-3** | **View** | Interactive dashboard displaying all academic tasks, each with its ID badge, title, priority pill, due date badge, status, and description. Supports live search, multi-field filtering, and sorting. |
| **FR-4** | **Update** | Existing tasks can be updated by ID via the Edit modal, single-click completion toggle, or `PUT /api/tasks/<id>`. |
| **FR-5** | **Delete** | Tasks can be deleted by ID via a confirmation modal or `DELETE /api/tasks/<id>`. |
| **FR-6** | **Error Handling** | Distinguishes unknown IDs (`404 Not Found` with specific message `"Task with ID <id> does not exist"`), reports invalid inputs (`400 Bad Request` with field-level error dictionary), and guarantees failed operations are never reported as successful. |
| **FR-7** | **ID Integrity** | Each ID uniquely identifies at most one task. Updating a task strictly retains its ID. Deleting a task immediately removes it from subsequent views and persistent storage. New IDs are generated monotonically and never collide. |

---

### Non-Functional Requirements

| ID | Requirement | Implementation Details |
|---|---|---|
| **NFR-1** | **Usability** | Clear, accessible labels for all actions and fields. Instant feedback via toast notifications, inline validation messages, status pills, and deletion confirmation dialogs. |
| **NFR-2** | **Data Integrity** | Uses atomic disk writes (`os.replace` + `os.fsync`) via temporary file staging to eliminate partial writes or corruption during power loss. Strict pre-save payload validation and thread locking (`threading.RLock`). |
| **NFR-3** | **Reliability & Persistence** | Tasks are stored in a human-readable JSON storage file (`data/tasks.json`). All saved tasks remain available across server restarts. Detects corrupted files and automatically creates emergency `.corrupt` backups. |
| **NFR-4** | **Performance** | Sub-millisecond read/write performance for student workloads (100+ tasks process in < 50ms). Responsive client-side UI with instant live filtering and search. |
| **NFR-5** | **Privacy** | The application binds strictly to localhost (`127.0.0.1:5000`) and stores task data locally on disk, ensuring student coursework data is not exposed to unauthorized network audiences. Zero external telemetry or third-party CDNs. |

---

## 🛠️ Architecture & Project Structure

```
c:\new project\
├── app.py                     # Flask application factory, routes, and API endpoints
├── models.py                  # Domain models, payload validators, and custom exceptions
├── task_storage.py            # Thread-safe atomic JSON file storage engine
├── task_service.py            # Business logic layer for CRUD operations & ID integrity
├── seed_data.py               # Sample data generator for realistic coursework
├── requirements.txt           # Dependencies
├── static/
│   ├── css/
│   │   └── style.css          # Responsive design, color-coded priorities, and toast styling
│   └── js/
│       └── app.js             # Client-side state manager, AJAX calls, and UI event listeners
├── templates/
│   ├── base.html              # HTML5 boilerplate, header, toasts, and footer
│   └── index.html             # Student dashboard, stats bar, task grid, and modal dialogs
└── tests/
    ├── test_fr_requirements.py   # Unit & API test suite for FR-1 through FR-7
    └── test_nfr_requirements.py  # Validation test suite for NFR-1 through NFR-5
```

---

## 📡 REST API Reference

| Method | Endpoint | Description | Status Codes |
|---|---|---|---|
| `GET` | `/api/tasks` | List tasks (supports `status`, `priority`, `search`, `sort_by`, `sort_order`) | `200 OK` |
| `POST` | `/api/tasks` | Create a new task | `201 Created`, `400 Bad Request`, `500 Error` |
| `GET` | `/api/tasks/<id>` | Get task details by ID | `200 OK`, `404 Not Found` |
| `PUT` | `/api/tasks/<id>` | Update an existing task by ID (retains ID) | `200 OK`, `400 Bad Request`, `404 Not Found` |
| `DELETE` | `/api/tasks/<id>` | Delete an existing task by ID | `200 OK`, `404 Not Found` |
| `GET` | `/api/stats` | Get dashboard summary counts (total, pending, overdue, etc.) | `200 OK` |
