### Preamble ###################################################################
#
# Author            : Max Collins
#
# Github            : https://github.com/maxcollins1999
#
# Title             : utils.py 
#
# Date Last Modified: 17/12/2019
#
# Notes             : Contains the generic functions that are used by 
#                     photo_frame.py and pho_data.py.
#
################################################################################

### Imports ####################################################################

#Global
import csv
import re
import pathlib
import time
import requests
import json
import urllib.request
from PIL import Image

################################################################################

### Paths ######################################################################

api_state = pathlib.Path(__file__).parent / 'save_states' / 'api_status.csv'

################################################################################

def remove_punc(comment):
    """Takes a string and removes all punctuation except for ':' and then 
    returns the result.
    """
    
    temp = ''
    punc = '''!()-[]{};'"\<>./?@#$%^&*_~'''
    for char in comment:
        if char not in punc:
            temp = temp+char
        elif char == "-":
            temp = temp + ' '
    return temp


def remove_stop_words(line, stopWords):
    """Takes a string and a list of words to remove and returns the string 
    without those words.
    """

    for stop in stopWords:
        r_pat = re.compile(r'(,|\b|\s)('+stop+r')(\s|\b|,)',re.IGNORECASE)
        line = re.sub(r_pat,' ',line)
    if line.isspace():
        line = None
    return line


def api_available():
    """Reads the api_state.csv file in /save_state and determines whether 
    the mappify api can be used for free. Returning a boolean True:use and 
    False:don't use. If a day has passed, the number of available api uses is
    reset.
    """

    use = False
    fstrm = open(api_state,'r')
    lines = fstrm.readlines()
    fstrm.close()
    r_time, num_q = lines[1].split(',')
    r_time = float(r_time)
    num_q = int(num_q)
    elapsed = (time.time() - r_time) / 86400
    if elapsed > 1.0:
        num_q = '0' #Using a string to avoid converting it to a string later
        fstrm = open(api_state,'w')
        fstrm.write('time,number\n'+str(time.time())+','+num_q)
        fstrm.close()
        use = True
    elif num_q <= 2500:
        use = True
    return use


def api_use(url, payload):
    """Takes in the url of the api and the payload and performs the query. If 
    the query is successful the number of requests is updated in the file 
    /save_states/save_state.txt and the response is returned as a response 
    object. If the query is unsuccessful a None is returned.
    """

    try:
        response = requests.post(url, data = json.dumps(payload), 
                                headers={'content-type': 'application/json'})
    except:
        response = None
        raise ConnectionError('Critical API error')
    if response is not None:
        if response.status_code == 200:
            fstrm = open(api_state,'r')
            lines = fstrm.readlines()
            fstrm.close()
            r_time, num = lines[1].split(',')
            num = int(num)
            num += 1
            fstrm = open(api_state,'w')
            fstrm.write('time,number\n'+r_time+','+str(num))
            fstrm.close()
        elif response.status_code == 429:
            raise ConnectionRefusedError('Too many requests')
    return response


def im_dim(url):
    """Takes an image url and attempts to determine the dimensions of the image,
    if there is an error the function prints and error message and returns None.
    """


    width = None
    height = None
    try:
        image = Image.open(urllib.request.urlopen(url))
        width, height = image.size
    except:
        print('Failed to extract image dimensions from',url)
    return width, height


def loadFlags(file):
    """Takes in a filename/path and reads the data stored in the file. If it is 
    a single column of data returns a 1D list, if it is multiple columns of 
    data returns a 2D list. Note the first line is skipped as it assumes these 
    are column labels. 
    """
    
    with open(file) as fstrm:
        data = csv.reader(fstrm)
        vals = list(data)
    if all([len(val)==1 for val in vals]):
        data = [val[0] for val in vals[1:]]
    else:
        data = vals[1:]
    return data


def loadUpdate(file):
    """Takes a file name or path, loads an update csv file and returns a 
    dictionary with the relevant fields.
    """

    up_data = {
        'url' : [],
        'num' : [],
        'street' : [],
        'suburb' : []
    }
    with open(file) as fstrm:
        data = csv.reader(fstrm)
        vals = list(data)
    val_ind = [] #url | street_num | road_name | suburb
    if 'url' in vals[0]:
        val_ind.append(vals[0].index('url'))
    elif 'This field is prefilled. Please do not edit.':
        val_ind.append(vals[0].index('This field is prefilled. Please do not edit.'))
    val_ind.append(vals[0].index('Street Number'))
    val_ind.append(vals[0].index('Street/Road Name'))
    val_ind.append(vals[0].index('Suburb'))
    if None not in val_ind and len(vals)>1:
        for val in vals[1:]:
            if all([val[ind] != '' for ind in val_ind]):
                up_data['url'].append(val[val_ind[0]])
                up_data['num'].append(val[val_ind[1]])
                up_data['street'].append(val[val_ind[2]])
                up_data['suburb'].append(val[val_ind[3]])
    else:
        up_data = None
        raise ValueError('Update csv file is incorrectly formatted')
    return up_data

### Tests ######################################################################

if __name__ == '__main__':

    #Testing punctuation removal
    p_line = "I :like cats, they're very cute<>~!"
    p_line = remove_punc(p_line)
    if p_line == "I :like cats, they re very cute":
        print('utils.py test1 passed')
    else:
        print('utils.py test1 failed')
    
    #Testing remove_stop_words
    words  = ['These','are','naughty','words']
    sentence = 'I only like these good words'
    sentence = remove_stop_words(sentence,words)
    if sentence == 'I only like good ':
        print('utils.py test2 passed')
    else:
        print('utils.py test2 failed')

    #Testing API connection
    if api_available():
        url = 'https://mappify.io/api/rpc/address/geocode/'
        payload = {"streetAddress":"Not and Address","suburb":"Perth",
           "state":"WA","apiKey":"0e1edc2b-1f91-48b5-9df6-cf216b18afe2"}
        if api_use(url, payload):
            print('utils.py test3 passed')
        else:
            print('utils.py test3 failed')
    else:
        print('utils.py test3 unavailable')

    #Testing image dimenion extraction
    t_url = 'http://purl.slwa.wa.gov.au/slwa_b1763478_1.jpg'
    t_width, t_height = im_dim(t_url)
    if t_width == 760 and t_height == 565:
        print('utils.py test4 passed')
    else:
        print('utils.py test4 failed')

################################################################################