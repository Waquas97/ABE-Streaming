#!/bin/bash

#copy 4 sets
for copy in {1..4}; do
   # Outer loop for the streams (0 to 4)
   for stream in {0..4}; do
      ln -s "init-stream${stream}.m4s" "init-stream${stream}-copy${copy}.m4s"
       # Inner loop for the chunks (00001 to 00150)
       for chunk in $(seq -f "%05g" 1 150); do
           # Construct the file name
           file_name="chunk-stream${stream}-${chunk}.m4s"
           copy_name="chunk-stream${stream}-${chunk}-copy${copy}.m4s"
        
           ln -s $file_name $copy_name
        
       done
   done
done

