###########
Conventions
###########

Pre-Commit
----------
Tin uses ``pre-commit`` to ensure similarly formatted code
across the codebase. Once you have installed pre-commit (see :ref:`dev-setup`),
run

.. code-block:: bash

   pre-commit install

To install ``pre-commit`` hooks into git. Now, every time you commit, ``pre-commit``
will run your code against a formatter and linter, making your contribution
easier to review.

Commits
-------

Content
~~~~~~~
Tin doesn't follow a specific naming convention for commits; however,
if your commits are named well and are easy to review individually,
you are likely to receive a response faster. For example, a PR with commits like

* Add CI + Config for Javascript Formatter
* Autoformatted Javascript code

Will likely be reviewed faster than a PR with a single commit like

* Add Javascript Formatter and format code

Syncing with master
~~~~~~~~~~~~~~~~~~~
At some point in your PR, it's likely your branch and the master branch will diverge,
and at this point you'll have to either master into your branch, or rebase your changes
on top of master. *Tin prefers that you rebase*, in order to preserve linear history.

As a quick review on how to rebase with upstream, you can do

.. code-block:: bash

   git pull --rebase https://github.com/tjcsl/tin master

Signing Commits
~~~~~~~~~~~~~~~
This is not strictly a requirement, but it's highly recommended to sign commits.
It's a good developer habit, and makes it a little nicer to review your changes.
