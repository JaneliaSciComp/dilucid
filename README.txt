Dilucid

This project is a cron job that runs on login1.int.janelia.org.  It
monitors a folder (currently
/nrs/svoboda/dlc-drop-mouse-side-jaw-nose-tongue) for .avi files, and
when it finds them it runs DeepLabCut on them, placing the output .h5
file in a parallel location in 

    /nrs/svoboda/dlc-drop-mouse-side-jaw-nose-tongue-output .

DeepLabCut currently uses a model trained by Mike Economo on views of
a mouse's head from the side.  The model was trained on July 11, on
641 frames, and labels the jaw, nose, and tongue of the mouse.

Before building, you should figure out what user the cronjob will run
as, and then do the build while logged in as that user.

To build, you first need to build the Singularity image within which
DeepLabCut runs.  To do this, you need a linux box with root
privleges, and with Singularity installed (as of this writing, I last
used an Ubuntu 18.04.1 box).  Do this to build the image:

    sudo singularity build dlc.simg dlc.def

(Make sure you delete any old image named dlc.simg, or else
singularity will complain.)  After this completes, you may want to
chown/chmod dlc.simg to make it owned by you, and have normal file
permissions.

Next, run the provided build script:

    ./build

Next, modify the mouse-side-jaw-nose-tongue script to point to the
folders you want to use for input and output.

Next, modify crontab.crontab to point to your input folder and the
absolute bath of the mouse-side-jaw-nose-tongue script.

Next, if you have no jobs in your current crontab that you want to
keep, do

    crontab crontab.crontab

to install the crontab file.  Otherwise, you'll want to append the
contents of crontab.crontab to your existing crontab, with a command
like this:

    crontab -l | cat - crontab.crontab | crontab

After this, the contents of the input folder should automatically get
processed every 5 minutes.

ALT
2018-08-28
