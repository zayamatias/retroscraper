import logging
import sys
from tempfile import TemporaryFile
import pymysql as mysql
from time import sleep
import re
from bs4 import BeautifulSoup
from pytest import skip
from requests import get as requestsget
from requests import exceptions as requestsexceptions
from requests import Response as requestsResponse
from requests import post as requestspost
import json
import unicodedata

from sqlalchemy import over

def getDBCursor():
    global mydb
    connected = False
    while not connected:
        try:
            thiscursor = mydb.cursor()
            connected = True
        except Exception as e:
            print ('###### CANNOT CONNECT TO DB - '+str(e))
            print ('###### WAITING AND RETRYING')
            try:
                mydb.close()
                sleep(60)
                mydb = initiateDBConnect()
                thiscursor = mydb.cursor()
            except Exception as e:
                print ('###### CANNOT RECONNECT TO DB '+str(e))
    return thiscursor

def queryDB(sql,values,directCommit,logerror=False,retfull=False):
    global mydb
    mycursor = getDBCursor()
    if mycursor:
        #print('###### GOT A CURSOR FOR THE DB')
        if 'SELECT' in sql:
            #print('####### IS A SELECT QUERY')
            try:
                #print('####### GOING TO EXECUTE QUERY')
                mycursor.execute(sql, values)
                #print('####### EXECUTED QUERY - GOING TO GRAB RESULTS')
                myresult = mycursor.fetchall()
                #print('####### GRABBED ALL RESULTS')
                #print ('@@@@@@@@@@ '+str(mycursor._last_executed))
                if logerror:
                    pass
                    #print ('@@@@@@@@@@ '+str(mycursor._last_executed))
            except Exception as e:
                #print ('###### COULD NOT EXECUTE SELECT QUERY '+str(e))
                #print ('@@@@@@@@@@ '+str(mycursor._last_executed))
                mycursor.close()
                return None,False
            if mycursor.rowcount == 0:
                #print ('###### COULD NOT FIND IN THE DB')
                mycursor.close()
                return None,False
            else:
                if mycursor.rowcount == 1:
                    #print ('###### COULD FIND ONE RESULT '+str(myresult[0]))
                    if not retfull:
                        mycursor.close()
                        return myresult[0][0],True
                    else:
                        mycursor.close()
                        return myresult[0],True
                else:
                    #print ('###### FOUND SEVERAL RESULTS')
                    mycursor.close()
                    return myresult,True
        else:
            print('####### IT IS NOT A SELECT QUERY')
            try:
                mycursor.execute(sql, values)
                print (str(mycursor._last_executed))
                print('####### QUERY EXECUTED PROPERLY')
                if logerror:
                    print ('@@@@@@@@@@ '+str(mycursor._last_executed))
                    print('####### QUERY EXECUTED PROPERLY BIS')
                    pass
                mycursor.close()
                if directCommit:
                    mydb.commit()
            except Exception as e:
                print ('###### NO SELECT QUERY - COULD NOT EXECUTE QUERY '+str(e))
                print ('###### SQL '+str(sql))
                print ('###### VALUES '+str(values))
                print ('@@@@@@@@@@ '+str(mycursor._last_executed))
                print (str(mycursor._last_executed))
                mycursor.close()
                return None,False
        return None,True
    else:
        #print ('###### COULD NOT CREATE CURSOR FOR DB')
        return None,False


def initiateDBConnect():
    try:
        thisDB = mysql.connect(
        host='192.168.8.160',
        user='romhash',
        passwd='emulation',
        database='retroscraper',
        charset='utf8mb4',
        use_unicode=True
        )
    except Exception as e:
        logging.error ('###### CANNOT CONNECT TO DATABASE, Error:'+str(e))
        #print ('###### PLEASE MAKE SURE YOU HAVE A DATABASE SERVER THAT MATCHES YOUR CONFIGURATION')
        #print ('CONNECTION TO DB FAILED '+str(e))
        sys.exit()
    return thisDB

mydb = initiateDBConnect()

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
                req = requestsget(url,headers=headers)
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

def markEnhanced(gameid):
    enhquery='INSERT INTO enhanced (gameid) values (%s)'
    vals=(gameid)
    result = queryDB(enhquery,vals,True)
    return

def insertExternalRef (internaild,provider,externalid):
    query = 'INSERT INTO externalReference (gameId,externalID,ExternalProvider) values (%s,%s,%s)'
    vals=(internaild,externalid,provider)
    result = queryDB(query,vals,True)

