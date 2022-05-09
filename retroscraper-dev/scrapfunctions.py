from re import findall,sub,search
from xml.sax.saxutils import escape
from sys import exit as sysexit
from numpy import save
from checksums import getChecksums
from shutil import copyfile,rmtree
import apicalls
from os import path as ospath
from os import makedirs,remove,mkdir
from json import dumps as jsondumps
from json import loads as jsonloads
from uuid import getnode
import xml.etree.ElementTree as ET
from queue import Queue
from threading import Thread
from time import sleep
from googletrans import Translator
from pathlib import Path as Path

def getArcadeName(name):
    if '.' in name:
        name=name[:name.rindex('.')]
    callURL = 'http://www.mamedb.com/game/'+name+'.html'
    callURL2 = 'http://mamedb.blu-ferret.co.uk/game/'+name+'/'
    callURL3 = 'http://adb.arcadeitalia.net/dettaglio_mame.php?game_name=' + name
    #print ('###### GETTING ARCADE NAME IN URL '+callURL)
    response = apicalls.simpleCall(callURL)
    if response!= '':
        gamename = findall("<title>(.*?)<\/title>", response)[0].replace('Game Details:  ','').replace(' - mamedb.com','')
        return gamename
    #print('###### COULD NOT GET ARCADE NAME FROM MAMEDB')
    #print('RESOPONSE='+str(response)+']')
    #logging.debug('###### TRYING WITH BLU FERRET IN URL '+callURL2)
    response = apicalls.simpleCall(callURL2)
    if response !='':
        gamename = findall("\<title\>Game Details:  (\w*).*\<\/title\>", response[0])
        return gamename
    #print ('###### COULD NOT GET NAME FROM BLU FERRET')
    #logging.debug('###### TRYING WITH ARCADE ITALIA IN URL '+callURL3)
    response = apicalls.simpleCall(callURL3)
    if response != '':
        gamename = findall("<title>(.*?)<\/title>", response)[0].replace(' - MAME machine','').replace(' - MAME software','')
        gamename = gamename.replace(' - MAME machin...','')
    if gamename.upper()=='ARCADE DATABASE':
        #print('###### COULD NOT GET NAME FROM ARCADE ITALIA')
        gamename = ''
    #logging.info ('###### FOUND GAME IN ARCADEITALIA '+gamename)
    return gamename

def getInfoFromAPI(system,filename,sha1,md5,crc,apikey,uuid):
    filename = filename.replace ('\\','/')
    filename = filename[filename.rindex('/')+1:]
    result = apicalls.getSHA1(sha1, apikey,uuid)
    nosha = False
    if result.status_code == 404:
        nosha = True
        result = apicalls.getCRC(crc, apikey,uuid)
        if result.status_code == 404:
            result = apicalls.getMD5(md5, apikey,uuid)
            if result.status_code == 404:
                ### remove both lines below
                fname = filename[:filename.rindex('.')]
                if 75 in system:
                    #print ('going for arcadename')
                    arcadeName = getArcadeName(filename)
                    #print (arcadeName)
                    if arcadeName == '' or not arcadeName:
                        arcadeName = fname
                    try:
                        partnames = sub('[^A-Za-z0-9]+',' ',arcadeName).lower().split()
                    except Exception as e:
                        print ('###### ERROR WHEN GETTING ARCADE NAME '+str(arcadeName)+' ->'+str(e)+' in file '+str(fname))
                        sysexit()

                else:
                    partnames =  sub('[^A-Za-z0-9]+',' ',fname).lower().split()
                exclude_words = ['trsi','bill','sinclair','part','tape','gilbert','speedlock','erbesoftwares','aka','erbe','iso','psn','soft','crack','dsk','release','z80','2000','2001','2002','2003','2004','2005','2006','2007','2008','2009','2010','2011','2012','2013','2014','2015','2016','2017','2018','2019','2020','prototype','pirate','world','fre','h3c','jue','edition','c128','unl','1983','1984','ltd','side','1985','1986','1987','software','disabled','atx','bamcopy','playable','data','boot','xenophobia','code','dump','compilation','cd1','cd2','cd3','cd4','paradox','19xx','1988','1989','1990','1991','1992','1993','1994','1995','1996','manual','csl','defjam','files','pdx','doscopy','bootable','cracktro','flashtro','flt','checksum','error','qtx','aga','corrupt','disk1','disk2','disk3','disk4','disk5','disk6','italy','spain','psx','disc','demo','rev','slus','replicants','germany','france','start','tsth','patch','newgame','sega','beta','hack','rus','h1c','h2c','the','notgame','zzz','and','pal','ntsc','disk','file','inc','fullgame','48k','128k','16k','tap','tzx','usa','japan','europe','d64','t64','c64']
                sfname = sub("[\(\[].*?[\)\]]", "", fname)
                sfname = sfname.replace('_',' ').strip()
                for thissys in system:
                    for partname in partnames:
                        if len(partname)>3 and not (partname.lower() in exclude_words) :
                            result = apicalls.getSearch(str(thissys),partname, apikey,uuid)
                            if result.status_code !=404:
                                try:
                                    myresults = result.json()['response']['results']
                                except Exception as e:
                                    print ('ERROR IN JSON RECEIVED FROM BACKEND '+str(thissys)+' SEARCHING FOR '+partname)
                                    print (str(result.content))
                                    print ('ERROR '+str(e))
                                    continue
                                for searchable in myresults:
                                    if sfname.lower() == searchable['name']['text'].lower():
                                        result = apicalls.getURL(searchable['gameURL'], apikey,uuid)
                                        submitJson = '{"request": {"type": "romnotincluded","data": {"gameUrl":"'+searchable['gameURL']+'","systemid": "'+str(system)+'","filename": "'+filename+'","match":"'+fname+'","SHA1": "'+sha1+'","MD5": "'+md5+'","CRC": "'+crc+'"}}}'
                                        subresult = apicalls.postSubmit (submitJson,apikey,uuid)
                                        return result.json()['response']
                submitJson = '{"request": {"type": "norom","data": {"systemid": "'+str(system)+'","filename": "'+filename+'","SHA1": "'+sha1+'","MD5": "'+md5+'","CRC": "'+crc+'"}}}'
                result = apicalls.postSubmit (submitJson,apikey,uuid)
                response = {"game": {"ratings": [], "dates": [], "names": [{'text':filename,'region':'default'}], "roms": [], "cloneof": "0", "genres": [],\
                            "notgame": "false", "system": {"url": "/api/system/"+str(system[0]), "id": int(system[0])}, "players": {"text": "Unknown"},\
                            "synopsis": [{"text":"Could not find Synopsis","language":"en"}], "editor": {}, "medias": [], "developer": {}, "id":0,\
                            "modes": []}}
                return response
            else:
                nosha=True
        else:
            nosha=True
    try:
        response = result.json()['response']
        if nosha:
            try:
                gameid = str(response['game']['id'])
            except:
                gameid = '1'
            submitJson = '{"request": {"type": "nosha","data": {"gameid":"'+gameid+'","systemid": "'+str(system)+'","filename": "'+filename+'","SHA1": "'+sha1+'","MD5": "'+md5+'","CRC": "'+crc+'"}}'
            subresult = apicalls.postSubmit (submitJson,apikey,uuid)
    except Exception as e:
        print ('GETTING INFO FROM API: '+str(result.json())+' ERROR '+str(e))
        print (system,filename,sha1,md5,crc)
        response = None
        #sysexit()
    return response

