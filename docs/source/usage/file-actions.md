# File Actions

File actions are Tin's way of running commands on the files of an assignment.

For example, say you have a Java file used in a grader, and you wanted to compile
it into a `.class` file. Instead of compiling the java file locally and uploading
the class file to Tin each time you change it, you can upload the Java file to
Tin and use a file action to compile it to a `.class` file.

## The File Action Marketplace
When viewing a course, there will be a button called "Manage File Actions". This will take you to the
File Action Marketplace, where you can see every file action created across courses, or create your
own file action. We **strongly recommend** checking if a file action that suits your needs can be found
in the marketplace before creating your own.

After adding a file action to your course, you can edit it, copy it, or remove it from your course
by hovering over it.

## File Action Commands
Let's take the previous example of compiling all `.java` files uploaded to Tin.
To do that, we need to:

1. Find all files _ending_ with `.java`
2. Run `javac <space separated filenames>`

To do this, we can create a file action with

- Match type set to "Ends with"
- Match value set to `.java`
- The command set to `javac $FILES`

```{note}
For security reasons, the command does not have the same capabilities
as a full shell. For example, redirections, heredocs, or command substitutions
are not possible. Instead, think of the command as being run as a subprocess.
```

## `$FILE` vs `$FILES`
In some cases, the need may arise to call a command on every
matching file, instead of a space separated list of filenames. In such
a case, one can use `$FILE` instead of `$FILES`.

To illustrate, suppose we had the following directory structure:
```
.
├── Bar.java
├── data.txt
└── Foo.java
```
Then, assuming that the match value is set to ending with `.java`,

- Setting the command to `javac $FILES` would run `javac Bar.java Foo.java`
- Setting the command to `javac $FILE` would first run `javac Bar.java` and after that, `javac Foo.java`
