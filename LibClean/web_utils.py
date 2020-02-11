### Preamble ###################################################################
#
# Author            : Max Collins
#
# Github            : https://github.com/maxcollins1999
#
# Title             : web_utils.py 
#
# Date Last Modified: 10/12/2019
#
# Notes             : Contains the generic functions required to convert a 
#                     photo_frame into readable .json and .js files for the 
#                     OldPerth website.
#
################################################################################

### Imports ####################################################################

#Global
import json
import pathlib
import random
from os import remove, listdir

#Local
if __name__ == '__main__' or __name__ == 'web_utils':
    from pho_data import pho_data
    from photo_frame import photo_frame
else:
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

### A Note on Image ID #########################################################
#
# If images are imported from multiple catalogues it is theoretically possible 
# for 2 distinct images to share the same image ID. As such each image stored in
# a photo_frame object is assigned an 8 digit ID based on their order in the 
# photo_frame object. The ID has little significance other than a number that 
# the OldPerth front-end uses to identify specific images.  
#
################################################################################

def latlon_format(photo):
    """Takes a pho_data object and returns the dictionary format for use by 
    latlon_dump().
    """

    t_url = thumb_url_form(photo.url)
    p_url = url_form(photo.url)
    form = {
        "years":[photo.year],
        "original_title":"",
        "date": str(photo.year),
        "width": photo.width,
        "folder": None,
        "height": photo.height,
        "text": None,
        "thumb_url": t_url,
        "title":photo.comment+ '<br/><br/>[Extracted Address: ' +\
            str(photo.b_add) + ', API Returned Address: ' + str(photo.a_add)+\
            '.]<br/>Year:',
        "image_url": p_url
    }
    return form


def thumb_url_form(url):
    """Takes the SLWA photo url and returns the thumbnail url. Note this 
    function is heavily influenced by the format of the catalogue and could be
    easily broken if the Library switches to a different url structure.
    """

    if url[-4:] != '.png' and url[-4:] != '.jpg':
        url = url + '.png'
    return url


def url_form(url):
    """Takes the SLWA photo url and returns the photo url. Note this 
    function is heavily influenced by the format of the catalogue and could be
    easily broken if the Library switches to a different url structure.
    """

    if url[-4:] != '.png' and url[-4:] != '.jpg':
        url = url + '.jpg'
    return url


def get_id(frame):
    """Takes a photo_frame object and returns a list containing each image's 
    uniquely generated ID.
    """

    num = len(frame.photos)
    im_id = []
    for i in range(0, num):
        buf = len(str(i))
        if buf <= 8:
            im_id.append('0'*(8-buf)+str(i))
        else:
            raise ValueError('Over 99 999 999 images')
    return im_id


def id_tbl_dump(frame, im_id):
    """Generates the translation table used by the OldPerth front-end scripts to
    determine which image the user is giving feedback on.
    """

    table = {}
    for i, id_num in enumerate(im_id):
        table[id_num] = frame.photos[i].url
    with open(p_table, 'w', encoding='utf-8') as fstrm:
        fstrm.write('var id_table = ')
        json.dump(table, fstrm, ensure_ascii=False, indent=4) 
        fstrm.write(';')

def get_latlon_data(frame, im_id):
    """Takes a photo_frame object and the generated image IDs returns the images 
    sorted by lat lon required for lat_lon_dump.
    """

    dump = {}
    for i, id_num in enumerate(im_id):
        if frame.photos[i].lat != 'NA' and frame.photos[i].lat:
            if frame.photos[i].lat+','+frame.photos[i].lon in dump:
                dump[frame.photos[i].lat+','+frame.photos[i].lon][id_num] = \
                    latlon_format(frame.photos[i])
            else:
                dump[frame.photos[i].lat+','+frame.photos[i].lon] = {}
                dump[frame.photos[i].lat+','+frame.photos[i].lon][id_num] = \
                    latlon_format(frame.photos[i])
    return dump


