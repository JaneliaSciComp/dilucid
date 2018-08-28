#! /usr/bin/python3

import sys
import os
import tempfile
import shutil
import runpy
import subprocess
import pwd
import time

def does_match_extension(file_name, target_extension) :
    # target_extension should include the dot
    extension = os.path.splitext(file_name)[1]
    return (extension == target_extension)


def replace_extension(file_name, new_extension) :
    # new_extension should include the dot
    base_name = os.path.splitext(file_name)[0]
    return base_name + new_extension


# this is the function we use to recurse
def evaluate_on_folder(source_folder_path, output_folder_path, n_submitted):

    # print to show progress
    print("%s:" % source_folder_path)

    # get a list of all files and dirs in the source, dest dirs
    try:
        source_entries = os.listdir(source_folder_path)
    except FileNotFoundError :
        # if we can't list the dir, warn but continue
        print("Warning: Folder %s doesn't seem to exist" % source_folder_path)   
        return n_submitted
    except PermissionError :
        # if we can't list the dir, warn but continue
        print("Warning: can't list contents of folder %s due to permissions error" % source_folder_path)
        return n_submitted
    
    # separate source file, dir names
    names_of_files_in_source_folder = []
    names_of_folders_in_source_folder = []
    for source_entry in source_entries :
        entry_path = os.path.join(source_folder_path, source_entry)
        if os.path.isdir(entry_path) :
            names_of_folders_in_source_folder.append(source_entry)
        elif os.path.isfile(entry_path) :
            names_of_files_in_source_folder.append(source_entry)
            
    # scan the source files, spawn a job for any without a .h5 file, 
    # or that are newer than the .h5 file
    has_been_run_on_one_file_in_this_folder = False
    for source_file_name in names_of_files_in_source_folder:
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
                        print("An object exists at target location %s, but it's neigher a file nor a folder.  Not submitting a job." 
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
                    subprocess.call('/usr/bin/touch "%s"' % lock_file_path, shell=True)
                    stdout_file_path = os.path.join(output_folder_path, replace_extension(source_file_name, '-stdout.txt'))
                    stderr_file_path = os.path.join(output_folder_path, replace_extension(source_file_name, '-stderr.txt'))
                    print("stdout_file_path: %s" % stdout_file_path)
                    print("stderr_file_path: %s" % stderr_file_path)
                    print("source_file_path: %s" % source_file_path)
                    print("lock_file_path: %s"   % lock_file_path)
                    print("target_file_path: %s" % target_file_path)
                    command_line = ( ( 'bsub -o "%s" -e "%s" -q gpu_any -n1 -gpu "num=1" singularity exec ' +
                                       '-B /scratch,/nrs --nv dlc.simg python3 mouse-side-jaw-nose-tongue-one.py "%s" "%s" "%s"' )
                                     % (stdout_file_path, stderr_file_path, source_file_path, lock_file_path, target_file_path) )
                    print('About to subprocess.call(): %s' % command_line)
                    print("PATH: %s" % os.environ['PATH'])
                    print("PWD: %s" % os.environ['PWD'])
                    subprocess.call(command_line, shell=True)
                    n_submitted = n_submitted + 1
        
    # for each dir in names_of_folders_in_source_folder, recurse
    for source_subfolder_name in names_of_folders_in_source_folder:
        n_submitted = evaluate_on_folder(os.path.join(source_folder_path, source_subfolder_name),
                                         os.path.join(output_folder_path, source_subfolder_name),
                                         n_submitted)
                    
    # return the updated count of copied files
    return n_submitted

# end of evaluate_on_folder




# main
source_root_folder_path = os.path.abspath(sys.argv[1])
output_root_folder_path = os.path.abspath(sys.argv[2])
n_submitted = evaluate_on_folder(source_root_folder_path, output_root_folder_path, 0)

# print the number of jobs submitted
print("%d jobs submitted" % n_submitted)
