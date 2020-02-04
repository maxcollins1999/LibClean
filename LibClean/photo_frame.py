### Preamble ###################################################################
#
# Author            : Max Collins
#
# Github            : https://github.com/maxcollins1999
#
# Title             : photo_frame.py 
#
# Date Last Modified: 13/1/2020
#
# Notes             : The outer class for the images. Contains a list of 
#                     pho_data objects which allows for higher level 
#                     manipulation required to generate the data for OldPerth.
#
################################################################################

### Imports ####################################################################

#Global
import pymarc
import re
import pathlib
import json
import csv
from tqdm import tqdm

#Local 
if __name__ == '__main__' or __name__ == 'photo_frame': 
    from pho_data import pho_data
    from utils import api_available, loadFlags, loadUpdate
else:
    from .pho_data import pho_data
    from .utils import api_available, loadFlags, loadUpdate

################################################################################

### Paths for Pathlib ##########################################################

p_aus_street_types = pathlib.Path(__file__).parent / 'parser_files' / \
                     'aus_street_types.txt'
p_perth_city_streets = pathlib.Path(__file__).parent / 'parser_files' / \
                     'perth_city_streets.txt'
p_stop_words = pathlib.Path(__file__).parent / 'parser_files' / 'stop_words.txt'
p_suburbs = pathlib.Path(__file__).parent / 'parser_files' / 'suburbs.txt'
p_pop_places = pathlib.Path(__file__).parent / 'parser_files' / 'pop_places.csv'
p_save_state = pathlib.Path(__file__).parent / 'save_states'
#True path for the marc data - needs to be updated for each new read
tp_marc_data = pathlib.Path(__file__).parent / 'marc_data' 
p_update = pathlib.Path(__file__).parent / 'update_data' 
p_dump = pathlib.Path(__file__).parent / 'data_dump' / 'data_dump.txt' 
p_spreadsheet = pathlib.Path(__file__).parent / 'data_dump' / 'data_sheet.csv' 

################################################################################

class photo_frame:
    
    photos = []
    suburbs = loadFlags(p_suburbs)
    cityStreets = loadFlags(p_perth_city_streets)
    streetFlags = loadFlags(p_aus_street_types)
    stopWords = loadFlags(p_stop_words)
    popPlaces = loadFlags(p_pop_places)

