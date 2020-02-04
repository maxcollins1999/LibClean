### Preamble ###################################################################
#
# Author            : Max Collins
#
# Github            : https://github.com/maxcollins1999
#
# Title             : pho_data.py 
#
# Date Last Modified: 17/12/2019
#
# Notes             : The base class for the images. Contains basic data and 
#                     methods required for base functionality of OldPerth
#
################################################################################

### Imports ####################################################################

#Global
import re
import time
import requests
import json

#Local
if __name__ == '__main__' or __name__ == 'pho_data':
    from utils import remove_punc, remove_stop_words, api_available, api_use,\
    im_dim
else:
    from .utils import remove_punc, remove_stop_words, api_available, api_use, \
    im_dim

################################################################################

### API Information ############################################################

# Mappify API
url = 'https://mappify.io/api/rpc/address/geocode/'
api_key = "API KEY GOES HERE" 

################################################################################

class pho_data:
    
    suburb = None #String surburb name
    road = None #String street name
    number = None #String street number
    width = None #Float width of the image
    height = None #Float length of the image
    lon = None #String longitude
    lat = None  #String latitude

    b_add = None
    a_add = None

    def __init__(self, url, comment, year= None, author = None):
        """Takes url (string image url), comment (string image comment)
        year (integer year the image was taken), author (string photographer) 
        and constructs pho_data object. 
        """
        
        self.url = url
        self.comment = comment
        self.year = year
        self.author = author

