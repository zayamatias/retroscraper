from importfunctions import handleImportError
import logging
import os
import socket
import sys
from pathlib import Path as Path
from queue import Queue
from threading import Thread
from time import sleep
try:
    import ifaddr
except Exception as e:
    handleImportError(str(e))
    import ifaddr
try:
    import paramiko
except Exception as e:
    handleImportError(str(e))
    import paramiko
try:
    from smb.SMBConnection import SMBConnection
except Exception as e:
    handleImportError(str(e))
    from smb.SMBConnection import SMBConnection
import apicalls

'''
def OpenFile(filename,mode,logging,thn):
    fileHnd = None
    logging.info ('###### OPENING FILE '+filename+' WITH MODE '+mode+' IN THREAD['+str(thn)+']')
    if testPathIsRemote(filename,logging,thn):
        logging.info('###### IT IS A REMOTE FILE THREAD['+str(thn)+']')
    else:
        fileHnd=open(filename,mode)
    return fileHnd
'''
def remotePathExists(config,path,ip,logging,thn):
    logging.info ('###### CHECKING IF REMOTE PATH EXISTS THREAD['+str(thn)+']')
    logging.info ('###### GOING TO CONNECT TO IP '+str(ip)+' IN THREAD ['+str(thn)+']')
    if 'ssh:' in path:
        pmsshClient = buildSSHClient(config,ip,logging,thn)
        try:
            ftp_client=pmsshClient.open_sftp()
            ftp_client.chdir(path)
            ftp_client.close()
            pmsshClient.close()
            return True
        except Exception as e:
            pmsshClient.close()
            return False
    if 'smb:' in path:
        ip,cpath = getFileBits(path,'smb://',thn)
        prefix = path[:path.index(ip)+len(ip)+1]
        check = listRemoteDirSMB(config,prefix,ip,cpath,thn,logging,False)
        if check!=None:
            return True
        else:
            return False


def buildSSHClient(config,ip,logging,thn):
    logging.info ('###### BULIDING SSH CLIENT IN THREAD['+str(thn)+']')
    pmsshClient = paramiko.SSHClient()
    logging.info ('###### CLIENT IS CREATED IN THREAD ['+str(thn)+']')
    logging.info ('###### CLIENT SETTING MISSING KEY POLICY IN THREAD ['+str(thn)+']')
    pmsshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    logging.info ('###### CLIENT SET MISSING KEY POLICY IN THREAD ['+str(thn)+']')
    logging.info ('###### CLIENT CONNECTING IN THREAD ['+str(thn)+']')
    try:
        pmsshClient.connect(ip, port=22, username=config['config']['remoteuser'],password=config['config']['remotepass'])
        logging.info ('###### CLIENT CONNECTED IN THREAD ['+str(thn)+']')
    except Exception as e:
        logging.error ('###### CANNOT CONNECT TO REMOTE SERVER ['+str(ip)+'] VIA SSH ['+str(e)+']  IN THREAD ['+str(thn)+']')
        pmsshClient = None
    return pmsshClient

def testPathIsRemote(mypath,logging,thn):
    try:
        showpath = mypath.encode('utf-8').decode()
    except:
        showpath = ''
    logging.info ('###### IS '+showpath+' REMOTE? THREAD['+str(thn)+']')
    if 'ssh:' in mypath or 'smb:' in mypath:
        logging.info ('###### YES THREAD['+str(thn)+']')
        return True
    else:
        logging.info ('###### NO THREAD['+str(thn)+']')
        return False

def removeSSHDir(config,path,logging,thn):
    return

