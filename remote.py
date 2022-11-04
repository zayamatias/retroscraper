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
def remotePathExists(path,ip,logging,thn):
    logging.info ('###### CHECKING IF REMOTE PATH EXISTS THREAD['+str(thn)+']')
    logging.info ('###### GOING TO CONNECT TO IP '+str(ip)+' IN THREAD ['+str(thn)+']')
    pmsshClient = buildSSHClient(ip,logging,thn)
    try:
        ftp_client=pmsshClient.open_sftp()
        ftp_client.chdir(path)
        ftp_client.close()
        pmsshClient.close()
        return True
    except Exception as e:
        pmsshClient.close()
        return False

def buildSSHClient(ip,logging,thn):
    logging.info ('###### BULIDING SSH CLIENT IN THREAD['+str(thn)+']')
    pmsshClient = paramiko.SSHClient()
    logging.info ('###### CLIENT IS CREATED IN THREAD ['+str(thn)+']')
    logging.info ('###### CLIENT SETTING MISSING KEY POLICY IN THREAD ['+str(thn)+']')
    pmsshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    logging.info ('###### CLIENT SET MISSING KEY POLICY IN THREAD ['+str(thn)+']')
    logging.info ('###### CLIENT CONNECTING IN THREAD ['+str(thn)+']')
    try:
        pmsshClient.connect(ip, port=22, username='pi',password='raspberry')
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


def makeDirSSH(ip,path,thn,logging):
    cmd = 'mkdir -p \''+path+'\''
    logging.info('###### GOING TO CREATE REMOTE DIR SSH '+path+' WITH COMMAND '+cmd+' IN THREAD ['+str(thn)+']')
    runRemoteCommand(ip,cmd,thn,logging)


def makeDirSMB(ip,path,thn,logging):
    return


def makeRemoteDir(path,thn,logging):
    if 'ssh:' in path:
        logging.info('###### GOING TO CREATE REMOTE SSH DIR '+path+' IN THREAD ['+str(thn)+']')
        ip,path = getFileBits(path,'ssh://',thn)
        makeDirSSH (ip,path,thn,logging)
    if 'smb:' in path:
        logging.info('###### GOING TO CREATE REMOTE SMB DIR '+path+' IN THREAD ['+str(thn)+']')
        ip,path = getFileBits(path,'smb://',thn)
        makeDirSMB (ip,path,thn,logging)


def getFileBits(filepath,typeremote,thn):
    part=filepath.replace (typeremote,'')
    ip = part [:part.index('/')]
    path = part [part.index('/'):]
    return ip,path

def copyToRemote (orig,dest,thn,logging):
    if 'ssh://' in dest:
        logging.info ('###### COPYING LOCAL FILE '+orig+' TO SSH DESTINATION '+dest+' THREAD['+str(thn)+'}')
        ip,destpath = getFileBits(dest,'ssh://',thn)
        logging.info ('###### GOING TO CONNECT TO IP '+str(ip)+' IN THREAD ['+str(thn)+']')
        pmsshClient = buildSSHClient(ip,logging,thn)
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
        logging.info ('###### COPYING LOCAL FILE '+orig+' TO SMB DESTINATION '+dest+' THREAD['+str(thn)+'}')
    return

def runRemoteCommand(ip,command,thn,logging):
    logging.info ('###### GOING TO CONNECT TO IP '+str(ip)+' IN THREAD ['+str(thn)+']')
    pmsshClient = buildSSHClient(ip,logging,thn)
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
                pmsshClient = buildSSHClient(ip,logging,thn)
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

def listRemoteDir(path,logging,thn):
    myfiles =[]
    if 'ssh:' in path:
        ip,chpath = getFileBits(path,'ssh://',thn)
        tmpfiles = listRemoteDirSSH(ip,chpath,thn,logging)
        for tfile in tmpfiles:
            myfiles.append('ssh://'+ip+tfile)

    if 'smb:' in path:
        ip,chpath = getFileBits(path,'ssh://',thn)
        myfiles = listRemoteDirSMB(ip,chpath,thn,logging)
    if myfiles:
        return myfiles

def listRemoteDirSSH (ip,path,thn,logging):
    tmpfiles = runRemoteCommand (ip,'find \''+path+'\' -maxdepth 1 -type f',thn,logging)
    tmpfileslist = tmpfiles.split('\n')
    del tmpfileslist[-1]
    return tmpfileslist

def listRemoteDirSMB (ip,path,logging):
    return runRemoteCommand (ip,'ls -1 '+path,logging)


def getRemoteEsConfig(ip,logging,thn):
    destconfig = str(Path.home())+'/.retroscraper/es_systems.cfg'    
    logging.info ('###### GOING TO DO CONFIG READ')
    ## try via ssh
    myconfig = runRemoteCommand(ip,'cat /etc/emulationstation/es_systems.cfg',thn,logging)
    ## To skip SSH
    ## myconfig = None
    if myconfig:
        myconfig = myconfig.replace('<path>','<path>ssh://'+ip)
    else:
        conn = SMBConnection('Anonymous','','retropie','retropie')
        conn.connect(ip)
        files = conn.listPath('configs','all/emulationstation')
        hpath = str(Path.home())+'/.retroscraper/'    
        for file in files:
            if file.filename=='es_systems.cfg':
                outfile = open(destconfig,'wb')
                myconfig = conn.retrieveFile('configs','all/emulationstation/'+file.filename,outfile,timeout=300)
                outfile.close()
                infile = open(destconfig,'r')
                myconfig = infile.read()
                infile.close()
                myconfig = myconfig.replace('<path>/home/pi/RetroPie','<path>smb://'+ip)
        if not myconfig:
            myconfig='<?xml version="1.0"?>\n<systemList>\n'
            systag='\t<system>\n\t\t<name>$NAME</name>\n\t\t<extension>$EXTENSIONS</extension>\n\t\t<platform>$NAME</platform>\n\t\t<path>$PATH</path>\n\t</system>\n'
            systems = conn.listPath('roms','')
            for system in systems:
                path = 'smb://'+ip+'/roms/'+system.filename
                sname=system.filename
                extns = apicalls.getSystemsExtensions(sname)
                thistag=systag.replace('$NAME',sname).replace('$PATH',path).replace('$EXTENSIONS',extns)
                myconfig=myconfig+thistag
            myconfig=myconfig+'</systemList>'
    if not myconfig:
        logging.error('###### COULD NOT FIND REMOTE CONFIG')
        return ''
    else:
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
            print (share)
            if 'roms' == share.name.lower():
                test = True
        print (test)
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
            if ('.' in ip.ip) and ('lo' not in ip.nice_name):
                print (ip)
    sys.exit()
    return myip,snet

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
    ip,snet = getNetInfo()
    tq = Queue()
    sq = Queue()
    foundlist =[]
    totthreads = 30
    threadList =[None]*totthreads
    n = 0
    done = False
    while not done:
        if n<256:
            for thrn in range (0,totthreads):
                if threadList[thrn]==None:
                    ipscan = ip[:ip.rindex('.')+1]+str(n)
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
                    foundlist.append(value)
        except:
           pass
        if all(x is None for x in threadList) and n>255:
            done = True
        sleep(0.1)
    return foundlist


