# File IO

## Assignment

Read from an input file and write the content to an output file.

## Sample Solution

```python
import sys

inp = sys.argv[1]
out = sys.argv[2]
with (
   open(inp, 'r') as f,
   open(out, 'w') as w
):
   w.write(f.read())
```

## Sample Grader

```{literalinclude} file_io.py
```
