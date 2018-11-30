#! /usr/bin/python3

import sys
import os
import tempfile
import shutil
import runpy
import subprocess
import pwd
import pathlib
import delectable.dlct as dlct

def find_output_file(output_folder_path, output_file_extension) :
    names_of_matching_files = find_files_matching_extension(output_folder_path, output_file_extension)
    matching_file_count = len(names_of_matching_files)
    if matching_file_count == 0 :
        raise RuntimeError("Unable to locate output file with extension %s in folder %s.  Maybe it wasn't produced?" 
                           % (output_file_extension, output_folder_path))
    if matching_file_count > 1 :
        raise RuntimeError("More than one file with extension %s in folder %s.  Not sure which one is the right one." 
                           % (output_file_extension, output_folder_path))

    return os.path.join(output_folder_path, names_of_matching_files[0]) 
# end of function

def find_optional_output_file(output_folder_path, output_file_extension) :
    names_of_matching_files = find_files_matching_extension(output_folder_path, output_file_extension)
    matching_file_count = len(names_of_matching_files)
    if matching_file_count == 0 :
        return []
    if matching_file_count > 1 :
        raise RuntimeError("More than one file with extension %s in folder %s.  Not sure which one is the right one." 
                           % (output_file_extension, output_folder_path))

    return [os.path.join(output_folder_path, names_of_matching_files[0])]
# end of function


def delete_input_file_and_empty_ancestral_folders(input_file_path_as_string, network_folder_path_as_string) :
    input_file_path = pathlib.Path(input_file_path_as_string)
    network_folder_path = pathlib.Path(network_folder_path_as_string)

    try :
        os.remove(str(input_file_path))
    except Exception as e :
        print('Tried to delete file %s, but was unable to do so for some reason' % input_file_path)
        return        
    
    single_network_folder_path = network_folder_path.parent ;
    common_path = pathlib.Path(os.path.commonpath([str(single_network_folder_path), str(input_file_path)]))
    if common_path != single_network_folder_path :
        print('Internal error: When checking for empty input folders, the single network path (%s) is not the common path for it and the input file path (%s)' %
              str(single_network_folder_path), 
              str(input_file_path))
        return

    target_folder_path = input_file_path.parent
    is_done = ( target_folder_path == single_network_folder_path )
    while not is_done :
        contents = os.listdir(str(target_folder_path)) 
        if dlct.is_empty(contents) :
            try :
                os.rmdir(str(target_folder_path)) 
            except Exception as e :
                print('Tried to delete folder %s, but was unable to do so for some reason' % str(target_folder_path))
                return    
            target_folder_path = target_folder_path.parent
            is_done = ( target_folder_path == single_network_folder_path )
        else :
            is_done = True 
# end of function


def evaluate_on_one_video(input_file_path, 
                          network_folder_path, 
                          lock_file_path, 
                          output_file_path, 
                          job_index_as_string_or_int):
    try:
        if isinstance(job_index_as_string, str):
            job_index = int(job_index_as_string_or_int)
        else:
            # apparently it's an int
            job_index = job_index_as_string_or_int
        # # Print the umask
        # print("umask -S:")
        # os.system("umask -S")
        # print("")

        # Make sure the input file exists within the container.  This
        # can fail because all the right folders have not been mounted
        # in the call to bsub.
        if not os.path.exists(input_file_path) :
            raise RuntimeError("Input file %s does not exist!  Did you mount all the needed folders with the -B option to bsub?" % input_file_path)

        # Set the umask so group members can delete stuff
        # The umask is u=rwx, g=rx, u=rx, for some reason...
        # (The bsub?  The singularity container?)  Dunno...
        # Anyway, we change it so that the final .h5 file is group-writable,
        # but others have no access
        os.umask(0o007)

        # Run the DLC eval script in a subprocess
        this_script_path = os.path.realpath(__file__)
        this_script_folder_path = os.path.dirname(this_script_path)
        dlc_eval_script_path = os.path.join(this_script_folder_path, 'delectable', 'apply_model.py')
        return_code = subprocess.call(['/usr/bin/python3', dlc_eval_script_path, network_folder_path, input_file_path, output_file_path])
        if return_code != 0 :
            raise RuntimeError('Calling the delectable apply_model.py script failed!')

        # If the job index is right, make a labeled video
        labeled_video_period = 100  # make a labeled video every this many videos
        if job_index % labeled_video_period == 0:
            make_labeled_video_script_path = os.path.join(this_script_folder_path, 'delectable', 'make_labeled_video.py')
            return_code = subprocess.call(['/usr/bin/python3', make_labeled_video_script_path, network_folder_path, input_file_path, output_file_path])
            if return_code != 0 :                
                print('Calling the delectable make_labeled_video.py script failed!')  # Don't error out for this

        # Remove the lock file
        if os.path.exists(lock_file_path) :
            os.remove(lock_file_path)

        # Remove the input movie video, if we have adequate permissions
        # But just keep on going if we don't
        delete_input_file_and_empty_ancestral_folders(input_file_path, network_folder_path)                                           

    except Exception as e:
        # Try to clean up some before re-throwing

        # Remove the lock file
        #print("Exception caught, about to delete lock file at %s" % lock_file_path)
        if os.path.exists(lock_file_path) :
            #print("Lock file exists, about to delete lock file at %s" % lock_file_path) 
            os.remove(lock_file_path)
 
        # Re-throw the exception
        raise e
# end of function


# main
if __name__ == '__main__':
    video_file_path = os.path.abspath(sys.argv[1])
    network_folder_path = os.path.abspath(sys.argv[2])
    lock_file_path = os.path.abspath(sys.argv[3])
    output_file_path = os.path.abspath(sys.argv[4])
    job_index_as_string = sys.argv[5]
    
    print('video_file_path: %s' % video_file_path)
    print('network_folder_path: %s' % network_folder_path)
    print('lock_file_path: %s' % lock_file_path)
    print('output_file_path: %s' % output_file_path)
    print('job_index_as_string: %s' % job_index_as_string)

    evaluate_on_one_video(video_file_path, network_folder_path, lock_file_path, output_file_path, job_index_as_string)