def isValidVersion(appVer,apikey,uuid):
    verJson = apicalls.getVersion(apikey,uuid)
    try:
        reqVer = verJson['response']['version']
    except:
        reqVer = '9999999999999999'
    return (appVer==reqVer)

def getUniqueID():
    return ''.join(findall('..', '%012x' % getnode())).upper()

def loadConfig(logging,q):
    config = dict()
    config['config']=dict()
    config['config']["SystemsFile"]=""
    config['config']["MountPath"]=""
    config['decorators']=dict()
    logging.info ('###### SETTING UP ')
    homedir = str(Path.home())+'/.retroscraper/'
    if not ospath.isdir(homedir):
        try:
            makedirs(homedir)
            logging.info ('####### CREATED HOMEDIR DIRECTORY')
        except Exception as e:
            logging.error ('###### ERROR SAVING CONFIG IN '+str(homedir)+'  ERROR '+str(e))
            q.put('CONFIG ERROR!','popup','I CANNOT CREATE A CONFIG FILE '+str(e))
            return config
    configfilename= homedir+'retroscraper.cfg'
    if not ospath.isfile(configfilename):
        try:
            logging.info ('###### CONFIG FILE DOES NOT EXIST, CREATING ONE')
            f = open(configfilename, "w")
            logging.info ('###### CONFIG FILE DOES NOT EXIST, CREATED ONE')
            f.write(jsondumps(config))
            logging.info ('###### CONFIG FILE DOES NOT EXIST, CLOSING ONE')
            f.close()
            return config
        except Exception as e:
            q.put('CONFIG ERROR!','popup','I CANNOT CREATE A CONFIG FILE '+str(e))
            return config
            
    logging.info ('###### READING CONFIG FILE')
    f = open(configfilename, "r")
    try:
        logging.info ('###### READING CONFIG FILE INTO JSON')
        configret = jsonloads(f.read())
        logging.info ('###### SUCCESS')
        f.close()
    except Exception as e:
        logging.info ('###### FAILURE, CREATING EMPTY CONFIG')
        configret = dict()
        configret['config']=dict()
        f.close()
        saveConfig(configret,q)
    logging.info ('###### RETURNING CONFIG')
    return configret

def saveConfig(config,q):
    homedir = str(Path.home())+'/.retroscraper/'
    configfilename= homedir+'retroscraper.cfg'
    try:
        f = open(configfilename, "w")
        f.write(jsondumps(config))
        f.close()
    except Exception as e:
        q.put('CONFIG ERROR!','popup','I CANNOT CREATE A CONFIG FILE '+str(e))
        return config
    return

