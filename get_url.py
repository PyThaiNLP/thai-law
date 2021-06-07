#!/usr/bin/env python
# coding: utf-8

# In[467]:


import numpy as np
import pandas as pd
pd.set_option('display.max_colwidth', -1)
from tqdm.auto import tqdm

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import warnings
warnings.filterwarnings('ignore')


chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

import os
f=os.path.join("data","last/")
if not os.path.exists(f):
    os.makedirs(f)

# ## [Thai Annotated Code](https://www.krisdika.go.th/web/guest/thai-code-annotated)

# ### Get Law Groups

# In[269]:


#get law groups
driver = webdriver.Chrome("/usr/lib/chromium-browser/chromedriver",chrome_options=chrome_options)
driver.get('https://www.krisdika.go.th/web/guest/thai-code-annotated')
soup = BeautifulSoup(driver.page_source)
driver.close()

law_groups = pd.DataFrame([i.text for i in soup.find_all('a',class_='ksdk-theme-bg-third-color')])
law_groups['law_group'] = law_groups[0].map(lambda x: x.split('(')[0][:-1])
law_groups['nb_laws'] = law_groups[0].map(lambda x: int(x.split('(')[1][:-1]))
law_groups['nb_pages'] = np.ceil(law_groups['nb_laws']/10).astype(int)
law_groups = law_groups.drop(0,1)
#law_groups.to_csv('data/last/law_groups.csv',index=False)
law_groups


# ## Get Law URLs and Sub-law Lists

# In[612]:


def get_law_urls(law_group, nb_pages):
    #open list page
    driver = webdriver.Chrome("/usr/lib/chromium-browser/chromedriver",chrome_options=chrome_options)
    driver.get('https://www.krisdika.go.th/web/guest/thai-code-annotated')
    #click law group
    link = driver.find_element_by_partial_link_text(law_group)
    link.click()
    
    #check if max pagination button appeared
    try:
        element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.LINK_TEXT, str(nb_pages)))
        )
    except:
        print('Max pagination button not found')
    
    #get law _urls
    laws = []
    law_urls = []
    sub_law_urls = []
    for nb_page in tqdm(range(1, nb_pages+1)):
        link = driver.find_element_by_link_text(str(nb_page))
        link.click()
        soup = BeautifulSoup(driver.page_source)
        laws+=[i.text for i in soup.find_all('li', class_='thca-list-law-name')]
        law_urls+=[i.find_all('li')[-1].find('a').get('href') for i in soup.find_all('ul', class_='thca-list-icon')]
        sub_law_soup = [i for i in soup.find_all('li', class_='thca-list-sub-law') if i.find('a').text=='แสดงสารบัญลูกบทตามสารบัญกฎหมาย']
        sub_law_urls+=[i.find('a').get('href') for i in sub_law_soup]
        
    #close driver
    driver.close()
    
    #summarize to df
    df = pd.DataFrame({'title':laws, 'law_url':law_urls, 'sub_law_url':sub_law_urls})
    df['sysid'] = df.law_url.map(lambda x: x.split('=')[-2].split('&')[0])
    df['law_group'] = law_group
    return df


# In[616]:


dfs = []
for row in tqdm(law_groups.iloc[20:,:].itertuples(index=False)):
    print(row[0])
    df = get_law_urls(row[0],row[2])
    dfs.append(df)


# In[618]:


law_url_df = pd.concat(dfs)
law_url_df


# In[619]:


#designate law types
law_types = ['รัฐธรรมนูญ', 'พระราชบัญญัติ', 'พระราชกำหนด','ประมวลกฎหมาย', 'ประมวลรัษฎากร','ประกาศ','คำสั่ง','พระธรรมนูญ']

def get_law_type(law_name, law_types=law_types, max_char=13):
    for l in law_types:
        if l in law_name[:max_char]:
            return l
    return 'others'

law_url_df['law_type'] = law_url_df.title.map(get_law_type)
law_url_df.law_type.value_counts()


# In[620]:


law_url_df[['sysid','law_type']].drop_duplicates().law_type.value_counts()


# In[621]:


# law_url_df.to_csv('data/v0.3/law_url_df.csv',index=False)
law_url_df = pd.read_csv('data/last/law_url_df.csv')
law_url_df


# In[622]:


law_groups.nb_laws.sum()


# ### Get All Law URLs and Sub-law URLs

# In[891]:


def get_law_items(url):
    #open url
    driver = webdriver.Chrome("/usr/lib/chromium-browser/chromedriver",chrome_options=chrome_options)
    driver.get(url)

    #display 100 items
    #check if max pagination button appeared
    try:
        element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'dhxtoolbar_text'))
        )
    except:
        print('Pagination button not found')
    
    #change pagination to max display per page
    links = driver.find_elements_by_class_name('dhxtoolbar_text')
    links[-1].click()
    links = driver.find_elements_by_class_name('btn_sel_text')
    links[-1].click()

    #expand first one
    link = driver.find_element_by_class_name('grid_collapse_icon')
    link.click()

    #expand the rest
    links = driver.find_elements_by_class_name('grid_collapse_icon')
    for l in links[1:]:
        #some are unclickable
        try:
            l.click()
        except:
            pass

    #get all sublaws
    soup = BeautifulSoup(driver.page_source)
    evs = soup.find_all('tr',class_='ev_material')
    odds = soup.find_all('tr',class_='odd_material')
    
    #close
    driver.close()

    #put into df
    ds = []
    for i in evs:
        item_name = i.text
        if item_name[-1]=='\xa0': continue
        item_url = i.find('a').get('href')
        ds.append((item_name, item_url, url))
    for i in odds:
        item_name = i.text
        if item_name[-1]=='\xa0': continue
        item_url = i.find('a').get('href')
        ds.append((item_name, item_url, url))

    return ds


# In[824]:


#deduplicate by sub_law_url
law_url_df = pd.read_csv('data/last/law_url_df_new.csv')
law_url_dedup = law_url_df.groupby('sub_law_url').title.max().reset_index()
law_url_dedup


# In[909]:


# ds = []
# for url in tqdm(law_url_dedup[law_url_dedup.law_group=='ทรัพย์สินทางปัญญา'].sub_law_url):
#     ds+=get_law_items(url)

ds = []
for url in tqdm(law_url_dedup.sub_law_url):
    ds+=get_law_items(url)
    
d = pd.DataFrame(ds)
d.columns = ['item_name','item_url','sub_law_url']
d


# In[930]:


#attach title of main law
res = d.merge(law_url_dedup, on='sub_law_url',how='left')
res['sysid'] = res.item_url.map(lambda x: x.split('sysid=')[-1][:-8])
res = res[['title','sub_law_url','sysid','item_name','item_url']]

#there are duplicates for law updates
#sysid 0 is when there is no data available
res.shape, res.sysid.nunique()


# In[932]:


# res.to_csv('data/v0.3/law_item_urls.csv',index=False)
res = pd.read_csv('data/last/law_item_urls_new.csv')
res.shape


# In[ ]:




