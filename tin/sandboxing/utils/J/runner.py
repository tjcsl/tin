#   Line 16 & 18:  file_name and points
#   Line 23: list the expected .class files
#   Line 131: if JUnit test requires text files, shutil each one.
#   Line 277:  list the Junit methods, subtract points.

import os

import shutil

import subprocess

import sys

import signal


student_submission_file_name = "BST_Generic"    # change filename
score = 10                             # total points

jar_entry_point = "TestRunner_TIN"
list_of_common_files = [ "Stuff.class", "TreeNode.class", "TestRunner_TIN.class" , "BST_GenericTest.class" ]     # change here

BASE_PATH = "/".join(sys.argv[2].split("/")[:-2])

#BASE_PATH_W_UNAME = BASE_PATH + f"/{sys.argv[3].lower()}" # teacher username is SMTorbert rather than smtorbert
BASE_PATH_W_UNAME = "/".join(sys.argv[2].split("/")[:-1])

env = os.environ.copy()
env["JAVA_HOME"] = "/usr/lib/jvm/java-11-openjdk-amd64"
env["PATH"] = "/usr/lib/jvm/java-11-openjdk-amd64/bin:/usr/lib/jvm/java-11-openjdk-amd64/jre/bin:" + env["PATH"]

#new_file_path = BASE_PATH_W_UNAME + f"/{student_submission_file_name}.java"
new_file_path = f"{student_submission_file_name}.java"

for fname in os . listdir( BASE_PATH_W_UNAME ) :
    # remove any old class files
    if 'class' in fname and fname[ -5 : ] == 'class' :
        os . remove( BASE_PATH_W_UNAME  + f"/{fname}" )

    # remove any old jar files
    if 'jar' in fname and fname[ -3 : ] == 'jar' :
        os . remove( BASE_PATH_W_UNAME  + f"/{fname}" )

for file_name in list_of_common_files: # *** CHANGE... THIS WAS LOWER BEFORE ***
    shutil.copy(f"{BASE_PATH}/{file_name}", f"{BASE_PATH_W_UNAME}/{file_name}")

shutil.copy(sys.argv[2], f'{BASE_PATH_W_UNAME}/{new_file_path}' )   # rename their submission to be WhateverClassName.java

stream = subprocess.run(f"javac -J-Xmx128m {new_file_path}", capture_output=True, text=True, shell=True, env=env, cwd=BASE_PATH_W_UNAME)

#if stream . returncode != 0 :
if len( stream . stderr) > 0  and 'error' in stream . stderr :     # ignore warnings
    print( 'Compile errors...' )
    score = 0
    print( stream . stderr )
else :
    shutil.copy(f"{BASE_PATH}/Manifest.txt", f"{BASE_PATH_W_UNAME}/Manifest.txt")    # must find this file
    #shutil.copy(f"{BASE_PATH}/widgets.txt", f"{BASE_PATH_W_UNAME}/widgets.txt")  # comment out Line 134
    #shutil.copy(f"{BASE_PATH}/strings.txt", f"{BASE_PATH_W_UNAME}/strings.txt")  # comment out Line 134

    stream = subprocess.run(f"jar -J-Xmx128m cvfme {sys.argv[3]}.jar Manifest.txt {jar_entry_point} *.class", capture_output=True, text=True, shell=True, env=env, cwd=BASE_PATH_W_UNAME)

    runFlag = True

    stream = subprocess.run(f"java -Xmx128m -jar {sys.argv[3]}.jar", capture_output=True, text=True, shell=True, env=env , cwd=BASE_PATH_W_UNAME)

    # clean up
    os . remove( f"{BASE_PATH_W_UNAME}/{student_submission_file_name}.class" )

    for file_name in list_of_common_files:
        os . remove( f"{BASE_PATH_W_UNAME}/{file_name}" )

    os . remove( f"{BASE_PATH_W_UNAME}/Manifest.txt" )
    os . remove( f"{BASE_PATH_W_UNAME}/{sys.argv[3]}.jar" )

    # *** student's last submission remains as Sentence.java for possible future teacher annotation and/or modification ***
    # UPDATE - not really - file stored in "Submit" is actually a py file !!!
    # end

    if runFlag :
        junit_output = stream.stdout
        junit_error  = stream.stderr

        if len( junit_error ) != 0 :
            print( 'Errors...' )
            print( junit_error )
        else :
            #print( junit_output )   #  Success, 1/1 passed, END
            print( open( f"{BASE_PATH_W_UNAME}/stdout.txt") . read() )        # see the student output
            txt = junit_output . split( '\n' )      # get the JUnit output

            if txt[0] == 'Success' :
                print( '*** Success! ***\n\nYou passed ALL of the tests.\n' )

            elif len( txt ) < 2 :
                print( 'Empty output from JUnit' )
                score = score // 2         # set the score for no output, 50%
                print( 'Your submission may have called System.exit(0)' )

            else :
                print( 'Uh-oh.' )
                print( '*' * 20 )
                txtlen = len( txt )
                txtpos = 2
                while txtpos < txtlen - 2 :
                    failedAt = txt[txtpos]     # save the failed method to subtract the points, later
                    print( txt[txtpos] )       # displays the JUnit method that failed

                    while txt[txtpos+1] != 'STOP':   # STOP must be in the TestRunner_TIN
                        print( txt[txtpos+1] )     # displays the description of the failure. Failure may be multiple lines.
                        txtpos += 1

                    print( '*' * 20 )

                    if 'testIntegerObjects' in failedAt  :     #  specify which method(s) failed with points.  Line 277
                        score -= 2

                    elif 'testStuffObjects' in failedAt  :
                        score -= 2

                    elif 'stringToString' in failedAt :
                        score -= 2

                    txtpos += 2

                pos = txt[1] . index( '/' )


print( 'Score: {}' . format( score ) )        #  Tin puts the score in the table

with open( sys.argv[4] , 'a' ) as logfile :
    uname = sys.argv[3]

    if uname[0] == '2' :
        lname = uname[5:]
        fname = uname[4]

    else :
        lname = uname[2:]
        fname = uname[0]

    logfile . write( '{},{},{}\n' . format( lname , fname , score ) )
