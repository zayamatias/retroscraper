from hashlib import md5 as hashlibmd5
from hashlib import sha1 as hashlibsha1
from ipaddress import ip_address
from zlib import crc32 as zlibcrc32
import sqlite3 as sl
from pathlib import Path as Path
import logging
import remote
import os


def getRemoteChksums(config,filepath,logging,thn):
    if 'ssh://' in filepath:
        ip,chkfile = remote.getFileBits(filepath,'ssh://',thn)
        chkfile=chkfile.replace('$','\$')
        logging.info('###### THIS IS A SSH CALCULATION FOR '+str(chkfile)+' AT '+ip+' THREAD['+str(thn)+']')
        sha1 =''
        md5=''
        crc =''
        while sha1 == '':
            sha1= remote.runRemoteCommand (ip,'sha1sum -b "'+chkfile+'"',thn,logging)
            sha1 = sha1.replace('\n','')
            if sha1 == '':
                logging.info ('###### COULD NOT GET SSHA FOR ['+chkfile+'], RETRYING IN THREAD ['+thn+']')
        while md5 =='':
            md5 = remote.runRemoteCommand (ip,'md5sum "'+chkfile+'"',thn,logging)
            md5 = md5.replace('\n','')
        while crc == '':
            crc = remote.runRemoteCommand (ip,'crc32 "'+chkfile+'"',thn,logging)
            crc = crc.replace('\n','')
        return sha1.split(' ')[0].upper(),md5.split(' ')[0].upper(),crc.split(' ')[0].upper()
    if 'smb://' in filepath:
        ip,chkfile = remote.getFileBits(filepath,'smb://',thn)
        logging.info('###### THIS IS A SMB CALCULATION FOR '+str(chkfile)+' AT '+ip+' THREAD['+str(thn)+']')
        localfilename = remote.getSMBfile(config,ip,chkfile,thn,logging)
        rsha1,rmd5,rcrc = calculate(config,localfilename,logging,thn)
        os.remove(localfilename)
        return rsha1,rmd5,rcrc
        

def calculate(config,file,logging,thn):
    if not remote.testPathIsRemote(file,logging,thn):
        try:
            showfile = file.encode('utf-8').decode()
        except:
            showfile = ''
        logging.info ('####### CALCULATING CHECKSUMS FROM FILE DIRECTLY '+str(showfile)+'THREAD['+str(thn)+']')
        BUF_SIZE = 65536
        bytes = 0
        md5 = hashlibmd5()
        sha1 = hashlibsha1()
        crcvalue= 0 
        with open(file, 'rb') as f:
            while True:
                logging.info ('####### '+showfile+' STILL CALUCLATING CHECKSUMS '+str(bytes)+'THREAD['+str(thn)+']')
                try:
                    data = f.read(BUF_SIZE)
                    if not data:
                        logging.info ('####### '+showfile+' REACHED END OF FILE DATA THREAD['+str(thn)+']')
                        break
                    bytes=bytes + BUF_SIZE
                    md5.update(data)
                    sha1.update(data)
                    crcvalue = zlibcrc32(data, crcvalue)
                except Exception as e:
                    logging.error ('##### ERROR, FILE HAS DISSAPEARED! '+str(e)+'THREAD['+str(thn)+']')
        rsha1 = sha1.hexdigest().upper()
        rmd5 = md5.hexdigest().upper()
        rcrc = format(crcvalue & 0xFFFFFFFF, '08x').upper()
        logging.info ('####### DONE CALCULATING CHECKSUMS FROM FILE DIRECTLY THREAD['+str(thn)+']')
        return rsha1,rmd5,rcrc
    else:
        logging.info ('###### THIS IS A REMOT FILE, I\'LL GET THE REMOTE WAY THREAD['+str(thn)+']')
        return getRemoteChksums(config,file,logging,thn)