### Public Methods #############################################################    
    
    def readxml(self, filename , n = None):
        """Takes in the name of a file containing a MARC 21 .xml database dump 
        and reads the first n unique photos. If n = None reads in all photos 
        in the database dump. A list of pho_data objects is then created from 
        the parsed image metadata.
        """

        p_marc_data = tp_marc_data / filename
        p_marc_data = str(p_marc_data.absolute())
        records=pymarc.marcxml.parse_xml_to_array(p_marc_data, strict=False,\
                                                  normalize_form=None)
        if not n:
            n = len(records)
        elif n > len(records)-1:
            n = len(records)
            
        for i in range(0,n):
            author, year, images = self.getRecordData(records[i])
            for j in range(0,len(images[0])):
                if not self.__isPresent(images[1][j])[0]:
                    self.photos.append(pho_data(images[1][j],images[0][j],year,
                                                author))
                    
                    
    def findLocation(self):
        """Iterates through the list of photos and attempts to extract the 
        street address from the parsed metadata.
        """

        for photo in tqdm(self.photos):
            photo.ext_address(self.suburbs,self.cityStreets,self.streetFlags,
                              self.stopWords, self.popPlaces)


    def popSearch(self):
        """Iterates through all images and searches for a popular place match. 
        If there is a match the relevant fields are updated.
        """

        for im in tqdm(self.photos):
            im.pop_search(self.popPlaces)


    def manualUpdate(self,url,num,road,suburb,lat,lon):
        """Takes 4 strings denoting the image url, street number, street name, 
        suburb and 2 floats denoting the latitude, longitude. If the image 
        exists in the current catalogue updates the relevant fields.
        """

        for im in self.photos:
            if url == im.url:
                im.update_address(num, road, suburb, lat, lon)
                break
    
    
    def saveState(self):
        """Saves the current set of photos to a JSON file
        """

        states = []
        state_path = p_save_state / 'save_state.json'
        for photo in self.photos:
            states.append(photo.save_dict())
        with open(state_path, 'w', encoding='utf-8') as fstrm:
            json.dump(states, fstrm, ensure_ascii=False, indent=4) 

    
    def loadState(self, name = 'save_state.json'):
        """ Takes the name of the JSON save file and loads a previous object 
        state from the JSON file, merging with the current object state. 
        Duplicate images are discarded.
        """
              
        state_path = p_save_state / name
        with open(state_path, 'rb') as fstrm:
            states = json.load(fstrm)
        print('\nLoading and merging data\n')
        for im_dict in tqdm(states):
            if not self.__isPresent(im_dict['url'])[0]:
                self.photos.append(pho_data(im_dict['url'], im_dict['comment']))
                self.photos[-1].load_dict(im_dict)
            
        
    def getRecordData(self, record):
        """Takes a record object generated from pymarc and returns the author, 
        year and a 2D list containing the image urls and image comments.
        """
        
        images = []
        
        yrpat = re.compile(r'(\d{4})') #Pattern to match year
        
        author = record.author()    #Extracts author from entry
        
        if record['260']:           #Extracts year from entry 
            year = re.findall(yrpat, record['260'].value())
            if len(year) > 0:
                year = int(year[0])
            else:
                year = None
        elif record['264']:          
            year = re.findall(yrpat, record['264'].value())
            if len(year) > 0:
                year = int(year[0])
            else:
                year = None
        else:
            year = None
            
        comments = [val.get_subfields('z')[0] for val in \
                   record.get_fields('856') if len(val.get_subfields('z'))>0]

        urls = [val.get_subfields('u')[0] for i, val in \
               enumerate(record.get_fields('856')) if i < len(comments)]

        images.append(comments)
        images.append(urls)

        return author, year, images
    
    
    def dataDump(self):
        """Dumps current list of images and corresponding metadata into a pipe 
        separated file.
        """
    
        fstrm = open(p_dump,'w')
        fstrm.write('url|comment|year|photographer|suburb|road|number|lon|'\
                    'lat|address before api|address after api\n')
        tot_len = len(self.photos)
        for i, photo in enumerate(self.photos):
            fstrm.write(photo.__str__())
            if i < tot_len-1:
                fstrm.write('\n')
        fstrm.close()


    def genSpreadsheet(self):
        """Dumps current list of images and corresponding metadata into a human 
        readable CSV file.
        """

        with open(p_spreadsheet, mode='w', newline='') as fstrm:
            fstrm = csv.writer(fstrm, delimiter=',', quotechar='"', \
                quoting=csv.QUOTE_MINIMAL)
            fstrm.writerow(['url','comment','year','photographer','number',\
                'road','suburb','lat','lon','address before api',\
                'address after api'])
            for im in self.photos:
                fstrm.writerow([im.url,im.comment,im.year,im.author,im.number,\
                    im.road,im.suburb,im.lat,im.lon,im.b_add,im.a_add])
            

    
    def geo_locate_images(self, n = None):
        """Attempts to geolocate n images. If n is not specified or bigger than 
        the number of images stored, all images are geolocated. An error is 
        thrown if the API is unavailable.
        """

        if not n:
            n = len(self.photos)
        elif n > len(self.photos)-1:
            n = len(self.photos)
        pbar = tqdm(total = self.get_tot_togeo())
        g_count = 0
        i = 0
        available = api_available()
        while g_count < n and i < len(self.photos):
            available = api_available()
            if available and self.photos[i].lat is None and self.photos[i].road:
                try:
                    self.photos[i].get_coordinates()
                except ConnectionRefusedError:
                    pbar.close()
                    raise ConnectionRefusedError
                g_count+=1
                pbar.update(1)
            elif not available:
                raise ConnectionAbortedError('API is unavailable')
            i+=1
        pbar.close()
                

    def get_dims(self):
        """Iterates through the stored images, and if the image has a street 
        name their dimensions are extracted from their url.
        """

        for photo in tqdm(self.photos):
            if photo.road is not None:
                photo.get_im_dim()


    def add_update(self, f_name):
        """Takes the name of the CSV file located in LibClean/update_data and 
        updates the pho_data objects accordingly.
        """

        path = p_update / f_name
        up_data = loadUpdate(str(path.absolute()))
        for i, url in enumerate(up_data['url']):
            uin, ind = self.__isPresent(url)
            if uin:
                if up_data['street'][i] is None:
                    self.photos[ind].address_bad()
                else:
                    self.photos[ind].update_address(up_data['num'][i], 
                    up_data['street'][i], up_data['suburb'][i])


    def get_tot_im(self):
        """Returns the total number of images loaded into the LibClean.
        """

        return len(self.photos)

    
    def get_tot_loc(self):
        """Returns the total number of images that have been successfully 
        geolocated.
        """

        total = 0
        for im in self.photos:
            if im.lat is not None:
                if im.lat != 'NA':
                    total += 1
        return total


    def get_tot_pro(self):
        """Returns the total number of images that have been searched for a 
        street address.
        """

        total = 0
        for im in self.photos:
            if im.lat is not None:
                total += 1
        return total


    def get_tot_togeo(self):
        """Returns the number of images awaiting geolocation.
        """

        total = 0 
        for im in self.photos:
            if im.road is not None and im.lat is None:
                total += 1
        return total

