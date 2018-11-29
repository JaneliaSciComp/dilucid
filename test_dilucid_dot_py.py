#! /usr/bin/python3

import os
import shutil

if os.path.exists('test-folder'):    
    shutil.rmtree('test-folder')
shutil.copytree('virgin-test-folder', 'test-folder')

if os.path.exists('test-folder-output'):    
    shutil.rmtree('test-folder-output')
os.mkdir('test-folder-output')

os.system('python3 dilucid.py test-folder test-folder-output')