def processBezels(bezelURL, destbezel, apikey, uuid,filename,path,logging):
    logging.info ('+++++++==========###### PROCESS BEZEL FOR '+filename+' LOCATED AT '+path)
    logging.info ('###### DOWNLOADING BEZELS ')
    logging.info ('###### '+destbezel)
    destbezel = destbezel.replace('\\','/')
    path = path.replace('\\','/')
    filename = filename.replace('\\','/')
    bezeldir = destbezel[:destbezel.rindex('/')]
    if not ospath.isdir(bezeldir):
        makedirs(bezeldir)
    apicalls.getImageAPI(bezelURL,destbezel,apikey,uuid)
    zipname = filename[filename.rfind('/')+1:]
    logging.info ('###### ZIPNAME IS '+zipname)
    bezelcfg = path+'/'+zipname+'.cfg'
    logging.info ('###### BEZELCFG IS '+bezelcfg)
    bzlfile,bzlext = ospath.splitext (zipname)
    romcfg = bzlfile+'.cfg'
    logging.info ('###### ROMCFG IS '+romcfg)
    romcfgpath = bezeldir+'/'+romcfg
    logging.info ('###### ROMCFGPATH IS '+romcfgpath)
    f = open(bezelcfg, "w")
    f.write('input_overlay = "'+ bezeldir+'/'+romcfg+'"\n')
    f.close
    f = open(romcfgpath, "w")
    f.write('overlays = "1"\noverlay0_overlay = "'+destbezel+'"\noverlay0_full_screen = "true"\noverlay0_descs = "0"\n')
    f.close

def loadSystems(config,apikey,uuid,remoteSystems,q,trans,logging):
    ### LOAD SYSTEMS INTO MEMORY
    try:
        logging.info ('###### READING FROM '+config['config']['SystemsFile'])
    except:
        logging.error ('###### CONFIG SYSTEMSFILE IS EMPTY!!!')
        return []
    tree = ET.ElementTree()
    logging.info ('###### OPENING FILE')
    with open(config['config']['SystemsFile'], 'r') as xml_file:
        logging.info ('###### OPENED FILE')
        try:
            logging.info ('###### PARSING FILE')
            tree.parse(xml_file)
            logging.info ('###### PARSED FILE')
        except:
            logging.info ('###### ERROR IN THE XML, MAYBE 3 BYTES FOR UTF?')
            xml_file.seek(3)
            try:
                logging.info ('###### PARSING FILE ONE MORE TIME')
                tree.parse(xml_file)
                logging.info ('###### PARSED FILE')
            except:
                logging.error ('###### DEFINITELY BAD XML!')
                #q.put([trans['xmlerr'],'popup',trans['xmlerrmsg']])
                return 'XMLERROR'
    try:
        logging.info ('###### GETTING ROOT ELEMENT')
        root = tree.getroot()
        logging.info ('###### GOT ROOT ELEMENT')
        systems=[]
        for child in root:
            logging.info ('###### DOING CHILD '+child.tag.lower())
            if child.tag.lower() == 'system':
                logging.info ('###### IT IS A SYSTEM TAG - CREATE NEW DICT')
                mySystem=dict()
                logging.info ('###### IT IS A SYSTEM TAG - GIVE IT EMPTY ID')
                mySystem['id']=[]
                logging.info ('###### ITERATING THROUGH CHILDS')
                for xmlSystem in child:
                    try:
                        logging.info ('###### GET SYSTEM INFO')
                        mySystem[xmlSystem.tag.lower()]=xmlSystem.text
                    except Exception as e:
                        print('CANNOT GET TAG NAME '+str(e))
                        pass
                    logging.info ('###### GOT SYSTEM TAG ['+xmlSystem.tag.lower()+']')
                    if str(xmlSystem.tag.upper())=='NAME':
                        logging.info ('###### STARTING SYSTEM ==================================================')
                        logging.info ('###### GOT SYSTEM NAME - WILL TRY TO MATCH IT')
                        for rSystem in remoteSystems['systems']:
                            try:
                                logging.info ('###### GOT NAMES '+str(rSystem['lookupnames']))
                            except:
                                pass
                            for sysname in rSystem['lookupnames']:
                                try:
                                    if xmlSystem.text.upper() == sysname.upper():
                                        mySystem['id'].append(rSystem['id'])
                                        break
                                except:
                                    pass
                if 'path' in mySystem.keys():
                    ### TODO DISTINCT WINDOWS OR LINUX
                    if mySystem['path'][-1] != '/':
                        mySystem['path']=mySystem['path']+'/'
                if mySystem['id']:
                    systems.append(mySystem)
                    logging.info('###### FOUND '+str(jsondumps(systems)))
                else:
                    q.put(['errorlabel','text',trans['unksystem']+' '+str(mySystem['name'])])
    except Exception as e:
        print ('CANNOT PARSE XML '+str(e))
        systems=[]
    return systems

def loadCompanies(apikey,uuid):
    externalCompanies = apicalls.getCompaniesFromAPI(apikey,uuid)
    companies = dict()
    for thisCompany in externalCompanies['companies']:
        companies[str(thisCompany['id'])]=thisCompany['text']
    return companies

def multiDisk(filename):
    checkreg = '\([P|p][A|a][R|r][T|t][^\)]*\)|\([F|f][I|i][L|l][E|e][^\)]*\)|\([D|d][I|i][S|s][K|k][^\)]*\)|\([S|s][I|i][D|d][E|e][^\)]*\)|\([D|d][I|i][S|s][C|c][^\)]*\)|\([T|t][A|a][P|p][E|e][^\)]*\)'
    matchs = search(checkreg,filename)
    return matchs