### Private Methods ############################################################
        
    def __isPresent(self,url):
        """ Determines if the url is present in the current set of images and 
        returns a tuple (boolean, numeric index).
        """
        
        present = False
        ind = None
        for i, im in enumerate(self.photos):
            if im.url == url:
                present = True
                ind = i
        return present, ind

### Tests ######################################################################
    
if __name__ == '__main__':

    p_marc_data = tp_marc_data / 'marc21 - test.xml'
    p_marc_data = str(p_marc_data.absolute())
    test_frame = photo_frame()
    
    #Testing marc21 .xml reading
    try:
        test_record=pymarc.marcxml.parse_xml_to_array(p_marc_data, 
                                                      strict=False, 
                                                      normalize_form=None)
        print('photo_frame.py test1 passed')
    except:
        print('photo_frame.py test1 failed')
    
    #Testing getRecordData method
    author, year, image = test_frame.getRecordData(test_record[0])
    if author is None and year == 1905 and image[0][0] == \
    'Federal Hotel, 179 Wellington Street, Perth, ca.1905' and image[1][0] == \
    'http://purl.slwa.wa.gov.au/slwa_b1763478_1':
        print('photo_frame.py test2 passed')
    else:
        print('photo_frame.py test2 failed')
        
    #Testing .xml reading
    test_frame.readxml(p_marc_data, n = 2)
    if test_frame.photos[0].__str__() == \
    'http://purl.slwa.wa.gov.au/slwa_b1763478_1|Federal Hotel, 179 Wellington'\
    +' Street, Perth, ca.1905|1905|None|None|None|None|None|None|None|None|'+\
    'None|None' and test_frame.photos[1].__str__() == \
    'http://purl.slwa.wa.gov.au/slwa_b1763521_1|006207PD: Supreme Court'+\
    ' Building, Perth. Sign reads: Dogs not allowed in the garden,'+\
    ' ca.1905|1905|None|None|None|None|None|None|None|None|None|None': 
        print('photo_frame.py test3 passed')
    else:
        print('photo_frame.py test3 failed')
        
    #Testing address extraction
    test_frame.findLocation()
    if test_frame.photos[0].__str__() == 'http://purl.slwa.wa.gov.a'+\
    'u/slwa_b1763478_1|Federal Hotel, 179 Wellington Street, Perth, ca.1905'+\
    '|1905|None|Perth|Wellington Street|179|None|None|None|None|'+\
    '179 Wellington Street Perth|None':
        print('photo_frame.py test4 passed')
    else:
        print('photo_frame.py test4 failed')

    #Testing geolocation capabilities
    if api_available():
        test_frame.geo_locate_images()
        if test_frame.photos[0].__str__() == 'http://purl.slwa.wa.gov.au/slwa'+\
            '_b1763478_1|Federal Hotel, 179 Wellington Street, Perth, ca.'+\
            '1905|1905|None|PERTH|WELLINGTON STREET|179|115.859879|'+\
            '-31.951837|None|None|179 Wellington Street Perth|'+\
            '179 WELLINGTON STREET PERTH':
            print('photo_frame.py test5 passed')
        else:
            print('photo_frame.py test5 failed')
    else:
        print('photo_frame.py test5 unavailable')
    
    #Testing image dimension extraction
    test_frame.get_dims()
    if test_frame.photos[0].__str__() == 'http://purl.slwa.wa.gov.au/slwa'+\
    '_b1763478_1|Federal Hotel, 179 Wellington Street, Perth, ca.'+\
    '1905|1905|None|PERTH|WELLINGTON STREET|179|115.859879|'+\
    '-31.951837|760|565|179 Wellington Street Perth|179 WELLINGTON STREET PERTH':
        print('photo_frame.py test6 passed')
    else:
        print('photo_frame.py test6 failed')

################################################################################       