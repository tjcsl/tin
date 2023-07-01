import org.junit.runner.JUnitCore;
import org.junit.runner.Result;
import org.junit.runner.notification.Failure;
import java.io.PrintStream;
import java.io.BufferedOutputStream;
import java.io.FileOutputStream;
import java.io.FileNotFoundException;
import java.util.List;

public class Runner {
    public static void main(String[] args) throws FileNotFoundException {
        JUnitCore jc = new JUnitCore() ;
        PrintStream realOut = System.out;
        PrintStream realErr = System.err;

        System.setOut(new PrintStream(new BufferedOutputStream(new FileOutputStream("stdout.txt")), true));
        System.setErr(new PrintStream(new BufferedOutputStream(new FileOutputStream("stderr.txt")), true));
  
        Result result = jc.run(Grader.class);
  
        System.setOut(realOut);
        System.setErr(realErr);
  
        int n = result.getRunCount();
  
        if (result.wasSuccessful()) {
            System.out.println("Success");
            System.out.println(n + "/" + n + " cases passed");
        } else {
            System.out.println("Failure");
            List<Failure> mylist = result.getFailures();
            int m = mylist.size();
            System.out.println(( n - m ) + "/" + n + " cases passed");
   
            for (Failure failure : mylist) {
                System.out.println(failure.getDescription());
                System.out.println(failure.getException());
                System.out.println("STOP");
            }
        }
        System.out.println("END") ;
    }
}