def multiHack(filename):
    checkreg = '\(.*[H|h][A|a][C|c][K|k][^\)]*\)|\(.*[B|b][E|e][T|t][A|a][^\)]*\)'
    matchs = search(checkreg,filename)
    return matchs

def multiCountry(filename):
    checkreg = '\([E|e][U|u][R|r][O|o][P|p][E|e][^\)]*\)|\([U|u][S|s][A|a][^\)]*\)|\([J|j][A|a][P|p][A|a][N|n][^\)]*\)|\([E|e][U|u][R|r][A|a][S|s][I|i][A|a][^\)]*\)'
    matchs = search(checkreg,filename)
    if not matchs:
        checkreg = '\([S|s][P|p][A|a][I|i][N|n][^\)]*\)|\([F|f][R|r][A|a][N|n][C|c][E|e][^\)]*\)|\([G|g][E|e][R|r][M|m][A|a][N|n][Y|y][^\)]*\)'
        matchs = search(checkreg,filename)
    if not matchs:
        checkreg = '\([E|e][N|n][G|g][^\)]*\)|\([R|r][U|u][^\)]*\)|\([E|e][^\)]*\)|\([U|u][^\)]*\)|\([J|j][^\)]*\)|\([S|s][^\)]*\)|\([N|n][^\)]*\)|\([F|f][^\)]*\)|\([J|j][P|p][^\)]*\)|\([N|n][L|l][^\)]*\)|\([K|k][R|r][^\)]*\)|\([E|e][S|s][^\)]*\)'
        matchs = search(checkreg,filename)
    return matchs

def multiVersion(filename):
    checkreg = '.*[V|v]\d*\.\w*'
    matchs = search(checkreg,filename)
    if not matchs:
        checkreg = '\(.*[H|h][A|a][C|c][K|k][^\)]*\)|\([P|p][R|o][T|t][O|o][T|t][Y|y][P|p][E|e][^\)]*\)|\([D|d][E|e][M|m][O|o][^\)]*\)|\([S|s][A|a][M|m][P|p][L|l][E|e][^\)]*\)|\([B|b][E|e][T|t][A|a][^\)]*\)'
        matchs = search(checkreg,filename)
    return matchs

def getMediaUrl(mediapath,file,medias,mediaList,logging,regionList=['wor']):
    imageURL = ''
    destfile =''
    for mediatype in mediaList:
        for region in regionList:
            for img in medias:
                #logging.info('####### MEDIATYPE '+str(mediatype)+'   IMG VALUES '+str(img.values()))
                if mediatype=='box-2D':
                    if mediatype in img.values():
                        destfile = mediapath+file+'.'+img['format']
                        imageURL = img['url'].replace(img['region'],'wor')
                        logging.info ('###### RETURNING '+imageURL)
                        return imageURL,destfile
                else:
                    if mediatype in img.values() and region in img.values():
                        destfile = mediapath+file+'.'+img['format']
                        imageURL = img['url']
                        return imageURL,destfile
    return imageURL,destfile


