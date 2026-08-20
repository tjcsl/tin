from pathlib import Path

from celery import shared_task
from django.utils import timezone

from tin.apps.assignments.models import Assignment, Folder

from .models import Course


@shared_task(bind=True)
def import_course_data_tasks(self, target_id, source_id, data):
    target_course = Course.objects.get(pk=target_id)

    folder_ids = data.get("folder_ids", [])
    individual_assignment_ids = data.get("assignment_ids", [])

    assignments_to_process = []

    folders = Folder.objects.filter(id__in=folder_ids)
    for folder in folders:
        folder_assignments = list(folder.assignments.all())
        folder.pk = None
        folder._state.adding = True
        folder.course = target_course
        folder.save()

        for a in folder_assignments:
            assignments_to_process.append((a, folder.id))

    individual_assignments = Assignment.objects.filter(id__in=individual_assignment_ids)
    for a in individual_assignments:
        assignments_to_process.append((a, None))

    total = len(assignments_to_process)

    for index, (old_assignment, new_folder_id) in enumerate(assignments_to_process):
        old_grader_fpath = (
            Path(old_assignment.grader_file.path) if old_assignment.grader_file else None
        )
        old_assignment_files = old_assignment.list_files()
        assignment = old_assignment
        assignment.pk = None
        assignment._state.adding = True
        assignment.course = target_course
        assignment.folder_id = new_folder_id
        assignment.assigned = timezone.now()
        assignment.grader_file = None

        if data.get("hide"):
            assignment.hidden = True
        assignment.save()
        assignment.make_assignment_dir()

        if data.get("copy_graders") and old_grader_fpath is not None:
            assignment.save_grader_file(old_grader_fpath.read_bytes().decode())

        if data.get("copy_files"):
            for _, filename, path, _, _ in old_assignment_files:
                content = Path(path).read_bytes()
                assignment.save_file(content, filename)

        self.update_state(
            state="PROGRESS",
            meta={
                "current": index + 1,
                "total": total,
                "percent": int(((index + 1) / total) * 100) if total > 0 else 100,
            },
        )

    return {"status": "Completed", "total": total}
