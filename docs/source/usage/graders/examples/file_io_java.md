# File IO

## Assignment

Read the integers in `input.txt` and write their sum to `output.txt`.

The student submits a `Summer.java` class with a `public static void run()`
method. The teacher provides `input.txt` by uploading it as a **Manage-file**,
so Tin stages it next to the submission automatically - this is the Java
equivalent of the Python grader's `--read` argument.

## Sample Solution

```java
import java.io.File;
import java.io.PrintWriter;
import java.util.Scanner;

public class Summer {
    public static void run() throws Exception {
        long sum = 0;
        try (Scanner in = new Scanner(new File("input.txt"))) {
            while (in.hasNextInt()) {
                sum += in.nextInt();
            }
        }
        try (PrintWriter out = new PrintWriter("output.txt")) {
            out.println(sum);
        }
    }
}
```

## Sample Grader

```{literalinclude} file_io_grader.java
:language: java
```

```{note}
Upload `input.txt` as a Manage-file on the assignment's "Edit" page. Any data or
helper files listed there are staged next to the submission before it is
compiled and run.
```
