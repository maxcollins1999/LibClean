### Preamble ###################################################################
#
# Author            : Max Collins
#
# Github            : https://github.com/maxcollins1999
#
# Title             : drive_class.py 
#
# Date Last Modified: 9/1/2020
#
# Notes             : The wrapper class for the google drive object. Contains 
#                     all relevant methods to download and upload save states 
#                     to the Curtin Hive Google Drive
#
################################################################################

### Imports ####################################################################

#Global
import pathlib
import os
import time
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

#Local 

################################################################################

### Paths for Pathlib ##########################################################

p_data =  pathlib.Path(__file__).parent / 'drive_data'
p_secret = pathlib.Path(__file__).parent / 'drive_data' / 'client_secrets.json' 
p_creds = pathlib.Path(__file__).parent / 'drive_data' / 'mycreds.txt' 
p_pull_save = pathlib.Path(__file__).parent / 'save_states' \
             / 'cloud_save_state.json'
p_push_save = pathlib.Path(__file__).parent / 'save_states' / 'save_state.json'

################################################################################

class old_drive:

### Folder ID ##################################################################
    folder_id = "EXTRACTED VALUE GOES HERE"
################################################################################
    drive = None
    
    def __init__(self):
        """Initialises the old_drive object and attempts to validate credentials
        to connect user to google drive.
        """
        
        if os.path.exists(p_secret):
            o_dir = os.getcwd()
            os.chdir(p_data)
            gauth = GoogleAuth()
            os.chdir(o_dir)
            if os.path.exists(p_creds):
                gauth.LoadCredentialsFile(p_creds)
            if gauth.credentials is None:
                # Authenticate if they're not there
                o_dir = os.getcwd()
                os.chdir(p_data)
                gauth.LocalWebserverAuth()
                os.chdir(o_dir)
            elif gauth.access_token_expired:
                # Refresh them if expired
                gauth.Refresh()
            else:
                # Initialize the saved creds
                gauth.Authorize()
            # Save the current credentials to a file
            gauth.SaveCredentialsFile(p_creds)

            self.drive = GoogleDrive(gauth)
        else:
            raise FileNotFoundError('No client_secrets.json was found')

### Public Methods #############################################################    

    def list_saves(self):
        """Returns a dictionary of the file ids and dates for each of the saves 
        stored on the google drive.
        """

        files = {}
        fileList = self.drive.ListFile({'q': "'"+self.folder_id+"' in parents and trashed=false"}).GetList()
        for file in fileList:
            files[file['id']] = time.ctime(float(file['title'][:-5]))
        return files


    def pull_curr_save(self):
        """Pulls the most recently added save.
        Note: To load save use 
        photo_frame.loadState(name = 'cloud_save_state.json')
        """

        c_time = 0.0
        fileList = self.drive.ListFile({'q': "'"+self.folder_id+"' in parents and trashed=false"}).GetList()
        for file in fileList:
            if float(file['title'][:-5]) > c_time:
                c_time = float(file['title'][:-5]) 
                c_id = file['id']
        if len(fileList)==0:
            raise FileNotFoundError('No save file found on Google drive')
        else:
            self.pull_save(c_id)


    def push_save(self):
        """Pushes the current OldPerth save_state.json to the google drive. 
        Note: The save is given the name <seconds since epoch>.json
        """

        t = time.time()
        file = self.drive.CreateFile({'parents': [{'id': self.folder_id}],'title':str(t)+'.json'})
        file.SetContentFile(str(p_push_save.absolute()))
        file.Upload()


    def pull_save(self, id):
        """Takes a save_state id and pulls the save from the google drive.
        """

        fileList = self.drive.ListFile({'q': "'"+self.folder_id+"' in parents and trashed=false"}).GetList()
        for file in fileList:
            if file['id'] == id:
                  file.GetContentFile(str(p_pull_save.absolute()))

################################################################################