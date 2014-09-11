# A series of useful python functions, written for Hogarth by Josh Smith in 2014

import datetime
import hashlib
import os
import time
import subprocess as sp
from subprocess import PIPE
import shutil

def check_pid(pid):
    """Check whether the process with the given pid is running. Return True or
    False accordingly"""
    try:
        os.kill(int(pid), 0) #Sends a harmless signal to the proc
    except OSError as e:
        if e.args[0] == 3:
            return False
        else:
            raise
    else:
        return True

def get_md5(from_file, chunk_size=8192):
    """Returns an MD5 hash of from_file, processing the file in chunks of chunk_size"""
    #Read file in 8192 byte chunks
    f=open(from_file, 'rb')
    hash_out = hashlib.md5()
    while True:
        chunk = f.read(chunk_size)
        if chunk == '':
            break
        else:
            hash_out.update(chunk)
    f.close()
    return hash_out.hexdigest()

class FileNotOnSource(Exception):
    pass

def careful_delete(folder, files_to_remove):
    """Check that nothing important is within folder, then remove it.

    :param folder: Full path to candidate for removal.
    :param files_to_remove: Files which should be removed from the folder.
    """

    dir_rm = sp.call(['rmdir', folder], stderr=sp.PIPE)

    #Unless...
    if dir_rm > 0:

        #Hmm. Well, it's probably just empty dirs and .DS_Stores, right?
        delete_it = True

        find_files = sp.Popen(['find', folder, '-type', 'f'], stdout=sp.PIPE).communicate()
        files_present = find_files[0].strip().split('\n')
        #If there are any files in subdirectories of dirname...
        if files_present[0]:
            #...and if any of them aren't files we don't want...
            for filepath in files_present:
                filename = filepath.split('/')[-1]
                if filename[0] not in files_to_remove:
                    #Then don't delete it
                    delete_it = False

        if delete_it:
            sp.call(['rm', '-r', folder])

def moveFile(source_file_path, source_dir, dest, mode='copy', create_dirs=True):
    """Used to move a file within source_dir  to a similar directory on dest; 
    will copy single files across while preserving directory structure. 
    
    moveFile(/source/a/b/thefile.txt, b/thefile.txt, /dest/)
    will attempt to copy thefile.txt to /dest/b/thefile.txt, and create the 
    directory on b if it doesn't exist. 

    file_path: str (path)
        Full path to the file to be moved
    source_dir: str (path)
        The section of the path containing directories to be created on the     
        dest. 
    dest: str (path)
        The destination. Files will be created at dest/source_dir.
    mode: str - default = 'copy'
        'move' - Move the files and delete them from source
        'copy' - copy the files.
    create_dirs: bool
        Create dirs in source_dir which don't exist in dest"""

    def back_one(path):
        return '/'.join(path.split('/')[:-1])

    def create_dirs(source_dir):
        
        dir_array = source_dir.split('/')

        for i in range(1, len(dir_array)):
            #...keep moving one dir back and trying to create it.
            try:
                dir_to_create = '/'.join(dir_array[:len(dir_array)-i])
                os.mkdir(dir_to_create)
                
                #Success! No exception! Make the other folders. 
                for j in range(i+1,len(dir_array)):
                    os.mkdir('/'.join(dir_array[:i]))
                continue

            #If we couldn't make the dir and there's still some to try, keep
            #trying. otherwise, raise an exception.
            except OSError:
                if i == len(dir_array):
                    raise OSError("Could not create file " +\
                                  os.path.join(dest,dir_to_create))
                else:
                    pass
        
    source_file_path = os.path.abspath(source_file_path)
    dest_file_path = os.path.abspath(os.path.join(dest,source_dir))

    if not os.path.exists(source_file_path):
        raise FileNotOnSource(source_file_path)

    if mode == 'copy':
        while True:
            try:
                shutil.copy(source_file_path, dest_file_path)
            #If transfer fails due to unfound path on dest...
            except IOError:
                create_dirs(source_dir)


    if mode == '':
        while True:
            try:
                shutil.copy(source_file_path, dest_file_path)
            #If transfer fails due to unfound path on dest...
            except IOError:
                for i in range(len(source_dir.split('/'))-1):
                    #...keep moving one dir back and trying to create it.
                    try:
                        dir_to_create = back_one(source_dir)
                        os.mkdir(dir_to_create)
                        #If it works, try moving the file again.
                        continue
                    except OSError:
                        pass