def lat_lon_dump(latlon_data):
    """Takes the latlon data generated by get_latlon_data() and generates the 
    latlon files located in /front-end/by-location.
    """

    for co in latlon_data:
        path = p_latlon_dump / (co.replace(',','') + '.json')
        path = str(path.absolute())
        with open(path, 'w', encoding='utf-8') as fstrm:
            json.dump(latlon_data[co], fstrm, ensure_ascii=False, indent=4)


def id_co_dump(frame, im_id):
    """Takes a photo_frame object and the generated image IDs and generates the 
    ID to coordinate files for the OldPerth website front-end, located in 
    /front-end/id4-to-location. 
    """

    dump = {}
    for i, id_num in enumerate(im_id):
        if frame.photos[i].lat != 'NA' and frame.photos[i].lat:
            if id_num[:4] in dump:
                dump[id_num[:4]][id_num] = frame.photos[i].lat+','+\
                    frame.photos[i].lon
            else:
                dump[id_num[:4]] = {}
                dump[id_num[:4]][id_num] = frame.photos[i].lat+','+\
                    frame.photos[i].lon
    for co in dump:
        path = p_id_co_dump / (co + '.json')
        path = str(path.absolute())
        with open(path, 'w', encoding='utf-8') as fstrm:
            json.dump(dump[co], fstrm, ensure_ascii=False, indent=4)  


def pop_json_dump(frame, im_id):
    """Takes a photo_frame object and the generated image IDs and generates the 
    popular.json file for the OldPerth website front-end, located /front-end.
    """

    dump = {}
    for i, id_num in enumerate(im_id):
        if frame.photos[i].lat != 'NA' and frame.photos[i].lat:
            vals = latlon_format(frame.photos[i])
            del vals['original_title'], vals['folder']
            dump[id_num] = vals
    path = str(p_pop_json.absolute())
    with open(path, 'w', encoding='utf-8') as fstrm:
        json.dump(dump, fstrm, ensure_ascii=False, indent=4) 


def lat_lon_count_dump(latlon_data):
    """Takes the latlon_data generated by get_latlon_data() and generates the 
    lat-lon-counts.js file required to update the OldPerth website front-end, 
    located in /front-end.
    """

    path = str(p_latlon_count.absolute())
    dump = {}
    for co in latlon_data:
        dump[co] = {}
        for id_num in latlon_data[co]:
            if latlon_data[co][id_num]['date'] in dump[co]:
                dump[co][latlon_data[co][id_num]['date']] += 1
            else:
                dump[co][latlon_data[co][id_num]['date']] = 1
    with open(path, 'w', encoding='utf-8') as fstrm:
        fstrm.write('var lat_lons =')
        json.dump(dump, fstrm, ensure_ascii=False, indent=4) 
        fstrm.write(';')


def pop_js_dump(latlon_data):
    """Takes the latlon_data generated by get_latlon_data() and generates the 
    popular-photos.js file required to update the OldPerth website front-end, 
    located in /front-end/js.
    """

    path = str(p_pop_js.absolute())
    dump = []
    for co in latlon_data:
        for id_num in latlon_data[co]:
            temp = {
                'id':id_num,
                'date':latlon_data[co][id_num]['date'],
                'desc':latlon_data[co][id_num]['title'],
                'loc':None,
                'height':latlon_data[co][id_num]['height']
            }
            dump.append(temp)
    with open(path, 'w', encoding='utf-8') as fstrm:
        fstrm.write('export var popular_photos =')
        json.dump(dump, fstrm, ensure_ascii=False, indent=4) 
        fstrm.write(';')


def toloc_js_dump(frame):
    """Takes the photo_frame object and generates the to_loc.js file required 
    to update the OldPerth website front-end, located in 
    /front-end/oldperth_data.
    """

    path = str(p_toloc_js.absolute())
    dump = {}
    for im in frame.photos:
        add = False
        if im.lat is None:
            add = True
        if add:
            dump[url_form(im.url)] = {'url':im.url,
                                      'comment':im.comment}
    #A subset of unlocated images is pushed. Too many images causes some 
    # browsers to not load images correctly.
    num = 300
    if len(dump) < num:
        num = len(dump)
    dump = dict(random.sample(dump.items(), num))
    with open(path, 'w', encoding='utf-8') as fstrm:
        fstrm.write('var toloc =')
        json.dump(dump, fstrm, ensure_ascii=False, indent=4) 
        fstrm.write(';')
    