def getfromDB(config,file,logging,thn):
    rsha1=''
    rmd5=''
    rcrc=''
    try:
        logging.info ('###### CONNECTING TO CHECKSUMS DB THREAD['+str(thn)+']')
        con = sl.connect(str(Path.home())+'/.retroscraper/retroscraper.db')
        logging.info ('###### CONNECTED TO CHECKSUMS DB THREAD['+str(thn)+']')
    except Exception as e:
        logging.error ('###### ERROR CONNECTING TO CEHCKSUMS DB '+str(e)+'THREAD['+str(thn)+']')
        return rsha1,rmd5,rcrc
    logging.info ('###### GETTING VALUES FORM DB THREAD['+str(thn)+']')
    query = 'SELECT sha1,md5,crc FROM CSUMS WHERE filename=?'
    try:
        qfile = file.encode().decode('utf-8')
        values=(qfile,)
        cur = con.execute(query,values)
        data = cur.fetchall()
        logging.info ('###### GOT VALUES FORM DB THREAD['+str(thn)+']')
        for row in data:
            rsha1 = row[0]
            rmd5 = row[1]
            rcrc = row[2]
    except Exception as e:
        logging.error ('###### ERROR GETTING FROM DB -> '+str(e)+'THREAD['+str(thn)+']')
        data =[]
        try:
            logging.info ('###### CREATING EMPTY INSTANCE OF DB THREAD['+str(thn)+']')
            con.execute("""
                CREATE TABLE CSUMS (
                filename VARCHAR (500) NOT NULL PRIMARY KEY,
                sha1 VARCHAR(100),
                md5 VARCHAR(100),
                crc VARCHAR(100));
                """)
            con.commit()
        except Exception as e:
            logging.info ('###### ERROR CREATING EMPTY INSTANCE OF DB '+str(e)+'THREAD['+str(thn)+']')
    if rsha1=='' or rmd5=='' or rcrc=='':
        logging.info ('###### THERE WAS NO SHA IN DB SO I CALCULATE IT THREAD['+str(thn)+']')
        rsha1, rmd5, rcrc = calculate(config,file,logging,thn)
        if rsha1!='':
            sql = 'REPLACE INTO CSUMS (filename,sha1,md5,crc) VALUES (?,?,?,?)'
            try:
                efile = file.encode().decode('utf-8')
            except:
                efile =''
            values = (efile,rsha1,rmd5,rcrc)
            try:
                logging.info ('###### INSERTING VALUES IN DB THREAD['+str(thn)+']')
                if efile !='':
                    con.execute(sql,values)
                    con.commit()
                    logging.info ('###### INSERTED VALUES THREAD['+str(thn)+']')
                else:
                    logging.info ('##### FILE NOT INSERTED INTO THE DB DUE TO STRANGE ENCODING IN THREAD ['+str(thn)+']')
            except Exception as e:
                try:
                    showfile = file.encode('utf-8').decode()
                except:
                    showfile =''
                logging.error ('======>>>>'+str(e)+' ====>'+showfile+'THREAD['+str(thn)+']')
    logging.info ('###### CLOSING CHECKSUMS DB THREAD['+str(thn)+']')
    con.close()
    logging.info ('###### RETURNING FROM CALCULATIONS THREAD['+str(thn)+']')
    return rsha1,rmd5,rcrc

def getChecksums(file,config,logging,thn):
    logging.info ('###### CALCULATING CHECKSUMS THREAD['+str(thn)+']')
    try:
        if not config['config']['nodb']:
            logging.info ('###### GETTING FROM DB THREAD['+str(thn)+']')
            sha1, md5, crc = getfromDB(config,file,logging,thn)
        else:
            logging.info ('###### CALCULATING THREAD['+str(thn)+']')
            sha1, md5, crc = calculate(config,file,logging,thn)
        return sha1,md5,crc
    except Exception as e:
        logging.error ('###### ERROR IN CHECKSUMS '+str(e)+'THREAD['+str(thn)+']')
        sha1, md5, crc = getfromDB(config,file,logging,thn)
        return sha1,md5,crc