def chkSyn(gameid,synopsis):
    query = 'SELECT `text` from gameSynopsis where gameid=%s and langue=%s'
    vals=(gameid,'en')
    result = queryDB(query,vals,True)
    if result[0]:
        pass #there is a synopsis
    else:
        #we need to insert synopsis
        insSyn(gameid,synopsis)

def getEamonDetails(game):
    URL = 'https://www.eamonag.org/columns/reviews-all.html'
    soup = BeautifulSoup(simpleCall(URL),features="lxml")
    rJson = dict()
    try:
        lookup = game[game.index('-')+2:].lower()
    except:
        lookup = game.lower()
    if lookup == 'main hall & beginners cave':
        lookup = 'the begginer\'s cave'
    print (lookup)
    for ol in soup.find_all('ol'):
        for li in ol.find_all('li',recursive=False):
            try:
                gname = str(li.find_all('a')[0].contents[0])
            except:
                gname = str(li.contents[0])
            if gname.lower()==lookup:
                print ('+++++++++++++++++++++++ '+lookup+'='+gname)
                overview =''
                addesc = False
                for p in li.find_all('ul',recursive=False)[0].find_all('p'):
                    try:
                        if str(p.contents[0]).index('Description:')==0:
                            overview = str(p.contents[0])[str(p.contents[0]).index('Description')+13:]
                            addesc = True
                            continue
                    except:
                        pass
                    try:
                        if str(p.contents[0]).index('Comment:')==0:
                            addesc = False
                            continue
                    except:
                        pass
                    if addesc:
                        overview = overview + str(p.contents[0])
                if overview:
                    if overview[0]=='"':
                        overview=overview[1:]
                    if overview[0]=='\'':
                        overview=overview[1:]
                    overview=overview.strip()
                    try:
                        if overview[len(overview)-1]=='"':
                            overview=overview[:-1]
                    except:
                        pass
                    try:
                        if overview[len(overview)-1]=='\'':
                            overview=overview[:-1]
                    except:
                        pass
                    try:
                        overview = overview.replace('\r\n',' ')
                    except:
                        pass
                    try:
                        overview = overview.replace('\r',' ')
                    except:
                        pass
                    try:
                        overview = overview.replace('\t',' ')
                    except:
                        pass
                    try:
                        overview=overview.replace('\n',' ')
                    except:
                        pass
                    rJson['Overview']=overview
    
    return rJson


def getLBDetails(URL):
    URL = 'https://gamesdb.launchbox-app.com'+URL
    soup = BeautifulSoup(simpleCall(URL),features="lxml")
    rJson = dict()
    rJson['id']=URL[URL.rindex('/')+1:]
    for table in soup.find_all('table'):
        if table.has_attr('class'):
            tc = table['class']
            if "table" in tc and "table-striped" in tc and "table-bordered" in tc and "table-hover" in tc and "table-details" in tc:
                for tr in table.find_all('tr'):
                    mykey=''
                    myvalue=''
                    for td in tr.find_all('td'):
                        if td.has_attr('class'):
                            if "row-header" in td['class']:
                                if td.contents:
                                    mykey=td.contents[0].strip()
                    if mykey != '':
                        if  mykey in ['Developers','Publishers','Genres','Wikipedia','Video Link']:
                            islink = True
                        else:
                            islink = False
                        if mykey in ['Overview']:
                            isdiv = True
                        else:
                            isdiv = False
                        for td in tr.find_all('td'):
                            if not td.has_attr('class'):
                                if not isdiv:
                                    children = td.find_all('span')
                                else:
                                    children = td.find_all('div')
                                for child in children:
                                    if child.has_attr('class'):
                                        if 'view' in child['class']:
                                            if islink:
                                                links = child.find_all('a')
                                                if links:
                                                    if links[0].contents:
                                                        myvalue = str(links[0].contents[0]).strip()
                                                    else:
                                                        myvalue =''
                                                else:
                                                    myvalue =''
                                            else:
                                                if child.contents:
                                                    myvalue =child.contents[0].strip()
                                                else:
                                                    myvalue=''
                    if mykey:
                        rJson[mykey]=myvalue
    return rJson

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

