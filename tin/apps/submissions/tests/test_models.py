from pathlib import Path

from ..models import Submission, upload_submission_file_path


def test_submission_save_file(settings, submission: Submission):
    file_path = upload_submission_file_path(submission, "")
    submission.save_file("something")
    assert submission.file.name == file_path

    submission_path = submission.file_path
    assert submission_path is not None
    submission_path = Path(submission_path)
    assert submission_path == Path(settings.MEDIA_ROOT) / file_path
    assert submission_path.exists()


def test_make_submission_backup(submission: Submission):
    submission.create_backup_copy("HI")
    backup_file = submission.backup_file_path
    assert backup_file is not None
    backup_path = Path(backup_file)
    assert backup_path.exists()
    assert backup_path.read_text("utf-8") == "HI"