def removeSMBDir(config,path,logging,thn):
    nosmb = path.replace('smb://','')
    ip = nosmb[:nosmb.index('/')]
    noip = nosmb.replace(ip+'/','')
    share = noip[:noip.index('/')]
    fpath = noip[noip.index('/'):]
    logging.info ('###### DOING SMB CREATE DIR FOR '+path+' IN THREAD '+str(thn))
    conn = SMBConnection('Anonymous','','retropie','retropie')
    logging.info ('###### CONNECTING VIA SMB TO '+str(ip))
    conn.connect(ip)
    try:
        conn.deleteFiles(share,fpath+'*',)
    except Exception as e:
        logging.error ('###### CANNOT REMOVE CONTENTS OF '+fpath+' IN SHARE '+share+' ('+str(e)+')')
    
    return

def removedir(config,path,logging,thn):
    if 'ssh://' in path:
        removeSSHDir(config,path,logging,thn)
    if 'smb://' in path:
        removeSMBDir(config,path,logging,thn)
    return


def makeDirSSH(config,ip,path,thn,logging):
    cmd = 'mkdir -p \''+path+'\''
    logging.info('###### GOING TO CREATE REMOTE DIR SSH '+path+' WITH COMMAND '+cmd+' IN THREAD ['+str(thn)+']')
    runRemoteCommand(config,ip,cmd,thn,logging)

def getSMBfile(config,ip,chkfile,thn,logging):
    tpath = chkfile[1:]
    share = tpath[:tpath.index('/')]
    filename = tpath[tpath.index('/'):]
    logging.info ('###### DOING SMB GET FILE FOR '+filename+' IN THREAD '+str(thn))
    conn = SMBConnection('Anonymous','','retropie','retropie')
    logging.info ('###### CONNECTING VIA SMB TO '+str(ip))
    conn.connect(ip)
    outfilename = str(Path.home())+'/.retroscraper/filetmp/tmpfile'+str(thn)+'.bin'    
    outfile = open(outfilename,'wb')
    conn.retrieveFile(share,filename,outfile)
    outfile.close()
    return outfilename


def makeDirSMB(config,ip,path,thn,logging):
    logging.info ('###### DOING SMB CREATE DIR FOR '+path+' IN THREAD '+str(thn))
    conn = SMBConnection('Anonymous','','retropie','retropie')
    logging.info ('###### CONNECTING VIA SMB TO '+str(ip))
    conn.connect(ip)
    if path[-1]=='/':
        path=path[:-1]
    if path[0]=='/':
        path=path[1:]
    rpath = path[path.index('/')+1:]
    share = path[:path.index('/')]
    try:
        conn.createDirectory(share,rpath)
    except:
        logging.error ('###### CANNOT CREATE REMOTE DIR '+path+' IN SHARE '+share)
    return


def makeRemoteDir(config,path,thn,logging):
    if 'ssh:' in path:
        logging.info('###### GOING TO CREATE REMOTE SSH DIR '+path+' IN THREAD ['+str(thn)+']')
        ip,path = getFileBits(path,'ssh://',thn)
        makeDirSSH (config,ip,path,thn,logging)
    if 'smb:' in path:
        logging.info('###### GOING TO CREATE REMOTE SMB DIR '+path+' IN THREAD ['+str(thn)+']')
        ip,path = getFileBits(path,'smb://',thn)
        makeDirSMB (config,ip,path,thn,logging)


def getFileBits(filepath,typeremote,thn):
    part=filepath.replace (typeremote,'')
    ip = part [:part.index('/')]
    path = part [part.index('/'):]
    return ip,path