def getWiiDetails(game):
    rJson=dict()
    baseURL = 'https://wiki.dolphin-emu.org'
    sURL = baseURL+'/index.php?search='
    urlGame = game.replace(' ','+')
    URL = sURL+urlGame+'&title=Special%3ASearch&go=Go'
    soap = BeautifulSoup(simpleCall(URL),features="lxml")
    overview=''
    for div in soap.find_all('div',{'class':'mw-search-result-heading'}):
        link = div.contents[0]['href']
        wikiname = div.contents[0].contents[0].lower().replace(' - ',' ').replace(' : ',' ').replace('- ',' ').replace(': ',' ')
        cgame =  game.lower().replace(' - ',' ').replace(' : ',' ').replace('- ',' ').replace(': ',' ')
        print (cgame,wikiname)
        if wikiname==cgame:
            detURL = baseURL+link
            detsoap = BeautifulSoup(simpleCall(detURL),features="lxml")
            detdiv = detsoap.find_all('div',{'class':'mw-content-ltr'})[0]
            p = detdiv.find_all('p',recursive=False)[0]
            overview=''
            for cnt in p.contents:
                overview=overview+cnt.text
    print ("[[[[[[[[[[[[[[["+overview+']]]]]]]]]]]]]]]]]]')
    rJson['Overview']=overview
    return rJson


def getDetails(game,systemnames):
    URL = 'https://gamesdb.launchbox-app.com/games/results?id='+game
    if 'Nintendo WII' in systemnames:
        gdetails = getWiiDetails(game)
        return gdetails
    if 'Eamon' in game:
        print ('EAMON!')
        gdetails = getEamonDetails(game)
        return gdetails
    ngame = game.replace ('-','')
    ngame = ngame.replace (':','')
    ngame = ngame.replace ('  ',' ')
    gdetails = ''
    soup = BeautifulSoup(simpleCall(URL),features="lxml")
    for a in soup.find_all('a', href=True):
        if a.has_attr('class'):
            if 'list-item' in a['class']:
                link = a['href']
                hs = a.find_all(re.compile('^h[1-6]$'))[0].contents[0]
                hs = hs.replace ('-','')
                hs = hs.replace (':','')
                hs = hs.replace ('  ',' ')
                s1 = strip_accents(hs.lower())
                s2 = strip_accents(ngame.lower())
                print ('comparing '+s1+' with '+s2+' equals '+str(s1==s2))
                if s1 == s2 :
                    for p in a.find_all('p'):
                        if p.has_attr('class'):
                            if 'sub' in p['class']:
                                platform = p.contents[0]
                                for cksys in systemnames:
                                    if cksys.upper() in platform.upper():
                                        gdetails = getLBDetails(link)
    if not gdetails:
        gdetails=dict()
        gdetails['Name']=game
        gdetails['Overview']=''
    return gdetails

def insSyn(gameid,synopsis):
    newsypquery = 'INSERT INTO gameSynopsis (langue,text,gameid) values (%s,%s,%s)'
    if synopsis != '':
        vals = ('en',synopsis,gameid)
        result = queryDB(newsypquery,vals,True)
        markEnhanced(gameid)
    return 


def createGames():
    query = 'SELECT max(id) FROM games'
    vals=()
    results = queryDB(query,vals,False)
    currid = results[0]+1
    print (currid)
    query = "SELECT filename,sha1 from temporaryroms where gameid = %s and system=%s group by sha1"
    vals=(0,'[135]')
    games = queryDB(query,vals,False)
    newgamequery = 'INSERT into games (id,notgame,cloneof,system,players,editor,developer,confirmed,fromcache) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)'
    newnamequery = 'INSERT INTO gameNames (region,text,gameid) values (%s,%s,%s)'
    tromsupd = 'UPDATE temporaryroms set gameid=%s where sha1=%s'
    for game in games[0]:
        sgname = re.sub("[\(\[].*?[\)\]]", "", game[0])
        sgname = sgname[:sgname.rindex('.')]
        gamename = sgname.strip()
        print ('['+gamename+']')
        gJson = getDetails(gamename,['MS-DOS','WINDOWS'])
        if gJson:
            print ('INSERTING GAMEID '+str(currid)+' FOR GAME')
            vals = (currid,0,0,135,0,0,0,0,0)
            result = queryDB(newgamequery,vals,True)
            vals = ('wor',gJson['Name'],currid)
            result = queryDB(newnamequery,vals,True)
            insSyn(currid,gJson['Overview'])
            vals = (currid,game[1])
            result = queryDB(tromsupd,vals,True)
            currid=currid+1

