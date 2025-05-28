.. _dev-setup:

Setting up a development environment
------------------------------------

First, you will need to install the following:

* ``python``
* ``pipenv``
* ``git``

You will also need a Github account.

First, `fork <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo#forking-a-repository>`_
tin. Then you can clone tin onto your computer with

.. code-block:: bash

   git clone https://github.com/YOUR_GITHUB_USERNAME/tin


After that, install dependencies and follow standard django procedures

.. note::

    If you're on windows and get errors about ``python3`` not existing,
    try using ``python`` instead of ``python3``.


.. code-block:: bash

   pipenv install --dev
   python3 manage.py migrate
   python3 create_debug_users.py


Now you're all set! Try running the development server

.. code-block:: bash

   python3 manage.py runserver

Head on over to `http://127.0.0.1:8000 <http://127.0.0.1:8000>`_, and login
as ``admin`` and the password you just entered.

Docker
------
If you prefer, you can also run the development setup with `Docker <https://www.docker.com/>`_. To do so,
``cd`` into the project directory and run::

    docker compose build
    docker compose up

The latter command will start up the django development server, as well as celery tasks for submissions.
