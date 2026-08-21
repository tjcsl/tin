import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

// Your grader must be a JUnit test class named `Grader`, uploaded as the
// assignment's grader file. Tin compiles it with the student's `Calculator`
// submission and runs it in the sandbox; the score is the fraction of these
// @Test methods that pass.
public class Grader {

    @Test
    public void case1() {
        assertEquals(3, Calculator.add(1, 2));
    }

    @Test
    public void case2() {
        assertEquals(7, Calculator.add(3, 4));
    }

    @Test
    public void largeNumbers() {
        assertEquals(21345, Calculator.add(1000, 20345));
    }

    @Test
    public void case4() {
        assertEquals(132, Calculator.add(54, 78));
    }

    // "Secret" cases: use assertTrue, NOT assertEquals. On failure assertEquals
    // prints "expected:<X> but was:<Y>" -- which hands the student the answer, so
    // they could just hardcode it. assertTrue only prints "AssertionError", so
    // the expected value stays hidden. Use it for cases you don't want revealed.
    @Test
    public void secretCase1() {
        assertTrue(Calculator.add(120, 80) == 200);
    }

    @Test
    public void secretCase2() {
        assertTrue(Calculator.add(-50, 50) == 0);
    }
}
