# Add Numbers

## Assignment

Write a class called `Calculator` with a method
`public static int add(int x, int y)` that returns their sum $x + y$.

The student submits this as `Calculator.java` (the file name must match the
class name).

## Example Solution

```java
public class Calculator {
    public static int add(int x, int y) {
        return x + y;
    }
}
```

## Example Grader

Upload the following JUnit test class as the assignment's grader. It must be
named `Grader`:

```{literalinclude} addition_grader.java
:language: java
```

This grader uses no `@Weight` annotations, so each of the 6 tests is worth 1
point (the default) - set the assignment's "Points possible" to 6. To make some
checks worth more, add `@Weight(n)`; see the {doc}`Nth Fibonacci <fibonacci_java>`
example.

The last two tests are **secret cases**: they use `assertTrue` instead of
`assertEquals` on purpose. On failure, `assertEquals` prints
`expected:<…> but was:<…>` - which hands the student the answer to hardcode -
whereas `assertTrue` prints only `AssertionError`, keeping the expected value
hidden. Reserve `assertEquals` for cases where revealing the answer is fine.
