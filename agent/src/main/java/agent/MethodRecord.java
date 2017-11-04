package agent;

import java.util.List;

public class MethodRecord {
    private String methodLongName;
	private String selfHashToken;
    private List<String> inputToken;
    private String outputToken;
    
    public MethodRecord(String methodLongName, String selfHashToken, List<String> inputToken, String outputToken){
        this.methodLongName = methodLongName;
        this.selfHashToken = selfHashToken;
        this.inputToken = inputToken;
        this.outputToken = outputToken;
    }

    public static String GetRecordVariableName(){
        return "qazwsxedc123321";
    }

    public String DeclareRecordVariable(){
        StringBuilder sb = new StringBuilder();
        sb.append("String ");
        sb.append(GetRecordVariableName());
        sb.append(" = ");
        sb.append("\""+this.methodLongName+"\""+"+\",\"+");
        sb.append("\"\"+"+this.selfHashToken+"+\",\"+");
        for(int i=0; i<this.inputToken.size(); i++){
            sb.append("\"\"+"+this.inputToken.get(i)+"+\",\"+");
        }
        sb.append("\"\" + "+this.outputToken);
        return sb.toString();
    }

    public String GetRecordCodeToken(){
        String[] elements = new String[inputToken.size() + 2];
        elements[0] = selfHashToken;
        elements[elements.length-1] = outputToken;
        for(int i=0; i<this.inputToken.size(); i++){
            elements[i+1] = inputToken.get(i);
        }
        return String.join(",", elements);
    }
}