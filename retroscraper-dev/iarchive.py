import apicalls
import re
from bs4 import BeautifulSoup
from urllib import parse

def getFileFromIA(URL,filename,queue):
    romlist = []
    soup = BeautifulSoup(apicalls.simpleCall(URL),features="lxml")
    for a in soup.find_all('a', href=True):
        if a.contents[0]!='View Contents':
            romlist.append((a.contents[0],a['href']))
    downloadURL=''
    for rom in romlist:
        try:
            if filename[:filename.rindex('.')].lower() == rom[0][:rom[0].rindex('.')].lower():
                downloadURL = rom[1]
                break
        except:
            pass
    
    return downloadURL
    

URL = 'https://archive.org/download/redump.3DO.revival'
chkrom = 'Myst (USA).chd'
destdir = '/tmp/'
queue =''
durl = getFileFromIA(URL,chkrom,queue)
if durl !='':
    destfile = destdir+parse.unquote(durl, encoding='utf-8', errors='replace')
    apicalls.download_file(URL+'/'+durl,destfile)