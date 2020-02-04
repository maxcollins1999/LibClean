### Preamble ###################################################################
#
# Author            : Max Collins
#
# Github            : https://github.com/maxcollins1999
#
# Title             : ftp_class.py 
#
# Date Last Modified: 6/1/2020
#
# Notes             : Contains the wrapper classes for ftplib to allow for 
#                     connection retrying and SSL explicit encryption. 
#
################################################################################

### Imports ####################################################################

#Global
import ftplib
import time
from getpass import getpass
from ssl import SSLSocket

################################################################################

### FTP_TLS OSError Workaround #################################################
#Workaround taken from: https://stackoverflow.com/questions/46633536/getting-a-oserror-when-trying-to-list-ftp-directories-in-python

class ReusedSslSocket(SSLSocket):
    def unwrap(self):
        pass


class MyFTP_TLS(ftplib.FTP_TLS):
    """Explicit FTPS, with shared TLS session"""
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            # reuses TLS session   
            conn = self.context.wrap_socket(conn,
                                            server_hostname=self.host,
                                            session=self.sock.session)           
            #we should not close reused ssl socket when file transfers finish
            conn.__class__ = ReusedSslSocket  
        return conn, size

################################################################################

class ftp_wrap():

### Server Name ################################################################
    s_name = 'FTP SERVER NAME GOES HERE' 
################################################################################
    ftps = None

    def __init__(self, uname, pword):
        """Takes username and password and constructs the FTPS object.
        """

        self.uname = uname
        self.pword = pword
        self.get_connect()

### Public Methods #############################################################

    def get_connect(self):
        """Uses the FTPS wrapper and constructs an FTPS object.
        """

        self.ftps = None
        self.ftps = MyFTP_TLS(self.s_name)
        self.ftps.login(self.uname, self.pword)
        self.ftps.prot_p()

    
    def con_retry(self):
        """If the ftps object has been disconnected from the server will 
        perform exponential back-off to connect up to a wait time of 40 seconds 
        inclusive.
        """

        t = 5
        suc = False
        while t <= 40 and not suc:
            print('\nAttempting to reconnect to server\n')
            time.sleep(t)
            self.get_connect()
            if self.ftps is None:
                t = t * 2
            else:
                suc = True
