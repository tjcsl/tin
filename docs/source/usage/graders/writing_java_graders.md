# Writing a Grader (Java)

```{caution}
It isn't as simple as it sounds - there are certain traps
that are easy to fall into. Read the full page before writing a grader.
```

```{note}
This page covers **Java** graders (assignments whose grader language is Java).
If you are grading Python assignments, see {doc}`writing_python_graders` instead.
```

Unlike Python assignments - where you write the whole grader script yourself -
Java assignments let Tin do the heavy lifting. You only write a
[JUnit 4](https://junit.org/junit4/) test class named `Grader`, and Tin
compiles it together with the student's submission, runs it inside the sandbox,
and turns the JUnit results into a score automatically.

## How do I write one?

Create the assignment with its grader language set to **Java**, then upload a
single file - a JUnit test class - as the grader. Your test class **must** be
named `Grader` (it is stored as `Grader.java`):

```java
import static org.junit.Assert.assertEquals;
import org.junit.Test;

public class Grader {
    @Test
    public void addsTwoNumbers() {
        assertEquals(5, Calculator.add(2, 3));
    }

    @Test
    public void addsNegativeNumbers() {
        assertEquals(-1, Calculator.add(2, -3));
    }
}
```

Behind the scenes, for each submission Tin:

1. stages your `Grader.java`, the student's submission, a Tin-provided JUnit
   runner (`Runner.java`), and any {ref}`Manage-files <java-manage-files>` next
   to one another,
2. compiles them together and runs `Runner` inside the sandbox (the runner
   simply does `JUnitCore.runClasses(Grader.class)`), and
3. adds up the weights of your passing `@Test` methods and reports that
   {ref}`score <java-automatic-scoring>`.

You never invoke `javac`/`java` yourself, and you never call the sandbox
wrapper — Tin does all of that. You just describe the tests.

```{tip}
Each `@Test` method is worth 1 point by default. Annotate a test with
`@Weight(n)` to make it worth `n` points instead. See
{ref}`Automatic Scoring <java-automatic-scoring>`.
```

See {doc}`examples_java` for complete example graders.

## Restrictions on Student Submissions

The student's file must contain a single top-level `public` class, and the
**file name must match that class name**. Tin saves the submission under the
"file name" you set on the assignment's "Edit" page, so if the student's class
is `Calculator`, the file name must be `Calculator.java`. A mismatch makes the
Java compiler reject the submission before any test runs.

Your `Grader` refers to the student's class by name (`Calculator` above), so
decide on the class and method signatures up front and tell your students.

Student submissions run in the same sandbox as Python submissions, including:

- A memory limit
- A restriction on the number of subprocesses that can be launched.
- Being unable to access the internet (can be configured)
- No access to the rest of the filesystem - only the (temporary) directory the
  submission is compiled and run in.

To allow submissions to access the internet, go to the assignment's "Edit" page
and check the box labeled "Give submissions internet access".

```{caution}
Be careful when enabling internet access - this makes it easier for
students to cheat.
```

```{caution}
JUnit runs the student's code inside the **same** JVM as your `Grader`. Treat
student code as hostile: a submission that calls `System.exit` will abort
the run (Tin scores it `0`), and a submission stuck in an infinite loop will be
killed when the grader times out. Avoid designs where a student's return value
is used to decide the grade in an unsafe way (e.g. reflection into the grader).
```

If you need to change the memory limit, please {doc}`contact Tin developers </contact>`.

(java-manage-files)=
### Giving Students access to specific files

Java graders do not use the `--read`/`--write` wrapper arguments that Python
graders do. Instead, upload any extra files the assignment needs - helper
classes, test-data files, expected-output files - as **Manage-files** on the
assignment's "Edit" page. Tin automatically stages every Manage-file next to the
student's submission before compiling, so:

- `.java` helper files are compiled alongside the submission and `Grader`.
- data files (e.g. `input.txt`) are readable from the working directory by their
  plain name.

Files a student's code writes (e.g. `output.txt`) should be created in the
working directory, which is always writable.

```{note}
Tin stages every Manage-file **except** ones that would clobber the machinery:
the student's own class, `Grader.java`, Tin's `Runner.java`, and any file
beginning with `grader`. Don't rely on uploading a file with one of those names.
```

See {doc}`the File IO example <examples/file_io_java>` for a grader that stages
an input file this way.

```{tip}
For security, keep reference solutions and expected results inside your
`Grader.java` (or `.java` reference files) rather than uploading them as
separate data files.
```

## Grader Output

Anything the student's code (or your `Grader`) prints to standard output is
shown to the student. JUnit failure messages are surfaced too, so an
`assertEquals` mismatch or a thrown exception's message will be visible - **keep
solution details out of assertion messages** if you don't want students to see
them.

If the submission does not compile, Tin shows the compiler errors and scores the
submission `0`. If the grader exceeds its timeout (set on the assignment's "Edit"
page), the student sees `[Grader timed out]` and no score is recorded.

(java-automatic-scoring)=
### Automatic Scoring

You do **not** print a `Score:` line yourself - Tin computes it from the JUnit
results. Each `@Test` method is worth **1 point by default**; annotate it with
`@Weight(n)` to make it worth `n` points. (`@Weight` is supplied by Tin - your
grader can use it with no import.) The score is the **sum of the weights of the
passing tests**:

$$\text{score} = \sum_{\text{passing tests}} \text{weight}$$

Set the assignment's "Points possible" to the total weight of all your tests. If
the weights add up to **more** than "Points possible", the surplus is extra
credit.

```java
public class Grader {
    @Test @Weight(1) public void handlesEmpty()    { /* ... */ }  // 1 point
    @Test @Weight(1) public void handlesOne()       { /* ... */ }  // 1 point
    @Test @Weight(3) public void handlesLargeInput(){ /* ... */ }  // 3 points
}
```

This grader is worth 5 points (1 + 1 + 3); a submission that passes the first
two but fails the last scores 2. You can freely mix annotated and unannotated
tests - anything without `@Weight` counts as 1.

```{note}
A submission that fails to compile, calls `System.exit`, or times out is
scored `0` - the automatic scoring only runs when JUnit produces a result.
```
