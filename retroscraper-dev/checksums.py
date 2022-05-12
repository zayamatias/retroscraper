from hashlib import md5 as hashlibmd5
from hashlib import sha1 as hashlibsha1
from zlib import crc32 as zlibcrc32
import sqlite3 as sl
from pathlib import Path as Path
import logging


def calculate(file,logging):
    logging.info ('####### CALCULATING CHECKSUMS FROM FILE DIRECTLY '+str(file))
    BUF_SIZE = 65536
    bytes = 0
    md5 = hashlibmd5()
    sha1 = hashlibsha1()
    crcvalue= 0 
    with open(file, 'rb') as f:
        while True:
            logging.info ('####### '+file+' STILL CALUCLATING CHECKSUMS '+str(bytes))
            try:
                data = f.read(BUF_SIZE)
                if not data:
                    logging.info ('####### '+file+' REACHED END OF FILE DATA')
                    break
                bytes=bytes + BUF_SIZE
                md5.update(data)
                sha1.update(data)
                crcvalue = zlibcrc32(data, crcvalue)
            except Exception as e:
                logging.error ('##### ERROR, FILE HAS DISSAPEARED! '+str(e))
    rsha1 = sha1.hexdigest().upper()
    rmd5 = md5.hexdigest().upper()
    rcrc = format(crcvalue & 0xFFFFFFFF, '08x').upper()
    logging.info ('####### DONE CALCULATING CHECKSUMS FROM FILE DIRECTLY')
    return rsha1,rmd5,rcrc

def getfromDB(file,logging):
    try:
        logging.info ('###### CONNECTING TO CEHCKSUMS DB')
        con = sl.connect(str(Path.home())+'/.retroscraper/retroscraper.db')
        logging.info ('###### CONNECTED TO CEHCKSUMS DB')
    except Exception as e:
        logging.info ('###### ERROR CONNECTING TO CEHCKSUMS DB '+str(e))
    rsha1=''
    rmd5=''
    rcrc=''
    with con:
        try:
            logging.info ('###### GETTING VALUES FORM DB')
            query = 'SELECT sha1,md5,crc FROM CSUMS WHERE filename=?'
            values=(file,)
            cur = con.execute(query,values)
            data = cur.fetchall()
            logging.info ('###### GOT VALUES FORM DB')
            for row in data:
                rsha1 = row[0]
                rmd5 = row[1]
                rcrc = row[2]
        except Exception as e:
            logging.error ('###### ERROR GETTING FROM DB -> '+str(e))
            data =[]
            try:
                logging.info ('###### CREATING EMTY INSTANCE OF DB')
                con.execute("""
                    CREATE TABLE CSUMS (
                    filename VARCHAR (500) NOT NULL PRIMARY KEY,
                    sha1 VARCHAR(100),
                    md5 VARCHAR(100),
                    crc VARCHAR(100)
                    );
                    """)   
            except Exception as e:
                logging.info ('###### ERROR CREATING EMTY INSTANCE OF DB '+str(e))
    if rsha1=='':
        logging.info ('###### THERE WAS NO SHA IN DB SO I CALCULATE IT')
        rsha1, rmd5, rcrc = calculate(file,logging)
        sql = 'INSERT INTO CSUMS (filename,sha1,md5,crc) VALUES (?,?,?,?)'
        values = (file,rsha1,rmd5,rcrc)
        try:
            logging.info ('###### INSERTING VALUES IN DB')
            con.execute(sql,values)
            con.commit()
            logging.info ('###### INSERTED VALUES')
        except Exception as e:
            logging.error ('======>>>>'+str(e)+' ====>'+file)
    logging.info ('###### RETURNING FROM CALCULATIONS')
    return rsha1,rmd5,rcrc

def getChecksums(file,config,logging):
    try:
        if not config['config']['nodb']:
            logging.info ('###### GETTING FROM DB')
            sha1, md5, crc = getfromDB(file,logging)
        else:
            logging.info ('###### CALCULATING')
            sha1, md5, crc = calculate(file,logging)
        return sha1,md5,crc
    except Exception as e:
        logging.error ('###### ERROR IN CHECKSUMS '+str(e))
        sha1, md5, crc = getfromDB(file,logging)
        return sha1,md5,crc
