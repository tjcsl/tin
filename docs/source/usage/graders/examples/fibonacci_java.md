# Nth Fibonacci

## Assignment

Write a class called `Fibonacci` with a method `public static long fib(int n)`
that returns the `n`th Fibonacci number, where `fib(1) == 1` and `fib(2) == 1`.

The student submits this as `Fibonacci.java`.

## Sample Solution

```java
public class Fibonacci {
    public static long fib(int n) {
        long cur = 1, next = 1;
        for (int i = 1; i < n; i++) {
            long tmp = cur + next;
            cur = next;
            next = tmp;
        }
        return cur;
    }
}
```

## Example Grader

```{literalinclude} fibonacci_grader.java
:language: java
```

This grader uses `@Weight(n)` to weight the harder cases more heavily: the
weights are `1 + 1 + 1 + 2 + 5 = 10`, so set the assignment's "Points possible"
to 10. Note `fib10` has no `@Weight` and so is worth 1 point (the default) - you
can mix weighted and unweighted tests freely. A submission that passes
everything except `fib50` scores 5 out of 10.
