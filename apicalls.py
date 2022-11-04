import json
import logging
import os
import platform
import shutil
import sys
from http.client import HTTPConnection
from io import BytesIO
from pathlib import Path
from urllib import parse
from retroscraper import handleImportError
import remote
import requests
try:
    from bs4 import BeautifulSoup
except Exception as e:
    handleImportError(str(e))
    from bs4 import BeautifulSoup
try:
    from PIL import Image
except Exception as e:
    handleImportError(str(e))
    from PIL import Image

from requests import Response as requestsResponse
from requests import exceptions as requestsexceptions
from requests.models import Response as reqResponse


def backendURL():
    #return "http://192.168.8.160"
    return "http://77.68.23.83"

def download_file(url,dest,queue):
 with open(dest, "wb") as f:
    print("Downloading %s" % dest)
    response = requests.get(url, stream=True)
    if response.status_code==200:
        total_length = response.headers.get('content-length')
        if total_length is None: # no content length header
            f.write(response.content)
        else:
            dl = 0
            total_length = int(total_length)
            for data in response.iter_content(chunk_size=4096):
                dl += len(data)
                f.write(data)
                done = int(50 * dl / total_length)
                sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50-done)) )    
                sys.stdout.flush()
            return True
    else:
        return False

def simpleCall(url):
    #logging.debug ('###### CALLING URL '+URL)
    response = ''
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    try:
        #logging.debug ('###### ATCUAL CALL')
        success = False
        retries = 10
        while not success and retries > 1:
            try:
                req = requests.get(url,headers=headers)
                success = True
            except requestsexceptions.Timeout:
                #logging.error ('###### REQUEST TIMED OUT')
                retries = retries - 1 
            except requestsexceptions.TooManyRedirects:
                pass
                #logging.error ('###### URL SEEMS TO BE WRONG '+URL)
            except requestsexceptions.RequestException as e:
                #logging.error ('###### UNHANDLED ERROR '+str(e))
                retries = retries -1
        if req.status_code==200:
            response = req.text
        else:
            response =''
        #logging.debug ('###### GOT A RESPONSE')
        return response
    except Exception as e:
        #logging.error ('###### COULD NOT CALL URL '+str(URL)+' - Error '+str(e))
        return ''


def getSystemsExtensions(sysname):
    myextpage = simpleCall('https://raw.githubusercontent.com/RetroPie/RetroPie-Setup/master/platforms.cfg')
    splitpage = myextpage.split('\n')
    for line in splitpage:
        try:
            chk=line.split('_')[0]
            ext=line.split('=')[1].replace('"','')
            if chk==sysname.lower() and '_ext' in line:
                return ext
                ## DEFAULT EXTENSIONS
        except:
            pass
    return '.zip .ZIP .7z .7Z'