def escapeChar(fromStr,char):
    """Append any instance of char in from_str with a backslash"""
    return(fromStr.replace(char,'\\' + char))

def appendIndex(filename, ext, path):
    """Append an index to a path.

    Given a file 'filename' at location 'path' with extension 'ext', 
    this will return the path of filename(n)ext, where n is the lowest integer for 
    which filename(n-1)ext already exitsts.
    
    As an example, given a directory /tmp/adir conatining a.txt and a(1).txt,
    appendIndex('a','.txt','/tmp/adir') will return a(2).txt

    Variables:
    
    filename: STR
        The name of the file
    ext: STR
        The file's extension
    path: STR
        A path to the directory the file resides in. 
    """

    index = 1

    appendedFile = filename + "(" + str(index) + ")" + ext
    appendedPath = os.path.join(path, appendedFile)

    while os.path.exists(appendedPath):

        index += 1
        appendedFile = filename + "(" + str(index) + ")" + ext
        appendedPath = os.path.join(path, appendedFile)

    return appendedPath


def dirBeingWrittenTo(path):
    """Uses lsof to get access tags on all files in path

    Returns true if any file is being written to.

    """
    lsofOut = sp.Popen(["lsof", "+D", path, "-F", "a"],
                                stdout=PIPE, stderr=PIPE)
    lsofStdout = lsofOut.communicate()[0].split()
    
    for accessType in lsofStdout:
        if 'w' in accessType:
            return True
    
    #If nothing is writing to a file, or there are no files in path:
    return False

def immediateSubdirs(theDir):
    """Returns a list of immediate subdirectories of theDir"""

    return [name for name in os.listdir(theDir)
        if os.path.isdir(os.path.join(theDir,name))]


def prepend(pre, post):
    """If 'pre' is defined, append it to post, concatenate and return"""
    if pre != None:
        return pre + post

    else:
        return post

def printAndLog(toPrint, logFiles=[], syslogFiles=[], ts='long', quiet=False):
    """Prints toPrint to stdOut and also to all files in logFiles. 

    If ts is passed, will print the time of the log.

    Variables:
     
    toPrint: STR
        The string to be logged.
    logFiles: LIST of FILES
        A list of files to be logged to. Should be open file objects.
    sysLogFiles: LIST of FILES
        Files in this list will have any \n newline characters replaced with \r
        This should be used for any file being monitored by rsyslog or similar.
    ts: STR - 'long' or 'short - default short
        The type of timestamp to be appended to the file
        See docs for timeStamp
    quiet: BOOL - default False
        Print to stdout if false.
    """

    if ts:
        ts = str(timeStamp(ts))
        toPrint = ts + " " + toPrint

    if not quiet:
        print toPrint
    for f in logFiles:
        f.write(toPrint)
    for f in syslogFiles:
        f.write(toPrint)

def timeStamp(form='long'):
    """Prints the current time in a one of two formats. Useful for logging. 

    ts can take values 'long' or 'short'. Examples:
    
    >>> hogpy.timeStamp('long')
    2014-03-10 15:00:02 :
    
    >>> hogpy.timeStamp('short')
    0310-1500    

    """

    ts = time.time()

    if form == 'short':
        return datetime.datetime.fromtimestamp(ts).strftime('%m%d-%H%M')

    if form == 'long':
        return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d '+\
                                                            '%H:%M:%S') + " :"


def unescape(fromStr):
    """Removes backslashes used to escape characters"""
    return fromStr.replace('\\','')

