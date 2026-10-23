"""
app.py - Flask Application Entrypoint for Student Academic Task Management.
Fulfills FR-1 through FR-7 and Non-Functional Requirements NFR-1 to NFR-5.
"""

import os
import sys
from datetime import date
from flask import Flask, render_template, request, jsonify, abort

from models import (
    ValidationError,
    TaskNotFoundError,
    VALID_PRIORITIES,
    VALID_STATUSES
)
from task_storage import JsonTaskStorage, StorageError
from task_service import TaskService


def create_app(storage_path: str = "data/tasks.json") -> Flask:
    """Application factory for Flask."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.urandom(24)
    app.json.sort_keys = False

    storage = JsonTaskStorage(file_path=storage_path)
    service = TaskService(storage=storage)

    # -------------------------------------------------------------
    # Template Filter Helpers
    # -------------------------------------------------------------
    @app.context_processor
    def inject_global_vars():
        return {
            "today_date": date.today().strftime("%Y-%m-%d"),
            "valid_priorities": VALID_PRIORITIES,
            "valid_statuses": VALID_STATUSES
        }

    # -------------------------------------------------------------
    # HTML View Routes
    # -------------------------------------------------------------
    @app.route("/")
    def index():
        """Renders the interactive student task dashboard (NFR-1 Usability)."""
        tasks = service.list_tasks()
        stats = service.get_stats()
        return render_template("index.html", tasks=tasks, stats=stats)

    # -------------------------------------------------------------
    # REST API Routes
    # -------------------------------------------------------------
    @app.route("/api/tasks", methods=["GET"])
    def api_list_tasks():
        """
        FR-3: View task list.
        Supports status, priority, search, sort_by, sort_order parameters.
        """
        status = request.args.get("status")
        priority = request.args.get("priority")
        search = request.args.get("search")
        sort_by = request.args.get("sort_by", "due_date")
        sort_order = request.args.get("sort_order", "asc")

        tasks = service.list_tasks(
            status=status,
            priority=priority,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return jsonify({
            "success": True,
            "count": len(tasks),
            "data": tasks
        }), 200

    @app.route("/api/tasks", methods=["POST"])
    def api_create_task():
        """
        FR-1: Create task.
        FR-2: Validates all details.
        FR-6: Reports invalid input.
        """
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Request body must be valid JSON with Content-Type 'application/json'."
            }), 400

        data = request.get_json()
        try:
            created = service.create_task(data)
            return jsonify({
                "success": True,
                "message": f"Task #{created['id']} created successfully.",
                "data": created
            }), 201
        except ValidationError as ve:
            return jsonify({
                "success": False,
                "error": ve.message,
                "details": ve.errors
            }), 400
        except StorageError as se:
            return jsonify({
                "success": False,
                "error": f"Failed to save task to storage: {str(se)}"
            }), 500

    @app.route("/api/tasks/<task_id>", methods=["GET"])
    def api_get_task(task_id):
        """
        FR-3: View single task details.
        FR-6: Distinguishes unknown task IDs from existing tasks.
        """
        try:
            task = service.get_task(task_id)
            return jsonify({
                "success": True,
                "data": task
            }), 200
        except ValidationError as ve:
            return jsonify({
                "success": False,
                "error": ve.message,
                "details": ve.errors
            }), 400
        except TaskNotFoundError as te:
            return jsonify({
                "success": False,
                "error": str(te),
                "task_id": te.task_id
            }), 404

    @app.route("/api/tasks/<task_id>", methods=["PUT"])
    def api_update_task(task_id):
        """
        FR-4: Update existing task by ID.
        FR-6: Distinguishes unknown task IDs from existing tasks and validates input.
        FR-7: ID integrity: retains original ID.
        """
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Request body must be valid JSON with Content-Type 'application/json'."
            }), 400

        data = request.get_json()
        try:
            updated = service.update_task(task_id, data)
            return jsonify({
                "success": True,
                "message": f"Task #{updated['id']} updated successfully.",
                "data": updated
            }), 200
        except ValidationError as ve:
            return jsonify({
                "success": False,
                "error": ve.message,
                "details": ve.errors
            }), 400
        except TaskNotFoundError as te:
            return jsonify({
                "success": False,
                "error": str(te),
                "task_id": te.task_id
            }), 404
        except StorageError as se:
            return jsonify({
                "success": False,
                "error": f"Failed to update task in storage: {str(se)}"
            }), 500

    @app.route("/api/tasks/<task_id>", methods=["DELETE"])
    def api_delete_task(task_id):
        """
        FR-5: Delete task by ID.
        FR-6: Distinguishes unknown task IDs from existing tasks.
        FR-7: Deleting removes it from subsequent views.
        """
        try:
            service.delete_task(task_id)
            return jsonify({
                "success": True,
                "message": f"Task #{task_id} was deleted successfully."
            }), 200
        except ValidationError as ve:
            return jsonify({
                "success": False,
                "error": ve.message,
                "details": ve.errors
            }), 400
        except TaskNotFoundError as te:
            return jsonify({
                "success": False,
                "error": str(te),
                "task_id": te.task_id
            }), 404
        except StorageError as se:
            return jsonify({
                "success": False,
                "error": f"Failed to delete task from storage: {str(se)}"
            }), 500

    @app.route("/api/stats", methods=["GET"])
    def api_get_stats():
        """Returns statistics for student dashboard."""
        return jsonify({
            "success": True,
            "data": service.get_stats()
        }), 200

    # -------------------------------------------------------------
    # Error Handlers
    # -------------------------------------------------------------
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "error": "Endpoint not found."}), 404
        return render_template("base.html", content="<div class='container mt-5'><h3>404 - Page Not Found</h3></div>"), 404

    @app.errorhandler(500)
    def internal_error(e):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "error": "An internal server error occurred."}), 500
        return render_template("base.html", content="<div class='container mt-5'><h3>500 - Server Error</h3></div>"), 500

    return app


app = create_app()

if __name__ == "__main__":
    # NFR-5 Privacy: Bind exclusively to 127.0.0.1 (localhost)
    print("Starting Student Academic Task Manager on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=False)
