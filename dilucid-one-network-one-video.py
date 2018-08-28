#! /usr/bin/python3

import sys
import os
import tempfile
import shutil
import runpy
import subprocess
import pwd

def get_username():
    return pwd.getpwuid( os.getuid() )[ 0 ]

def evaluate_on_one_video(source_input_file_name, lock_file_name, destination_output_file_name):
    this_script_path = os.path.realpath(__file__)
    this_script_folder_path = os.path.dirname(this_script_path)
    source_dlc_root_path = os.path.normpath(os.path.join(this_script_folder_path, "dlc-modded"))

    initial_folder_path = os.getcwd()
    #temp_folder_path = tempfile.mkdtemp()
    print("username is %s" % get_username()) 
    temp_folder_path = os.path.join("/scratch", get_username())
    print("temp_folder_path is %s" % temp_folder_path) 

    did_create_dlc_container_path = False
    try:
        dlc_container_path = tempfile.mkdtemp(prefix=temp_folder_path+"/")
        did_create_dlc_container_path = True
        print("dlc_container_path is %s" % dlc_container_path) 

        dlc_root_path = os.path.join(dlc_container_path, "dlc-modded") ;
        print("dlc_root_path is %s" % dlc_root_path) 

        shutil.copytree(source_dlc_root_path, dlc_root_path)

        #source_input_file_name = sys.argv[1]
        source_input_file_path = os.path.abspath(source_input_file_name)

        source_input_file_base_name = os.path.basename(source_input_file_path)
        (input_file_stem_name, input_file_extension) = os.path.splitext(source_input_file_base_name)

        input_file_path = os.path.join(dlc_root_path,
                                       "videos",
                                       "the-video" + input_file_extension)

        # Copy the input video to the DLC "videos" folder, should be on scratch drive
        shutil.copyfile(source_input_file_path, input_file_path)

        # Synthesize absolute path to the video-analysis script
        analysis_folder_path = os.path.join(dlc_root_path, "Analysis-tools")
        analyze_video_script_path = os.path.join(analysis_folder_path, "AnalyzeVideos.py")
        print("analysis_folder_path: %s\n" % analysis_folder_path)
        print("analyze_video_script_path: %s\n" % analyze_video_script_path)

        #  
        os.chdir(analysis_folder_path)
        #exec(open(analyze_video_script_path).read())
        runpy.run_path(analyze_video_script_path)
        #subprocess.call("bsub -q gpu_any -n1 -gpu "num=1" cd %s ; "  )
        os.chdir(initial_folder_path)

        output_file_extension = ".h5"
        source_output_file_path = os.path.join(dlc_root_path,
                                               "videos",
                                               "the-video" + "DeepCut_resnet50_licking-side2Jul11shuffle1_400000" + output_file_extension)
        destination_output_file_path = os.path.abspath(destination_output_file_name)

        # Check the umask
        print("umask -S:")
        os.system("umask -S")
        print("")

        # The umask is u=rwx, g=rx, u=rx, for some reason...
        # (The bsub?  The singularity container?)  Dunno...
        # Anyway, we change it so that the final .h5 file is group-writable,
        # but others have no access
        os.umask(0o007)

        print("About to copy result to final location...")
        print("source_output_file_path: %s" % source_output_file_path)
        print("destination_output_file_path: %s" % destination_output_file_path)
        shutil.copyfile(source_output_file_path, destination_output_file_path)

        # Remove the temporary folder we created
        shutil.rmtree(dlc_container_path)

        # Remove the input movie video, if we have adequate permissions
        try:
            os.remove(source_input_file_path)
        except Exception as e :
            print('Tried to delete %s, but was unable to do so for some reason' % source_input_file_path)

        # Remove the lock file
        lock_file_path = os.path.abspath(lock_file_name)
        if os.path.exists(lock_file_path) :
            os.remove(lock_file_path)

    except Exception as e:
        # Remove the temporary folder
        if did_create_dlc_container_path :
            shutil.rmtree(dlc_container_path)
        # Remove the lock file
        lock_file_path = os.path.join(source_input_file_name + ".lock")
        if os.path.exists(lock_file_path) :
            os.remove(lock_file_path)
        # cd back to the initial folder
        os.chdir(initial_folder_path)
        # Re-throw the exception
        raise e



# main
video_file_path = os.path.abspath(sys.argv[1])
lock_file_path = os.path.abspath(sys.argv[2])
output_file_path = os.path.abspath(sys.argv[3])
evaluate_on_one_video(video_file_path, lock_file_path, output_file_path)