def getFileInfo(file,system,companies,emptyGameTag,apikey,uuid,q,sq,config,logging,filext,tq,thn):
    logging.info ('###### STARTING FILE '+file)
    file=file.replace('\\','/')
    file=str(file)
    if ospath.isdir(file):
        logging.info ('###### THIS IS A DIRECTORY!')
        tq.put(thn)
        return
    mysha1,mymd5,mycrc = getChecksums(file,config)
    ## PROCESS FILE AND START DOING MAGIC
    result = getInfoFromAPI (system['id'],file,mysha1,mymd5,mycrc,apikey,uuid)
    try:
        gsysid = result['game']['system']['id']
    except Exception as e:
        if 75 in system['id']:
            gsysid = 75
        else:
            gsysid = system['id'][0]
    ### AQUISTOY
    thisTag = emptyGameTag
    ### Take care of multisystems
    simplefile = file[file.rindex('/')+1:file.rindex('.')]
    logging.info ('###### SIMPLE FILE NAME :['+str(simplefile)+']')
    system['path'] = system['path'].replace('\\','/')
    try:
        pf =  config['config']['preferbox']
    except:
        config['config']['preferbox']= False
    if not config['config']['preferbox']:
        logging.info ('###### DOWNLOADING SCREENSHOT')
        imageURL,destimage = getMediaUrl(system['path']+'images/',simplefile,result['game']['medias'],['mixrbv1','ss','sstitle'],logging,['wor','default'])
    else:
        logging.info ('###### DOWNLOADING BOX')
        imageURL,destimage = getMediaUrl(system['path']+'images/',simplefile,result['game']['medias'],['box-2D'],logging,['wor'])
    try:
        nv =  config['config']['novideodown']
    except:
        config['config']['novideodown']= False
    if not config['config']['novideodown']:
        logging.info ('###### DOWNLOADING VIDEO')
        videoURL,destvideo = getMediaUrl(system['path']+'videos/',simplefile,result['game']['medias'],['video-normalized'],logging,['wor','default'])
    else:
        logging.info ('###### NOT DOWNLOADING VIDEO')
        videoURL = ''
        destvideo = ''
    marqueeURL,destmarquee = getMediaUrl(system['path']+'marquees/',simplefile,result['game']['medias'],['screenmarqueesmall'],logging,['wor','default',])
    logging.info ('++++++++++++++++ TRYING TO GET BEZELS')
    destbezel=''
    bezelURL=''
    logging.info ('FIRST CASE ')
    dpath = system['path'].replace('/roms/','/overlays/')+'bezels/'
    logging.info ('###### CONVERTING '+str(system['path'])+'    '+dpath)
    bezelURL,destbezel = getMediaUrl(dpath,simplefile,result['game']['medias'],['bezel-16-9'],logging,['wor','default'])
    if destbezel=='' and config['config']['sysbezels']: ## CONFIG UPDATE
        sysmedias=[{"url": "/api/medias/"+str(gsysid)+"/system/bezel-16-9(wor).png",
          "region": "wor",
          "type": "bezel-16-9",
          "format": "png"
        }]
        bezelURL,destbezel = getMediaUrl(system['path'].replace('/roms/','/overlays/')+'bezels/','system_bezel-'+str(gsysid),sysmedias,['bezel-16-9'],logging,['wor','default'])
    logging.info ('++++++++++++++++ BACK FROM BEZELS')
    if imageURL !='':
        success = apicalls.getImageAPI(imageURL,destimage,apikey,uuid)
        if not success:
            destimage =''
    if videoURL !='':
        success = apicalls.getImageAPI(videoURL,destvideo,apikey,uuid)
        if not success:
            destvideo =''
    if marqueeURL !='':
        success = apicalls.getImageAPI(marqueeURL,destmarquee,apikey,uuid)
        if not success:
            destmarquee =''
    if bezelURL !='':
        logging.info ('==================================##### PROCESSNG BEZEL')
        logging.info ('##### URL='+str(bezelURL))
        logging.info ('###### DESTBEZEL = '+str(destbezel))
        processBezels(bezelURL,destbezel,apikey,uuid,file,system['path'],logging)
    thisTag = thisTag.replace('$PATH',escape(file))
    logging.info ('###### GAME NAMES FOUND :['+str(result['game']['names'])+']')
    gameName = result['game']['names'][0]['text']
    logging.info ('###### GAME NAME FOUND :['+gameName+']')
    matchs = multiDisk(simplefile)
    logging.info ('###### MULTI DISK MATCH :['+str(matchs)+']')
    vmatchs = multiVersion(simplefile)
    logging.info ('###### VERSION MATCH :['+str(vmatchs)+']')
    cmatchs = multiCountry(simplefile)
    logging.info ('###### COUNTRY MATCH :['+str(cmatchs)+']')
    hmatchs = multiHack(simplefile)
    logging.info ('###### HACK MATCH :['+str(hmatchs)+']')
    try:
        if cmatchs and config['config']['decorators']['country']:
            gameName = gameName+' '+cmatchs.group(0).replace('_',' ')
    except:
        logging.info ('###### NO COUNTRY SELECTION CONFIGURED')
    try:
        if matchs and config['config']['decorators']['disk']:
            gameName = gameName+' '+matchs.group(0).replace('_',' ')
    except:
        logging.info ('###### NO DISK SELECTION CONFIGURED')
    try:
        if vmatchs and config['config']['decorators']['version']:
            gameName = gameName+' '+vmatchs.group(0).replace('_',' ')
    except:
        logging.info ('###### NO VERSION SELECTION CONFIGURED')
    try:
        if hmatchs and config['config']['decorators']['hack']:
            gameName = gameName+' '+vmatchs.group(0).replace('_',' ')+''+filext
    except:
        logging.info ('###### NO HACK SELECTION CONFIGURED')
    q.put(['gamelabel','text',' Game : '+gameName])
    q.put(['gameimage','source',destimage])
    thisTag = thisTag.replace('$NAME',escape(gameName))
    description = 'Description for this game is empty!'
    founddesc = False
    if result['game']['synopsis']:
        try:
            if not config['config']['language']:
                config['config']['language']='en'
        except:
                config['config']['languags']='en'
        language = config['config']['language']
        logging.info ('###### SEARCHING DESCRIPTION IN '+str(language))
        for desc in result['game']['synopsis']:
            logging.info ('###### FOUND LANGUAGE '+desc['language'].upper())
            if desc['language'].upper()==language.upper():
                description= desc['text'].replace('&quot;','"')
                founddesc=True
                break
        if not founddesc:
            logging.info ('###### COULD NOT FIND DESCRIPTION IN YOU PREFERRED LANGUAGE '+str(config['config']['language'])+' SO I\'M DEFAULTING TO FIRST FOUND')
            untdesc = result['game']['synopsis'][0]['text'].replace('&quot;','"')
            try:
                if config['config']['usegoogle']:
                    translator=Translator()
                    langtot = config['config']['language']
                    translation = translator.translate(untdesc,dest=langtot)
                    description = translation.text
                    logging.info ('###### I\'VE TRANSLATED THE TEXT ')
                else:
                    description = untdesc
            except:
                description = untdesc
    logging.info ('###### PUTTING DESCRPTION IN QUEUE')
    q.put(['gamedesc','text',description])
    logging.info ('###### DESCRPTION IN QUEUE')
    try:
        logging.info ('###### REPLACING DESCRIPTION IN TAG')
        thisTag = thisTag.replace('$DESCRIPTION',escape(description))
        logging.info ('###### REPLACED DESCRIPTION IN TAG')
    except Exception as e:
        logging.error ('###### CANNT REPLACE TRANSLATION '+str(e))
    ratings = ''
    #if result['game']['ratings']:
    #    for rating in result['game']['ratings']:
    #        ratings =  ratings + ' ' + rating['type']+':'+rating['text']
    #    ratings = ratings[1:]
    logging.info ('###### REPLACING RATINGS IN TAG')
    thisTag = thisTag.replace('$RATING',escape(ratings))
    logging.info ('###### REPLACED RATINGS IN TAG')
    editor = 'Unknown'
    logging.info ('###### REPLACING EDITOR IN TAG')
    if 'id' in result['game']['editor'].keys():
        logging.info ('###### LOOKING FOR EDITOR ID')
        edid = str(result['game']['editor']['id'])
        logging.info ('###### EDITOR ID FOUND')
    try:
        logging.info ('###### GETTING COMPANY - EDITOR ID')
        editor = companies[edid]
        logging.info ('###### GOT COMPANY - EDITOR ID')
    except:
        logging.info ('###### COULDNOT GET COMPANY - EDITOR ID')
        pass
    logging.info ('###### REPLACING EDITOR')
    thisTag = thisTag.replace('$PUBLISHER',escape(editor))
    logging.info ('###### REPLACED EDITOR')
    developer = 'Unknown'
    if 'id' in result['game']['developer'].keys():
        logging.info ('###### GETTING DEV ID')
        devid = str(result['game']['developer']['id'])
        logging.info ('###### GOT DEV ID')
        try:
            logging.info ('###### GETTING DEVELOPER NAME')
            developer = companies[devid]
            logging.info ('###### GOT DEVELOPER NAME')
        except:
            logging.info ('###### COULD NOT GET DEVELOPER NAME')
            pass
    logging.info ('###### REPLACE DEV')
    thisTag = thisTag.replace('$DEVELOPER',escape(developer))
    genre=''
    logging.info ('###### REPLACE IMAGE')
    thisTag = thisTag.replace('$IMAGE',escape(destimage))
    logging.info ('###### REPLACE VIDEO')
    thisTag = thisTag.replace('$VIDEO',escape(destvideo))
    logging.info ('###### REPLACE MARQUEE')
    thisTag = thisTag.replace('$MARQUEE',escape(destmarquee))
    logging.info ('###### REPLACE RELEASE DATE')
    thisTag = thisTag.replace('$RELEASEDATE','')
    thisTag = thisTag.replace('$PLAYERS','')
    thisTag = thisTag.replace('$GENRE','')
    ### Repalce all tags with value from response
    logging.info ('###### PUT IN QUEUE')
    q.put(['scrapPB','valueincrease'])
    logging.info ('###### DID PUT IN QUEUE')
    logging.info ('###### PUT IN SQUEUE')
    sq.put ((thisTag,int(result['game']['id'])))
    logging.info ('###### DID PUT IN SQUEUE')
    logging.info ('###### PUT IN TQUEUE')
    tq.put(thn)
    logging.info ('###### DID PUT IN TQUEUE')
    logging.info ('###### DONE FILE '+file)
    return

