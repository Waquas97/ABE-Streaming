import struct
import sys
import os
import timeit
import time
import csv
import subprocess

#scheme=sys.argv[1]
scheme="allI"
print(scheme)


####################################### CIPHER Initialization ###################################################
def run_command(command, *args):
    """Run a command with arguments and return the output."""
    try:
        result = subprocess.run([command] + list(args), check=True, capture_output=True, text=True)
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        print(f"Error running command {command}: {e}")
        return e.stdout, e.stderr

def dec(public_key_file, user_key_file, input_file):
    stdout, stderr = run_command('cpabe-dec', public_key_file, user_key_file, input_file,'-k')
    return stdout, stderr

# print("\n#######################\nCipher initialization time:", init_time,"\n#######################\n")
########################################### END CIPHER INIT #####################################################



################################################################ Parse I,P,B Frames ############################################################

def parse(input_filename):
    with open(input_filename, 'rb') as f:
        data= bytearray(f.read())


    # Find the mdat box
    mdat_pos = data.find(b'mdat')
    if mdat_pos == -1:
        raise ValueError("No 'mdat' box found in the file")


    num_entries_pos = mdat_pos  # mdat box starts with 4 bytes of 'size', 4 bytes of 'mdat' and 4 bytes of 'version and flags'

    index=num_entries_pos+4 #skip mdat name

    Iframes={}
    Pframes={}
    Bframes={}
    while index< len(data):                                     #CHECK document for detailed explanation why Im not using MDAT size as limit, chunks end with MDAT itself.
        nalsize= struct.unpack('>I', data[index:index+4])[0]
        #print(nalsize)
        index=index+4
        #typenal=int(data[index])
        typenal=(data[index])& 0b11111
        # print (hex(data[index]))
        if typenal==5:                                                                          #IDR frame with nal type 5: +1 to save type byte,-1 to accomodate for that type byte, +6 for integrity and -6 for accomodating size
            Iframes[index+1+6]=nalsize-1-6 

        if typenal==1:
            if data[index+1]==136:                                                              #I frame with slice type: 7, golumb(0001000) [As found: decimal(136) hex(88)]          
                Iframes[index+1+6]=nalsize-1-6 

            elif data[index+1] & 0b1111100 == 0b0011100:                                        #B frame with slice type: 6, golumb(00111)   [As found: decimal(158/159) hex(9E/9F)]
                Bframes[index+1+6]=nalsize-1-6

            elif data[index+1] & 0b1111100 == 0b0011000:                                        #P frame with slice type: 5, golumb(00110)   [As found: decimal(156/155) hex(9A/9B)]
                Pframes[index+1+6]=nalsize-1-6
                #print(data[index+1],'p detected',data[index+2])



            elif data[index+1] & 0b1110000 == 0b0110000:                                        #I frame with 2 slice type golumb(011)
                Iframes[index+1+6]=nalsize-1-6 
            
            elif data[index+1] & 0b1110000 == 0b0100000:                                        #B frame with slice type: 1, golumb(010)
                Bframes[index+1+6]=nalsize-1-6

            elif data[index+1] & 0b1000000 == 0b1000000:                                        #P frame with 0 slice type golumb(1)
                Pframes[index+1+6]=nalsize-1-6
                #print(data[index+1],'p detected',data[index+2])

            else: print("something wrong with frame type slice detection")
                
        index=index+nalsize
    #print(len(Pframes),'Pframesinchunk')


    return(Iframes,Pframes,Bframes,data)

############################################################################# END parsing ######################################################



def decrypt(Iframes,Pframes,Bframes,data,input_filename):

    if scheme== 'allI':
        encframes=dict(Iframes)

    if scheme== '3P':
        newdict=dict(Iframes)
        for index, (key, value) in enumerate(Pframes.items()):
            if index % 3 == 0:  # Check if the index is every third entry
                newdict[key] = value
        encframes = dict(sorted(newdict.items()))

    if scheme== '2P':
        newdict=dict(Iframes)
        for index, (key, value) in enumerate(Pframes.items()):
            if index % 2 == 0:  # Check if the index is even (every second entry)
                newdict[key] = value
        encframes = dict(sorted(newdict.items()))


    if scheme== 'allP':
        newdict=dict(Iframes)
        newdict.update(Pframes)
        encframes = dict(sorted(newdict.items()))

    if scheme== 'onlyallP':
        encframes=dict(Pframes)


    for a in reversed(encframes):
        
        data_to_decrypt = data[a:a+encframes[a]]

        with open('tempdec.txt.cpabe', 'wb') as f:
            f.write(data_to_decrypt)

        dec_output, dec_error = dec('pub_key', 'user_key', 'tempdec.txt.cpabe')
        
        if len(dec_output)!=0: print('Dec Output:', dec_output)
        if len(dec_error)!=0: print('Dec Error:', dec_error)


        with open('tempdec.txt', 'rb') as f:
            decrypted_data= f.read()

        # PUT DECRYPTED DATA
        data[a:a+encframes[a]] = decrypted_data

        #ACCOMODATE FOR CHANGING FRAME SIZE DUE TO CPABE
        data[a-11:a-7]= (len(decrypted_data)+7).to_bytes(4,byteorder='big')  # +7 because we skip 1 byte for slice type and 6 bytes for heade


    # Write the modified data back to a new file
    with open(input_filename.replace("enc_", "dec_"), 'wb') as f:
        f.write(data)


#######################################################  Execution ###############################################

def start_decryption(input_filename):

#input_filename="enc_allI_chunk-stream0-00001.m4s"
    #decryption_start_time = time.perf_counter_ns()
    
    Iframes,Pframes,Bframes,data=parse(input_filename)
    decrypt(Iframes,Pframes,Bframes,data,input_filename)
    #if int(input_filename.split('-')[-1].split('.')[0])>6: time.sleep(10)      # delay time to check effect
    
    #decryption_end_time = time.perf_counter_ns()
    #segment_decryption_time = (decryption_end_time - decryption_start_time)/1000000000
    #with open("time.txt",'a') as f:
    #    f.write(str(segment_decryption_time))   
    #print(segment_decryption_time)

start_decryption(sys.argv[1])