def copyToRemote (config,orig,dest,thn,logging):
    if 'ssh://' in dest:
        logging.info ('###### COPYING LOCAL FILE '+orig+' TO SSH DESTINATION '+dest+' THREAD['+str(thn)+'}')
        ip,destpath = getFileBits(dest,'ssh://',thn)
        logging.info ('###### GOING TO CONNECT TO IP '+str(ip)+' IN THREAD ['+str(thn)+']')
        pmsshClient = buildSSHClient(config,ip,logging,thn)
        retries = 10
        success = False
        while not success and retries >0:
            try:
                logging.info ('###### LAUNCH SFTP CLIENT IN THREAD ['+str(thn)+']')
                ftp_client=pmsshClient.open_sftp()
                logging.info ('###### COPYING LOCAL FILE '+orig+' TO SSH DESTINATION '+destpath+' THREAD['+str(thn)+'}')
                result = ftp_client.put(orig,destpath)
                
                logging.info ('###### DID PUT WITH RESULTY '+str(result)+' IN THREAD ['+str(thn)+']')
                logging.info ('###### CLOSED SFTP CLIENT IN THREAD ['+str(thn)+']')
                success = True
                logging.info ('###### SUCCESFULLY COPIED FILE TO REMOTE IN THREAD ['+str(thn)+']')
            except Exception as e:
                if ('size mismatch in put!' not in str(e)) and ('Server connection dropped' not in str(e)):
                    logging.error ('###### COULD NOT COPY FILE '+str(e)+' IN THREAD['+str(thn)+']')
                else:
                    logging.info ('###### SOME ERROR IN COPY TO RMEOTE '+str(e)+' IN THREAD ['+str(thn)+']')
                retries = retries -1
                #logging.info ('###### GOING TO CONNECT TO IP '+str(ip)+' IN THREAD ['+str(thn)+']')
                #pmsshClient=buildSSHClient(ip,logging,thn)
        if retries == 0:
            logging.error ('###### COULD NOT COPY TO REMOTE '+orig+' TO '+dest+' IN THREAD ['+str(thn)+']')
        pmsshClient.close()
    else:
        nosmb = dest.replace('smb://','')
        ip=nosmb[:nosmb.index('/')]
        path = nosmb.replace(ip,'')
        logging.info ('###### DOING SMB COPY FILE FOR '+dest+' IN THREAD '+str(thn))
        conn = SMBConnection('Anonymous','','retropie','retropie')
        logging.info ('###### CONNECTING VIA SMB TO '+str(ip))
        conn.connect(ip)
        if path[-1]=='/':
            path=path[:-1]
        if path[0]=='/':
            path=path[1:]
        rpath = path[path.index('/')+1:]
        share = path[:path.index('/')]
        try:
            infile = open(orig,'rb')
            conn.storeFile(share,rpath,infile)
            infile.close()
        except:
            logging.error ('###### CANNOT CREATE REMOTE DIR '+rpath+' IN SHARE '+share)
        return
        logging.info ('###### COPYING LOCAL FILE '+orig+' TO SMB DESTINATION '+dest+' THREAD['+str(thn)+'}')
    return

def runRemoteCommand(config,ip,command,thn,logging):
    logging.info ('###### GOING TO CONNECT TO IP '+str(ip)+' IN THREAD ['+str(thn)+']')
    pmsshClient = buildSSHClient(config,ip,logging,thn)
    logging.info ('###### EXECUTING REMOTE '+str(command)+' THREAD['+str(thn)+']')
    success = False
    retries = 10
    while not success and retries >0:
        try:
            stdin, stdout, stderr = pmsshClient.exec_command(command, timeout=None)
            while not stdout.channel.exit_status_ready():
                sleep(.1)
            success = True
        except Exception as e:
            logging.error ('###### COULD NOT EXECUTE REMOTE COMMAND '+command+' ERRROR '+str(e)+' IN THREAD ['+str(thn)+']')
            if not pmsshClient:
                pmsshClient = buildSSHClient(config,ip,logging,thn)
            retries = retries -1
    if retries == 0:
        logging.error ('###### COULD NOT EXECUTE REMOTE COMMAND '+command+' IN THREAD ['+str(thn)+']')
        cmd_output = ''
    else:
        cmd_output = stdout.read()
    try:
        if not isinstance(cmd_output, str):
            cmd_output = cmd_output.decode('utf-8')
    except Exception as e:
        logging.error ('###### I CANNOT DECODE CMD RESULT '+str(e)+' IN THREAD['+str(thn)+']')
    if retries >0:
        logging.info ('###### +++++++++++++++++++++++ RETURN WAS '+str(cmd_output)+' AND STDERR ['+str(stderr.read())+'] THREAD['+str(thn)+']')
        stdin.close()
    if pmsshClient:
        pmsshClient.close()
    return cmd_output

