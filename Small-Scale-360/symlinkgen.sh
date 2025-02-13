#!/bin/bash


#copy 4 sets
for tile in {1..9}; do
   for copy in {1..4}; do
      # Outer loop for the streams (0 to 4)
      for stream in {0..3}; do
         ln -s "init-stream${stream}.m4s" "init-stream${stream}-copy${copy}.m4s"
          # Inner loop for the chunks (00001 to 00074)
          for chunk in $(seq -f "%05g" 1 74); do
              # Construct the file name
              file_name="tile${tile}-chunk-stream${stream}-${chunk}.m4s"
              copy_name="tile${tile}-chunk-stream${stream}-${chunk}-copy${copy}.m4s"
           
              sudo ln -s $file_name $copy_name
        
          done
      done
   done
done

#copy 4 sets
for scheme in {"allI","allP"};do
   for tile in {1..9}; do
      for copy in {1..4}; do
         # Outer loop for the streams (0 to 4)
         for stream in {0..3}; do
            ln -s "init-stream${stream}.m4s" "init-stream${stream}-copy${copy}.m4s"
            # Inner loop for the chunks (00001 to 00074)
            for chunk in $(seq -f "%05g" 1 74); do
               # Construct the file name
               file_name="tile${tile}-enc_${scheme}_chunk-stream${stream}-${chunk}.m4s"
               copy_name="tile${tile}-enc_${scheme}_chunk-stream${stream}-${chunk}-copy${copy}.m4s"
            
               sudo ln -s $file_name $copy_name
         
            done
         done
      done
   done
done
