package agent;

import javassist.ClassClassPath;
import javassist.ClassPath;
import javassist.ClassPool;
import javassist.CtClass;
import javassist.CtField;
import javassist.CtMethod;
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

public class Agent {
    public static boolean isDebug = false;
    public static boolean isPrintRecord = false;       
    public static <ClassPathForGeneratedClasses> void premain(String agentArgs, Instrumentation inst) throws Exception {
        inst.addTransformer(new ClassFileTransformer() {
            
            public boolean isInitiated = false;

            public void AddWriteMethod(CtClass cc){
                try{
                    StringBuilder writeMethodSrc = new StringBuilder();
                    writeMethodSrc.append("public static synchronized void write(String content){ ");
                    writeMethodSrc.append("content = content + \"\\n\"; ");
                    writeMethodSrc.append("if(bw == null){ ");
                    writeMethodSrc.append("try { ");
                    writeMethodSrc.append("f = new File(\"traces\"+fileNum+\".txt\");");
                    writeMethodSrc.append("FileWriter fw = new FileWriter(f, true); ");
                    writeMethodSrc.append("bw = new BufferedWriter(fw); ");
                    writeMethodSrc.append("} ");
                    writeMethodSrc.append("catch(Exception e){ System.out.println(\"$$$$$$$ EXCEPTION - cant instantiate bufferedwriter $$$$$$$\"); System.out.println(e.toString()); } ");
                    writeMethodSrc.append(" } ");
                    writeMethodSrc.append("bw.write(content); bw.flush(); writesNum++;");
                    writeMethodSrc.append("if(writesNum > 20000000){ ");
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

            public void AddWriteField(CtClass cc){
                try{
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
                }catch(Exception e){
                    System.out.println("$$$$ Exception - cant add field $$$$");
                    System.out.println(e.toString());
                }
            }

            public void initiate(String name, ClassLoader loader, ProtectionDomain protectionDomain) {
                try{
                    if(!isInitiated){
                        isInitiated = true;
                        ClassPool cp = ClassPool.getDefault();
                        cp.importPackage("java.io.BufferedWriter");
                        cp.importPackage("java.io.FileWriter");
                        cp.importPackage("java.io.File");
                        CtClass cc = cp.makeClass("agent.SingleFileWriter");
                        AddWriteField(cc);                        
                        AddWriteMethod(cc);
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
                return (isJavaClass || isJunitClass || isJdk || isSun || isSurefire || isMaven || isTestClass);
            }

            public boolean isIgnoredMethod(CtMethod method) {
                if(method == null){
                    return true;
                }
                String lowerMethodName = method.getLongName();
                Random r = new Random();
                int Lowest = 1;
                int Highest = 200;
                int rolledNumber = r.nextInt(Highest - Lowest + 1) + Lowest;
				boolean isNative = Modifier.isNative(method.getModifiers());
                boolean isAbstract = Modifier.isAbstract(method.getModifiers());
                boolean isUnlucky = rolledNumber != 1;
                boolean isTestMethod = lowerMethodName.contains("test");
                return (isNative || isAbstract || isTestMethod);
			}

            public void treatMethod(CtMethod method) throws IllegalClassFormatException{
                try{
                    if(isDebug) System.out.println("Examining Method: "+method.getLongName());                        
                    // m.addLocalVariable("elapsedTime", CtClass.longType);
                    MethodRecord record = new MethodRecord(method.getLongName(), GetSelfHashTokenFromMethod(method), GetInputTokenFromMethod(method), GetOutputTokenFromMethod(method));
                    // String afterCode = String.format("try{ %s; agent.SingleFileWriter.write(%s); } catch(NoClassDefFoundError e) { System.out.println(\"writer not found\"); }", record.DeclareRecordVariable(), MethodRecord.GetRecordVariableName());
                    String afterCode = String.format("%s; agent.SingleFileWriter.write(%s);", record.DeclareRecordVariable(), MethodRecord.GetRecordVariableName());
                    if(isPrintRecord){
                        afterCode = afterCode + String.format("System.out.println(%s);",MethodRecord.GetRecordVariableName());
                    }
                    method.insertAfter(afterCode);
                }catch(Exception e){
                    System.out.println("$$$$ EXCEPTION - cant insert after $$$$");
                    System.out.println("Method name: "+method.getLongName());
                    System.out.println(e.toString());
                }
            }
            
            @Override
            public byte[] transform(ClassLoader classLoader, String className, Class<?> aClass, ProtectionDomain protectionDomain, byte[] bytes) throws IllegalClassFormatException {
                this.initiate(className, classLoader, protectionDomain);

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

	protected static String GetSelfHashTokenFromMethod(CtMethod m) throws NotFoundException {
		String selfHashToken;
        if(Modifier.isStatic(m.getModifiers())){
            selfHashToken = "\"STATIC\"";
        }else{
            selfHashToken = "System.identityHashCode( $0 )";
        }
        return selfHashToken;
	}

    protected static List<String> GetInputTokenFromMethod(CtMethod m) throws NotFoundException {
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

	protected static String GetOutputTokenFromMethod(CtMethod m) throws NotFoundException {
		String outputToken;
        CtClass retType = m.getReturnType();
        if(retType == CtClass.voidType){
            outputToken = "\"VOID\"";
        } else if (retType.isPrimitive()) {
            outputToken = "$_";
        } else {
            outputToken = " ($_ == null ? \"NULL\" : \"\"+System.identityHashCode( $_ )) ";
        }
        return outputToken;
	}

}

