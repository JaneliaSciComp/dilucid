# coding: utf-8

############################
# This configuration file sets various parameters for running a trained model,
# that performed well on train/test set on videos
############################

# Filename and path to behavioral video (for labeling)
videofolder = '../videos/'
cropping = False
videotype='.avi' #type of videos to analyze 
#Note: under the hood there is moviepy, which can handle many types of videos:
#https://zulko.github.io/moviepy/_modules/moviepy/video/io/VideoFileClip.html

# If you have stacks of tiffs (instead of videos) you can use "AnalyzeABunchofPictures.py"

# ROI dimensions / bounding box (only used if cropping == True)
# x1,y1 indicates the top left corner and
# x2,y2 is the lower right corner of the croped region.

x1 = 0
x2 = 640
y1 = 277
y2 = 624

# Analysis Network parameters:

scorer = 'MNE'
Task = 'licking-side2'
date = 'Jul11'
trainingsFraction = 0.95  # Fraction of labeled images used for training
resnet = 50
snapshotindex = -1
shuffle = 1

storedata_as_csv=False #if true then the time series of poses will (also) be saved as csv. 

# For plotting:
trainingsiterations = 400000  # type the number listed in .pickle file
pcutoff = 0.9  # likelihood cutoff for body part in image
# delete individual (labeled) frames after making video?
deleteindividualframes = False
alphavalue=.6 # "strength/transparency level of makers" in individual frames (Vary from 0 to 1. / not working in "MakingLabeledVideo_fast.py")
dotsize = 7
#colormap='' #other colorschemes: 'cool' and see https://matplotlib.org/examples/color/colormaps_reference.html
colormap = 'Pastel1' #set color map, i.e. viridis, cool, hsv

