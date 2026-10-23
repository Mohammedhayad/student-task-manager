/**
 * app.js - Client-Side Interactive Controller for Student Academic Task Manager
 * Enforces FR-1 to FR-7 and provides rich Usability (NFR-1) and Responsive Performance (NFR-4).
 */

document.addEventListener("DOMContentLoaded", () => {
    // State management
    const state = {
        tasks: [],
        stats: {},
        currentFilterStatus: "all",
        currentFilterPriority: "all",
        currentSearch: "",
        currentSortBy: "due_date",
        currentSortOrder: "asc",
        activeTaskIdForDelete: null
    };

    // DOM Elements
    const taskListContainer = document.getElementById("taskListContainer");
    const emptyState = document.getElementById("emptyState");
    const taskCountEl = document.getElementById("taskCount");
    const searchInput = document.getElementById("searchInput");
    const clearSearchBtn = document.getElementById("clearSearchBtn");
    const statusFilter = document.getElementById("statusFilter");
    const priorityFilter = document.getElementById("priorityFilter");
    const sortBySelect = document.getElementById("sortBySelect");
    const sortOrderSelect = document.getElementById("sortOrderSelect");
    const toastContainer = document.getElementById("toastContainer");

    // Stat elements
    const statTotal = document.getElementById("statTotal");
    const statPending = document.getElementById("statPending");
    const statInProgress = document.getElementById("statInProgress");
    const statCompleted = document.getElementById("statCompleted");
    const statOverdue = document.getElementById("statOverdue");

    // Modal elements
    const createModal = document.getElementById("createModal");
    const editModal = document.getElementById("editModal");
    const deleteModal = document.getElementById("deleteModal");
    const openCreateModalBtn = document.getElementById("openCreateModalBtn");
    const emptyCreateBtn = document.getElementById("emptyCreateBtn");
    const createTaskForm = document.getElementById("createTaskForm");
    const editTaskForm = document.getElementById("editTaskForm");
    const confirmDeleteBtn = document.getElementById("confirmDeleteBtn");

    // -----------------------------------------------------------------
    // Notification Toast System (NFR-1 Usability)
    // -----------------------------------------------------------------
    function showToast(message, type = "success") {
        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        
        let icon = "✅";
        if (type === "error") icon = "❌";
        if (type === "info") icon = "ℹ️";

        toast.innerHTML = `
            <span class="toast-icon">${icon}</span>
            <span class="toast-message">${escapeHtml(message)}</span>
            <button class="toast-close" aria-label="Close notification">&times;</button>
        `;

        const closeBtn = toast.querySelector(".toast-close");
        closeBtn.addEventListener("click", () => toast.remove());

        toastContainer.appendChild(toast);

        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.opacity = "0";
                toast.style.transition = "opacity 0.3s ease";
                setTimeout(() => toast.remove(), 300);
            }
        }, 4000);
    }

    function escapeHtml(text) {
        if (!text) return "";
        return String(text)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // -----------------------------------------------------------------
    // API Data Operations
    // -----------------------------------------------------------------
    async function fetchTasks() {
        try {
            const params = new URLSearchParams({
                status: state.currentFilterStatus,
                priority: state.currentFilterPriority,
                search: state.currentSearch,
                sort_by: state.currentSortBy,
                sort_order: state.currentSortOrder
            });

            const res = await fetch(`/api/tasks?${params.toString()}`);
            const data = await res.json();
            
            if (data.success) {
                state.tasks = data.data;
                renderTaskList();
            } else {
                showToast(data.error || "Failed to load tasks.", "error");
            }
        } catch (err) {
            showToast("Network error while loading tasks.", "error");
            console.error("Fetch tasks error:", err);
        }
    }

    async function fetchStats() {
        try {
            const res = await fetch("/api/stats");
            const data = await res.json();
            if (data.success) {
                state.stats = data.data;
                updateStatsUI();
            }
        } catch (err) {
            console.error("Fetch stats error:", err);
        }
    }

    function updateStatsUI() {
        if (!state.stats) return;
        statTotal.textContent = state.stats.total ?? 0;
        statPending.textContent = state.stats.pending ?? 0;
        statInProgress.textContent = state.stats.in_progress ?? 0;
        statCompleted.textContent = state.stats.completed ?? 0;
        statOverdue.textContent = state.stats.overdue ?? 0;
    }

    // -----------------------------------------------------------------
    // Due Date Helper Calculations
    // -----------------------------------------------------------------
    function getDueDateMeta(dateStr, isCompleted) {
        if (!dateStr) return { text: "No due date", className: "" };
        
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const [y, m, d] = dateStr.split("-").map(Number);
        const due = new Date(y, m - 1, d);
        due.setHours(0, 0, 0, 0);

        const diffTime = due.getTime() - today.getTime();
        const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));

        if (isCompleted) {
            return { text: `Due: ${dateStr}`, className: "" };
        }

        if (diffDays < 0) {
            const overdueDays = Math.abs(diffDays);
            return {
                text: `⚠️ Overdue by ${overdueDays} day${overdueDays > 1 ? "s" : ""} (${dateStr})`,
                className: "is-overdue"
            };
        } else if (diffDays === 0) {
            return { text: `⏳ Due Today (${dateStr})`, className: "is-today" };
        } else if (diffDays === 1) {
            return { text: `📅 Due Tomorrow (${dateStr})`, className: "" };
        } else {
            return { text: `📅 Due in ${diffDays} days (${dateStr})`, className: "" };
        }
    }

    // -----------------------------------------------------------------
    // Task List Rendering (FR-3)
    // -----------------------------------------------------------------
    function renderTaskList() {
        taskListContainer.innerHTML = "";
        taskCountEl.textContent = state.tasks.length;

        if (state.tasks.length === 0) {
            emptyState.style.display = "block";
            return;
        }

        emptyState.style.display = "none";

        state.tasks.forEach(task => {
            const isCompleted = task.status === "Completed";
            const dueMeta = getDueDateMeta(task.due_date, isCompleted);
            const priorityClass = (task.priority || "Medium").toLowerCase();
            const statusClass = (task.status || "Pending").toLowerCase().replace(" ", "-");

            const card = document.createElement("div");
            card.className = `task-card priority-border-${priorityClass} ${isCompleted ? "completed-task" : ""}`;
            card.id = `task-card-${task.id}`;

            card.innerHTML = `
                <div class="task-check-wrapper">
                    <input type="checkbox" class="custom-checkbox task-status-toggle" 
                           data-task-id="${task.id}" 
                           ${isCompleted ? "checked" : ""}
                           title="Toggle Completion Status (FR-4)" 
                           aria-label="Toggle task ${task.id} completion">
                </div>
                <div class="task-details">
                    <div class="task-meta-top">
                        <span class="task-id-tag">#${task.id}</span>
                        <span class="status-badge status-${statusClass}">${escapeHtml(task.status)}</span>
                        <span class="priority-pill priority-pill-${priorityClass}">${escapeHtml(task.priority)} Priority</span>
                        <span class="due-date-pill ${dueMeta.className}">${escapeHtml(dueMeta.text)}</span>
                    </div>
                    <h3 class="task-title">${escapeHtml(task.title)}</h3>
                    ${task.description ? `<p class="task-description">${escapeHtml(task.description)}</p>` : ""}
                    <div class="task-dates-info">
                        Created: ${formatDate(task.created_at)} ${task.updated_at !== task.created_at ? `&bull; Edited: ${formatDate(task.updated_at)}` : ""}
                    </div>
                </div>
                <div class="task-actions">
                    <button class="btn-icon-action btn-edit" data-task-id="${task.id}" title="Edit Task Details (FR-4)">
                        ✏️ Edit
                    </button>
                    <button class="btn-icon-action btn-delete" data-task-id="${task.id}" title="Delete Task (FR-5)">
                        🗑️ Delete
                    </button>
                </div>
            `;

            taskListContainer.appendChild(card);
        });

        attachCardActionListeners();
    }

    function formatDate(isoStr) {
        if (!isoStr) return "";
        try {
            const d = new Date(isoStr);
            return d.toLocaleDateString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
        } catch {
            return isoStr;
        }
    }

    // -----------------------------------------------------------------
    // Card Action Event Handlers
    // -----------------------------------------------------------------
    function attachCardActionListeners() {
        // Toggle complete checkbox
        document.querySelectorAll(".task-status-toggle").forEach(checkbox => {
            checkbox.addEventListener("change", async (e) => {
                const taskId = e.target.getAttribute("data-task-id");
                const newStatus = e.target.checked ? "Completed" : "Pending";
                await updateTaskStatusQuick(taskId, newStatus);
            });
        });

        // Edit button
        document.querySelectorAll(".btn-edit").forEach(btn => {
            btn.addEventListener("click", () => {
                const taskId = btn.getAttribute("data-task-id");
                openEditModal(taskId);
            });
        });

        // Delete button
        document.querySelectorAll(".btn-delete").forEach(btn => {
            btn.addEventListener("click", () => {
                const taskId = btn.getAttribute("data-task-id");
                openDeleteModal(taskId);
            });
        });
    }

    async function updateTaskStatusQuick(taskId, newStatus) {
        try {
            const res = await fetch(`/api/tasks/${taskId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status: newStatus })
            });
            const data = await res.json();
            if (data.success) {
                showToast(`Task #${taskId} marked as ${newStatus}.`, "success");
                await fetchTasks();
                await fetchStats();
            } else {
                showToast(data.error || "Failed to update task status.", "error");
                await fetchTasks(); // Revert checkbox UI
            }
        } catch (err) {
            showToast("Network error while updating status.", "error");
            await fetchTasks();
        }
    }

    // -----------------------------------------------------------------
    // Modal Helpers
    // -----------------------------------------------------------------
    function openModal(modalEl) {
        modalEl.classList.add("is-open");
        modalEl.setAttribute("aria-hidden", "false");
    }

    function closeModal(modalEl) {
        modalEl.classList.remove("is-open");
        modalEl.setAttribute("aria-hidden", "true");
        clearModalErrors(modalEl);
    }

    function clearModalErrors(modalEl) {
        modalEl.querySelectorAll(".field-error").forEach(el => el.textContent = "");
        modalEl.querySelectorAll(".is-invalid").forEach(el => el.classList.remove("is-invalid"));
    }

    function showFieldErrors(modalEl, errors) {
        clearModalErrors(modalEl);
        if (!errors) return;
        for (const [field, msg] of Object.entries(errors)) {
            const errorDiv = modalEl.querySelector(`#${modalEl.id === "createModal" ? "create" : "edit"}${capitalize(field)}Error`);
            const inputField = modalEl.querySelector(`[name="${field}"]`);
            if (errorDiv) errorDiv.textContent = msg;
            if (inputField) inputField.classList.add("is-invalid");
        }
    }

    function capitalize(str) {
        if (!str) return "";
        return str.charAt(0).toUpperCase() + str.slice(1).replace(/_([a-z])/g, g => g[1].toUpperCase());
    }

    // Setup close listeners for all modals
    document.querySelectorAll("[data-close-modal]").forEach(btn => {
        btn.addEventListener("click", () => {
            const modalId = btn.getAttribute("data-close-modal");
            closeModal(document.getElementById(modalId));
        });
    });

    window.addEventListener("click", (e) => {
        if (e.target.classList.contains("modal-backdrop")) {
            closeModal(e.target);
        }
    });

    window.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            document.querySelectorAll(".modal-backdrop.is-open").forEach(closeModal);
        }
    });

    // -----------------------------------------------------------------
    // Create Task (FR-1, FR-2, FR-6)
    // -----------------------------------------------------------------
    function initCreateModal() {
        createTaskForm.reset();
        clearModalErrors(createModal);
        // Default due date to today
        const today = new Date().toISOString().split("T")[0];
        document.getElementById("createDueDate").value = today;
        openModal(createModal);
        document.getElementById("createTitle").focus();
    }

    openCreateModalBtn.addEventListener("click", initCreateModal);
    emptyCreateBtn.addEventListener("click", initCreateModal);

    createTaskForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        clearModalErrors(createModal);

        const formData = new FormData(createTaskForm);
        const payload = {
            title: formData.get("title"),
            description: formData.get("description"),
            due_date: formData.get("due_date"),
            priority: formData.get("priority"),
            status: formData.get("status")
        };

        const submitBtn = document.getElementById("saveCreateBtn");
        submitBtn.disabled = true;
        submitBtn.textContent = "Creating...";

        try {
            const res = await fetch("/api/tasks", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (res.ok && data.success) {
                showToast(data.message || "Task created successfully!", "success");
                closeModal(createModal);
                await fetchTasks();
                await fetchStats();
            } else {
                if (data.details) {
                    showFieldErrors(createModal, data.details);
                }
                showToast(data.error || "Failed to create task.", "error");
            }
        } catch (err) {
            showToast("Network error while creating task.", "error");
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = "Create Task";
        }
    });

    // -----------------------------------------------------------------
    // Edit Task (FR-4, FR-6, FR-7)
    // -----------------------------------------------------------------
    async function openEditModal(taskId) {
        clearModalErrors(editModal);
        try {
            const res = await fetch(`/api/tasks/${taskId}`);
            const data = await res.json();
            if (!data.success) {
                showToast(data.error || "Task not found.", "error");
                return;
            }

            const task = data.data;
            document.getElementById("editTaskId").value = task.id;
            document.getElementById("editTaskIdDisplay").textContent = `#${task.id}`;
            document.getElementById("editTitle").value = task.title;
            document.getElementById("editDescription").value = task.description || "";
            document.getElementById("editDueDate").value = task.due_date;
            document.getElementById("editPriority").value = task.priority;
            document.getElementById("editStatus").value = task.status;

            openModal(editModal);
            document.getElementById("editTitle").focus();
        } catch (err) {
            showToast("Failed to fetch task details.", "error");
        }
    }

    editTaskForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        clearModalErrors(editModal);

        const taskId = document.getElementById("editTaskId").value;
        const formData = new FormData(editTaskForm);
        const payload = {
            title: formData.get("title"),
            description: formData.get("description"),
            due_date: formData.get("due_date"),
            priority: formData.get("priority"),
            status: formData.get("status")
        };

        const submitBtn = document.getElementById("saveEditBtn");
        submitBtn.disabled = true;
        submitBtn.textContent = "Saving...";

        try {
            const res = await fetch(`/api/tasks/${taskId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (res.ok && data.success) {
                showToast(data.message || `Task #${taskId} updated successfully.`, "success");
                closeModal(editModal);
                await fetchTasks();
                await fetchStats();
            } else {
                if (data.details) {
                    showFieldErrors(editModal, data.details);
                }
                showToast(data.error || "Failed to update task.", "error");
            }
        } catch (err) {
            showToast("Network error while saving changes.", "error");
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = "Save Changes";
        }
    });

    // -----------------------------------------------------------------
    // Delete Task (FR-5, FR-6, FR-7)
    // -----------------------------------------------------------------
    function openDeleteModal(taskId) {
        const task = state.tasks.find(t => String(t.id) === String(taskId));
        state.activeTaskIdForDelete = taskId;
        document.getElementById("deleteTaskIdDisplay").textContent = `#${taskId}`;
        document.getElementById("deleteTaskTitleDisplay").textContent = task ? task.title : "";
        openModal(deleteModal);
    }

    confirmDeleteBtn.addEventListener("click", async () => {
        const taskId = state.activeTaskIdForDelete;
        if (!taskId) return;

        confirmDeleteBtn.disabled = true;
        confirmDeleteBtn.textContent = "Deleting...";

        try {
            const res = await fetch(`/api/tasks/${taskId}`, {
                method: "DELETE"
            });
            const data = await res.json();

            if (res.ok && data.success) {
                showToast(data.message || `Task #${taskId} deleted successfully.`, "success");
                closeModal(deleteModal);
                await fetchTasks();
                await fetchStats();
            } else {
                showToast(data.error || "Failed to delete task.", "error");
            }
        } catch (err) {
            showToast("Network error while deleting task.", "error");
        } finally {
            confirmDeleteBtn.disabled = false;
            confirmDeleteBtn.textContent = "Delete Task";
            state.activeTaskIdForDelete = null;
        }
    });

    // -----------------------------------------------------------------
    // Toolbar Filters & Search Event Listeners
    // -----------------------------------------------------------------
    let searchTimeout = null;
    searchInput.addEventListener("input", (e) => {
        const val = e.target.value.trim();
        clearSearchBtn.style.display = val ? "block" : "none";
        
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            state.currentSearch = val;
            fetchTasks();
        }, 250);
    });

    clearSearchBtn.addEventListener("click", () => {
        searchInput.value = "";
        clearSearchBtn.style.display = "none";
        state.currentSearch = "";
        fetchTasks();
    });

    statusFilter.addEventListener("change", (e) => {
        state.currentFilterStatus = e.target.value;
        fetchTasks();
    });

    priorityFilter.addEventListener("change", (e) => {
        state.currentFilterPriority = e.target.value;
        fetchTasks();
    });

    sortBySelect.addEventListener("change", (e) => {
        state.currentSortBy = e.target.value;
        fetchTasks();
    });

    sortOrderSelect.addEventListener("change", (e) => {
        state.currentSortOrder = e.target.value;
        fetchTasks();
    });

    // Stat cards click-to-filter
    document.querySelectorAll(".stat-card").forEach(card => {
        card.addEventListener("click", () => {
            const filter = card.getAttribute("data-filter");
            if (filter === "all") {
                statusFilter.value = "all";
                state.currentFilterStatus = "all";
            } else if (filter === "pending") {
                statusFilter.value = "Pending";
                state.currentFilterStatus = "Pending";
            } else if (filter === "in_progress") {
                statusFilter.value = "In Progress";
                state.currentFilterStatus = "In Progress";
            } else if (filter === "completed") {
                statusFilter.value = "Completed";
                state.currentFilterStatus = "Completed";
            }
            fetchTasks();
        });
    });

    // Initial load
    fetchTasks();
    fetchStats();
});
