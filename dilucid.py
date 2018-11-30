#! /usr/bin/python3

# This script is run on the dilucid root folder.  It enumerates all
# the folders within that folder (not recursively), and then calls
# dilucid-one-network.py on each of the subfolders.

import sys
import os
import tempfile
import shutil
import runpy
import subprocess
import pwd
import time
import pathlib

def does_match_extension(file_name, target_extension) :
    # target_extension should include the dot
    extension = os.path.splitext(file_name)[1]
    return (extension == target_extension)

def replace_extension(file_name, new_extension) :
    # new_extension should include the dot
    base_name = os.path.splitext(file_name)[0]
    return base_name + new_extension

def is_empty(list) :
    return len(list)==0

def common_prefix_path(path1_as_string, path2_as_string) :
    # Re-implement os.path.commonpath(), b/c Python 3.4 doesn't have it.
    path1_as_tuple = pathlib.Path(path1_as_string).parts
    path2_as_tuple = pathlib.Path(path2_as_string).parts
    n1 = len(path1_as_tuple)
    n2 = len(path2_as_tuple)
    max_n = min(n1, n2)
    n = max_n  # fallback number of common elements if all elements turn out to be equal
    for i in range(max_n) :
        if path1_as_tuple[i] != path2_as_tuple[i] :
            n = i
            break
    result_as_tuple = path1_as_tuple[:n]
    result_as_string = os.path.join(*result_as_tuple)
    return result_as_string

def process_files_in_one_folder(dilucid_code_folder_path, mount_folder_path, source_folder_path, names_of_source_files, output_folder_path, network_folder_path, n_submitted) :
    # Scan the source files, spawn a job for any without a .h5 file, 
    # or that are newer than the .h5 file.
    print("In subfolder %s, found %d files" % (source_folder_path, len(names_of_source_files)))
    has_been_run_on_one_file_in_this_folder = False
    for source_file_name in names_of_source_files:
        if does_match_extension(source_file_name, ".avi") :
            source_file_path = os.path.join(source_folder_path, source_file_name)
            lock_file_path = os.path.join(output_folder_path, source_file_name + ".lock")
            target_file_path = os.path.join(output_folder_path, replace_extension(source_file_name, ".h5"))
            if os.path.exists(target_file_path) :
                if os.path.isdir(target_file_path) :
                    # An object exists at the target path, but (oddly) it's a folder
                    print("An object exists at target location %s, but it's a folder.  Not submitting a job." % target_file_path)
                    do_it = False
                else :
                    if os.path.isfile(target_file_path) :
                        # run the script only if the source is more recent than the target
                        # and also if the the source has not been modified in the waiting period
                        # This last is to prevent files that are currently being written from being analyzed.
                        waiting_period = 300  # seconds
                        current_time = time.time()
                        source_modification_time = os.path.getmtime(source_file_path)
                        target_modification_time = os.path.getmtime(target_file_path) 
                        print("current time: %s" % current_time)
                        print("source mod time: %s" % source_modification_time)
                        print("target mod time: %s" % target_modification_time)                      
                        do_it = ( ( source_modification_time >= target_modification_time ) and 
                                  ( current_time > source_modification_time + waiting_period ) )
                    else :
                        # The file exists, but is neither a file or a folder.  WTF?
                        print("An object exists at target location %s, but it's neither a file nor a folder.  Not submitting a job." 
                              % target_file_path)
                        do_it = False
            else :
                # target file does not exist
                do_it = True

            do_it_for_reals = do_it and not os.path.exists(lock_file_path)
            if do_it_for_reals :    
                if not has_been_run_on_one_file_in_this_folder :
                    os.makedirs(output_folder_path, exist_ok=True)
                    has_been_run_on_one_file = True            
                    #subprocess.call('/usr/bin/touch "%s"' % lock_file_path, shell=True)
                    pathlib.Path(lock_file_path).touch()
                    stdout_file_path = os.path.join(output_folder_path, replace_extension(source_file_name, '-stdout.txt'))
                    stderr_file_path = os.path.join(output_folder_path, replace_extension(source_file_name, '-stderr.txt'))
                    delectable_path = os.path.join(dilucid_code_folder_path, 'delectable') 
                    singularity_image_path = os.path.join(delectable_path, 'dlc.simg')
                    print("stdout_file_path: %s" % stdout_file_path)
                    print("stderr_file_path: %s" % stderr_file_path)
                    print("mount_folder_path: %s" % mount_folder_path)
                    print("source_file_path: %s" % source_file_path)
                    print("lock_file_path: %s"   % lock_file_path)
                    print("target_file_path: %s" % target_file_path)
                    #command_line = ( ( 'bsub -o "%s" -e "%s" -q gpu_any -n2 -gpu "num=1" singularity exec ' +
                    #                   '-B "%s" --nv delectable/dlc.simg python3 dilucid-one-network-one-video.py "%s" "%s" "%s" "%s"' )
                    #                 % (stdout_file_path, stderr_file_path, mount_folder_path, source_file_path, network_folder_path, lock_file_path, target_file_path) )
                    job_id = n_submitted   # will start from zero
                    command_line_as_list = [ 'bsub', 
                                             '-o', stdout_file_path, 
                                             '-e', stderr_file_path, 
                                             '-q', 'gpu_any',
                                             '-n2', 
                                             '-gpu', 'num=1', 
                                             'singularity', 'exec',
                                             '-B', mount_folder_path,
                                             '--nv', singularity_image_path, 
                                             '/usr/bin/python3', 
                                             'dilucid-one-network-one-video.py',
                                             source_file_path, 
                                             network_folder_path, 
                                             lock_file_path, 
                                             target_file_path,
                                             str(n_submitted) ]
                    print('About to subprocess.call(): %s' % repr(command_line_as_list))
                    print("PATH: %s" % os.environ['PATH'])
                    print("PWD: %s" % os.environ['PWD'])
                    #return_code = subprocess.call(command_line, shell=True)
                    return_code = subprocess.call(command_line_as_list)
                    if return_code == 0 :
                        n_submitted = n_submitted + 1
                    else :
                        print('bsub call failed!')
                        try :
                            if os.path.exists(lock_file_path) :
                                os.remove(lock_file_path)
                        except Exception as e :
                            print('...and unable to delete lock file %s for some reason' % lock_file_path)                            

    return n_submitted
