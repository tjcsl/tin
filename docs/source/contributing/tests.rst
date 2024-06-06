############
Adding Tests
############


How to add tests
----------------

Tin uses ``pytest`` and ``pytest-django`` to run tests. You can add tests
to a new app in one of two ways:

1. Creating a new file in the app called ``tests.py``
2. Creating a directory called ``tests/`` and adding files that are prefixed with ``test_``
   inside the directory

You can then write a function whose name is prefixed ``test_``, and that
will be run as a test. A sample test might look like

.. code-block:: python

   def test_addition():
      assert 1+1 == 2

You can then run the tests with ``python3 manage.py test``.


Writing good tests
------------------
Good tests should test the behavior of a specific view or method, and (ideally) not depend on anything else.
For example, say we had this view

.. code-block:: python

   def my_view(request):
      # this view is at /hi/
      return redirect("/courses/")

A good test for this view would be

.. code-block:: python

    from tin.tests import is_redirect


    def test_my_view(client):
        response = client.get("/hi/")
        assert is_redirect(response)


.. _tin-utilities:

Utilities
---------
Tin provides several fixtures to ease the process of writing tests.
The most commonly used is the :func:`.login` decorator to login in a
django ``client`` as a user. It also provides some utility functions
for checking the types of requests, like :func:`.is_redirect` and :func:`.is_login_redirect`.

Let's look at an example using all three

.. code-block:: python

   from tin.tests import login, is_redirect, is_login_redirect


   def test_redirect(client):
      # client is an anonymous user
      response = client.get(reverse("courses:add"))
      assert is_login_redirect(response)

   @login("student")
   def test_redirect(client):
      # client is logged in as a student
      response = client.get(reverse("courses:add"))
      assert is_redirect(response)

   @login("admin")
   def test_redirect(client):
      # client is logged in as an admin
      response = client.get(reverse("courses:add"))
      assert not is_redirect(response)



Tips and Tricks
---------------

Pytest
~~~~~~
You can pass arguments to ``pytest`` by passing in ``--``
after ``python3 manage.py test``. For example, to see the stdout
for all tests, run

.. code-block::

   python3 manage.py test -- -rP

Or to run specific sets of tests:

.. code-block::

   # run all tests in this file
   python3 manage.py test -- tin/apps/courses/courses/tests.py

   # run all tests in this directory
   python3 manage.py test -- tin/apps/courses/assignments/tests/

   # run test_redirect in courses/tests.py
   python3 manage.py test -- tin/apps/courses/courses/tests.py::test_redirect

For more details, check out the `pytest documentation <https://docs.pytest.org/en/stable/>`_.

.. admonition:: Implementation Detail

   As of the last time this page was updated,
   ``python3 manage.py test`` is a wrapper around the raw ``pytest``
   executable. As such, you can replace ``python3 manage.py test --`` with just ``pytest``.

   Note that this may not stay the same in the future, so if you encounter any problems
   try using ``python3 manage.py test`` as a first step.

Parameterization
~~~~~~~~~~~~~~~~
Make heavy use of ``pytest.mark.parametrize`` (`docs <https://docs.pytest.org/en/stable/how-to/parametrize.html>`_).
Parameterizing tests allows for cleaner debugging when they fail. For example, consider this test case

.. code-block:: python

   def test_something():
      for i in (1, 2):
          assert 1+i == 2

When this test fails, it's difficult to tell at which value of ``i``
it failed at. Consider the following instead:

.. code-block:: python

   @pytest.mark.parametrize("i", (1, 2))
   def test_something(i):
      assert i+1 == 2


Now when this test fails, pytest tells us exactly which value of ``i`` it failed at!
These can also be arbitrarily nested

.. code-block:: python

   @pytest.mark.parametrize("i", range(3))
   @pytest.mark.parametrize("j", range(3))
   def test_commutative_addition(i, j):
      assert i+j == j+i

Here, ``test_commutative_addition`` would be run
with values of :math:`i` and :math:`j` such that
:math:`(i,j)\in\{(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), ..., (2, 2)\}`

Fixtures
~~~~~~~~
Finding yourself repeating setup code a lot? Write a `pytest fixture <https://docs.pytest.org/en/7.1.x/how-to/fixtures.html>`_
to do the setup for you.

For example, if you find yourself needing to create a second student often, you could do something like this

.. code-block:: python

   @pytest.fixture
   def studentB(django_user_model):
      user = django_user_model.objects.create(username="studentB")
      user.is_student = True
      user.save()
      return user

   def test_two_students(studentB):
      # do stuff with studentB
      ...


.. note::

   The ``django_user_model`` fixture comes from the ``pytest-django`` plugin.
   Tin also provides some convenience fixtures, see :ref:`tin-utilities` for more details.



If a fixture only sets up something, and does not return
anything, use it with ``pytest.usefixtures``.

.. code-block:: python

   @pytest.fixture
   def all_assigments_quiz(assignment):
      assignment.is_quiz = True
      assignment.save()

   @pytest.usefixtures("all_assigments_quiz")
   def test_something(assignment):
      # test something, but now assignment is a quiz
      ...


.. admonition:: Implementation Detail

    This is actually how :func:`.login` works, it's simply a wrapper around
    the ``admin_login``, ``student_login`` and ``teacher_login`` fixtures.
