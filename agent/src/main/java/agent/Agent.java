package agent;

import javassist.CannotCompileException;
import javassist.ClassClassPath;
import javassist.ClassPath;
import javassist.ClassPool;
import javassist.CtClass;
import javassist.CtField;
import javassist.CtMethod;
import javassist.CtNewMethod;
import javassist.Modifier;
import javassist.NotFoundException;
import javassist.bytecode.AnnotationsAttribute;
import javassist.bytecode.AttributeInfo;
import javassist.bytecode.ClassFile;
import javassist.bytecode.MethodInfo;

import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.IllegalClassFormatException;
import java.lang.instrument.Instrumentation;
import java.security.ProtectionDomain;
import java.util.ArrayList;
import java.util.List;

import javax.print.DocFlavor.STRING;

import org.omg.IOP.TAG_ORB_TYPE;

public class Agent {
    public static boolean isDebug = false;
    public static boolean isPrintRecord = true;       
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
                    writeMethodSrc.append("FileWriter fw = new FileWriter(\"myfile.txt\", true); ");
                    writeMethodSrc.append("bw = new BufferedWriter(fw); ");
                    writeMethodSrc.append("} ");
                    writeMethodSrc.append("catch(Exception e){ System.out.println(\"$$$$$$$ EXCEPTION $$$$$$$\"); System.out.println(e.toString()); } ");
                    writeMethodSrc.append(" } ");
                    writeMethodSrc.append("bw.write(content); bw.flush();");
                    writeMethodSrc.append(" }");
                    CtMethod m = CtNewMethod.make(writeMethodSrc.toString(), cc);
                    m.setModifiers(Modifier.PUBLIC | Modifier.STATIC | Modifier.SYNCHRONIZED);
                    cc.addMethod(m);
                }catch(Exception e){
                    System.out.println("$$$$ Exception $$$$");
                    System.out.println(e.toString());
                }
            }

            public void AddWriteField(CtClass cc){
                try{
                    CtField fileNameField;			
                    fileNameField = CtField.make("public static BufferedWriter bw = null;", cc);
                    fileNameField.setModifiers(Modifier.PUBLIC | Modifier.STATIC);
                    cc.addField(fileNameField,"null");
                }catch(Exception e){
                    System.out.println("$$$$ Exception $$$$");
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
                        cc.writeFile("generated\\classes");
			            cc.toClass(loader, protectionDomain);
                        ClassPath cpath = new ClassClassPath(cc.getClass());
                        cp.insertClassPath(cpath);
                    }
                }catch(Exception e){
                    System.out.println("$$$$ EXCEPTION $$$$");
                    System.out.println(e.toString());
                }
            }

            public boolean isIgnoredClass(String className){
                String[] s = className.split("/");
                boolean isJavaClass = s[0].equals("java");
                boolean isJunitClass = s[0].equals("org") && s[1].equals("junit");
                boolean isSun = s[0].equals("sun") || s[1].equals("sun");
                return (isJavaClass || isJunitClass || isSun);
            }

            public void treatMethod(CtMethod method) throws IllegalClassFormatException{
                try{
                    if(isDebug) System.out.println("Examining Method: "+method.getLongName());                        
                    // m.addLocalVariable("elapsedTime", CtClass.longType);
                    MethodRecord record = new MethodRecord(method.getLongName(), GetSelfHashTokenFromMethod(method), GetInputTokenFromMethod(method), GetOutputTokenFromMethod(method));
                    if(isDebug) System.out.println(record.DeclareRecordVariable());
                    String afterCode = String.format("%s; agent.SingleFileWriter.write(%s);", record.DeclareRecordVariable(), MethodRecord.GetRecordVariableName());
                    if(isPrintRecord){
                        afterCode = afterCode + String.format("System.out.println(%s);",MethodRecord.GetRecordVariableName());
                    }
                    method.insertAfter(afterCode);
                }catch(Exception e){
                    System.out.println("$$$$ EXCEPTION $$$$");
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
                    if(isDebug) System.out.println("Examining Class: "+name);
                    name = name.split("$")[0];
                    ClassPool cp = ClassPool.getDefault();
                    cp.importPackage(name);
                    cp.appendClassPath(System.getProperty("user.dir"));
                    CtClass cc = cp.get(name);
                    if(cc.isInterface()){
                        return null;
                    }
                    CtMethod[] methods = cc.getDeclaredMethods();
                    if(isDebug) System.out.println(String.format("num of methods in %s is %s", name, ""+methods.length));
                    for(CtMethod m : methods){
                        treatMethod(m);
                    }
                    byte[] byteCode = cc.toBytecode();
                    cc.detach();
                    return byteCode;
                } catch (Exception ex) {
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