def guessGames():
    query = "SELECT filename,`system`,sha1 from temporaryroms where gameid=%s and `system`!=%s group by sha1"
    vals=(0,'[135]')
    srchquery = 'SELECT distinct(gameid),gr.romfilename,systemid  from gameRoms gr  left join games g ON g.id =gr.gameid  where gr.romfilename  like %s and systemid in %s'
    updquery = 'UPDATE temporaryroms set possiblegameid = %s where sha1 = %s'
    #srchquery = "SELECT distinct(gameid),gn.`text`  from gameNames gn left join games g ON g.id =gn.gameid  where gn.`text` like %s and g.`system` in %s"
    results = queryDB(query,vals,False)
    for x in range (3,6):
        print ('Doing Range '+str(x))
        for result in results[0]:
            try:
                sname =''
                if ', the ' in result[0].lower():
                    pname = result[0].lower().replace(', the','')
                    sname = 'the '+pname
                    sname = sname[:x]
                    print ('##### '+result[0])
                    print ('+++++ '+sname)
                if sname =='' and ', la ' in result[0].lower():
                    pname = result[0].lower().replace(', la','')
                    sname = 'la '+pname
                    sname = sname[:x]
                    print ('##### '+result[0])
                    print ('+++++ '+sname)
                if sname =='' and ', a ' in result[0].lower():
                    pname = result[0].lower().replace(', a','')
                    sname = 'a '+pname
                    sname = sname[:x]
                    print ('##### '+result[0])
                    print ('+++++ '+sname)
                if sname =='' and ', los ' in result[0].lower():
                    pname = result[0].lower().replace(', los','')
                    sname = 'los '+pname
                    sname = sname[:x]
                    print ('##### '+result[0])
                    print ('+++++ '+sname)
                if sname =='':
                    sname = result[0][:x]+'%'
                sname = sname.lower()
            except:
                continue
            systems = result[1].strip('][').split(', ')
            for sysid in systems:
                systems.append(int(sysid))
                systems.remove(sysid)
            if systems[0]=='135':
                systems.remove('135')
                systems.append(135)
                systems.append(136)
                systems.append(137)
                systems.append(138)
            vals = (sname,systems)
            posresults = queryDB(srchquery,vals,False,False,True)
            if posresults[0]!=None:
                if type(posresults[0][0]) == int:
                    insert = (posresults[0],)
                else:
                    insert = posresults[0]
                nicestr=''
                for item in insert:
                    nicestr = nicestr+str(item[0])+'\n'+item[1]+':'+str(item[2])+'\n'
                vals = (nicestr,result[2])
                print ("Updated for "+result[0])
                insresult = queryDB(updquery,vals,True,False,False)
                #print (result[0],insresult)

def relateGames ():
    eamon = False
    wii = False
    if eamon:
        query = 'SELECT id,system from games where id in (select distinct(gn.gameid) from gameNames gn where `text` like %s) order by id'
        vals= ('Eamon%')
        startgame = 0
    else:
        if not wii:
            #query = "SELECT id,system from games where id < %s"
            query = 'SELECT id,system from games where id not in (select distinct(gs.gameid) from gameSynopsis gs where langue=%s and `text` != %s) order by id'
            vals =('en','')
            startgame = 111200
        if wii:
            query = 'SELECT id,system from games where system=%s and id not in (select distinct(gs.gameid) from gameSynopsis gs where langue=%s and `text` != %s) order by id'
            vals =(16,'en','')
            startgame = 0

    sysquery = 'SELECT common_names from systems where id =%s'
    namequery = 'SELECT text from gameNames where gameid=%s'
    gamelist = queryDB(query,vals,False)
    for game in gamelist[0]:
        print (game)
        gameid = game[0]
        if int(gameid) < startgame:
            print ('Skipping')
            continue
        vals = (game[1])
        mysystemres = queryDB(sysquery,vals,False)
        vals = (gameid)
        mynameres = queryDB(namequery,vals,False)
        if not (type(mynameres[0])==tuple):
            print ("adding tuple")
            namesresult = (((mynameres[0],),),)
        else:
            namesresult = mynameres
        print (namesresult[0])
        counter =0
        for spname in namesresult[0]:
            print (counter, game,mysystemres[0],spname[0])
            gamedetails = getDetails(spname[0],mysystemres[0].split(','))
            print (gamedetails)
            if eamon:
                break
            try:
                if wii and gamedetails['Overview']!='':
                    break
            except:
                pass
            try:
                if 'id' in gamedetails.keys():
                    break
            except:
                pass
            counter = counter + 1
        print (gamedetails)
        try:
            synop = gamedetails['Overview']
        except:
            synop =''
        chkSyn(gameid,synop)
        try:
            exid = gamedetails['id']
            insertExternalRef(gameid,'LaunchBox',exid)
        except:
            pass
relateGames()
