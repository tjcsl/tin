# Submission Caps
Teachers can set up maximum amounts of submissions for each assignment - this can be edited
on the assignment's edit page. If needed, the max amount can also be adjusted on a per-student
basis, by clicking on a student's submission

Let's assume it is before the assignment due date. Then, the maximum amount of submissions a student
has is processed as follows:

1. If the student is a teacher or superuser, they automatically have infinite submissions
1. If the student has a submission cap override, that is used.
1. Finally, the assignments submission cap (if it exists) is used. If it does not exist,
    infinite submissions are allowed.

The process for after an assignment is due is as follows:

1. If the student is a teacher or superuser, they automatically have infinite submissions
1. If the student has a submission cap override for after the due date, that is used.
1. If the student has a submission cap override for *before* the due date, that is used.
1. If the assignment has a submission cap for after the due date, it will be used.
1. Finally, the assignments submission cap (if it exists) is used. If it does not exist,
    infinite submissions are allowed.
