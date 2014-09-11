#!/usr/bin/env python2.7
"""A series of useful python functions, written by Josh Smith in 2014"""

import datetime
import hashlib
import os
import time
import subprocess as sp
from subprocess import PIPE
import shutil

def check_pid(pid):
    """Check whether the process with pid is running. Return True or False.

    Note - currently does not work with Windows"""
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
    """Returns an MD5 hash of from_file, processing the file in chunks of
    chunk_size - by default this is 8192 bytes"""
    f = open(from_file, 'rb')
    hash_out = hashlib.md5()
    while True:
        chunk = f.read(chunk_size)
        if chunk == '':
            break
        else:
            hash_out.update(chunk)
    f.close()
    return hash_out.hexdigest()

def careful_delete(folder, files_to_remove):
    """Check that nothing 'important' is within folder, then remove it.

    folder : string
        Full path to candidate for removal.
    files_to_remove : list : strings
        A list of Files which should be removed from the folder.

    NOTE: This is unix specific, since it uses rmdir and find. OS agnostic
    version under development
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

def back_one(path):
    """Return the directory one step deeper than path

    >>> back_one("/tmp/pindle/Cranston")
    '/tmp/pindle'
    """
    return '/'.join(path.split('/')[:-1])


def escape_char(from_str,char):
    """Append any instance of char in from_str with a backslash

    >>> escape_char("brickly manhang", "a")
    'brickly m\anh\ang'
    """
    return(from_str.replace(char,'\\' + char))

def appendIndex(filename, ext, path):
    """Append an index to a path, ensuring the indexed filename is unique
    within its parent directory.

    Given a file 'filename' at location 'path' with extension 'ext',
    this will return the path of filename(n)ext, where n is the lowest integer
    for which filename(n-1)ext already exists.
    
    As an example, given a directory /tmp/adir containing a.txt and a(1).txt,
    appendIndex('a','.txt','/tmp/adir') will return a(2).txt

    filename : str
        The name of the file
    ext : str
        The file's extension
    path : str
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

