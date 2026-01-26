# Nth Fibonacci

## Assignment

Write a program that takes an integer `n` and returns the nth Fibonacci number.

## Sample Solution

```python
import sys

n = int(sys.argv[1])-1
nums = [0, 1]
while n >= len(nums):
   nums.append(nums[-1] + nums[-2])
return nums[n]
```

## Example Grader

```{literalinclude} fibonacci.py
```
