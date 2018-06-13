# JavaTracer

A maven project containing a Java-Agent that, when attached, traces all method invocations.
The goal of this project is to instrument a java program such that rich traces of the test-suite would be available, for automated fault localization techniques. However, it may be useful for many other use cases.

Version `1.1` (see 'Updates' for more information)

## Description & Features

  - `traces.txt` file will be created, containing all of the traces
  - A trace is a log that contains various data about the invocation of a method
  - Data that is currently being traced:
    -   Method's name
    -   If method is non-static, `hashcode` of the invoking object, `STATIC` otherwise
    -   If method has parameters, the arguments (value for primitive parameters, `hashcode` for non-primitive parameters)
    -   If finishes succesfully, the return value (value for primitive return type, `hashcode` for non-primitive return type, `VOID` for void return types)
    -   If does not finish succesfully (e.g. exception was thrown), instead of the above return value, the trace will contain "EXCEPTION" - **Work In Progress**

## Setup & Parameters

  - If you would like to remove a common prefix from all traces, please view the `PREFIX_COMMONMATH` constant in `MethodRecord.java`
  - TODO: explain sampleRate

## Prerequisites

* Java Development Kit (V == [7u60](http://www.oracle.com/technetwork/java/javase/downloads/java-archive-downloads-javase7-521261.html))
* Maven (V >= 3.3.9)

## Build

```
$ # From the root dir
$ mvn package
```

## Run on the Example Project

```
$ # From the root dir
$ java -javaagent:agent/target/agent-0.1-SNAPSHOT.jar -jar other/target/other-0.1-SNAPSHOT.jar
```

## Use Case 1: Attach Agent to a Project

Similar to _Run on the Example Project_
```
java -javaagent:<full-path-to-agent.jar> -jar <full-path-to-target-jar.jar>
```

## Use Case 2: Attach Agent to Test Suit

### For projects built using _maven_ and the  _surefire_ plugin

Add _argLine_ element under _configuration_, e.g.:
```
<build>
  <plugins>
    ...
    <plugin>
      <groupId>org.apache.maven.plugins</groupId>
      <artifactId>maven-surefire-plugin</artifactId>
      <configuration>
        <argLine>-javaagent:"<full-path-to-agent.jar>"</argLine>
        ...
      </configuration>
    </plugin>
    ...
  </plugins>
  ...
</build>
```

### Then, run the project's test suite using the following command

*Note that you might need to run `mvn package` first.

```
mvn surefire:test
```
Alternatively, you can just run a specific test class or a single test (see "useful operations" below).

### Useful maven/surefire operations:

1. Running a single test class. Example: class name = `FunctionUtilsTest`

```
mvn surefire:test -Dtest=FunctionUtilsTest -fae
```

2. Running a single test method. Example: class name = `GradientFunctionTest`, method name = `test2DDistance`

```
mvn surefire:test -Dtest=GradientFunctionTest#test2DDistance -fae
```

3. Rebuild the whole project without running the test suit

```
mvn install -DskipTests -fae
```

4. Fail at End. If `-fae` flag is present, the command will only fail the build afterward all test have finished

## Versions

#### 1.1
- Added tracing support for constructors
- Some optimizations

## References & Recognitions

* [Amir Elmishali](https://github.com/amir9979). A contributor to this project
* [Thomas Queste](http://www.tomsquest.com/about). Thomas' [blog post](http://tomsquest.com/blog/2014/01/intro-java-agent-and-bytecode-manipulation/) helped greatly in the making of this project
