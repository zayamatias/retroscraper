import logging
import requests
from requests import exceptions as requestsexceptions
from requests import Response as requestsResponse
import shutil
from PIL import Image
from io import BytesIO
import platform
from pathlib import Path
import os
import sys

def backendURL():
    #return "http://192.168.8.160/"
    return "http://77.68.23.83/"

def download_file(url,dest,queue):
 with open(dest, "wb") as f:
    print("Downloading %s" % dest)
    response = requests.get(url, stream=True)
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


def getImageAPI(url,destfile,apikey,uuid,force=False):
    try:
        if (not force) and (not os.path.isfile(destfile)) and Path(destfile).stat().st_size<2:
            logging.info ('####### NOT DOWNLOADING FILE, IT ALREADY EXISTS')
            return
    except:
        pass
    myHeader = {"apikey":apikey,"uuid":uuid,"plat":platform.platform(),"User-Agent": "Retroscraper"}
    retries = 10
    finalURL = backendURL()+url
    while retries > 0:
        try:
            r = requests.get(finalURL, stream=True, headers=myHeader)
            if r.status_code == 200:
                with open(destfile, 'wb') as f:
                    r.raw.decode_content = True
                    if destfile:
                        shutil.copyfileobj(r.raw, f)
                    else:
                        img = Image.open(BytesIO(r.content))
                        return img
                if int(Path(destfile).stat().st_size) < 2:
                    finalUrl = backendURL()+'/api/medias/0/noimage.png'
                else:
                    return True
            else:
                if ('.png' in url) and r.status_code==404:
                    r = requests.get(backendURL()+'/api/medias/0/noimage.png', stream=True, headers=myHeader)
                    if r.status_code == 200:
                        with open(destfile, 'wb') as f:
                            r.raw.decode_content = True
                            if destfile:
                                shutil.copyfileobj(r.raw, f)
                                return True
                            else:
                                img = Image.open(BytesIO(r.content))
                                return img
                    else:
                        return False
                if ('.mp4' in url) and r.status_code==404:
                    return False
        except Exception as e:
            logging.error ('###### ERROR DOWNLOADING IMAGE '+str(e))
            #print ('###### ERROR DOWNLOADING IMAGE '+str(e))
        retries = retries -1
    return False



def getCallHandler(url,apikey,uuid):
    retries = 50
    success = False
    header = {"apikey":apikey,"uuid":uuid,"plat":platform.platform(),"User-Agent": "Retroscraper"}
    while retries > 0:
        try:
            result = requests.get(url, headers=header)
            if result.status_code==200 or result.status_code == 404:
                try:
                    jsonr = result.json()
                    return result
                except:
                    logging.eror ('####### THERE IS AN ERROR WITH TEH BACKEND JSON')
            else:
                if result.status_code == 403:
                    myResponse = requestsResponse()
                    myResponse.status_code=403
                    type(myResponse).text='{"response":{"error":"Not authorized to use API"}}'.encode('utf-8')
                    return myResponse
                else:
                    logging.info ('###### GOT RESULT '+str(result.status_code)+' FROM SERVER')
        except:
            retries = retries -1
    myResponse = requestsResponse()
    myResponse.status_code=404
    type(myResponse).text='{"response":{"error":"cannot read from API","url":'+url+'}}'.encode('utf-8')
    return myResponse

def postCallHandler(url,apikey,uuid,data):
    header = {"apikey":apikey,"uuid":uuid,"plat":platform.platform(),"User-Agent": "Retroscraper"}
    retries = 10
    while retries > 0:
        try:
            result = requests.post(url, headers=header,data=data)
            if result.status_code==200 or result.status_code == 404:
                return result
        except:
            retries = retries -1
    myResponse = requestsResponse()
    myResponse.status_code=404
    type(myResponse).text='{"response":{"error":"cannot send to API"}'.encode('utf-8')
    return myResponse

def getVersion(apikey,uuid):
    url = backendURL()+'/api/version'
    myVersion = getCallHandler(url,apikey,uuid)
    if myVersion.status_code == 200:
        return myVersion.json()
    else:
        return '{"response":{"version":"error"}}'

def getLanguagesFromAPI(apikey,uuid):
    url = backendURL()+'/api/translations.json'
    result = getCallHandler(url, apikey,uuid)
    if result.status_code != 200:
        return []
    else:
        return result.json()['translations']

def getSystemsFromAPI(apikey,uuid):
    url = backendURL()+'/api/systems'
    result = getCallHandler(url, apikey,uuid)
    if result.status_code != 200:
        return []
    else:
        return result.json()['response']

def getCompaniesFromAPI(apikey,uuid):
    url = backendURL()+'/api/companies'
    result = getCallHandler(url, apikey,uuid)
    if result.status_code == 404:
        return []
    else:
        return result.json()['response']

def getAllGames(sysid,apikey,uuid):
    url = backendURL()+'/api/system/'+str(sysid)
    result = getCallHandler(url, apikey,uuid)
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

def getSHA1(sha1,apikey,uuid):
    logging.info ('###### GETTING BY SHA1')
    url = backendURL()+'/api/sha1/'+sha1
    return getCallHandler(url, apikey,uuid)

def getCRC(crc,apikey,uuid):
    logging.info ('###### GETTING BY CRC')
    url = backendURL()+'/api/crc/'+crc
    return getCallHandler(url, apikey,uuid)

def getMD5(md5,apikey,uuid):
    logging.info ('###### GETTING BY MD5')
    url = backendURL()+'/api/md5/'+md5
    return getCallHandler(url, apikey,uuid)

def getSearch(thissys,partname, apikey,uuid):
    logging.info ('###### GETTING BY SEARCH '+str(partname))
    url = backendURL()+'/api/search/'+thissys+'/'+partname
    return getCallHandler(url, apikey,uuid)

def getURL(URL, apikey,uuid):
    url = backendURL()+URL
    return getCallHandler(url, apikey,uuid)

def postSubmit (subJson,apikey,uuid):
    url = backendURL()+'/api/submit'
    return postCallHandler(url,apikey,uuid,subJson)

