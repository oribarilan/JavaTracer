# JavaTracer

A maven project containing a Java-Agent that, when attached, traces all method invocations.
The goal of this project is to instrument a java program such that rich traces of the test-suite would be available, for automated fault localization techniques. However, it may be useful for many other use cases.

## Description & Features

  - `traces.txt` file will be created, containing all of the traces
  - A trace is a log that contains various data about the invocation of a method
  - Data that is currently being traced:
    -   Method's name
    -   If method is non-static, `hashcode` of the invoking object, `STATIC` otherwise
    -   If method has parameters, the arguments (value for primitive parameters, `hashcode` for non-primitive parameters)
    -   If finishes succesfully, the return value (value for primitive return type, `hashcode` for non-primitive return type, `VOID` for void return types)
    -   If does not finish succesfully (e.g. exception was thrown), instead of the above return value, the trace will contain "EXCEPTION" - **Work In Progress**

## Prerequisites

* Java
* Maven

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
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-surefire-plugin</artifactId>
  <configuration>
    <argLine>-javaagent:"<full-path-to-agent.jar>"</argLine>
    ...
  </configuration>
</plugin>
```

### Then, run the project's test suite using the following command

```
mvn surefire:test
```

(notice that you might need to run `mvn package` first)

## References & Recognitions

* [Amir Elmishali](https://github.com/amir9979). A contributor to this project
* [Thomas Queste](http://www.tomsquest.com/about). Thomas' [blog post](http://tomsquest.com/blog/2014/01/intro-java-agent-and-bytecode-manipulation/) helped greatly in the making of this project
