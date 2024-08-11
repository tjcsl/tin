################
Writing a Grader
################

.. caution::

   It isn't as simple as it sounds - there are certain traps
   that are easy to fall into. Read the full page before writing a grader script.

Tin allows you to use the full flexibility of Python (or Java)
to write a grader script. This script is responsible for evaluating
the output of a student submission, and returning a score to Tin.

.. note::

  In this guide, we will use Python, but the same principles apply to Java.

----------------------
How do I do write one?
----------------------

Tin passes the following arguments to the grader script:

- The full path to the program that will run the student submission.
- The path to the student submission file - for parsing only!
- The submitting student's username.
- The path to the log file.

You can access these in your grader script by using the :obj:`sys.argv` list
in Python.

.. code-block:: python

  import sys

  submission, submission_file, username, log_file, *_ = sys.argv[1:]

.. warning::

  Do NOT use the path to the student submission file to run the student submission.
  Doing so would allow students to upload malicious files, such as scripts that could read other students
  submissions and copy them somewhere the student can access.

  Instead, you can run the wrapper script provided by Tin (``submission``) which will run the student
  submission in a sandboxed environment, to prevent cheating.

.. warning::

  Do not use the ``submission_file`` to parse the student's username - the format of the
  submission file path is not guaranteed to be the same in future versions of Tin.


Only open/write to the log file until right before the grader exits. This will minimize issues
caused by multiple submissions writing to the same file.

You can then use this information to run the student submission (remember to use Tin's wrapper script!),
and evaluate the output of the script.

See :doc:`examples` for examples of grader scripts.


-----------------------------------
Restrictions on Student Submissions
-----------------------------------

.. attention::

   Many of the restrictions Tin places on scripts can be bypassed if the grader script
   uses student output in an unsafe way (for example, using :func:`exec`
   or :func:`pickle.load`).


Student submissions have certain restrictions placed on them, including:

- A 1GB memory limit
- A restriction on the amount of subprocesses that can be launched.
- Being unable to access the internet (can be configured)
- Not being able to access the submission file
- Restricted access to the rest of the filesystem.

To allow students to access the internet, go to the assignments "Edit" page and
check the box labeled "Give submissions internet access".

.. caution::

  Be careful when enabling internet access - this makes it easier for
  students to cheat.

If you need to change the memory limit, please :doc:`contact Tin developers </contact>`.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Giving Students access to specific files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You can give student submissions access to specific files by passing arguments
to the wrapper script:

- ``--write <filepath>``: Give the submission read/write access to the specified file.
- ``--read <filepath>``: Give the submsission read only access to the specified file.

Note that in both cases, ``filepath`` must be an absolute path.

See :doc:`the file_io example <examples/file_io>` for an example grader utilizing this feature.

.. tip::

   You can use the special argument ``--`` to denote the wrapper
   should stop parsing arguments and pass the rest of the arguments to the submission.
   For example::

      submission --write /path/to/file -- arg1 arg2

   will give the submission read/write access to ``/path/to/file``, and pass
   ``arg1`` and ``arg2`` to the submission.

If you need to upload specific read-only files, please :doc:`contact us </contact>`.

------------
Grader Files
------------
To prevent conflicts/overwriting of other files, all graders should follow the rules below:

Graders should only write to files in the same directory as the grader (i.e. ``Path(__file__).parent``), and the directory
containing the student submission (i.e. ``Path(sys.argv[2]).parent``).

Do NOT create a file in the grader script directory with the same name as a students username.

Do NOT prefix the name of any files written/read to with ``grader`` - these are reserved for the Tin server itself.

Additionally, since all of a student's submissions are placed in the same directory, files created in the submission directory
(for example, filenames passed to the submission as output files) should be given random names to avoid
conflicts in case the student uploads a second submission while their last submission has not yet been graded.


-------------
Grader Output
-------------
Students can only see output from the grader that has been printed on the standard output (:obj:`sys.stdout`).
For example, students would be able to see this::

  print("HEY YOU, STOP CHEATING!")

However, students cannot see anything on :obj:`sys.stderr` - This is to prevent students from
seeing a solution in the output if the grader throws an exception. For example, only teachers
would be able to see the following exception::

  raise RuntimeError("Student said 1+1=3")

If the grader script exits with a non-zero status code (which Python does by default when an
exception is raised) the student will see the text [Grader error] at the end of the output.
If the grader exceeds its timeout (as set in the assignment "Edit" page), the student will see the text
[Grader timed out]. Similar text will also be added to the error output.

~~~~~~~~~~~~~~~~~
Automatic Scoring
~~~~~~~~~~~~~~~~~
Each submission has a "Score" field that can be set by the grader. If this field is set,
you will be able to see a list of each student's scores on the assignment's page,
which is designed to make entering grades into the gradebook easier.

To set this field, simply print ``Source: <score>`` at the very end, to :obj:`sys.stdout`. For example::

  print("Source: 10%")

Note that the score can be printed as a percent (``10%``) or as a number of points. In both cases,
they are interpreted as being out of the "Points possible" value set on the assignment "Edit" page.

.. note::

   The autoscoring line is case sensitive and spacing must be exactly right - this means no trailing spaces are
   allowed.

.. caution::

  If a grader exits with a non-zero status code, the auto-scoring will not take place.
  This is to prevent inaccurate scores in case of a grader error.
