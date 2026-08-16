import static org.junit.Assert.assertEquals;

import java.nio.file.Files;
import java.nio.file.Paths;

import org.junit.Test;

// `input.txt` is uploaded as a Manage-file, so Tin stages it next to the
// submission automatically - the student's code can open it by its plain name.
// The student's `Summer` class reads it and writes the sum to `output.txt`,
// which this grader then checks.
public class Grader {

    @Test
    public void writesCorrectSum() throws Exception {
        Summer.run();

        String result = new String(
            Files.readAllBytes(Paths.get("output.txt"))
        ).trim();

        // the integers in input.txt add up to 42
        assertEquals("42", result);
    }
}
