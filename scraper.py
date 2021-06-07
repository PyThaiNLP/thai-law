from ntpath import join
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

path = os.path.join('data','last')

headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}

law_groups = pd.read_csv(os.path.join(path,'law_groups.csv'))

list_law_groups = law_groups['law_group'].to_list()+['others']

list_sysid = []

for i in list_law_groups:
    p = os.path.join(path,'law', i)
    if not os.path.exists(p):
        os.makedirs(p)
    list_sysid+=[".".join(f.split(".")[:-1]) for f in os.listdir(path=p) if os.path.isfile(f)]


def gethtml(sysid):
    return "https://www.krisdika.go.th/librarian/getfile?sysid={sysid}&ext=htm".format(sysid=sysid)

def get_data(sysid):
    r2 = requests.get(gethtml(sysid), verify=False,headers=headers)
    d = r2.content.decode("TIS-620")
    soup = BeautifulSoup(d,'html.parser')
    return soup.text

law_groups = pd.read_csv(os.path.join(path,'law_url_df.csv'))
law_sysid = [(i,j) for i,j in zip(law_groups['sysid'].to_list(),law_groups['law_group'].to_list())]

for i,j in law_sysid:
    if i in list_sysid:
        continue
    p = os.path.join(path,'law', j, str(i)+'.txt')
    with open(p,'w',encoding='utf-8') as f:
        f.write(get_data(str(i)))