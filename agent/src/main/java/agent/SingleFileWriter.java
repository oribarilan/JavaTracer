// package agent;

// import java.io.BufferedWriter;
// import java.io.File;
// import java.io.FileWriter;
// import java.io.IOException;

// public abstract class SingleFileWriter{
//     private static BufferedWriter bw = null;
//     private static File f = null;
//     private static int fileNum = 0;
//     public static synchronized void write(String content){ 
//         content = content + "\n";
//         if(bw == null){ 
//             try {
//                 f = new File("traces"+fileNum+".txt");
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
//             if(f.length() > 4000000000.0){ 
//                 fileNum++;
//                 bw = null;
//             }
//         }catch(IOException e){
//             System.out.println("$$$$$$$ EXCEPTION - cant write or flush $$$$$$$");
//             System.out.println(e.toString());
//         }
//     }
// }