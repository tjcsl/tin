import os
import shutil
import subprocess
import sys

# TODO: populate from db filename (needs to match public class name)
submission_name = "FROM_DB"

# TODO: total points, also from db
score = -1

jar_runner = "Runner"

# TODO: also needs to be specified from the database, as a part of managing assignment files
files_needed = [
    "FROM_DB.class",
]

assignment_path = "/".join(sys.argv[2].split("/")[:-2])  # media/assignment-X

assignment_user_path = "/".join(sys.argv[2].split("/")[:-1])  # media/assignment-X/username

# TODO: preferably find alternative to this
env = os.environ.copy()
env["JAVA_HOME"] = "/usr/lib/jvm/java-11-openjdk-amd64"
env["PATH"] = (
    "/usr/lib/jvm/java-11-openjdk-amd64/bin:/usr/lib/jvm/java-11-openjdk-amd64/jre/bin:"
    + env["PATH"]
)

submission_filename = f"{submission_name}.java"
submission_class_filename = f"{submission_name}.class"

# remove any old class files or jar files
for file in os.listdir(assignment_user_path):
    if file.endswith("class") or file.endswith("jar"):
        os.remove(assignment_user_path + f"/{file}")

# copy all the files needed for the assignment
for file_name in files_needed:
    shutil.copy(f"{assignment_path}/{file_name}", f"{assignment_user_path}/{file_name}")

# copy the submission file
shutil.copy(sys.argv[2], f"{assignment_user_path}/{submission_filename}")

# compile the submission
stream = subprocess.run(
    f"javac -J-Xmx128m {submission_filename}",
    capture_output=True,
    text=True,
    shell=True,
    env=env,
    cwd=assignment_user_path,
)

if len(stream.stderr) > 0 and "error" in stream.stderr:  # any compile errors (but not warnings)
    print("Compile errors...")
    score = 0
    print(stream.stderr)
else:
    # TODO: hardcode this file copy, along with Runner.java (or Runner.class)
    shutil.copy(f"{assignment_path}/Manifest.txt", f"{assignment_user_path}/Manifest.txt")

    # create the jar file
    subprocess.run(
        f"jar -J-Xmx128m cvfme {sys.argv[3]}.jar Manifest.txt {jar_runner} *.class",
        capture_output=True,
        text=True,
        shell=True,
        env=env,
        cwd=assignment_user_path,
    )

    run_flag = True

    # run the jar file (JUnit tests)
    stream = subprocess.run(
        f"java -Xmx128m -jar {sys.argv[3]}.jar",
        capture_output=True,
        text=True,
        shell=True,
        env=env,
        cwd=assignment_user_path,
    )

    # clean up
    os.remove(f"{assignment_user_path}/{submission_class_filename}")

    for file_name in files_needed:
        os.remove(f"{assignment_user_path}/{file_name}")

    os.remove(f"{assignment_user_path}/Manifest.txt")  # again, hardcode into the for loop above
    os.remove(f"{assignment_user_path}/{sys.argv[3]}.jar")

    # TODO: possibly unnecessary (never gets overwritten)?
    if run_flag:
        junit_output = stream.stdout
        junit_error = stream.stderr

        if len(junit_error) != 0:
            print("Errors...")
            print(junit_error)
        else:
            print(open(f"{assignment_user_path}/stdout.txt").read())  # print the student output
            runner_result = junit_output.split("\n")  # get the JUnit output

            # TODO: move this to Runner.java instead of re-parsing output
            if runner_result[0] == "Success":
                print("*** Success! ***\n\nYou passed ALL of the tests.\n")

            elif len(runner_result) < 2:
                print("Empty output from JUnit")
                score = score // 2  # set the score for no output, 50%
                print("Your submission may have called System.exit(0)")

            else:
                print("Uh-oh.")
                print("*" * 20)
                count = len(runner_result)
                result_position = 2
                while result_position < count - 2:
                    fail = runner_result[result_position]  # save the failed method
                    print(fail)  # displays the JUnit method that failed

                    while runner_result[result_position + 1] != "STOP":  # From Runner.java
                        print(runner_result[result_position + 1])  # failure description
                        result_position += 1

                    print("*" * 20)

                    # TODO: handle this better somehow (database???)
                    if "testIntegerObjects" in fail:
                        score -= 2
                    elif "testStuffObjects" in fail:
                        score -= 2
                    elif "stringToString" in fail:
                        score -= 2

                    result_position += 2

                pos = runner_result[1].index("/")  # TODO: why is this here?

print("Score: {}".format(score))  # Tin's format

# TODO: do username parsing in a better way
with open(sys.argv[4], "a") as logfile:
    uname = sys.argv[3]

    # student
    if uname[0] == "2":
        lname = uname[5:]
        fname = uname[4]

    # teacher
    else:
        lname = uname[2:]
        fname = uname[0]

    logfile.write("{},{},{}\n".format(lname, fname, score))
