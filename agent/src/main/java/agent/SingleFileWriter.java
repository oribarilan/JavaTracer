// package agent;

// import java.io.BufferedWriter;
// import java.io.FileWriter;
// import java.io.IOException;

// public abstract class SingleFileWriter{
//     private static BufferedWriter bw = null;
//     public static synchronized void write(String content){ 
//         content = content + "\n";
//         if(bw == null){ 
//             try { 
//                 FileWriter fw = new FileWriter("traces.txt", true); 
//                 bw = new BufferedWriter(fw);
//             }
//             catch(Exception e){ 
//                 System.out.println("$$$$$$$ EXCEPTION - cant instantiate bufferedwriter $$$$$$$");
//                 System.out.println(e.toString());
//             } 
//         }
//         try{
//             bw.write(content);
//             bw.flush();
//         }catch(IOException e){
//             System.out.println("$$$$$$$ EXCEPTION - cant write or flush $$$$$$$");
//             System.out.println(e.toString());
//         }
//     }
// }