### Public Methods #############################################################
        
    def __str__(self):
        """Returns some object state as a string. 
        """
        
        state = str(self.url) + '|' + str(self.comment) + \
                '|' + str(self.year) + '|' + str(self.author) + '|' + \
                str(self.suburb) + '|' + str(self.road) + '|' + \
                str(self.number) + '|' + str(self.lon) + '|' + str(self.lat) +\
                '|' + str(self.width) + '|' + str(self.height) + '|' +\
                str(self.b_add) + '|' + str(self.a_add)
        
        return state
    
    
    def ext_address(self,suburbs,cityStreets,streetFlags,stopWords,popPlaces):
        """Takes the paths of the word flags and searches the comment field 
        and attempts to extract the location of the image, updating the suburb 
        road and number fields.
        """
        
        if self.road is None and self.lat != 'NA':
            self.__pop_sweep(popPlaces)
            if self.road is None:
                self.__city_street_sweep(cityStreets)
            if self.road is None:
                self.__street_sweep(streetFlags, stopWords)
            if self.road is None:
                self.lat = 'NA'
                self.lon = 'NA'
            self.__suburb_sweep(suburbs)
            if self.road is not None:
                if self.number is not None:
                    self.b_add = self.number + ' ' + self.road + ' ' + self.suburb
                else:
                    self.b_add = self.road + ' ' + self.suburb


    def address_bad(self):
        """Setter method that sets latitude and longitude fields to 'NA' and 
        road, number and suburb fields to None. Should be called if there is not 
        enough information to perform get_coordinates() or if it is known the 
        image has no address. 
        """

        self.road = None
        self.number = None
        self.suburb = None
        self.lat = 'NA'
        self.lon = 'NA'
        self.a_add = None


    def get_coordinates(self):
        """Attempts to connect to the mappify API and determine the latitude and 
        longitude of the image based on the data stored in the object fields. 
        This method should always be run after the ext_address() method is run.
        If coordinates are found the lat and lon fields are updated accordingly,
        otherwise if there is no valid address the pho_data address fields are 
        set to None. 
        """

        suc = False
        if self.road and self.lon is None:
            if api_available():
                if self.number:
                    num = self.number + ' '
                else:
                    num = ''
                if self.suburb:
                    sub = self.suburb
                else:
                    sub = 'Perth'
                payload = {"streetAddress":num+self.road,
                           "suburb":sub,"state":"WA",
                           "apiKey": api_key}
                response = api_use(url,payload)
                if response:
                    json_resp = response.json()
                    if json_resp["result"]:
                        if json_resp["result"]["streetName"] and \
                        json_resp["result"]["streetType"]:
                            if json_resp["result"]["streetName"].lower() in \
                            self.road.replace("'","").lower():
                                suc = True
                    if suc:
                        if json_resp["result"]["numberFirst"] is not None:
                            self.number = str(json_resp["result"]["numberFirst"]) 
                        self.road = json_resp["result"]["streetName"]+ \
                                    ' ' +json_resp["result"]["streetType"]
                        self.suburb = json_resp["result"]["suburb"]
                        self.lat = str('{:.6f}'.format(json_resp["result"]["location"]["lat"]))
                        self.lon = str('{:.6f}'.format(json_resp["result"]["location"]["lon"]))
                        if self.road is not None:
                            if self.number is not None:
                                self.a_add = self.number + ' ' + self.road + ' ' + self.suburb
                            else:
                                self.a_add = self.road + ' ' + self.suburb
                    else:
                        self.address_bad()


    def get_im_dim(self):
        """Using the extracted url attempts to determine the dimensions of the 
        image.
        """

        if self.url and self.width is None:
            if self.url[-4:] == '.jpg' or self.url[-4:] == '.png':
                self.width, self.height = im_dim(self.url)
            else:
                self.width, self.height = im_dim(self.url+'.png')


    def save_dict(self):
        """Returns the fields as a dictionary for use in the photo_frame 
        saveState() method.
        """

        state = {
            'number': self.number,
            'road': self.road,
            'suburb': self.suburb,
            'lon': self.lon,
            'lat':self.lat,
            'width':self.width,
            'height':self.height,
            'url':self.url,
            'comment':self.comment,
            'year':self.year,
            'author':self.author,
            'b_add':self.b_add,
            'a_add':self.a_add
        }
        return state


    def load_dict(self, dict):
        """Takes a dictionary generated from the save_dict() method and copies 
        the object states except for the url and comment.
        """

        self.number = dict['number']
        self.road = dict['road']
        self.suburb = dict['suburb']
        self.lon = dict['lon']
        self.lat = dict['lat']
        self.width = dict['width']
        self.height = dict['height']
        self.year = dict['year']
        self.author = dict['author']
        self.b_add = dict['b_add']
        self.a_add = dict['a_add']


    def update_address(self, num, street, sub, lat = None, lon = None):
        """Takes a string street number, string street name and a string suburb 
        name and updates the relevant fields. If lat and lon are set as None 
        they will be positioned by the get coordinates function.
        """

        self.number = num
        self.road = street
        self.suburb = sub
        #lat lon set to None so that they will be positioned by the 
        # get_coordinates method. 
        if self.road is not None:
            self.a_add = None
            if self.number is not None:
                self.b_add = self.number + ' ' + self.road + ' ' + self.suburb
            else:
                self.b_add = self.road + ' ' + self.suburb
            if lat is not None and lon is not None:
                lat = str('{:.6f}'.format(float(lat)))
                lon = str('{:.6f}'.format(float(lon)))
            self.lat = lat
            self.lon = lon
        

    def pop_search(self, popPlaces):
        """Takes a list of popular places and performs a search for popular 
        places in the comment field of all images. This includes located images. 
        If a match is found relevant location data is updated. 
        """

        match = self.__pop_sweep(popPlaces)
        if match:
            if self.number is not None:
                self.b_add = self.number + ' ' + self.road + ' ' + self.suburb
            else:
                self.b_add = self.road + ' ' + self.suburb
            self.a_add = None