def listRemoteDir(config,path,logging,thn):
    myfiles =[]
    if 'ssh:' in path:
        ip,chpath = getFileBits(path,'ssh://',thn)
        tmpfiles = listRemoteDirSSH(config,ip,chpath,thn,logging)
        for tfile in tmpfiles:
            myfiles.append('ssh://'+ip+tfile)

    if 'smb:' in path:
        ip,chpath = getFileBits(path,'smb://',thn)
        prefix = path[:path.index(ip)+len(ip)+1]
        myfiles = listRemoteDirSMB(config,prefix,ip,chpath,thn,logging)
    if myfiles:
        return myfiles

def listRemoteDirSSH (config,ip,path,thn,logging):
    tmpfiles = runRemoteCommand (config,ip,'find \''+path+'\' -maxdepth 1 -type f',thn,logging)
    tmpfileslist = tmpfiles.split('\n')
    del tmpfileslist[-1]
    return tmpfileslist

def listRemoteDirSMB (config,prefix,ip,path,thn,logging,returnlist=True):
    logging.info ('###### DOING SMB LIST DIR FOR '+path+' IN THREAD '+str(thn))
    conn = SMBConnection('Anonymous','','retropie','retropie')
    logging.info ('###### CONNECTING VIA SMB TO '+str(ip))
    conn.connect(ip)
    if path[-1]=='/':
        path=path[:-1]
    if path[0]=='/':
        path=path[1:]
    rpath = path[path.index('/')+1:]
    share = path[:path.index('/')]
    listfiles=[]
    try:
        files = conn.listPath(share,rpath)
    except:
        logging.info ('###### COULD NOT READ REMOTE SMB PATH '+rpath+' IN SHARE  '+share)
        return None
    logging.info ('######  FOUND THESE FILES '+str(files))
    for file in files:
        if file.filename !='.' and file.filename !='..':
            listfiles.append(prefix+share+'/'+rpath+'/'+file.filename)
    return listfiles



def getRemoteEsConfig(config,ip,logging,thn):
    destconfig = str(Path.home())+'/.retroscraper/es_systems.cfg'    
    logging.info ('###### GOING TO DO REMOTE CONFIG READ')
    ## try via ssh
    myconfig = runRemoteCommand(config,ip,'cat /etc/emulationstation/es_systems.cfg',thn,logging)
    logging.info ('###### GOT ['+str(myconfig)+'] AS REMOTE CONFIG')
    ## To skip SSH
    ## myconfig = None
    if myconfig:
        logging.info ('###### THERE IS A CONFIG SO REPLACE EVERY PATH BY SSH')
        myconfig = myconfig.replace('<path>','<path>ssh://'+ip)
    else:
        logging.info ('###### CANNOT GET CONFIG BY SSH LET\'S TRY SMB!')
        conn = SMBConnection('Anonymous','','retropie','retropie')
        logging.info ('###### CONNECTING VIA SMB TO '+str(ip))
        conn.connect(ip)
        files = conn.listPath('configs','all/emulationstation')
        logging.info ('###### GOT THIS LIST OF FILES '+str(files))
        for file in files:
            logging.info ('###### CHECKING FILE '+str(file))
            if file.filename=='es_systems.cfg':
                logging.info ('###### FOUND THE CONFIGURATION FILE!')
                outfile = open(destconfig,'wb')
                myconfig = conn.retrieveFile('configs','all/emulationstation/'+file.filename,outfile,timeout=300)
                outfile.close()
                infile = open(destconfig,'r')
                myconfig = infile.read()
                infile.close()
                myconfig = myconfig.replace('<path>/home/pi/RetroPie','<path>smb://'+ip)
                logging.info ('###### FILE READ AND REPLACED PATHS WITH SMB!')
                break
        if not myconfig:
            logging.info ('###### I COULD NOT FIND A CONFIG FILE, SO I\'M CREATING ONE')
            systems = conn.listPath('roms','')
            if systems:
                myconfig='<?xml version="1.0"?>\n<systemList>\n'
                systag='\t<system>\n\t\t<name>$NAME</name>\n\t\t<extension>$EXTENSIONS</extension>\n\t\t<platform>$NAME</platform>\n\t\t<path>$PATH</path>\n\t</system>\n'
                for system in systems:
                    path = 'smb://'+ip+'/roms/'+system.filename
                    sname=system.filename
                    extns = apicalls.getSystemsExtensions(sname)
                    thistag=systag.replace('$NAME',sname).replace('$PATH',path).replace('$EXTENSIONS',extns)
                    myconfig=myconfig+thistag
                myconfig=myconfig+'</systemList>'
                logging.info ('###### FILE WAS CREATED INTERNALLY')
            else:
                logging.info ('###### I COULD NOT FIND REMOTE SYSTEMS, SORRY!')
    if not myconfig:
        logging.error('###### COULD NOT FIND REMOTE CONFIG')
        return ''
    else:
        logging.info ('###### WRITING LOCALLY '+str(myconfig))
        outfile = open(destconfig,'w')
        outfile.write (myconfig)
        outfile.close()
        return destconfig


