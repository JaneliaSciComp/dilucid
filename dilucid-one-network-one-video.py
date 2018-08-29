#! /usr/bin/python3

import sys
import os
import tempfile
import shutil
import runpy
import subprocess
import pwd
import pathlib

def get_username():
    return pwd.getpwuid( os.getuid() )[ 0 ]

def is_empty(list) :
    return len(list)==0

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
        if is_empty(contents) :
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
                          output_file_path):

    # Determine the absolute path to the "reference" DLC folder
    this_script_path = os.path.realpath(__file__)
    this_script_folder_path = os.path.dirname(this_script_path)
    template_dlc_root_folder_path = os.path.normpath(os.path.join(this_script_folder_path, "dlc-modded"))

    # Determine the absolute path to the parent temp folder that we can write to (e.g. /scratch/svobodalab)
    initial_working_folder_path = os.getcwd()
    print("username is %s" % get_username()) 
    scratch_folder_path = os.path.join("/scratch", get_username())
    print("scratch_folder_path is %s" % scratch_folder_path) 

    scratch_dlc_container_path_maybe = []  # want to keep track of this so we know whether or not to delete it
    try:
        # Make a temporary folder to hold the temporary DLC folder
        # (want to have them for different instances running on same
        # node without collisions)
        scratch_dlc_container_path = tempfile.mkdtemp(prefix=scratch_folder_path+"/")
        scratch_dlc_container_path_maybe = [scratch_dlc_container_path]
        print("scratch_dlc_container_path is %s" % scratch_dlc_container_path) 

        # Determine the absolute path to the temporary DLC folder 
        scratch_dlc_root_folder_path = os.path.join(scratch_dlc_container_path, "dlc-modded") ;
        print("scratch_dlc_root_folder_path is %s" % scratch_dlc_root_folder_path) 

        # Copy the reference DLC folder to the temporary one
        shutil.copytree(template_dlc_root_folder_path, scratch_dlc_root_folder_path)

        # Copy the configuration file into the scratch DLC folder
        configuration_file_name = "myconfig_analysis.py" ;
        configuration_file_path = os.path.join(network_folder_path, configuration_file_name)
        scratch_configuration_file_path = os.path.join(scratch_dlc_root_folder_path, configuration_file_name)
        shutil.copyfile(configuration_file_path, scratch_configuration_file_path)
        
        # There should be exactly one folder within the network folder.
        # That's the "model" folder, which contains two folders: "test" and "train".
        # get a list of all files and dirs in the source, dest dirs
        try:
            network_folder_contents = os.listdir(network_folder_path)
        except FileNotFoundError :
            # if we can't list the folder, give up
            raise RuntimeError("Network folder %s doesn't seem to exist" % network_folder_path)   
        except PermissionError :
            # if we can't list the dir, warn but continue
            raise RuntimeError("Can't list contents of network folder %s due to permissions error" % network_folder_path)
        names_of_folders = [item
                            for item
                            in network_folder_contents
                            if os.path.isdir(os.path.join(network_folder_path, item))]
        if is_empty(names_of_folders) :
            raise RuntimeError("Network folder %s has no subfolders" % network_folder_path)
        model_folder_name = names_of_folders[0] ;
        model_folder_path = os.path.join(network_folder_path, model_folder_name)
        
        # Copy the model folder to the scratch DLC folder, in the right place
        scratch_model_folder_path = os.path.join(scratch_dlc_root_folder_path, "pose-tensorflow", "models", model_folder_name)
        shutil.copytree(model_folder_path, scratch_model_folder_path)

        # Copy the input video to the "videos" folder within the scratch DLC folder
        input_file_base_name = os.path.basename(input_file_path)
        (input_file_stem_name, input_file_extension) = os.path.splitext(input_file_base_name)
        scratch_input_file_path = os.path.join(scratch_dlc_root_folder_path,
                                                 "videos",
                                                 "the-video" + input_file_extension)
        shutil.copyfile(input_file_path, scratch_input_file_path)

        # Determine absolute path to the (scratch version of the) video-analysis script
        analysis_folder_path = os.path.join(scratch_dlc_root_folder_path, "Analysis-tools")
        analyze_video_script_path = os.path.join(analysis_folder_path, "AnalyzeVideos.py")
        print("analysis_folder_path: %s\n" % analysis_folder_path)
        print("analyze_video_script_path: %s\n" % analyze_video_script_path)

        # cd into the scratch analysis folder, run the script, cd back
        os.chdir(analysis_folder_path)
        runpy.run_path(analyze_video_script_path)
        os.chdir(initial_working_folder_path)

        # Print the umask
        print("umask -S:")
        os.system("umask -S")
        print("")

        # Set the umask so group members can delete stuff
        # The umask is u=rwx, g=rx, u=rx, for some reason...
        # (The bsub?  The singularity container?)  Dunno...
        # Anyway, we change it so that the final .h5 file is group-writable,
        # but others have no access
        os.umask(0o007)

        # Copy the scratch output file to the final output file location
        output_file_extension = ".h5"
        scratch_output_file_path = os.path.join(scratch_dlc_root_folder_path,
                                                "videos",
                                                "the-video" + 
                                                    "DeepCut_resnet50_licking-side2Jul11shuffle1_400000" + 
                                                    output_file_extension)
        print("About to copy result to final location...")
        print("scratch_output_file_path: %s" % scratch_output_file_path)
        print("output_file_path: %s" % output_file_path)
        shutil.copyfile(scratch_output_file_path, output_file_path)

        # Remove the scratch folder we created to hold the scratch DLC folder
        shutil.rmtree(scratch_dlc_container_path)

        # Remove the lock file
        if os.path.exists(lock_file_path) :
            os.remove(lock_file_path)

        # Remove the input movie video, if we have adequate permissions
        # But just keep on going if we don't
        delete_input_file_and_empty_ancestral_folders(input_file_path, network_folder_path)                                           


    except Exception as e:
        # Try to clean up some before re-throwing

        # Remove the scratch folder
        if not is_empty(scratch_dlc_container_path_maybe) :
            shutil.rmtree(scratch_dlc_container_path_maybe[0])
        # Remove the lock file
        lock_file_path = os.path.join(input_file_name + ".lock")
        if os.path.exists(lock_file_path) :
            os.remove(lock_file_path)
        # cd back to the initial folder
        os.chdir(initial_working_folder_path)
        # Re-throw the exception
        raise e



# main
video_file_path = os.path.abspath(sys.argv[1])
network_folder_path = os.path.abspath(sys.argv[2])
lock_file_path = os.path.abspath(sys.argv[3])
output_file_path = os.path.abspath(sys.argv[4])
evaluate_on_one_video(video_file_path, network_folder_path, lock_file_path, output_file_path)

