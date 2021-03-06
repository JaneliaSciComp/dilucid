Dilucid

This project is based on the DeepLabCut project:

https://github.com/AlexEMG/DeepLabCut

All the code under the dlc folder is the original DeepLabCut code, and
therefore carries its own copyright and license (GPLv3).

This project implements a cron job that runs on
login1.int.janelia.org.  It monitors a folder (usually named something
like /something/something/dilucid-drop) for .avi files, and when it
finds them it runs DeepLabCut on them, placing the output .h5 file in
a parallel location, typically named something like

    /something/something/dilucid-drop-output .

Each folder under dilucid-drop is a "single-network folder".  The
network used to analyze the videos placed in that folder is found in a
subfolder named "network" under the single-network folder.

For instance, Mike Economo trained a network on views of
a mouse's head from the side.  The model was trained on July 11, on
641 frames, and labels the jaw, nose, and tongue of the mouse.  With
this model and a few videos in place, the folder structure looks like:

dilucid-drop
└── side
    ├── network
    │   ├── licking-side2Jul11-trainset95shuffle1
    │   └── myconfig_analysis.py
    ├── v_cam_0_v057.avi
    └── inner-folder
        ├── bar.avi
        └── foo.avi

licking-side2Jul11-trainset95shuffle1 is a folder taken from the
pose-tensorflow/models folder of a DeepLabCut folder hierarchy used
for training the model.  myconfig_analysis.py is the
myconfig_analysis.py file copied from the root of the DeepLabCut
folder hierarchy used for training (and testing) the model.  The .avi
files are files to be analyzed.

Before building Dilucid, you should figure out what user the cronjob
will run as, and then do the build while logged in as that user.

To build, you first need to build the Singularity image within which
DeepLabCut runs.  To do this, you need a linux box with root
privleges, and with Singularity installed (as of this writing, I last
used an Ubuntu 18.04.1 box).  Do this to build the image:

    sudo singularity build dlc.simg dlc.def

(Make sure you delete any old image named dlc.simg, or else
singularity will complain.)  After this completes, you may want to
chown/chmod dlc.simg to make it owned by you, and have normal file
permissions.

Next, create a file name dilucid-configuration that points to the
folders you want to use for input and output.  See
dilucid-configuration-svoboda and dilucid-configuration-dudman for
examples.

Next, if you have no jobs in your current crontab that you want to
keep, do

    ./turn-on

to add the dilucid-launching line to the crontab file.  (You can
delete this line with the ./turn-off bash script.)

After this, the contents of the input folder should automatically get
processed every 5 minutes.

ALT
2018-10-29

