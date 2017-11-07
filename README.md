# Sample Java Agent and Bytecode manipulation 

Sample maven project containing a Java agent and examples of bytecode manipulation with ASM and Javassist.

See article on my blog : 


## Build

```
$ # From the root dir
$ mvn package
```

## Run

```
$ # From the root dir
$ java -javaagent:agent/target/agent-0.1-SNAPSHOT.jar -jar other/target/other-0.1-SNAPSHOT.jar
```

Thanks to Thomas Queste for his [blog post](http://tomsquest.com/blog/2014/01/intro-java-agent-and-bytecode-manipulation/) which helped greatly in the first version of this project.
