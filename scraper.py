import numpy as np
import pandas as pd
import requests
import json
import re

from datetime import datetime
from bs4 import BeautifulSoup

# loading urls from json file
with open('utils\\urls.json') as json_file:
    url_dict = json.load(json_file)

##### ------------------------------------------------- #####
##### ----------     Scraping Data Table     ---------- #####
##### ------------------------------------------------- #####

# souping url html from table
source = requests.get(url_dict['table']).text
soup = BeautifulSoup(source, 'lxml')

##### ---------- Table Header ---------- #####

table_head = soup.find('thead')

date_list = []
poll_list = []

for head in table_head.find_all('th')[1:]:
    head_list = head.text.split('Poll by ')

    date_list.append(head_list[0])
    poll_list.append(head_list[1])

##### ----------- Table Body ----------- #####

table_body = soup.find('tbody')

data_list = []

for cell in table_body.find_all('td'):
    data_list.append(cell.text)

remn_list, leav_list, unde_list = np.array_split(data_list, 3)


##### ------------------------------------------------- #####
##### ----------     Scraping Data Notes     ---------- #####
##### ------------------------------------------------- #####

FROM_PATTERN_1 = re.compile('(?<=Data from:)(.*)(?=Notes)')
FROM_PATTERN_2 = re.compile('(?<=Data from:)(.*)(?=Pollster)')
MTHD_PATTERN = re.compile('(?<=Data collection mode)(.*)(?=Sample Size)')
SIZE_PATTERN = re.compile('(?<=Sample Size)[0-9]*')


# souping url html from notes
source = requests.get(url_dict['notes']).text
soup = BeautifulSoup(source, 'lxml')

##### ------- Side-Bar Meta Info ------- #####

from_list = []
mthd_list = []
size_list = []

for div in soup.find_all('div', class_='well'):

    if 'Notes' in div.text:
        from_ = FROM_PATTERN_1.search(div.text)[0]
    else:
        from_ = FROM_PATTERN_2.search(div.text)[0]

    mthd = MTHD_PATTERN.search(div.text)[0]
    size = SIZE_PATTERN.search(div.text)[0]
    
    # appending lists
    from_list.append(from_)
    mthd_list.append(mthd)
    size_list.append(size)


# creating dataframe
df = pd.DataFrame(list(zip(
                  date_list,
                  poll_list,
                  remn_list,
                  leav_list,
                  unde_list,
                  from_list,
                  mthd_list,
                  size_list
                 )))

# adding columns names
column_names = ['date', 'pollster', 'remain', 'leave', 'undecided', 'data_from', 'method', 'sample_size']
df.columns = column_names

# cleaning date variable
df.date = df.date.apply(lambda date_str : datetime.strptime(date_str, '%d %B %Y'))

# cleaning data variables
for col_name in ['remain', 'leave', 'undecided']:
    df[col_name] = df[col_name].apply(lambda pct_str : int(pct_str.replace('%', '')) / 100)

# sorting dataframe correctly
df = df.sort_index(ascending=False, axis=0).reset_index().drop('index', axis=1)

# saving dataframe to csv
df.to_csv('utils\\poll_data.csv')

print('Data scraped, cleaned, and saved successfully!')
