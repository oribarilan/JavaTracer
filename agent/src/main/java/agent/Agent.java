package agent;

import javassist.ClassClassPath;
import javassist.ClassPath;
import javassist.ClassPool;
import javassist.CtClass;
import javassist.CtField;
import javassist.CtMethod;
import javassist.CtBehavior;
import javassist.CtConstructor;
import javassist.CtNewMethod;
import javassist.Modifier;
import javassist.NotFoundException;

import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.IllegalClassFormatException;
import java.lang.instrument.Instrumentation;
import java.security.ProtectionDomain;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

import java.io.FileReader;
import java.io.File;
import java.io.BufferedReader;

public class Agent {
    public static boolean isDebug = false;
    public static boolean isPrintRecord = false;
    public static boolean isSamplingEnabled = true;

    public static String PATH_TO_CONFIG = "agent_config.cfg";
    public static long SEED = 7;

    //if true, tracer will switch output files every 20,000,000 records
    public static boolean isFileSwitch = false;

    public static <ClassPathForGeneratedClasses> void premain(String agentArgs, Instrumentation inst) throws Exception {
        inst.addTransformer(new ClassFileTransformer() {

            public boolean isInitiated = false;
            public boolean shouldTransform = false;
            public double SAMPLE_RATE;

            public void AddWriteMethod(CtClass cc){
                try{
                    StringBuilder writeMethodSrc = new StringBuilder();
                    writeMethodSrc.append("public static synchronized void write(String content){ ");
                    writeMethodSrc.append("content = content + \"\\n\"; ");
                    writeMethodSrc.append("if(lineSet == null) { lineSet = new HashSet(); }");
                    writeMethodSrc.append("if(bw == null){ ");
                    writeMethodSrc.append("try { ");
                    writeMethodSrc.append("f = new File(\"traces\"+fileNum+\".log\");");
                    writeMethodSrc.append("FileWriter fw = new FileWriter(f, true); ");
                    writeMethodSrc.append("bw = new BufferedWriter(fw); ");
                    writeMethodSrc.append("} ");
                    writeMethodSrc.append("catch(Exception e){ System.out.println(\"$$$$$$$ EXCEPTION - cant instantiate bufferedwriter $$$$$$$\"); System.out.println(e.toString()); } ");
                    writeMethodSrc.append(" } ");
                    writeMethodSrc.append(" if(!lineSet.contains(content)) { bw.write(content); bw.flush(); writesNum++; lineSet.add(content); }");
                    writeMethodSrc.append(" if(lineSet.size() > 50000) { lineSet = new HashSet(); }");
                    writeMethodSrc.append(String.format("if(%s && writesNum > 20000000){ ", isFileSwitch));
                    writeMethodSrc.append("fileNum++;");
                    writeMethodSrc.append("bw.close();");
                    writeMethodSrc.append("bw = null;");
                    writeMethodSrc.append("writesNum = 0;");
                    writeMethodSrc.append(" }");
                    writeMethodSrc.append(" }");
                    CtMethod m = CtNewMethod.make(writeMethodSrc.toString(), cc);
                    m.setModifiers(Modifier.PUBLIC | Modifier.STATIC | Modifier.SYNCHRONIZED);
                    cc.addMethod(m);
                }catch(Exception e){
                    System.out.println("$$$$ Exception - cant add to method $$$$");
                    System.out.println(e.toString());
                }
            }

            public void AddRandomMethod(CtClass cc){
                try{
                    StringBuilder writeMethodSrc = new StringBuilder();
                    writeMethodSrc.append("public static double randomlyShouldSample(){ ");
                    writeMethodSrc.append("if (random == null) {");
                    writeMethodSrc.append("random = new Random();");
                    writeMethodSrc.append("}");
                    writeMethodSrc.append("return random.nextDouble();");
                    writeMethodSrc.append(" }");
                    CtMethod m = CtNewMethod.make(writeMethodSrc.toString(), cc);
                    m.setModifiers(Modifier.PUBLIC | Modifier.STATIC);
                    cc.addMethod(m);
                }catch(Exception e){
                    System.out.println("$$$$ Exception - cant add to method AddRandomMethod $$$$");
                    System.out.println(e.toString());
                }
            }

            public void AddWriteField(CtClass cc){
                try{
                    CtField randomField;
                    randomField = CtField.make("public static Random random = null;", cc);
                    randomField.setModifiers(Modifier.PUBLIC | Modifier.STATIC);
                    cc.addField(randomField, "null");

                    CtField writesNumField;
                    writesNumField = CtField.make("public static int writesNum = 0;", cc);
                    writesNumField.setModifiers(Modifier.PUBLIC | Modifier.STATIC);
                    cc.addField(writesNumField, "0");

                    CtField fileNumberField;
                    fileNumberField = CtField.make("public static int fileNum = 0;", cc);
                    fileNumberField.setModifiers(Modifier.PUBLIC | Modifier.STATIC);
                    cc.addField(fileNumberField, "0");

                    CtField fileField;
                    fileField = CtField.make("public static File f = null;", cc);
                    fileField.setModifiers(Modifier.PUBLIC | Modifier.STATIC);
                    cc.addField(fileField,"null");

                    CtField fileNameField;
                    fileNameField = CtField.make("public static BufferedWriter bw = null;", cc);
                    fileNameField.setModifiers(Modifier.PUBLIC | Modifier.STATIC);
                    cc.addField(fileNameField,"null");

                    CtField fieldLineSet;
                    fieldLineSet = CtField.make("public static HashSet lineSet = null;", cc);
                    fieldLineSet.setModifiers(Modifier.PUBLIC | Modifier.STATIC);
                    cc.addField(fieldLineSet,"null");
                }catch(Exception e){
                    System.out.println("$$$$ Exception - cant add field $$$$");
                    System.out.println(e.toString());
                }
            }

            public void initiate(String name, ClassLoader loader, ProtectionDomain protectionDomain) {
                try{
                    if(!isInitiated){
                        isInitiated = true;

                        // read config file
                        File fil = new File(PATH_TO_CONFIG);
                        FileReader inputFil = new FileReader(fil);
                        BufferedReader in = new BufferedReader(inputFil);
                        String s = in.readLine();
                        int i = 0;
                        double[] values = new double[10];
                        while (s != null) {
                            // Skip empty lines.
                            s = s.trim();
                            if (s.length() == 0) {
                                continue;
                            }

                            values[i] = Double.parseDouble(s); // This is line 19.
                            s = in.readLine();
                            i++;
                        }
                        in.close();
                        SAMPLE_RATE = values[0];
                        if(SAMPLE_RATE > 0){
                          shouldTransform = true;
                        }

                        ClassPool cp = ClassPool.getDefault();
                        cp.importPackage("java.io.BufferedWriter");
                        cp.importPackage("java.io.FileWriter");
                        cp.importPackage("java.io.File");
                        cp.importPackage("java.util.HashSet");
                        cp.importPackage("java.util.Random");
                        CtClass cc = cp.makeClass("agent.SingleFileWriter");
                        AddWriteField(cc);
                        AddWriteMethod(cc);
                        AddRandomMethod(cc);
                        cc.setModifiers(Modifier.PUBLIC);
                        cc.toClass(loader, protectionDomain);
                        ClassPath cpath = new ClassClassPath(cc.getClass());
                        cp.insertClassPath(cpath);
                    }
                }catch(Exception e){
                    System.out.println("$$$$ EXCEPTION - cant insert singlefilewriter class $$$$");
                    System.out.println(e.toString());
                }
            }

            public boolean isIgnoredClass(String className){
                if(className == null){
                    return true;
                }
                String lowerClassName = className.toLowerCase();
                String[] s = className.split("/");
                boolean isJavaClass = s[0].equals("java");
                boolean isJunitClass = lowerClassName.contains("junit");
                boolean isSun = s[0].equals("sun") || (s.length >= 2 && s[1].equals("sun"));
                boolean isSurefire = s.length >= 4 && s[0].equals("org") && s[1].equals("apache") && s[2].equals("maven") && s[3].equals("surefire");
                boolean isMaven = s.length >= 3 && s[0].equals("org") && s[1].equals("apache") && s[2].equals("maven") ;
                boolean isTestClass = lowerClassName.contains("test");
                boolean isJdk = lowerClassName.contains("jdk");

                boolean isTargetPackage = className.startsWith("org/apache/commons/math3/distribution/");

                return (isJavaClass || isJunitClass || isJdk || isSun || isSurefire || isMaven || isTestClass || !isTargetPackage);
            }

            public boolean isIgnoredMethod(CtMethod method) {
                if(method == null){
                    return true;
                }
                String lowerMethodName = method.getLongName();
                boolean isNative = Modifier.isNative(method.getModifiers());
                boolean isAbstract = Modifier.isAbstract(method.getModifiers());
                boolean isTestMethod = lowerMethodName.contains("test");

                // boolean isTargetMethod = method.getLongName().contains("getNumericalMean");

                return (isNative || isAbstract || isTestMethod);
            }

            public void treatMethod(CtBehavior method) throws IllegalClassFormatException{
                //CtBehavior is either a method or a constructor
                //for brevity, we use the variable name method
                String behaviorLongName;
                if(method instanceof CtMethod){
                  behaviorLongName = ((CtMethod) method).getLongName();
                }
                else //constructor
                {
                  // from SomePackage.SomeClass(),123,1
                  // to SomePackage.SomeClass.SomeClass(),123,1
                  // so constructor have the same form as methods
                  behaviorLongName = method.getLongName().replace("(", "."+method.getName()+"(");
                }
                try{
                    if(isDebug) System.out.println("Examining Method: "+method.getLongName());
                    // m.addLocalVariable("elapsedTime", CtClass.longType);
                    MethodRecord record = new MethodRecord(behaviorLongName, GetSelfHashTokenFromMethod(method), GetInputTokenFromMethod(method), GetOutputTokenFromMethod(method));
                    // String afterCode = String.format("try{ %s; agent.SingleFileWriter.write(%s); } catch(NoClassDefFoundError e) { System.out.println(\"writer not found\"); }", record.DeclareRecordVariable(), MethodRecord.GetRecordVariableName());
                    StringBuilder afterCode = new StringBuilder();
                    afterCode.append(record.DeclareRecordVariable()+";");
                    afterCode.append(String.format("if (!%s) {", isSamplingEnabled));
                    afterCode.append(String.format("agent.SingleFileWriter.write(%s);", MethodRecord.GetRecordVariableName()));
                    afterCode.append("}else{");
                    // afterCode.append(String.format("boolean javaagent_shouldSample = agent.SingleFileWriter.randomlyShouldSample(%s);", String.valueOf(SAMPLE_RATE)));
                    afterCode.append("boolean javaagent_shouldSample = agent.SingleFileWriter.randomlyShouldSample() < " + SAMPLE_RATE + ";");
                    afterCode.append("if (javaagent_shouldSample) {");
                    afterCode.append(String.format("agent.SingleFileWriter.write(%s);", MethodRecord.GetRecordVariableName()));
                    afterCode.append("}");
                    afterCode.append("}");
                    if(isPrintRecord){
                        afterCode.append(String.format("System.out.println(%s);",MethodRecord.GetRecordVariableName()));
                    }
                    method.insertAfter(afterCode.toString());
                }catch(Exception e){
                    System.out.println("$$$$ EXCEPTION - cant insert after $$$$");
                    System.out.println("Method name: "+method.getLongName());
                    System.out.println(e.toString());
                }
            }

            @Override
            public byte[] transform(ClassLoader classLoader, String className, Class<?> aClass, ProtectionDomain protectionDomain, byte[] bytes) throws IllegalClassFormatException {
                this.initiate(className, classLoader, protectionDomain);
                if(!shouldTransform){
                  return null;
                }

                try {
                    if(isIgnoredClass(className)){
                        return null;
                    }
                    //start
                    String name = className.replace("/", ".");
                    if(isDebug) System.out.println("Transforming Class: "+name);
                    name = name.split("$")[0];
                    ClassPool cp = ClassPool.getDefault();
                    cp.importPackage("agent.SingleFileWriter");
                    cp.appendClassPath("generated\\classes");
                    cp.appendClassPath(System.getProperty("user.dir"));
                    CtClass cc = cp.get(name);
                    if(cc.isInterface()){
                        return null;
                    }
                    CtMethod[] methods = cc.getDeclaredMethods();
                    for(CtMethod m : methods){
                        if(!isIgnoredMethod(m)){
                            treatMethod(m);
                        }
                    }
                    CtConstructor[] constructors = cc.getDeclaredConstructors();
                    for(CtConstructor c : constructors){
                      //treatMethod(c);
                    }
                    byte[] byteCode = cc.toBytecode();
                    cc.detach();
                    return byteCode;
                } catch (Exception ex) {
                    System.out.println("$$$$$$$$$$ Exception in transform $$$$$$$$$$$$$$");
                    ex.printStackTrace();
                }
                return null;
            }
        });
    }

