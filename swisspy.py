#!/usr/bin/env python2
"""A series of useful python functions, written by Josh Smith in 2014"""

import datetime
from filecmp import dircmp
import hashlib
import inspect
import os
import time
import platform
import subprocess as sp
from subprocess import PIPE
import sys

def append_index(filename, ext, path):
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
    appended_file = "{0}({1}){2}".format(filename, str(index), ext)
    appended_path = os.path.join(path, appended_file)
    while os.path.exists(appended_path):
        index += 1
        appended_file = "{0}({1}){2}".format(filename, str(index), ext)
        appended_path = os.path.join(path, appended_file)
    return appended_path

def careful_delete(folder, files_to_remove):
    """Check that nothing 'important' is within folder, then remove it.

    folder : string
        Full path to candidate for removal.
    files_to_remove : list : strings
        A list of Files which should be removed from the folder.

    NOTE: This is unix specific, since it uses rmdir and find. OS agnostic
    version under development
    """
    try:
        dir_rm = sp.call(['rmdir', folder], stderr=sp.PIPE)
    except OSError:
        print prog_not_found_msg('rmdir')
        raise

    #Unless...
    if dir_rm > 0:

        #Hmm. Well, it's probably just empty dirs and .DS_Stores, right?
        delete_it = True
        try:
            find_files = sp.Popen(['find', folder, '-type', 'f'],
                                  stdout=sp.PIPE).communicate()
        except OSError:
            print prog_not_found_msg('find')
            raise
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
            try:
                sp.call(['rm', '-r', folder])
            except OSError:
                print prog_not_found_msg('rm')
                raise

def check_pid(pid):
    """Check whether the process with pid is running. Return True or False.

    Note - currently does not work with Windows"""
    exit_on_platform("Windows")
    try:
        os.kill(int(pid), 0) #Sends a harmless signal to the proc
    except OSError as e:
        if e.args[0] == 3:
            return False
        else:
            raise
    else:
        return True

def dir_being_written_to(path):
    """Uses lsof to get access tags on all files in path. Return true if
    any file is being written to.

    NOTE: This uses lsof, so is Unix dependent
    """
    try:
        lsof_out = sp.Popen(["lsof", "+D", path, "-F", "a"],
                             stdout=PIPE, stderr=PIPE)
    except OSError:
        print prog_not_found_msg('lsof')
        sys.exit(1)
    lsof_stdout = lsof_out.communicate()[0].split()
    for access_type in lsof_stdout:
        if 'w' in access_type:
            return True
    #If nothing is writing to a file, or there are no files in path:
    return False

def dirs_match(dir_a, dir_b, ignore=['.DS_Store']):
    """Checks whether directories a and b differ in structure or content

    >>> dirs_match('/tmp','/tmp')
    True

    >>> dirs_match('/tmp', '/opt')
    False

    """
    comparison = dircmp(dir_a, dir_b, ignore=ignore)
    if comparison.left_only or comparison.right_only:
        return False
    else:
        return True

def escape_char(from_str,char):
    r"""Append any instance of char in from_str with a backslash

    >>> escape_char("brickly manhang", "a")
    'brickly m\\anh\\ang'
    """
    return(from_str.replace(char,'\\' + char))

def exit_on_platform(p, exit_code=1):
    """Exit from the script with exit_code if you're running on platform"""
    if platform.system() == platform:
        print "Error: This function does not work on {0} (yet)".format(platform)
        sys.exit(exit_code)

def get_dir_currently_running_in():
    """Returns a full path to the directory this script is being run from.
    """
    current_running_path = os.path.abspath(inspect.stack()[0][1])
    current_running_dir = os.path.dirname(current_running_path)
    return current_running_dir

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

def get_mod_time(a_file):
    """Return the last modification time of a_file"""
    return time.ctime(os.path.getmtime(a_file))

def immediate_subdirs(the_dir):
    """Returns a list of immediate subdirectories of the_dir"""
    return [name for name in os.listdir(the_dir)
            if os.path.isdir(os.path.join(the_dir,name))]

def make_file(location, name, content="CONTENT-AAAH"):
    """Make a small dummy file at the given location"""
    path = os.path.join(os.path.abspath(location), name)
    with open(path, 'w') as the_file:
        the_file.write(content)

def prepend(pre, post):
    """If pre is defined, append it to post, concatenate and return

    >>> prepend("dis", "co")
    'disco'
    >>> prepend(None, "buttress")
    'buttress'
    """
    if pre != None:
        return "{0}{1}".format(pre, post)
    else:
        return post

def print_and_log(to_print, log_files=[], syslog_files=[],
                  ts='long', quiet=False):
    """Prints to_print to stdout and also to all files in log_files.
    If ts is passed, will print the time of the log.

    to_print : str
        The string to be logged.
    log_files : list : paths
        A list of paths to be logged to. Should be open file objects.
    syslog_files : list : paths
        A list of alternative log files to write to. Soon to be deprecated.
    ts : str
        'long' or 'short - default: short
        The type of timestamp to be appended to the file
        See docs for time_stamp
    quiet : bool
        default: False
        Print to stdout if false.
    """
    if ts:
        ts = str(time_stamp(ts))
        to_print = "{0} {1}".format(ts, to_print)
    if not quiet:
        print to_print
    for f in log_files:
        with open(f, 'a') as file_:
            file_.write(to_print)
    for f in syslog_files:
        with open(f, 'a') as file_:
            file_.write(to_print)

def prog_not_found_msg(prog):
    """Returns a string explaining prog could not be found.

    TODO: Do away with this entirely (everything should be platform agnostic
    as far as possible)"""
    return "The program {p} could not be found. Please ensure you " \
           "are running this from an OS with {p} installed".format(p=prog)

def smooth_join(*args):
    """
    Join any number of paths together properly
    """
    out_path = ""
    for arg in args:
        out_path = os.path.join(out_path, arg)
    return os.path.abspath(out_path)

def time_stamp(form='long'):
    """Prints the current time in a one of two formats. Useful for logging. 

    form can take values 'long' or 'short'. Examples:
    
    hogpy.timeStamp('long')
    2014-03-10 15:00:02 :
    
    hogpy.timeStamp('short')
    0310-1500    

    """
    ts = time.time()
    if form == 'short':
        return datetime.datetime.fromtimestamp(ts).strftime('%m%d-%H%M')
    if form == 'long':
        return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d '+\
                                                            '%H:%M:%S') + " :"

def unescape(from_str):
    """Remove backslashes used to escape characters"""
    return from_str.replace('\\','')

if __name__ == '__main__':
    import doctest
    doctest.testmod()