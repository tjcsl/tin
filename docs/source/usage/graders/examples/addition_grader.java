import static org.junit.Assert.assertEquals;

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

    // "secret" cases the student does not see in the sample tests
    @Test
    public void secretCase1() {
        assertEquals(200, Calculator.add(120, 80));
    }

    @Test
    public void secretCase2() {
        assertEquals(0, Calculator.add(-50, 50));
    }
}