def findMissingGames(systemid,havelist,apikey,uuid,systems,queue,doDownload):
    allgames = apicalls.getAllGames(systemid,apikey,uuid)
    missfile ='missing.txt'
    f = open (missfile,'a')
    sysname = ''
    for thissys in systems:
        if systemid in thissys['id']:
            sysname = thissys['name']
            break
    f.write('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\nSystem: '+sysname+'\n++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n')
    for game in allgames:
        if game['gameid'] not in havelist:
            output =''
            thisGame = apicalls.getGame(game['gameid'],apikey,uuid)
            output = output+'Game: '+thisGame['game']['names'][0]['text']+'\n==========================================================================\nRoms:\n'
            queue.put(['gamelabel','text','Missing:'+thisGame['game']['names'][0]['text']])
            roms=''
            for rom in thisGame['game']['roms']:
                if doDownload:
                    apicalls.download_file('')
                roms = roms+rom['filename']+'\n'
            roms = roms + '--------------------------------------------------------------------------\n'
            output=output+roms
            f.write(output)
    f.close()
    return

def getSystemIcon(systemid,apikey,uuid):
    dpath = str(Path.home())+'/.retroscraper'
    dfile = dpath+'/system.png'
    if ospath.isfile(dfile):
        remove(dfile)
    apicalls.getImageAPI('/api/medias/'+str(systemid)+'/system/logo.png',dfile,apikey,uuid)
    return dfile