def web_wipe():
    """Removes the photo data from the website front-end. Note this does not 
    delete the photo_frame JSON save, only images currently in the website. 
    """

    #Deleting id_table.json
    try:
        remove(str(p_table.absolute()))
    except FileNotFoundError:
        print('id_table.js does not exist')

    #Deleting by-location
    try:
        file_list = listdir(p_latlon_dump)
        for file_name in file_list:
            path = p_latlon_dump / file_name
            remove(str(path.absolute()))
    except FileNotFoundError:
        print('by-location does not exist')

    #Deleting id4-to-location
    try:
        file_list = listdir(p_id_co_dump)
        for file_name in file_list:
            path = p_id_co_dump /file_name
            remove(str(path.absolute()))
    except FileNotFoundError:
        print('id4-to-location does not exist')

    #Deleting popular-photos.js
    try:
        remove(str(p_pop_js.absolute()))
    except FileNotFoundError:
        print('popular-photos.js does not exist')

    #Deleting lat-lon-counts.js
    try:
        remove(str(p_latlon_count.absolute()))
    except FileNotFoundError:
        print('lat-lon-counts.js does not exist')

    #Deleting popular.json
    try:
        remove(str(p_pop_json.absolute()))
    except FileNotFoundError:
        print('popular.json does not exist')

    #Deleting to_loc.js
    try:
        remove(str(p_toloc_js.absolute()))
    except FileNotFoundError:
        print('popular.json does not exist')

def web_drop(frame):
    """Takes a photo_frame object and updates the local website front-end files 
    accordingly. 
    """

    web_wipe()
    im_id = get_id(frame)
    id_tbl_dump(frame, im_id)
    toloc_js_dump(frame)
    latlon_data = get_latlon_data(frame,im_id)
    lat_lon_dump(latlon_data)
    id_co_dump(frame, im_id)
    pop_json_dump(frame,im_id)
    lat_lon_count_dump(latlon_data)
    pop_js_dump(latlon_data)

### Tests ######################################################################

if __name__ == '__main__':

    t_url1 = 'a_url.png'
    t_url2 = 'a_url'
    test_frame = photo_frame()
    test_frame.readxml('marc21 - test.xml',n=1)

    #Testing thumb_url_form
    if thumb_url_form(t_url1) == 'a_url.png' and thumb_url_form(t_url2) \
    == 'a_url.png':
        print('web_utils.py test1 passed')
    else:
        print('web_utils.py test1 failed')

    #Testing url_form
    if url_form(t_url1) == 'a_url.png' and url_form(t_url2) \
    == 'a_url.jpg':
        print('web_utils.py test2 passed')
    else:
        print('web_utils.py test2 failed')

    #Testing latlon_format
    t_form = latlon_format(test_frame.photos[0])
    if t_form['years'] == [1905] and t_form['original_title'] == '' and \
    t_form['date'] == '1905' and t_form['width'] == None and t_form['folder'] == \
    None and t_form['height'] == None and t_form['text'] == None and \
    t_form['thumb_url'] == 'http://purl.slwa.wa.gov.au/slwa_b1763478_1.png' and\
    t_form['title'] == 'Federal Hotel, 179 Wellington Street, Perth, ca.1905' \
    and t_form['image_url'] == 'http://purl.slwa.wa.gov.au/slwa_b1763478_1.jpg':
        print('web_utils.py test3 passed')
    else:
        print('web_utils.py test3 failed')

    #Testing get_id
    test_frame = photo_frame()
    test_frame.readxml('marc21 - test.xml',n=5)
    if get_id(test_frame)[4] == '00000004':
        print('web_utils.py test4 passed')
    else:
        print('web_utils.py test4 failed')

################################################################################