def checkEsIsPresent(ip,logging):
    try:
        conn = SMBConnection('Anonymous','','retropie','retropie')
        conn.connect(ip)
        test = False
        for share in conn.listShares():
            if 'roms' == share.name.lower():
                test = True
    except Exception as e:
        logging.error('###### EXCEPTION WHEN FINDING SHARES ['+str(e)+']')
    return test

def getNetInfo():
    myip =''
    snet = ''
    ifaces = ifaddr.get_adapters()
    #ifaces = netifaces.interfaces()
    #addr = netifaces.ifaddresses(iface)
    for iface in ifaces:
        for ip in iface.ips:
            if ('.' in ip.ip) and ('127.0' not in ip.ip):
                return ip.ip,ip.network_prefix
    
def testPort(ip,port,thrn,tq,sq):
    socket.setdefaulttimeout(5)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = s.connect_ex((ip,port))
    if result == 0:
        sq.put(ip)
    tq.put(thrn)
    s.close()
    return

def scan (logging):
    logging.info ('###### STARTING SCANNING OF REMOTE SYSTEMS')
    ip,snet = getNetInfo()
    logging.info ('###### MY IP IS '+str(ip)+' WITH SUBNET '+str(snet))
    tq = Queue()
    sq = Queue()
    foundlist =[]
    totthreads = 30
    threadList =[None]*totthreads
    n = 0
    done = False
    logging.info ('###### STARTING!')
    while not done:
        if n<256:
            for thrn in range (0,totthreads):
                if threadList[thrn]==None:
                    ipscan = ip[:ip.rindex('.')+1]+str(n)
                    logging.info ('###### TRYING IP '+str(ipscan))
                    runthread = Thread(target=testPort,args=(ipscan,445,thrn,tq,sq))
                    threadList[thrn]=runthread
                    runthread.start()
                    n = n +1
        try:
            value = tq.get_nowait()
            threadList[value].join()
            threadList[value]=None
        except:
            pass
        try:
            value = sq.get_nowait()
            if value !=ip:
                if checkEsIsPresent(value,logging):
                    logging.info ('###### FOUND IP '+str(value))
                    foundlist.append(value)
        except:
           pass
        if all(x is None for x in threadList) and n>255:
            done = True
        sleep(0.1)
    logging.info ('###### DONE SCANNING!')
    return foundlist