def scanSystems(q,systems,apikey,uuid,companies,config,logging,remoteSystems,selectedSystems,scanqueue,origrompath,trans):
    hpath = str(Path.home())+'/.retroscraper/'
    q.put(['gamelabel','text','Scanning Files'])
    missfile ='missing.txt'
    if ospath.isfile(missfile):
        remove(missfile)
    logging.info ('###### INTO SYSTEM SCAN')
    if not systems:
        logging.info ('###### NO SYSTEMS TO SCAN')
        print ('COULD NOT FIND ANY SYSTEMS - EXITING')
        return
    getmeout = False
    emptyGameTag = "<game><rating>$RATING</rating><lastplayed/><name>$NAME</name><marquee>$MARQUEE</marquee><image>$IMAGE</image><publisher>$PUBLISHER</publisher><releasedate>$RELEASEDATE</releasedate><players>$PLAYERS</players><video>$VIDEO</video><genre>$GENRE</genre><path>$PATH</path><playcount/><developer>$DEVELOPER</developer><thumbnail/><desc>$DESCRIPTION</desc></game>"
    for system in systems:
        if (system['name'] not in selectedSystems) and (selectedSystems!=[]) and selectedSystems[1]!=trans['all']:
            continue
        logging.info ('###### DOING '+str(system))
        if config['config']['MountPath']:
            system['path']=system['path'].replace(origrompath,config['config']['MountPath'])
        if not ospath.isdir(system['path']):
            errormsg = trans['nodirmsg'].replace('$DIR',str(system['path'])).replace('$SYS',str(system['name']))
            logging.error ('###### COULD NOT FIND PATH '+system['path'])
            q.put(['errorlabel','text',errormsg])
            continue
        outXMLFile = system['path']+'gamelist.xml'
        tmpxmlFile = hpath+'gamelist.xml'
        writeFile = open(tmpxmlFile,'w',encoding="utf-8")
        writeFile.write("<?xml version='1.0' encoding='utf-8'?><gameList>")
        romfiles=[]
        try:
            spath = system['path']
            if spath[-1] != '/':
                spath = spath +'/'
            try:
                if config['config']['recursive']:
                    romfiles = [x for x in sorted(Path(spath).glob('**/*.*')) if (('/images/' not in x.as_posix()) and ('/videos/' not in x.as_posix()) and ('/marquees/' not in x.as_posix()) and ('.cfg' not in x.name) and ('.save' not in x.name))]
                else:
                    romfiles = [x for x in sorted(Path(spath).glob('*.*')) if (('/images/' not in x.as_posix()) and ('/videos/' not in x.as_posix()) and ('/marquees/' not in x.as_posix()) and ('.cfg' not in x.name) and ('.save' not in x.name))]
            except:
                romfiles = [x for x in sorted(Path(spath).glob('*.*')) if (('/images/' not in x.as_posix()) and ('/videos/' not in x.as_posix()) and ('/marquees/' not in x.as_posix()) and ('.cfg' not in x.name) and ('.save' not in x.name))]
            logging.info ('###### FOUND '+str(len(romfiles))+' ROMS FOR SYSTEM')
        except Exception as e:
            logging.error ('####### CANNOT OPEN SYSTEM DIR '+system['path']+' ERROR '+str(e))
            errormsg = trans['nodirmsg'].replace('$DIR',str(system['path'])).replace('$SYS',str(system['name']))
            q.put(['errorlabel','text',errormsg])
            continue
        try:
            logging.info('==========='+str(len(romfiles)))
        except Exception as e:
            logging.error(str(e))
        if len(romfiles)==0:
            errormsg = trans['noromsmsg'].replace('$DIR',str(system['path'])).replace('$SYS',str(system['name']))
            q.put (['errorlabel','text',errormsg])
            continue
        if 75 in system['id']:
            sysid=75
        else:
            sysid=system['id'][0]
        getSystemIcon(sysid,apikey,uuid)
        q.put(['sysImage','source',hpath+'system.png'])
        q.put(['sysImageGame','source',hpath+'system.png'])
        q.put(['sysLabel','text','System : '+str(system['name'])+' - '+str(len(romfiles))+' files'])
        q.put(['scrapPB','max',len(romfiles)])
        q.put(['scrapPB','value',0])
        #### SYSTEM IMAGE
        try:
            cm = config['config']['cleanmedia']
        except:
            config['config']['cleanmedia'] = False
            saveConfig(config,q)
        if config['config']['cleanmedia']:
            try:
                rmtree(system['path']+'images/')
                logging.info ('###### DELETED DIRECTORY IMAGES ')
            except Exception as e:
                logging.info ('###### COULD NOT DELETE DIRECTORY IMAGES '+str(e))
            try:
                rmtree(system['path']+'videos/')
                logging.info ('###### DELETED DIRECTORY VIDEOS ')
            except Exception as e:
                logging.info ('###### COULD NOT DELETE DIRECTORY VIDEOS '+str(e))
            try:
                rmtree(system['path']+'marquees/')
                logging.info ('###### DELETED DIRECTORY MARQUEES ')
            except Exception as e:
                logging.info ('###### COULD NOT DELETE DIRECTORY MARQUEES '+str(e))
        if not ospath.isdir(system['path']+'images/'):
            mkdir(system['path']+'images/')
        if not ospath.isdir(system['path']+'videos/'):
            mkdir(system['path']+'videos/')
        if not ospath.isdir(system['path']+'marquees/'):
            mkdir(system['path']+'marquees/')
        currFileIdx = 0
        totalfiles = len(romfiles)
        sq = Queue()
        tq = Queue()
        donesystem = False
        thread_list = [None]*5
        queuefull = False
        havegames=[]
        while (currFileIdx < totalfiles) and not donesystem:
            if currFileIdx >= totalfiles:
                donesystem = True
            else:
                file = str(romfiles[currFileIdx])
                if '.' in file:
                    filext = file[file.rindex('.'):]
                else:
                    filext=''
                if not queuefull:
                    if (not filext in system['extension']) and not ('gaemlist.xml' in file.lower()):
                        try:
                            logging.info ('###### This file ['+file+'] is not in the list of accepted extensions')
                        except:
                            logging.info ('###### This file [] is not in the list of accepted extensions')
                        q.put(['scrapPB','valueincrease'])
                        sq.put ('')
                        currFileIdx = currFileIdx+1
                    else:
                        for thrn in range (0,5):
                            logging.info ('###### CHECKING THREAD '+str(thrn)+' WHICH HAS VALUE '+str(thread_list[thrn]))
                            if thread_list[thrn]==None:
                                currFileIdx = currFileIdx+1
                                logging.info ('###### STARTING FILE '+file+' IN THREAD '+str(thrn))
                                thread = Thread(target=getFileInfo,args=(file,system,companies,emptyGameTag,apikey,uuid,q,sq,config,logging,filext,tq,thrn))
                                thread_list[thrn]=thread
                                logging.info ('###### CHECKING THREAD '+str(thrn)+' WHICH HAS VALUE '+str(thread_list[thrn]))
                                thread.start()
                                queuefull = not (None in thread_list)
                                logging.info ('###### IS QUEUE FULL??? '+str(queuefull))
                                break
            try:
                value = tq.get_nowait()
                thread_list[value].join()
                thread_list[value]=None
                queuefull=False
            except:
                pass
            try:
                value = sq.get_nowait()
                try:
                    if value:
                        writeFile.write(value[0]+"")
                        havegames.append(value[1])
                except Exception as e:
                    logging.error ('###### UNABLE TO WRITE TO GAMELIST FILE:'+str(e))
            except:
                pass
            try:
                if scanqueue.get_nowait():
                    donesystem = True
                    getmeout = True
            except:
                pass
            sleep(0.1)
        logging.info ('###### CLOSING GAMELIST.XML')
        writeFile.write("</gameList>")
        logging.info ('###### FILE CLOSING GAMELIST.XML')
        writeFile.close()
        ###############################################################################
        bkcount = 1
        try:
            logging.info ('###### CHECKING IF NEED TO BACKUP OR NOT')
            chk  = config['config']['nobackup']
        except:
            logging.info ('###### THERE IS NO VALUE IN CONFIG')
            chk = True
            logging.info ('######DEFAULTED TO TRUE')
        if not chk:
            logging.info ('###### I NEED TO DO BACKUP')
            while ospath.isfile(outXMLFile+'.'+str(bkcount)):
                logging.info ('###### FILE '+str(bkcount)+' EXISTS')
                bkcount = bkcount + 1
            logging.info ('###### FILE '+str(bkcount)+' DOES NOT EXIST - MAKING BACKUP')
            if ospath.isfile(outXMLFile):
                result = copyfile(outXMLFile,outXMLFile+'.'+str(bkcount))
                logging.info ('###### FILE '+str(bkcount)+' BACKUP DONE')
        logging.info ('###### COPYING NEW GAMELIST')
        result = copyfile(tmpxmlFile,outXMLFile)
        logging.info ('###### COPIED NEW GAMELIST')
        try:
            findmissing=config['config']['findmissing']
        except:
            findmissing = False
        try:
            doDownload=config['config']['downloadmissing']
        except:
            doDownload = False
        if findmissing or doDownload:
            logging.info ('##### GOING TO FIND MISSING GAMES')
            findMissingGames(sysid,havegames,apikey,uuid,systems,q,doDownload)
            logging.info ('##### DONE FINDING MISSING GAMES')
        if getmeout:
            logging.info ('###### INFORMING SCAN DONE')
            q.put(['scandone','scandone',False])
            logging.info ('###### INFORMED SCAN DONE')
            q.put(['gamelabel','text',''])
            q.put(['gamedesc','text',''])
            q.put(['gameimage','source',''])
            q.put(['sysImage','source',''])
            q.put(['sysImageGame','source',''])
            q.put(['sysLabel','text',trans['alldone']])
            q.put(['scandone','scandone',True])
            if ospath.isfile(hpath+'system.png'):
                remove(hpath+'system.png')
            return
    q.put(['gamelabel','text',''])
    q.put(['gamedesc','text',''])
    q.put(['gameimage','source',''])
    q.put(['sysImage','source',''])
    q.put(['sysImageGame','source',''])
    q.put(['sysLabel','text',trans['alldone']])
    q.put(['scandone','scandone',True])
    if ospath.isfile(hpath+'system.png'):
        remove(hpath+'system.png')

def getAbsRomPath(testpath):
    #print ('Received path '+testpath)
    retpath = ''
    if 'roms' in testpath.lower():
        #print ('YES')
        retpath = testpath[:testpath.rindex('roms')+4]
        #print (retpath)
    return retpath