import struct
import sys
import os
import timeit
import time
import csv
import subprocess

num_chunks=int(sys.argv[1])+1
scheme=sys.argv[2]
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

def keygen(flag, user_key_file, public_key_file, master_key_file, attributes):
    stdout, stderr = run_command('cpabe-keygen', flag, user_key_file, public_key_file, master_key_file, attributes)
    return stdout, stderr

def enc(public_key_file, input_file, policy):
    stdout, stderr = run_command('cpabe-enc', public_key_file, input_file, policy,'-k')
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

    i_chunksize=0
    p_chunksize=0
    b_chunksize=0
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
            i_chunksize=i_chunksize+nalsize

        if typenal==1:
            if data[index+1]==136:                                                              #I frame with slice type: 7, golumb(0001000) [As found: decimal(136) hex(88)]          
                Iframes[index+1+6]=nalsize-1-6 
                i_chunksize=i_chunksize+nalsize

            elif data[index+1] & 0b1111100 == 0b0011100:                                        #B frame with slice type: 6, golumb(00111)   [As found: decimal(158/159) hex(9E/9F)]
                Bframes[index+1+6]=nalsize-1-6
                b_chunksize=b_chunksize+nalsize

            elif data[index+1] & 0b1111100 == 0b0011000:                                        #P frame with slice type: 5, golumb(00110)   [As found: decimal(156/155) hex(9A/9B)]
                Pframes[index+1+6]=nalsize-1-6
                p_chunksize=p_chunksize+nalsize
                #print(data[index+1],'p detected',data[index+2])



            elif data[index+1] & 0b1110000 == 0b0110000:                                        #I frame with 2 slice type golumb(011)
                Iframes[index+1+6]=nalsize-1-6 
                i_chunksize=i_chunksize+nalsize
            
            elif data[index+1] & 0b1110000 == 0b0100000:                                        #B frame with slice type: 1, golumb(010)
                Bframes[index+1+6]=nalsize-1-6
                b_chunksize=b_chunksize+nalsize

            elif data[index+1] & 0b1000000 == 0b1000000:                                        #P frame with 0 slice type golumb(1)
                Pframes[index+1+6]=nalsize-1-6
                p_chunksize=p_chunksize+nalsize
                #print(data[index+1],'p detected',data[index+2])

            else: print("something wrong with frame type slice detection")
                
        index=index+nalsize
    #print(len(Pframes),'Pframesinchunk')


    return(Iframes,Pframes,Bframes,i_chunksize,p_chunksize,b_chunksize,data)

############################################################################# END parsing ######################################################



def crypt(Iframes,Pframes,Bframes,data,stream):


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

    if scheme== 'full':
        newdict=dict(Iframes)
        newdict.update(Pframes)
        newdict.update(Bframes)
        encframes = dict(sorted(newdict.items()))

    crypt_time=0
    for a in reversed(encframes):
        

        data_to_encrypt = data[a:a+encframes[a]]
        #print(len(data_to_encrypt))
        #print(data[a-9:a-5])
        #print(data_to_encrypt)
        
        with open('temp.txt', 'wb') as f:
            f.write(data_to_encrypt)
            f.close()

        cryptstart_time = time.perf_counter_ns()
        enc_output, enc_error = enc('pub_key', 'temp.txt', 'attr1')
        cryptend_time = time.perf_counter_ns()
        crypt_time=crypt_time+(cryptend_time-cryptstart_time)
        
        #print('Enc Output:', enc_output)
        #print('Enc Error:', enc_error)


        with open('temp.txt.cpabe', 'rb') as f:
            encrypted_data= f.read()
            f.close()
            #print(len(encrypted_data))

        # execution_time = timeit.timeit(stmt=encryption_code, number=1000)
        # print(execution_time)

        # PUT ENCRYPTED DATA
        data[a:a+encframes[a]] = encrypted_data

        #ACCOMODATE FOR CHANGING FRAME SIZE DUE TO CPABE
        oldframesize=int.from_bytes(data[a-11:a-7],'big')
        data[a-11:a-7]= (len(encrypted_data)+7).to_bytes(4,byteorder='big')   # +7 because we skip 1 byte for slice type and 6 bytes for header
        newframesize=int.from_bytes(data[a-11:a-7],'big')
        # print(data[a-9:a-5])
        # print(int.from_bytes(data[a-9:a-5],'big'))

        with open('frame-size-change-'+str(stream)+'-'+scheme+'.csv', 'a') as f:
            f.write('{}\n'.format(
                newframesize- oldframesize
            ))
            f.close()
    #crypt_time=crypt_time/1000
    #print("chunk crypt time:",crypt_time)


    output_filename=input_filename.replace("original-dash/chunk", "enc-dash/enc_"+scheme+"_chunk")

    # Write the modified data back to a new file
    with open(output_filename, 'wb') as f:
        f.write(data)
        f.close()

    return(crypt_time)