def getImageAPI(config,url,destfile,apikey,uuid,thn,toi,cli,logging,force=False):
    remotefile =''
    if remote.testPathIsRemote(destfile,logging,thn):
        ### THIS IS A REMOTE DESTINATION, NEED TO FIRST DOWNLOAD A TEMP FILE AND THEN COPY
        logging.info ('###### IT IS A REMOTE IMAGE '+destfile+'IN THREAD ['+str(thn)+']')
        remotefile = destfile
        destfile = str(Path.home())+'/.retroscraper/imgtmp/tmp'+toi+str(thn)+'.png'
        logging.info ('###### GOING TO SAVE A TEMPORARY LOCALLY IN '+destfile+'IN THREAD ['+str(thn)+']')
    try:
        if (not force) and (not os.path.isfile(destfile)) and Path(destfile).stat().st_size<2:
            logging.info ('####### NOT DOWNLOADING FILE, IT ALREADY EXISTS THREAD['+str(thn)+']')
            return
    except:
        pass
    myHeader = {"apikey":apikey,"uuid":uuid,"plat":platform.platform(),"User-Agent": "Retroscraper"}
    retries = 10
    finalURL = backendURL()+url
    while retries > 0:
        try:
            logging.info ('###### GOING TO DOWNLOAD IMAGE '+destfile+' WITH URL '+finalURL+'IN THREAD ['+str(thn)+']')
            r = requests.get(finalURL, stream=True, headers=myHeader)
            if r.status_code == 200:
                logging.info ('###### PROPERLY DOWNLADED IMAGE '+destfile+' WITH URL '+finalURL+'IN THREAD ['+str(thn)+']')
                with open(destfile, 'wb') as f:
                    r.raw.decode_content = True
                    if destfile:
                        ### TODO, DISCERN REMOTE FILE TO COPY
                        logging.info ('###### COPYING RAW DATA TO '+destfile+' IN THREAD ['+str(thn)+']')
                        result = shutil.copyfileobj(r.raw, f)
                        logging.info ('###### CREATED IMAGE '+destfile+' WITH RESULT '+str(result)+' IN THREAD ['+str(thn)+']')
                        if remotefile !='':
                            remote.copyToRemote(config,destfile,remotefile,thn,logging)
                            try:
                                logging.info ('###### GOING TO REMOVE '+destfile+' IN THREAD ['+str(thn)+']')
                                if cli or not ('tmpss' in destfile):
                                    os.remove(destfile)
                                logging.info ('###### REMOVED '+destfile+' IN THREAD ['+str(thn)+']')
                                return destfile
                            except:
                                logging.error ('###### COULD NOT REMOVE '+destfile+' IN THREAD ['+str(thn)+']')
                                return ''
                    else:
                        img = Image.open(BytesIO(r.content))
                        logging.info ('###### CREATED IMAGE IN MEMORY IN THREAD ['+str(thn)+']')
                        return img
                if int(Path(destfile).stat().st_size) < 2:
                    finalUrl = backendURL()+'/api/medias/0/noimage.png'
                else:
                    return destfile
            else:
                if ('.png' in url) and r.status_code==404:
                    r = requests.get(backendURL()+'/api/medias/0/noimage.png', stream=True, headers=myHeader)
                    if r.status_code == 200:
                        with open(destfile, 'wb') as f:
                            r.raw.decode_content = True
                            if destfile:
                                shutil.copyfileobj(r.raw, f)
                                return destfile
                            else:
                                img = Image.open(BytesIO(r.content))
                                return img
                    else:
                        return False
                if ('.mp4' in url) and r.status_code==404:
                    return ''
        except Exception as e:
            logging.error ('###### ERROR DOWNLOADING IMAGE '+str(e)+' THREAD['+str(thn)+']')
        retries = retries -1
    return False

def getCallHandler(url,apikey,uuid,thn):
    if 'SHACAUSINGISSUES' in url:
        debug = True
        logging.info ('###### WERE IN THE CASE THREAD['+str(thn)+']')
        HTTPConnection.debuglevel = 1
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True    
    else:
        debug = False
    logging.info ('###### IN GET CALL HANDLER '+str(url)+' THREAD['+str(thn)+']')
    retries = 10
    header = {"apikey":apikey,"uuid":uuid,"plat":platform.platform(),"User-Agent": "Retroscraper"}
    logging.info ('###### USING HEADER '+str(header)+' THREAD['+str(thn)+']')
    while retries > 0:
        try:
            result = requests.get(url, headers=header)
            logging.info('###### RESULT CODE FROM API CALL '+str(result.status_code)+' THREAD['+str(thn)+']')
            if result.status_code==200 or result.status_code == 404:
                try:
                    if debug:
                        logging.warning ('####### RESULT IS  THREAD['+str(thn)+']')
                        logging.warning ('###### '+str(result.text)+' THREAD['+str(thn)+']')
                    jsonr = json.loads(result.text)
                    return result
                except Exception as e:
                    logging.error ('####### THERE IS AN ERROR WITH THE BACKEND JSON '+str(e)+' THREAD['+str(thn)+']')
                    logging.error ('####### '+str(url)+' THREAD['+str(thn)+']')
                    logging.error ('####### '+str(result.text)+' THREAD['+str(thn)+']')
                    logging.error ('####### RETRIES LEFT '+str(retries)+' THREAD['+str(thn)+']')
                    logging.error ('####### REQUEST METHOD '+str(result.request.method)+' THREAD['+str(thn)+']')
                    logging.error ('####### REQUEST HISTORY '+str(result.history[0].request.method)+' THREAD['+str(thn)+']')
                    retries = retries -1
            else:
                if result.status_code == 403:
                    logging.error ('###### GOT RESULT '+str(result.status_code)+' FROM SERVER FOR '+str(url)+' THREAD['+str(thn)+']')
                    myResponse = requestsResponse()
                    myResponse.status_code=403
                    type(myResponse).text='{"response":{"error":"Not authorized to use API"}}'
                    return myResponse
                else:
                    logging.error ('###### GOT RESULT '+str(result.status_code)+' FROM SERVER FOR '+str(url)+' THREAD['+str(thn)+']')
        except:
            retries = retries -1
    
    
    
    myResponse = requestsResponse()
    myResponse.status_code=404
    mytext = '{"response":{"error":"cannot read from API","url":"'
    mytext = mytext + str(url)
    mytext = mytext + '"}}'
    logging.info ('######+++++++ '+str(mytext)+' THREAD['+str(thn)+']')
    type(myResponse).text=mytext
    return myResponse

