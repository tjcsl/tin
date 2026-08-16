import static org.junit.Assert.assertEquals;

import org.junit.Test;

// Uploaded as the assignment's grader file (stored as `Grader.java`). Each test
// is worth 1 point unless annotated with @Weight(n). The score is the sum of the
// passing tests' weights, so set "Points possible" to the total (10 here).
public class Grader {

    @Test
    @Weight(1)
    public void fib1() {
        assertEquals(1L, Fibonacci.fib(1));
    }

    @Test
    @Weight(1)
    public void fib2() {
        assertEquals(1L, Fibonacci.fib(2));
    }

    // No @Weight, so this test is worth 1 point (the default).
    @Test
    public void fib10() {
        assertEquals(55L, Fibonacci.fib(10));
    }

    @Test
    @Weight(2)
    public void fib20() {
        assertEquals(6765L, Fibonacci.fib(20));
    }

    // The hardest case is worth the most.
    @Test
    @Weight(5)
    public void fib50() {
        assertEquals(12586269025L, Fibonacci.fib(50));
    }
}
