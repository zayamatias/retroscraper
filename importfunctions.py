import sys
import subprocess

def handleImportError(error):
    print ('Upgrading pip')
    result = subprocess.call([sys.executable,'-m','pip','install','--upgrade','pip','wheel','setuptools'])
    if result !=0:
        print ('If pip is not installed pls folow these instructions https://pip.pypa.io/en/stable/installation/')
        sys.exit()    
    if 'ifaddr' in error.lower():
        print ('Installing ifaddr, please wait')
        subprocess.call([sys.executable,'-m','pip','install','ifaddr'])
        return
    if 'paramiko' in error.lower():
        print ('Installing paramiko, please wait')
        #try:
        #    result = subprocess.call (['rustc','--version'])
        #except:
        #    result =1
        #if result !=0:
        #    print ('Installing Rust')
        #    subprocess.call(['wget','https://sh.rustup.rs','-O','/tmp/rust.sh'])
        #    subprocess.call(['sh','/tmp/rust.sh'])
        #    print ('Now run:')
        #    print ('source "$HOME/.cargo/env"')
        #    print ('And execute retroscraper again, sorry')
        #    sys.exit()
        print ('Installing paramiko')
        subprocess.call([sys.executable,'-m','pip','install','paramiko'])
        return
    if 'numpy' in error.lower():
        print ('Installing numpy, please wait')
        subprocess.call([sys.executable,'-m','pip','install','numpy'])
        return
    if 'smb' in error.lower():
        print ('Installing pysmb, please wait')
        subprocess.call([sys.executable,'-m','pip','install','pysmb'])
        return
    if 'bs4' in error.lower():
        print ('Installing beautifulsoup4, please wait')
        subprocess.call([sys.executable,'-m','pip','install','beautifulsoup4'])
        return
    if 'kivy' in error.lower():
        print ('Installing kivy, please wait')
        subprocess.call([sys.executable,'-m','pip','install','kivy'])
        subprocess.call([sys.executable,'-m','pip','install','kivy-garden.filebrowser'])
        return
    if 'googletrans' in error.lower():
        print ('Installing googletrans, please wait')
        subprocess.call([sys.executable,'-m','pip','install','googletrans==4.0.0rc1'])
        return
    if '_curses' in error.lower():
        print ('Installing curses for Windows, please wait')
        subprocess.call([sys.executable,'-m','pip','install','windows-curses'])
        return
    if 'PIL' in error.lower():
        print ('Installing Pillow, please wait')
        subprocess.call([sys.executable,'-m','pip','install','pillow'])
        return
    else:
        print ('There seems to be a module which has not be installed:')
        print (error)
        sys.exit()