# end of function


def process_single_network_folder(dilucid_code_folder_path, mount_folder_path, input_folder_path, output_folder_path, network_folder_path_maybe, n_submitted) :
    # print something to show progress
    if is_empty(network_folder_path_maybe) :
        # This means that we're in the root of the single-network
        # folder, so we print a message to say this
        print("Processing a single-network folder: %s" % input_folder_path)
    else :
        print("Processing subfolder: %s" % input_folder_path)

    # get a list of all files and dirs in the source, dest dirs
    try:
        input_folder_contents = os.listdir(input_folder_path)
    except FileNotFoundError :
        # if we can't list the dir, warn but continue
        print("Warning: Folder %s doesn't seem to exist" % source_folder_path)   
        return n_submitted
    except PermissionError :
        # if we can't list the dir, warn but continue
        print("Warning: can't list contents of folder %s due to permissions error" % source_folder_path)
        return n_submitted
    
    names_of_subfolders = [item 
                           for item 
                           in input_folder_contents 
                           if os.path.isdir(os.path.join(input_folder_path, item))]
    names_of_files = [item 
                      for item 
                      in input_folder_contents 
                      if os.path.isfile(os.path.join(input_folder_path, item))]

    if is_empty(network_folder_path_maybe) :
        # This means that we're in the root of the single-network
        # folder, so we look for a folder called "network", which
        # should contain the trained network to use.
        if "network" in names_of_subfolders :
            network_folder_path = os.path.join(input_folder_path, "network")
            network_folder_path_maybe = [ network_folder_path ]
            names_of_subfolders = [ item for item in names_of_subfolders if item!="network" ]
        else :
            print("Unable to find network folder within %s" % input_folder_path)
            return n_submitted
    else:
        # The maybe contains a value, so get it out This means that
        # we're within a single-network folder, but not in the root of
        # it.  Thus we already know the path to the trained network.
        network_folder_path = network_folder_path_maybe[0]

    # At this point, we know the network_folder_path, and
    # names_of_subfolders doesn't contain it (which is good)

    # Process the files in this folder
    n_submitted = process_files_in_one_folder(dilucid_code_folder_path, 
                                              mount_folder_path, 
                                              input_folder_path, 
                                              names_of_files, 
                                              output_folder_path, 
                                              network_folder_path, 
                                              n_submitted)
        
    # For each folder in names_of_subfolders, recurse
    for subfolder_name in names_of_subfolders:
        n_submitted = process_single_network_folder(dilucid_code_folder_path, 
                                                    mount_folder_path, 
                                                    os.path.join(input_folder_path, subfolder_name),
                                                    os.path.join(output_folder_path, subfolder_name),
                                                    network_folder_path_maybe,
                                                    n_submitted)
                    
    # return the updated count of copied files
    return n_submitted
# end of function   


def process_dilucid_root_folder(root_folder_path, root_output_folder_path):
    print("Processing the dilucid root folder: %s" % root_folder_path)
    
    path_to_this_script = os.path.realpath(__file__)
    dilucid_code_folder_path = os.path.dirname(path_to_this_script)

    # Get the path to mount explicitly in call to bsub.
    # This heuristic works for the Svoboda Lab and Dudman Lab installs, but
    # not clear how well it will generalize in the future...
    # Using commonprefix instead of common path b/c this runs on login one, which is running SL 7,
    # which runs Python 3.4, which doesn't yet support commonpath()
    mount_folder_path = common_prefix_path(root_folder_path, root_output_folder_path)
    print("mount_folder_path: %s" % mount_folder_path)

    n_submitted = 0
    try :
        root_folder_contents = os.listdir(root_folder_path)
    except FileNotFoundError :
        # if we can't list the dir, error
        print("Warning: Root folder %s doesn't seem to exist" % root_folder_path)   
        return n_submitted
    except PermissionError :
        # if we can't list the dir, error
        print("Warning: can't list contents of root folder %s due to permissions error" % root_folder_path)
        return n_submitted
    
    names_of_folders_in_root_folder = [item 
                                       for item 
                                       in root_folder_contents 
                                       if os.path.isdir(os.path.join(root_folder_path, item))]

    # for each dir in names_of_folders_in_root_folder, run process_dilucid_network_folder
    for network_folder_name in names_of_folders_in_root_folder:
        n_submitted_this = process_single_network_folder(dilucid_code_folder_path, 
                                                         mount_folder_path, 
                                                         os.path.join(root_folder_path, network_folder_name),
                                                         os.path.join(root_output_folder_path, network_folder_name),
                                                         [],
                                                         0)
        n_submitted = n_submitted + n_submitted_this

    return n_submitted
# end of process_dilucid_root_folder


#
# main
#
if __name__ == '__main__':
    input_root_folder_path = os.path.abspath(sys.argv[1])
    output_root_folder_path = os.path.abspath(sys.argv[2])
    n_submitted = process_dilucid_root_folder(input_root_folder_path, output_root_folder_path)
    print("%d jobs submitted total" % n_submitted)
