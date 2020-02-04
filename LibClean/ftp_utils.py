### Preamble ###################################################################
#
# Author            : Max Collins
#
# Github            : https://github.com/maxcollins1999
#
# Title             : ftp_utils.py 
#
# Date Last Modified: 13/1/2020
#
# Notes             : Contains the generic functions required to connect to the 
#                     server through FTPS (FTP with SSL or TSL exlicit 
#                     encryption) and push website updates. 
#
################################################################################

### Imports ####################################################################

#Global
import pathlib
import ftplib
import os
import time
from tqdm import tqdm
from getpass import getpass
from ssl import SSLSocket

#Local
if __name__ == '__main__' or __name__ == 'web_utils':
    from ftp_class import ftp_wrap
    from pho_data import pho_data
    from photo_frame import photo_frame
else:
    from .ftp_class import ftp_wrap
    from .pho_data import pho_data
    from .photo_frame import photo_frame

################################################################################

### Paths for Pathlib ##########################################################

p_latlon_dump = pathlib.Path(__file__).parent.absolute().parents[0] \
                / 'front-end' / 'by-location'
p_id_co_dump = pathlib.Path(__file__).parent.absolute().parents[0] \
               / 'front-end' / 'id4-to-location'
p_pop_json = pathlib.Path(__file__).parent.absolute().parents[0] \
             / 'front-end' / 'popular.json'
p_latlon_count = pathlib.Path(__file__).parent.absolute().parents[0] \
                 / 'front-end' / 'lat-lon-counts.js'
p_pop_js = pathlib.Path(__file__).parent.absolute().parents[0] \
           / 'front-end' / 'js' / 'popular-photos.js'
p_table = pathlib.Path(__file__).parent.absolute().parents[0] \
          / 'front-end' / 'oldperth_data' / 'id_table.js'
p_toloc_js = pathlib.Path(__file__).parent.absolute().parents[0] \
          / 'front-end' / 'oldperth_data' / 'to_loc.js'

################################################################################

def update_site():
    """When called, begins the chain of function calls required to update the
    OldPerth site.
    """

    w_ftps = ftp_wrap(input('\nUsername:'), getpass('\nPassword:'))
    server_clear(w_ftps)
    server_push(w_ftps)

def server_clear(w_ftps):
    """Takes the ftps wrapper object and removes the files that will conflict 
    with an update to the OldPerth site.
    """

    print('\nCleaning site for push')
    pbar = tqdm(total = 7)
    ftps = w_ftps.ftps
    try:
        dir_rm(ftps, '/by-location')
    except ftplib.error_perm:
        pass
    pbar.update(1)
    try:
        dir_rm(ftps, '/id4-to-location')
    except ftplib.error_perm:
        pass
    pbar.update(1)
    try:
        ftps.delete('/lat-lon-counts.js')
    except ftplib.error_perm:
        pass
    pbar.update(1)
    try:
        ftps.delete('/popular.json')
    except ftplib.error_perm:
        pass
    pbar.update(1)   
    try:
        ftps.delete('/js/popular-photos.js')
    except ftplib.error_perm:
        pass
    pbar.update(1)
    try:
        ftps.delete('/oldperth_data/id_table.js')
    except ftplib.error_perm:
        pass
    pbar.update(1)
    try:
        ftps.delete('/oldperth_data/to_loc.js')
    except ftplib.error_perm:
        pass
    pbar.update(1)
    pbar.close()


def server_push(w_ftps):
    """Takes the wrapper ftps object and pushes the new version of the website.
    """

    ftps = w_ftps.ftps
    print('\nPushing directories')
    dir_push(w_ftps, p_latlon_dump, '/by-location')
    dir_push(w_ftps, p_id_co_dump,'/id4-to-location')

    print('\nPushing loose files')
    pbar = tqdm(total = 5)
    load_file(w_ftps,'/lat-lon-counts.js', 
             open(p_latlon_count,'rb'))
    pbar.update(1)
    load_file(w_ftps,'/popular.json', 
             open(p_pop_json,'rb'))
    pbar.update(1)
    load_file(w_ftps,'/js/popular-photos.js', 
             open(p_pop_js,'rb'))
    pbar.update(1)
    load_file(w_ftps,'/oldperth_data/id_table.js', 
             open(p_table,'rb'))
    pbar.update(1)
    load_file(w_ftps,'/oldperth_data/to_loc.js', 
             open(p_toloc_js,'rb'))
    pbar.update(1)
    pbar.close()
    

def dir_rm(ftps, path):
    """Takes the ftps object and the path of a directory on the server and 
    sequentially deletes files until the directory can be deleted. Note: does 
    not delete other directories.
    """

    for (name, properties) in ftps.mlsd(path=path):
        if name in ['.', '..']:
            continue
        elif properties['type'] == 'file':
            ftps.delete(f"{path}/{name}")
    ftps.rmd(path)


def dir_push(w_ftps, l_path, e_path):
    """Takes the wrapper ftps object, the local path of the directory and the 
    desired external path and sequentially uploads the directory to the server.
    """

    ftps = w_ftps.ftps
    ftps.mkd(e_path)
    files = os.listdir(l_path)
    os.chdir(l_path)
    for f in tqdm(files):
        if os.path.isfile(os.path.join(l_path, f)):
            fh = open(f, 'rb')
            load_file(w_ftps,e_path+'/'+f, fh)
            fh.close()
        elif os.path.isdir(os.path.join(l_path, f)):
            ftps.cwd(e_path)
            ftps.mkd(f)
            ftps.cwd(f)
            dir_push(ftps, os.path.join(l_path, f), e_path+'/'+f)
            ftps.cwd('..')
            os.chdir('..')


def load_file(w_ftps, path, fstrm):
    """Takes the ftps wrapper, external path of the file and the open file 
    stream for the file to be uploaded, and uploads the file to the server. 
    This function retries connection using exponential rollback.
    """

    ftps = w_ftps.ftps
    try:
        ftps.storbinary('STOR '+path, fstrm)
    except:
        w_ftps.con_retry()
        ftps = w_ftps.ftps
        load_file(w_ftps,path,fstrm)

################################################################################