#######################################################  Execution ###############################################

for stream in range(0,5):
    no_iframes=0
    no_pframes=0
    no_bframes=0
    psize=0
    isize=0
    bsize=0
    total_crypt_time=0
    for i in range(1,num_chunks):
        #print("chunk-stream0-"+str(i).zfill(5)+".m4s")
        input_filename="original-dash/chunk-stream"+str(stream)+"-"+str(i).zfill(5)+".m4s"

        Iframes,Pframes,Bframes,IIsize,PPsize,BBsize,data=parse(input_filename)
        no_iframes=no_iframes+len(Iframes)
        no_pframes=no_pframes+len(Pframes)
        no_bframes=no_bframes+len(Bframes)
        isize=isize+IIsize
        psize=psize+PPsize
        bsize=bsize+BBsize

        chunktime=crypt(Iframes,Pframes,Bframes,data,stream)

        total_crypt_time+=chunktime

    # print("\n\nTotal I frames in "+stream+":",no_iframes)
    # print("total I frame size in "+stream+"=",isize)
    # print("avg I frame size in "+stream+"=",isize/no_iframes)

    # print("\nTotal P frames in "+stream+":",no_pframes)
    # print("total P frame size in "+stream+"=",psize)
    # print("avg P frame size in "+stream+"=",psize/no_pframes)

    # print("\nTotal B frames in "+stream+":",no_bframes)
    # print("total B frame size in "+stream+"=",bsize)
    # print("avg B frame size in "+stream+"=",bsize/no_bframes)

    # total_frames = no_iframes + no_pframes + no_bframes

    # # Calculate average sizes
    # avg_isize = isize / no_iframes
    # avg_psize = psize / no_pframes
    # avg_bsize = bsize / no_bframes

    # # Calculate percentages
    # percent_iframes = (no_iframes / total_frames) * 100
    # percent_pframes = (no_pframes / total_frames) * 100
    # percent_bframes = (no_bframes / total_frames) * 100

    # # Prepare data to write to CSV
    # data = [
    #     ["Frame Type", "Total Frames", "Total Size", "Average Size", "Percentage"],
    #     ["I", no_iframes, isize, avg_isize, percent_iframes],
    #     ["P", no_pframes, psize, avg_psize, percent_pframes],
    #     ["B", no_bframes, bsize, avg_bsize, percent_bframes]
    # ]

    # # File path for the output CSV
    # #frameinfo = "frame_infoenc_"+scheme+".csv"

    # # Write data to CSV
    # with open('frame_info_'+stream+'.csv', mode='w', newline='') as file:
    #     writer = csv.writer(file)
    #     writer.writerows(data)
    #     file.close()



    # print("\n\n#########################\ntotal crypt time for all chunks:",total_crypt_time/1000000000)


    with open('crypt-time_'+str(stream)+'-'+scheme+'.csv', 'a') as f:
        f.write('{}\n'.format(
            total_crypt_time/1000000000
        ))
        f.close()
