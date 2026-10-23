"""
seed_data.py - Populates sample academic coursework tasks for demonstration.
"""

from datetime import date, timedelta
from task_storage import JsonTaskStorage
from task_service import TaskService


def seed():
    today = date.today()
    storage = JsonTaskStorage("data/tasks.json")
    service = TaskService(storage=storage)

    # Only seed if currently empty
    tasks = service.list_tasks()
    if tasks:
        print(f"Storage already contains {len(tasks)} tasks. Skipping seed.")
        return

    sample_tasks = [
        {
            "title": "CS201 Data Structures Lab Report",
            "description": "Compare runtime efficiency and memory usage of AVL Trees vs Red-Black Trees. Include benchmark plots.",
            "due_date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
            "priority": "High",
            "status": "In Progress"
        },
        {
            "title": "MATH305 Linear Algebra Problem Set 5",
            "description": "Complete textbook exercises 14.1 through 14.8 on Orthogonal Projections and Gram-Schmidt orthogonalization.",
            "due_date": today.strftime("%Y-%m-%d"),
            "priority": "High",
            "status": "Pending"
        },
        {
            "title": "ENG102 Research Paper Outline",
            "description": "Submit a 2-page thesis proposal and annotated bibliography of 5 peer-reviewed sources.",
            "due_date": (today + timedelta(days=7)).strftime("%Y-%m-%d"),
            "priority": "Medium",
            "status": "Pending"
        },
        {
            "title": "PHYS110 Physics Midterm Exam Revision",
            "description": "Review chapters 1-6: Kinematics, Newton's Laws, Work-Energy Theorem, and Angular Momentum.",
            "due_date": (today + timedelta(days=12)).strftime("%Y-%m-%d"),
            "priority": "Medium",
            "status": "Pending"
        },
        {
            "title": "BIO105 Genetics Quiz 1",
            "description": "Review Mendelian inheritance and Punnett squares.",
            "due_date": (today - timedelta(days=3)).strftime("%Y-%m-%d"),
            "priority": "Low",
            "status": "Completed"
        }
    ]

    print("Seeding initial academic tasks...")
    for item in sample_tasks:
        created = service.create_task(item)
        print(f"  [+] Created Task #{created['id']}: {created['title']} ({created['priority']} Priority)")

    print(f"Successfully seeded {len(sample_tasks)} academic tasks.")


if __name__ == "__main__":
    seed()
