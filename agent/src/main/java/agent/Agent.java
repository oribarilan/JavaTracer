package agent;

import javassist.CannotCompileException;
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

import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.IllegalClassFormatException;
import java.lang.instrument.Instrumentation;
import java.security.ProtectionDomain;
import java.util.ArrayList;
import java.util.List;

public class Agent {

    public static void premain(String agentArgs, Instrumentation inst) {
        inst.addTransformer(new ClassFileTransformer() {
            @Override
            public byte[] transform(ClassLoader classLoader, String className, Class<?> aClass, ProtectionDomain protectionDomain, byte[] bytes) throws IllegalClassFormatException {
                try {
                    //ignore classes
                    String[] s = className.split("/");
                    boolean isJavaClass = s[0].equals("java");
                    boolean isJunitClass = s[0].equals("org") && s[1].equals("junit");
                    boolean isSun = s[0].equals("sun") || s[1].equals("sun");
                    if(isJavaClass || isJunitClass || isSun){
                        return null;
                    }
                    //start
                    String name = className.replace("/", ".");
                    System.out.println("Examining Class: "+name);
                    name = name.split("$")[0];
                    ClassPool cp = ClassPool.getDefault();
                    cp.importPackage(name);
                    cp.appendClassPath(System.getProperty("user.dir"));
                    CtClass cc = cp.get(name);
                    if(cc.isInterface()){
                        return null;
                    }
                    CtMethod[] methods = cc.getDeclaredMethods();
                    System.out.println(String.format("num of methods in %s is %s", name, ""+methods.length));
                    for(CtMethod m : methods){
                        System.out.println("Examining Method: "+m.getLongName());                        
                        // m.addLocalVariable("elapsedTime", CtClass.longType);
                        MethodRecord record = new MethodRecord(m.getLongName(), GetSelfHashTokenFromMethod(m), GetInputTokenFromMethod(m), GetOutputTokenFromMethod(m));
                        System.out.println(record.DeclareRecordVariable());
                        m.insertAfter(String.format("%s;System.out.println(%s);",record.DeclareRecordVariable(),MethodRecord.GetRecordVariableName()));
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