### Private Methods ############################################################

    def __city_street_sweep(self, cityStreets):
        """Takes a list of city streets in Perth and extracts any city addresses
        present in the comment field. If an address is found the street and 
        number fields are updated.
        """
           
        i = 0
        number = False

        punc_comment = remove_punc(self.comment)
        while not number and i < len(cityStreets): 
            punc_street = remove_punc(cityStreets[i]) #Removing punctuation
            pat = re.compile(r"(\d{1,3}[a-zA-Z]?)?\s("
                             +punc_street+r")",re.IGNORECASE)
            match = re.search(pat,punc_comment)
            if match: 
                if match.group(1):
                    self.number = match.group(1)
                    number = True
                self.road = cityStreets[i]
                self.suburb = 'Perth' #City streets are in Perth
            i+=1


    def __street_sweep(self, streetFlags, stopWords):
        """Takes a list of common street flags (road, street,...) and a list of 
        phrasing words to remove from the address (into, the on, ...) and 
        searches for possible addresses within the comment field. The longest 
        address with a street number is then selected and the street and number 
        fields are updated.
        """
                    
        i = 0
        length = 0
        num = False
        punc_comment = remove_punc(self.comment)
        while i < len(streetFlags):
            f_num = False
            punc_flag = remove_punc(streetFlags[i]) 
            pat = re.compile(r"(\d{1,3}[a-zA-Z]?)?\s?([a-zA-Z]*\s?[a-zA-Z]+\s)"+
                            r"("+punc_flag+r")(,|\s)",re.IGNORECASE)
            match = re.search(pat,punc_comment)
            if match:
                if match.group(2):
                    if match.group(1):
                        f_num = True
                    templine = remove_stop_words(match.group(2),stopWords)
                    if templine:
                        templine = templine.strip(' ')
                        f_len = len(templine.split(' '))
                    else:
                        f_len = 0
                    #Larger addresses are favoured and street numbers are 
                    # favoured above all else
                    if (f_len > length and num == f_num) or (f_num and not num)\
                        and f_len > 0:
                        self.road = templine +' '+match.group(3) 
                        num = f_num
                        length = f_len
                        if num:
                            self.number = match.group(1)
            i+=1


    def __suburb_sweep(self,suburbs):
        """Takes a list of Perth suburbs and if the suburb is not already 
        'Perth' handles searching for a street address and updates the suburb 
        field.
        """
            
        #Suburb is selected if it comes after the matched street
        if self.suburb is None and self.road is not None:
            i = 0
            found_suburb = False
            if self.number: #Pattern if there is a street number
                while not found_suburb and i < len(suburbs):
                    pat = re.compile(self.number+' '+self.road+r'.*'+\
                                     "("+suburbs[i]+")",re.IGNORECASE)
                    match = re.search(pat,self.comment)
                    if  match:
                        if match.group(1):
                            self.suburb = suburbs[i]
                            found_suburb = True
                    i+=1
            else: #Pattern if there is no street number
                while not found_suburb and i < len(suburbs):
                    pat = re.compile(self.road+r'.*'+"("+suburbs[i]+")",
                                    re.IGNORECASE)
                    match = re.search(pat,self.comment)
                    if  match:
                        if match.group(1):
                            self.suburb = suburbs[i]
                            found_suburb = True
                    i+=1
            if not found_suburb: #Suburb defaults to Perth if only a road is found
                self.suburb = 'Perth'


    def __pop_sweep(self, places):
        """Takes a list of popular places in Perth and handles searching for 
        the place in the metadata then returns a boolean representing if a 
        match was found. If a match is found the address data, latitude and 
        longitude fields are updated accordingly. 
        """

        punc_comment = remove_punc(self.comment)
        match = False
        i = 0
        while not match and i < len(places):
            if places[i][0].lower() in punc_comment.lower():
                match = True
            else:
                i+=1
        if match:
            if places[i][1] != '':
                self.number = places[i][1]
            else:
                self.number = None
            self.road=places[i][2].upper()
            self.suburb = places[i][3].upper()
            self.lat = str('{:.6f}'.format(float(places[i][4])))
            self.lon = str('{:.6f}'.format(float(places[i][5])))
        return match

### Tests ######################################################################

if __name__ == '__main__':
    
    #Testing object construction 
    test1 = pho_data('url','comment','year','author')
    if test1.__str__() == 'url|comment|year|author|None|None|None|None'+\
                          '|None|None|None':
        print('pho_data.py test1 passed')
    else:
        print('pho_data.py test1 failed')
        
    #Testing object construction    
    test2 = pho_data('url','comment')
    if test2.__str__() == 'url|comment|None|None|None|None|None|None'+\
                          '|None|None|None':
        print('pho_data.py test2 passed')
    else:
        print('pho_data.py test2 failed')
        
################################################################################     