# Docs

Tin uses [Sphinx](https://www.sphinx-doc.org/) to build its documentation.
The actual content is written in reStructuredText (`.rst`) format, and can
be found in the `docs/source` folder at the [Tin Github](https://github.com/tjcsl/tin).

## Building Docs

First, you must have a local copy of Tin on your computer (see {ref}`dev-setup`).
After that, `cd` into the `docs` folder.

Next, run the following commands based on your operating system

```bash
make.bat html  # Windows
make html  # *nix
```

The first time you build the docs, it may take some time. On future builds,
the html will be cached.

## Writing Documentation

Written documentation is in the Markdown format.

When writing a docstring for a method, attribute, or a function, we use the [Google style docstrings](https://google.github.io/styleguide/pyguide.html#383-functions-and-methods).
Do NOT include the type of a parameter in the docstring: that's redundant and harder to maintain. Instead,
prefer typehinting the actual typehint in the function, and sphinx will automatically parse that.

For example,

```python
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
```

## Tips and Tricks

Sometimes Sphinx will do some weird stuff and things will stop working nicely.
In this case, a simple `make cleanall` (or `make.bat cleanall` for Windows) should do the trick.

```{warning}
`make.bat cleanall` is \_untested\_ on Windows, be careful when using it. You can alternatively
use `make.bat clean` and remove the contents of `docs/source/reference`.
```
