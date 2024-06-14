#!/usr/bin/env python3
# imdbgallery.py
"""
########
BSD 2-Clause License

imdbgallery.py Copyright (c) 2024, Jonathan Adams https://github.com/jfadams1963
Based on Scrape_IMDB.py by IvRogoz https://github.com/IvRogoz with permission.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
########

 This is a modified version of https://github.com/IvRogoz
 Much of this code is due to a lot of work on the part of
 IvRogoz. I and anyone who uses and enjoys this code owes IvRogoz 
 a big thanks.
 
 June 2024 by https://github.com/jfadams1963:
 + Made changes to reflect the new structure on IMDb.
 + Cinemagoer functionality to specify movie|person by title|name.
 + Using SoupStrainer for more efficient html parsing.
 + Usage:
     imdbgallery.py movie <title|movieID>
     imdbgallery.py actor|person <name|personID>
"""


import sys
import os
import string
import re
import shutil
import requests
from random import randrange
import json
from bs4 import BeautifulSoup, SoupStrainer
from imdb import (Cinemagoer,
                  IMDbError,
                  IMDbDataAccessError)


arg1 = sys.argv[1]
arg2 = sys.argv[2]
is_person = 0
mediaview_url = "https://www.imdb.com/"

#### Cineamagoer section to get movieID or personID -jfadams1963
# Set up person|movie options
# Instantiate a Cinemagoer object
# Get a movies|persons object

# Strip input of punctuation, set arg1 to lower case
# IMDb queries are case insensitive
arg1 = ''.join([c for c in arg1.lower() if c not in string.punctuation])
arg2 = ''.join([c for c in arg2 if c not in string.punctuation])

#Use ID is initially false
use_id = 0
# Use person is initially false
person_id = 0

if arg2.isnumeric() is True:
    use_id = 1
    person_id = 1

#allow 'actor' for person
if arg1 in ('actor', 'person'):
    arg1 = 'person'
    is_person = 1


def get_random_line(fname) -> str:
    """
    Return a random line from opened file fname
    Uses reservoir sampling (with sample size of 1)
    """
    for l, aline in enumerate(fname, start=1):
        if randrange(l) == 0:  # random int [0..l)
            line = aline
    return line
# End get_random_line


# Instantiate a Cinemagoer object
movie = ''
persons = ''
try:
    ia = Cinemagoer()
    # Set title
    if (use_id == 1) and (is_person == 0):
        title = ia.get_movie(arg2)['title']
        movies = ia.search_movie(title)
        title_words = title.split()
        title_long = title_words[0]
        for w in range(1,4):
            try:
                title_long += '_' + title_words[w]
            except:
                break
    elif (use_id == 0) and (is_person == 0):
        title = arg2
        movies = ia.search_movie(arg2)
        title_words = title.split()
        title_long = title_words[0]
        for w in range(1,10):
            try:
                title_long += '_' + title_words[w]
            except:
                break
    # Set name
    if (use_id == 1) and (is_person == 1):
        nom = ia.get_person(arg2)['name']
        persons = ia.search_person(nom)
        name_words = nom.split()
        name_long = name_words[0]
        for w in range(1,4):
            try:
                name_long += '_' + name_words[w]
            except:
                break
    elif (use_id == 0) and (is_person == 1):
        persons = ia.search_person(arg2)
        name_words = arg2.split()
        name_long = name_words[0]
        for w in range(1,4):
            try:
                name_long += '_' + name_words[w]
            except:
                break
except  (IMDbError, IMDbDataAccessError) as err:
    print(err)
    sys.exit("Exception instantiating Cinemagoer")

# Set folder name to title or actor name
if is_person == 0:
    movie_id = movies[0].movieID
    print('ID',movie_id)
    imdb_ID = 'tt'+str(movie_id)
    folder = str(title_long)
    image_tag = str(title_long)
    base_url = "https://www.imdb.com/title/" + imdb_ID + "/mediaindex/"
elif is_person == 1:
    person_id = persons[0].personID
    imdb_ID = 'nm'+str(person_id)
    folder = str(name_long)
    image_tag = str(name_long)
    base_url = "https://www.imdb.com/name/" + imdb_ID + "/mediaindex/"
#### End Cinemagoer section


# Create directory based on title or name -jfadams1963
if not os.path.exists(folder):
    os.makedirs(folder)

folder = "./" + folder + "/"
print("Created Directory:", folder)

i = 0 # For indexing individual images -jfadams1963
url = base_url

print()
print("Scraping from:", url)

# use requests.get().content with random user-agent -jfadams1963
with open('user_agents.txt', encoding='utf8') as f:
    user_agent = get_random_line(f)[:-2]

htmldata = requests.get(base_url ,
                        headers = {'user-agent': user_agent},
                        timeout = 30).content

soup = BeautifulSoup(htmldata, 'html.parser')

## 20240607 IMDb changed the gallery page code. Each image now has a srcSet option
## with three different sized images. We parse the choices and select the largest.
## -jfadams1963

# Get a list of all Gallery image links
a_tags = soup.find_all('a')
links = []
for an in a_tags:
    if "image-gallery-image" in str(an):
        links.append(an)

# Print how many images found on current gallery page -jfadams1963
print("Found:", len(links), "images")
# Prompt for how many to download -jfadams1963
image_num_limit = int(input('Number of images to download:'))

if image_num_limit >= len(links):
    print("Will download " + str(len(links)))
else:
    print("Will download " + str(image_num_limit))

# Let's download the largest image from each srcSet
for index, link in enumerate(links):
    i += 1
    if i > image_num_limit:
        sys.exit(0)

    # Find the image element in the anchor
    image_set = link.find('img', {'srcset': True})
    srcset = image_set['srcset']

    # Split the srcSet string into individual entries
    entries = srcset.split(',')

    # Make a Dictionary to hold image URLs and their sizes 
    images = {}
    for entry in entries:
        parts = entry.strip().split(' ')
        if len(parts) == 2:
            url, size = parts
            size = size.replace('x', '')
            images[size] = url

    # Find the largest image (by size)
    largest_size = max(images.keys())
    image_url = images[largest_size]

    print('')
    print('Image no. ' + str(i) + ' of ' + str(image_num_limit))
    if image_url is None:
        print("No image found")
        continue

    # Let's get rid of rediculous file names  -jfadams1963
    # First grab the file's extention.
    extn = image_url.split('.')[-1]
    file_name = folder + image_tag + '_' + str(i) + '.' + extn
    print("Downloading " + image_url)
    print("Renaming to", file_name)

    try:
        ## use requests.get() with random user-agent -jfadams1963
        with open('user_agents.txt', encoding='utf8') as f:
            user_agent = get_random_line(f)[:-2]

        res = requests.get(image_url,
                           params = {'user-agent': user_agent},
                           stream = True, timeout = 30)

        exists = False
        if res.status_code == 200:
            exists = os.path.isfile(file_name)

        g = 0
        while exists:
            print("file exists:", file_name, "renaming...")
            g += 1
            file_name =folder+str(index)+"_"+str(g)+"_"+image_tag+'_'+str(i)+extn
            exists = os.path.isfile(file_name)

        with open(file_name,'wb', encoding=None) as f:
            shutil.copyfileobj(res.raw, f)

        saved = os.path.isfile(file_name)
        if saved:
            print(">>>> ",saved)
            print('Image successfully Downloaded: ',file_name)
        else:
            print("Image Couldn't be retrieved")

    except Exception as e:
        print(e)