def postCallHandler(url,apikey,uuid,data,logging,thn):
    logging.info ('###### IN POST CALL HANDLER '+str(url))
    header = {"apikey":apikey,"uuid":uuid,"plat":platform.platform(),"User-Agent": "Retroscraper"}
    retries = 10
    while retries > 0:
        try:
            data = data.encode(encoding='utf-8')
            result = requests.post(url, headers=header,data=data)
            logging.info ('###### SUBMITTED TO BACKEND AND GOT STATUS CODE '+str(result.status_code)+' THREAD['+str(thn)+']')
            if result.status_code==200 or result.status_code == 404:
                return result
            if result.status_code==405:
                logging.error ('###### GOT AN ERROR '+str(result.content))
                retries = retries -1
        except Exception as e:
            logging.error('####### POST REQUEST ERRORED '+str(e))
            retries = retries -1
    myResponse = None
    myResponse = requestsResponse()
    myResponse.status_code=404
    type(myResponse).text='{"response":{"error":"cannot send to API"}'
    return myResponse

def getVersion(apikey,uuid,thn):
    url = backendURL()+'/api/version'
    myVersion = getCallHandler(url,apikey,uuid,thn)
    if myVersion.status_code == 200:
        return myVersion.json()
    else:
        return '{"response":{"version":"error"}}'

def getLanguagesFromAPI(apikey,uuid,thn):
    url = backendURL()+'/api/translations.json'
    result = getCallHandler(url, apikey,uuid,thn)
    if result.status_code != 200:
        return []
    else:
        return result.json()['translations']

def getSystemsFromAPI(apikey,uuid,thn):
    url = backendURL()+'/api/systems'
    result = getCallHandler(url, apikey,uuid,thn)
    if result.status_code != 200:
        return []
    else:
        return result.json()['response']

def getCompaniesFromAPI(apikey,uuid,thn):
    url = backendURL()+'/api/companies'
    result = getCallHandler(url, apikey,uuid,thn)
    if result.status_code == 404:
        return []
    else:
        return result.json()['response']

def getAllGames(sysid,apikey,uuid,thn):
    url = backendURL()+'/api/system/'+str(sysid)
    result = getCallHandler(url, apikey,uuid,thn)
    if result.status_code != 200:
        return []
    else:
        return result.json()['Games']

def getGame(gameid,apikey,uuid):
    url = backendURL()+'/api/id/'+str(gameid)
    result = getCallHandler(url, apikey,uuid)
    if result.status_code != 200:
        return []
    else:
        return result.json()['response']

def getSHA1(sha1,apikey,uuid,thn):
    logging.info ('###### GETTING BY SHA1 THREAD['+str(thn)+']')
    url = backendURL()+'/api/sha1/'+sha1
    return getCallHandler(url, apikey,uuid,thn)

def getCRC(crc,apikey,uuid,thn):
    logging.info ('###### GETTING BY CRC THREAD['+str(thn)+']')
    url = backendURL()+'/api/crc/'+crc
    return getCallHandler(url, apikey,uuid,thn)

def getMD5(md5,apikey,uuid,thn):
    logging.info ('###### GETTING BY MD5 THREAD['+str(thn)+']')
    url = backendURL()+'/api/md5/'+md5
    return getCallHandler(url, apikey,uuid,thn)

def getSearch(thissys,partname, apikey,uuid,thn):
    logging.info ('###### GETTING BY SEARCH '+str(partname)+' THREAD['+str(thn)+']')
    url = backendURL()+'/api/search/'+thissys+'/'+partname
    return getCallHandler(url, apikey,uuid,thn)

def getDownSites(apikey,uuid,thn):
    response = getURL('/api/archive.json',apikey,uuid,thn)
    return response.json()

def getURL(URL, apikey,uuid,thn):
    url = backendURL()+URL
    return getCallHandler(url, apikey,uuid,thn)

def postSubmit (subJson,apikey,uuid,logging,thn):
    url = backendURL()+'/api/submit'
    return postCallHandler(url,apikey,uuid,subJson,logging,thn)

def downloadRom (URL,destpath,romname,thn):
    downURL = getFileFromIA(URL,romname)
    if downURL:
        destfile = destpath+parse.unquote(downURL, encoding='utf-8', errors='replace')
        result = download_file(URL+'/'+downURL,destfile,None,thn)
        return destfile

    
def getFileFromIA(URL,filename,thn):
    romlist = []
    soup = BeautifulSoup(simpleCall(URL,thn),features="lxml")
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
