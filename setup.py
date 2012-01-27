# This is an example setup.py file
# run it from the windows command line like so:
# > C:\Python2.4\python.exe setup.py py2exe
 
from distutils.core import setup
import py2exe, os
 
opts = { 
 "py2exe": { 
   # if you import .py files from subfolders of your project, then those are
   # submodules.  You'll want to declare those in the "includes"
   'includes':[],
 } 
} 
 
def filesinpath(path,ext):
  return [os.path.abspath(os.path.join(path,file)) for file in os.listdir(path) if file.endswith(ext)]
 
setup(
 
  #this is the file that is run when you start the game from the command line.  
  console=['typing.py'],
 
  #options as defined above
  options=opts,

 
  #data files - these are the non-python files, like images and sounds
  data_files = [
    (os.path.join('data','gunstar'), filesinpath(os.path.join('data','gunstar'),".png")),
    (os.path.join('data','assorted'), filesinpath(os.path.join('data','assorted'),".gif")),
    (os.path.join('data','copter'), filesinpath(os.path.join('data','copter'),".gif")),
    (os.path.join('data','soldier'), filesinpath(os.path.join('data','soldier'),".gif")),
    (os.path.join('data','ghost'), filesinpath(os.path.join('data','ghost'),".gif"))
  ],
 
  #this will pack up a zipfile instead of having a glut of files sitting
  #in a folder.
  zipfile="lib/shared.zip"
)