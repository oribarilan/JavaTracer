package agent;

import java.util.List;

public class MethodRecord {
    public static final String PREFIX_COMMONMATH = "org.apache.commons.math3.";


    private String methodLongName;
    private String minimalMethodLongName;
    private String selfHashToken;
    private List<String> inputToken;
    private String outputToken;

    public MethodRecord(String methodLongName, String selfHashToken, List<String> inputToken, String outputToken){
        //fix methodname - start
        //replace ',' with '_' because it will be contained in a CSV file
        methodLongName = methodLongName.replace(',', '_');
        methodLongName = methodLongName.replaceFirst("(?:[$][0-9])", "");
        //fix methodname - end
        this.methodLongName = methodLongName;
        this.selfHashToken = selfHashToken;
        this.inputToken = inputToken;
        this.outputToken = outputToken;
        //project-specific methodname optimization
        this.minimalMethodLongName = this.methodLongName;
        if(this.methodLongName.startsWith(PREFIX_COMMONMATH)){ //using replace to rename parameters as well
          this.minimalMethodLongName = this.methodLongName.replace(PREFIX_COMMONMATH, "");
        }
    }

    public static String GetRecordVariableName(){
        return "qazwsxedc123321";
    }

    public String DeclareRecordVariable(){
        StringBuilder sb = new StringBuilder();
        sb.append("String ");
        sb.append(GetRecordVariableName());
        sb.append(" = ");
        sb.append("\""+this.minimalMethodLongName+"\""+"+\",\"+");
        sb.append("\"\"+"+this.selfHashToken+"+\",\"+");
        for(int i=0; i<this.inputToken.size(); i++){
            sb.append("\"\"+"+this.inputToken.get(i)+"+\",\"+");
        }
        sb.append("\"\" + "+this.outputToken);
        return sb.toString();
    }

    public String GetRecordCodeToken(){
        String[] elements = new String[this.inputToken.size() + 2];
        elements[0] = selfHashToken;
        elements[elements.length-1] = outputToken;
        for(int i=0; i<this.inputToken.size(); i++){
            elements[i+1] = inputToken.get(i);
        }
        // not using String.join(",", elements) to support Java 7
        String codeToken = "";
        for(int i=0; i<elements.length; i++){
          codeToken = codeToken + elements[i] + ",";
        }
        codeToken = codeToken.substring(0, codeToken.length() - 1);
        return codeToken;
    }
}
