.. _dev-setup:

Setting up a development environment
------------------------------------

First, you will need to install the following:

* ``python``
* ``pipenv``
* ``git``

You will also need a GitHub account.

First, `fork <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo#forking-a-repository>`_
tin. Then you can clone tin onto your computer with

.. code-block:: bash

   git clone https://github.com/YOUR_GITHUB_USERNAME/tin

From here, you can either use a local setup, or use Docker. Check out the
relevant sections.

Local Setup
~~~~~~~~~~~

After that, install dependencies and follow standard django procedures

.. note::

    If you're on windows and get errors about ``python3`` not existing,
    try using ``python`` instead of ``python3``.


.. code-block:: bash

   pipenv install --dev
   pipenv run python3 manage.py migrate
   pipenv run python3 manage.py create_debug_users


Now you're all set! Try running the development server

.. code-block:: bash

   pipenv run python3 manage.py runserver

Head on over to `http://127.0.0.1:8000 <http://127.0.0.1:8000>`_, and login
as ``admin`` and the password you just entered.

Submissions
~~~~~~~~~~~

In order to actually create a submission, there are some more steps. First,
you'll need to install `redis <https://redis.io/download>`_.

After that, you'll want to start up the development server and create a course,
and an assignment in the course. After saving the assignment, you can hit "Upload grader"
to add a grader - the simplest example of a grader is located in ``scripts/sample_grader.py``.

Finally, before creating a submission, you'll need to start the celery worker. This can be done
by running the following command in a separate terminal::

  pipenv run celery -A tin worker --loglevel=info

Now you can try making a submission, and as long as your submission doesn't throw an error you
should get a 100%! Congrats on your brand new 5.0 GPA!

Docker
~~~~~~
If you prefer, you can also run the development setup with `Docker <https://www.docker.com/>`_. To do so,
``cd`` into the project directory and run::

    docker compose build
    docker compose up

The latter command will start up the django development server, as well as celery tasks for submissions.