	protected static String GetSelfHashTokenFromMethod(CtBehavior m) throws NotFoundException {
		String selfHashToken;
        if(Modifier.isStatic(m.getModifiers())){
            selfHashToken = "\"S\"";
        }else{
            selfHashToken = "System.identityHashCode( $0 )";
        }
        return selfHashToken;
	}

    protected static List<String> GetInputTokenFromMethod(CtBehavior m) throws NotFoundException {
        List<String> inputToken = new ArrayList<String>();
        CtClass[] pTypes = m.getParameterTypes();
        for(int i=0; i<pTypes.length; i++){
            String token = "$args[" + i + "]";
            CtClass pType = pTypes[i];
            if(!pType.isPrimitive()){
                token = String.format( " (%s == null ? \"NULL\" : \"\"+System.identityHashCode( %s )) ", token, token);
            }
            inputToken.add(token);
        }
        return inputToken;
	}

	protected static String GetOutputTokenFromMethod(CtBehavior m) throws NotFoundException {
    String outputToken;
    if(m instanceof CtMethod){
      CtClass retType = ((CtMethod) m).getReturnType();
      if(retType == CtClass.voidType){
          outputToken = "\"V\"";
      } else if (retType.isPrimitive()) {
          outputToken = "$_";
      } else {
          outputToken = " ($_ == null ? \"NULL\" : \"\"+System.identityHashCode( $_ )) ";
      }
    }
    else //constructor
    {
      outputToken = "\"C\"";
    }
    return outputToken;
	}

}
