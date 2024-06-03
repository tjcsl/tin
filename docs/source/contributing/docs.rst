####
Docs
####

Tin uses `Sphinx <https://www.sphinx-doc.org/>`_ to build its documentation.
The actual content is written in reStructuredText (``.rst``) format, and can
be found in the ``docs/source`` folder at the `Tin Github <https://github.com/tjcsl/tin>`_.

Building Docs
~~~~~~~~~~~~~
First, you must have a local copy of Tin on your computer (see :ref:`dev-setup`).
After that, ``cd`` into the ``docs`` folder.

Next, run the following commands based on your operating system

.. code-block:: bash

   make.bat html  # Windows
   make html  # *nix

The first time you build the docs, it may take some time. On future builds,
the html will be cached.

Writing Documentation
~~~~~~~~~~~~~~~~~~~~~
Documentation is written in reStructuredText (reST) format.
For a quick refresher on reST, check out the `Sphinx docs <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>`_.

.. note::

   Technically, you can write documentation in markdown. However, reST is preferred
   as it is more powerful and easier to extend than markdown

When writing a docstring for a method, attribute, or a function, we use the `Google style docstrings <https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings>`_.
Do NOT include the type of a parameter in the docstring: that's redundant and harder to maintain. Instead,
prefer typehinting the actual typehint in the function, and sphinx will automatically parse that.

For example,

.. code-block:: python

   # BAD
   def my_function(x):
      """
      A BAD docstring for my_function

      Args:
        x (int): the first parameter
      """
      return x+1

   # GOOD! Note how the parameter has the typehint, not the docstring
   def my_function(x: int):
      """
      A good docstring for my_function

      Args:
        x : the first parameter
      """
      return x+1

Tips and Tricks
~~~~~~~~~~~~~~~
Sometimes Sphinx will do some weird stuff and things will stop working nicely.
In this case, a simple ``make clean`` (or ``make.bat clean`` for Windows) should do the trick.
