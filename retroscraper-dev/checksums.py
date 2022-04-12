from hashlib import md5 as hashlibmd5
from hashlib import sha1 as hashlibsha1
from zlib import crc32 as zlibcrc32
import sqlite3 as sl



def calculate(file):
    BUF_SIZE = 65536
    md5 = hashlibmd5()
    sha1 = hashlibsha1()
    crcvalue= 0 
    with open(file, 'rb') as f:
        while True:
            try:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                md5.update(data)
                sha1.update(data)
                crcvalue = zlibcrc32(data, crcvalue)
            except Exception as e:
                print ('##### ERROR, FILE HAS DISSAPEARED! '+str(e))
    rsha1 = sha1.hexdigest().upper()
    rmd5 = md5.hexdigest().upper()
    rcrc = format(crcvalue & 0xFFFFFFFF, '08x').upper()
    return rsha1,rmd5,rcrc

def getfromDB(file):
    con = sl.connect('retroscraper.db')
    rsha1=''
    rmd5=''
    rcrc=''
    with con:
        try:
            query = 'SELECT sha1,md5,crc FROM CSUMS WHERE filename=?'
            values=(file,)
            cur = con.execute(query,values)
            data = cur.fetchall()
            for row in data:
                rsha1 = row[0]
                rmd5 = row[1]
                rcrc = row[2]
        except Exception as e:
            data =[]
            try:
                con.execute("""
                    CREATE TABLE CSUMS (
                    filename VARCHAR (500) NOT NULL PRIMARY KEY,
                    sha1 VARCHAR(100),
                    md5 VARCHAR(100),
                    crc VARCHAR(100)
                    );
                    """)   
            except:
                pass     
    if rsha1=='':
        rsha1, rmd5, rcrc = calculate(file)
        sql = 'INSERT INTO CSUMS (filename,sha1,md5,crc) VALUES (?,?,?,?)'
        values = (file,rsha1,rmd5,rcrc)
        try:
            con.execute(sql,values)
            con.commit()
        except Exception as e:
            print ('======>>>>'+str(e)+' ====>'+file)
    return rsha1,rmd5,rcrc

def getChecksums(file,config):
    try:
        if not config['config']['nodb']:
            sha1, md5, crc = getfromDB(file)
        else:
            sha1, md5, crc = calculate(file)
        return sha1,md5,crc
    except:
        sha1, md5, crc = getfromDB(file)
        return sha1,md5,crc
