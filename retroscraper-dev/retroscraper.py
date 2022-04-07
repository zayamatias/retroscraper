from curses.textpad import Textbox, rectangle
import logging
import os

#os.environ["KIVY_NO_CONSOLELOG"] = "1"
#os.environ["KCFG_KIVY_LOG_LEVEL"] = "info"
os.environ["KIVY_NO_ARGS"] = "1"
os.environ["KIVY_TEXT"] = "sdl2"
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from kivy.factory import Factory
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.image import AsyncImage
import scrapfunctions
import threading
import queue
from kivy.clock import Clock
import sys
from kivy.resources import resource_add_path, resource_find
import argparse
import curses
from time import sleep
import random
import signal
import logging
import apicalls
from kivy.config import Config
from math import ceil,sin,radians

globalapikey=''
version = '0.4'
trans = dict()

class MyPopup(FloatLayout):
    cancel = ObjectProperty(None)

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

class MainScreen(BoxLayout):

#### FILE CHOSER START
    stop_threads=False
    startlogox=0
    startlogoy=640
    angle = 0 
    supportedlanguages ={'af': 'afrikaans','sq': 'albanian','am': 'amharic','ar': 'arabic','hy': 'armenian','az': 'azerbaijani'\
                    ,'eu': 'basque','be': 'belarusian','bn': 'bengali','bs': 'bosnian','bg': 'bulgarian','ca': 'catalan'\
                    ,'ceb': 'cebuano','ny': 'chichewa','zh-cn': 'chinese (simplified)','zh-tw': 'chinese (traditional)'\
                    ,'co': 'corsican','hr': 'croatian','cs': 'czech','da': 'danish','nl': 'dutch','en': 'english'\
                    ,'eo': 'esperanto','et': 'estonian','tl': 'filipino','fi': 'finnish','fr': 'french','fy': 'frisian'\
                    ,'gl': 'galician','ka': 'georgian','de': 'german','el': 'greek','gu': 'gujarati','ht': 'haitian creole'\
                    ,'ha': 'hausa','haw': 'hawaiian','iw': 'hebrew','he': 'hebrew','hi': 'hindi','hmn': 'hmong'\
                    ,'hu': 'hungarian','is': 'icelandic','ig': 'igbo','id': 'indonesian','ga': 'irish','it': 'italian'\
                    ,'ja': 'japanese','jw': 'javanese','kn': 'kannada','kk': 'kazakh','km': 'khmer','ko': 'korean'\
                    ,'ku': 'kurdish (kurmanji)','ky': 'kyrgyz','lo': 'lao','la': 'latin','lv': 'latvian','lt': 'lithuanian'\
                    ,'lb': 'luxembourgish','mk': 'macedonian','mg': 'malagasy','ms': 'malay','ml': 'malayalam','mt': 'maltese'\
                    ,'mi': 'maori','mr': 'marathi','mn': 'mongolian','my': 'myanmar (burmese)','ne': 'nepali','no': 'norwegian'\
                    ,'or': 'odia','ps': 'pashto','fa': 'persian','pl': 'polish','pt': 'portuguese','pa': 'punjabi','ro': 'romanian'\
                    ,'ru': 'russian','sm': 'samoan','gd': 'scots gaelic','sr': 'serbian','st': 'sesotho','sn': 'shona','sd': 'sindhi'\
                    ,'si': 'sinhala','sk': 'slovak','sl': 'slovenian','so': 'somali','es': 'spanish','su': 'sundanese','sw': 'swahili'\
                    ,'sv': 'swedish','tg': 'tajik','ta': 'tamil','te': 'telugu','th': 'thai','tr': 'turkish','uk': 'ukrainian'\
                    ,'ur': 'urdu','ug': 'uyghur','uz': 'uzbek','vi': 'vietnamese','cy': 'welsh','xh': 'xhosa','yi': 'yiddish'\
                    ,'yo': 'yoruba','zu': 'zulu'}
    def dismiss_popup(self):
        self.dismissedpopup = True
        self._popup.dismiss()

    def show_dir_select(self):
        content = LoadDialog(load=self.selectdir, cancel=self.dismiss_popup)
        self._popup = Popup(title=trans['srd'], content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()


    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title=trans['ssf'], content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def show_info_popup(self,title,text,exit=False):
        if not exit:
            content = MyPopup(cancel=self.dismiss_popup)
        else:
            content = MyPopup(cancel=sys.exit)
        self._popup = Popup(title=title,content=content,
                            size_hint=(0.4, 0.2))
        try:
            self._popup.children[0].children[0].children[0].ids['popuplabel'].text = text
            self._popup.open()
        except:
            logging.error ('###### NO POPUP DEFINED')

    def selectdir(self,pathtofile,selectedfile):
        self.config['config']['MountPath']=pathtofile
        self.ids['maptopath'].text=pathtofile
        scrapfunctions.saveConfig(self.config)
        self.dismiss_popup()
        self.confok = self.initializeConfig()
        self.pathnokshown = False

    def load(self,pathtofile,selectedfile):
        logging.info ('##### LOADING SELECTED FILE '+str(selectedfile[0]))
        self.config['config']['SystemsFile']=selectedfile[0]
        scrapfunctions.saveConfig(self.config)
        self.dismiss_popup()
        self.confok = self.initializeConfig()
        self.pathnokshown = False
 
    def stopScanning(self,btn):
        self.scanqueue.put(True)
        self.callScanThreadEnd(False)

#### FILE CHOSER END
    def doDecorator(self,which):
        try:
            self.config['config']['decorators'][which]= not self.config['config']['decorators'][which]
        except:

            self.config['config']['decorators'][which]= True
        scrapfunctions.saveConfig(self.config)

    def doBezels(self,which):
        if which == 'game':
            try:
                self.config['bezels'] = not self.config['bezels']
            except:
                self.config['bezels'] = True
        if which == 'system':
            try:
                self.config['sysbezels'] = not self.config['sysbezels']
            except:
                self.config['sysbezels'] = True
        #logging.info (which)
        #logging.info (self.config['bezels'])
        #logging.info (self.config['sysbezels'])
        scrapfunctions.saveConfig(self.config)


    def deselectAll(self,btn=None):
        boxs = self.ids['systemschoice'].children
        for box in boxs:
            if box.children[0].text.upper()==trans['all'].upper():
                box.children[1].active=False
                break


    def selectAll(self,btn=None):
        boxs = self.ids['systemschoice'].children
        for box in boxs:
            if box.children[0].text.upper()==trans['all'].upper():
                if box.children[1].active:
                    box.children[1].active=False
                if not box.children[1].active:
                    box.children[1].active=True
            else:
                box.children[1].active=False

    def selectLang(self,btn=None):
        lanname = self.ids['langchoice'].text
        for pl in self.supportedlanguages.items():
            if pl[1].lower()==lanname.lower():
                self.config['config']['language']=pl[0]
                break
        scrapfunctions.saveConfig(self.config)
        self.loadLanguage(self.config['config']['language'])
        self.initLabels()

    def loadLanguage(self,lan):
        global trans
        logging.info ('###### GETTING LANGUAGES FROM REMOTE SERVER')
        complete = apicalls.getLanguagesFromAPI(self.apikey,self.uuid)
        logging.info ('###### GOT LANGUAGES FROM REMOTE SERVER')
        try:
            logging.info ('###### LOOKING FOR TRANSLATIONS IN '+str(lan))
            trans = complete[lan]
            logging.info ('###### FOUND THEM')
        except:
            logging.info('###### DFAULTING TO ENGLISH')
            try:
                trans = complete['en']
            except:
                print ('I CANNOT CONNECT TO TE BACKEND - EXITING')
                sys.exit()
        return 


    def initLabels(self):
        global trans
        self.ids['tabone'].text =trans['tabone']
        self.ids['tabtwo'].text =trans['tabtwo']
        self.ids['tabthree'].text =trans['tabthree']
        self.ids['tabfour'].text =trans['tabfour']
        self.ids['availsysLabel'].text=trans['availsys']
        self.ids['filesyslabel'].text=trans['filesys']
        self.ids['sysconfig'].text=trans['selfile']
        self.ids['sysrompathlabel'].text=trans['sysrompath']
        self.ids['maptopathlabel'].text=trans['maptopath']
        self.ids['selrompath'].text=trans['selpath']
        self.ids['gamedecorlabel'].text=trans['gamedecor']
        self.ids['versiondeclabel'].text=trans['versiondec']
        self.ids['countrydeclabel'].text=trans['countrydec']
        self.ids['hackdeclabel'].text=trans['hackdec']
        self.ids['diskdeclabel'].text=trans['diskdec']
        self.ids['preflanlabel'].text=trans['preflan']
        self.ids['usegooglelab'].text=trans['usegoogle']
        self.ids['bezeldownlabel'].text=trans['bezels']
        self.ids['sysbezellabel'].text=trans['sysbezels']
        self.ids['bezelssellabel'].text=trans['bezellabel']
        #self.ids['loadroot'].ids['loadbox'].ids['cancelbutton'].text=trans['cancel']
        #self.ids['selectbutton'].text=trans['select']
        #self.ids['okpopupbutton'].text=trans['okpopup']

    def initializeConfig(self):
        global trans
        logging.info ('###### LOADING CONFIG')
        self.config = scrapfunctions.loadConfig(logging)
        logging.info ('###### CONFIG LOADED')
        try:
            logging.info ('###### LOADING LANGUAGE FROM CONFIG')
            self.loadLanguage(self.config['config']['language'])
            logging.info ('###### LANGUAGE LOADED '+self.config['config']['language'])
        except:
            logging.info ('###### LANGUAGE DEFAULTED TO EN')
            self.loadLanguage('en')
        logging.info ('###### TESTING TRANS VARIABLE')
        if not trans:
            logging.info ('###### TRANS VARIABLE IS FALSE, ERROR')
            ## Special case with API
            self.show_info_popup('Backend Issue!','Cannot connect to backend.Are you connected to the internet?',True)
            return False
        logging.info ('###### TESTING CONFIG')
        if not self.config:
            logging.info ('###### THERE IS NO CONFIG, RETURNING ERROR')
            return False
        try:
            if not os.path.isfile(self.config['config']['SystemsFile']):
                ### Try to locate es_systems:
                if os.path.isfile('~/.emulationstation/es_systems.cfg'):
                    self.config['config']['SystemsFile'] = '~/.emulationstation/es_systems.cfg'
                if os.path.isfile('/etc/emulationstation/es_systems.cfg'):
                    self.config['config']['SystemsFile'] = '/etc/emulationstation/es_systems.cfg'
                if not os.path.isfile(self.config['config']['SystemsFile']):
                    logging.error('###### SYSTEMS FILE CANNOT BE FOUND '+str(self.config['config']['SystemsFile']))
                    return False
        except Exception as e:
            return False
        try:
            self.ids['systemsfile'].text= self.config['config']['SystemsFile']
        except:
            logging.error ('###### NO SYSTEMS FILE LABEL')
        logging.info ('###### GET SUSTEMS FROM BACKEND')
        self.remoteSystems = apicalls.getSystemsFromAPI(self.apikey,self.uuid)
        logging.info ('###### GOT SYSTEMS FROM BACKEND '+str(bool(self.remoteSystems)))
        logging.info ('###### LOAD SYSTEMS INTO CONFIG')
        self.systems = scrapfunctions.loadSystems(self.config,self.apikey,self.uuid,self.remoteSystems,self.q,trans,logging)
        logging.info ('###### LOADED SYSTEMS INTO CONFIG '+str(bool(self.systems)))
        if not self.systems:
            ## Special case with API
            self.show_info_popup('Backend Issue!','Cannot retrieve the systems from the backend.Are you connected to the internet?',True)
        else:
            try:
                self.ids['systemschoice'].remove_widget(self.ids['systemschoice'].children[0])
            except:
                pass
            totsystems = len(self.systems)
            if totsystems>5:
                totsystems=totsystems+1
            scols = 7
            srows = ceil(totsystems/scols)
            newbox= self.ids['systemschoice'] #.add_widget(newbox)
            newbox.clear_widgets()            
            newbox.size=(0,srows*20)
            newbox.orientation='lr-tb'
            newbox.cols=scols
            newbox.rows=srows
            newbox.size_hint=(1,None)
            try:
                if totsystems>5:
                    box= BoxLayout()
                    box.orientation='horizontal'
                    box.cols=2
                    box.rows=1
                    box.size_hint=(None,None)
                    box.size=(170,20)
                    lbl= Label() 
                    lbl.font_size=10
                    lbl.outline_color=(0,0,0)
                    lbl.outline_width=1
                    lbl.font_name='font.ttf'
                    lbl.text=trans['all']
                    lbl.text_size=(145,20)
                    lbl.valign='center'
                    chkbox = CheckBox(size_hint_x=0.2,active=True,color=(1,1,1))
                    chkbox.bind(on_press=self.selectAll)
                    box.add_widget(chkbox)
                    box.add_widget(lbl)
                    newbox.add_widget(box)

                for syst in self.systems:                
                    box= BoxLayout()
                    box.orientation='horizontal'
                    box.cols=2
                    box.rows=1
                    box.size_hint=(None,None)
                    box.size=(170,20)
                    lbl= Label()
                    lbl.font_size=10
                    lbl.outline_color=(0,0,0)
                    lbl.outline_width=1
                    lbl.font_name='font.ttf'
                    lbl.text_size=(145,20)
                    lbl.valign='center'
                    lbl.text=syst['name']
                    chkbox = CheckBox()
                    chkbox.size_hint_x=0.2
                    chkbox.bind(on_press=self.deselectAll)
                    box.add_widget(chkbox)
                    box.add_widget(lbl)
                    newbox.add_widget(box)
            except Exception as e:
                logging.error ('###### NO SYSTEMS CHOICE LAYOUT PRESENT '+str(e))
            self.companies = scrapfunctions.loadCompanies(self.apikey,self.uuid)
            try:
                self.ids['startScraping'].text = trans['stscr']
                self.ids['startScraping'].disabled = False
            except:
                logging.error ('###### NO START SCRAPPING BUTTON')
            self.rompath = scrapfunctions.getAbsRomPath(self.systems[0]['path'])
            self.ids['esrompath'].text = self.rompath
            self.ids['maptopath'].text = self.config['config']['MountPath']
            
            try:
                self.ids['bezeldown'].active=self.config['config']['bezels']
            except:
                self.config['config']['bezels'] = False
                self.ids['bezeldown'].active=False
            try:
                self.ids['sysbezeldown'].active=self.config['config']['sysbezels']
            except:
                self.config['config']['sysbezels'] = False
                self.ids['sysbezeldown'].active=False

            try:
                decorators = self.config['config']['decorators']
            except:
                self.config['config']['decorators']=dict()
                decorators = self.config['config']['decorators']
            for decorator in decorators:
                if self.config['config']['decorators'][decorator]:
                    try:
                        self.ids[decorator+'mod'].active=True
                    except:
                        logging.error ('###### CONFIG '+decorator+' DOES NOT EXIST')
                        pass
            try:
                test = self.config['config']['language']
            except:
                self.config['config']['language']='en'
            sls = []
            for sl in self.supportedlanguages.items():
                sls.append(sl[1])
                if sl[0]==self.config['config']['language'].lower():
                    self.ids['langchoice'].text=sl[1]
            self.ids['langchoice'].values = sls
            try:
               self.usegoogle=self.config['config']['usegoogle']
            except:
                self.config['config']['usegoogle']=False
            self.ids['usegoogle'].active = self.config['config']['usegoogle']
            self.initLabels()
            return True


    def toggleUseGoogle(self,btn=None):
        self.config['config']['usegoogle']=self.ids['usegoogle'].active
        scrapfunctions.saveConfig(self.config)
        return 

    def ScanToggle(self,btn=None):
        if not self.scanning:
            self.ids['startScraping'].text = trans['stoscr']
            boxs = self.ids['systemschoice'].children
            #boxs = grid.children
            systemstoscan=['NONE']
            for box in boxs:
                if box.children[1].active:
                    if box.children[0].text.upper()==trans['all']:
                        systemstoscan=[]
                        break
                    else:
                        systemstoscan.append(box.children[0].text)
            self.scanqueue = queue.Queue()
            self.t = threading.Thread(target= scrapfunctions.scanSystems,args=(self.q,self.systems,self.apikey,self.uuid,self.companies,self.config,logging,self.remoteSystems,systemstoscan,self.scanqueue,self.rompath,trans))
            self.t.start()
            self.scanning=True
        else:
            self.scanqueue.put(True)
    
    def callScanThreadEnd(self,gentle):
        self.t.join()
        if not gentle:
            self.ids['sysLabel'].text=trans['swasab']
            self.scanning = False
        else:
            self.ids['sysLabel'].text=trans['scanend']
            self.scanning = False
        self.ids['startScraping'].text=trans['stscr']
  
    def show_popup(self,which):
        if not self.dismissedpopup and not self.popupshown:
            if which == 'confnotok':
                self.show_info_popup(trans['nosys'],trans['nosysmsg'])
            if which == 'vernotok':
                self.show_info_popup(trans['outver'],trans['outvermsg'],True)
            if which == 'pathnotok':
                self.show_info_popup(trans['pathwarn'],trans['pathwarnmsg'],False)
            self.popupshown = True

    def getQueue(self,event):
        global trans
        if not trans:
            return
        if not self.validversion:
            self.validversion = scrapfunctions.isValidVersion(self.version,self.apikey,self.uuid)
            if not self.validversion:
                self.show_popup("vernotok")
                return

        if not self.confok :
            self.ids['startScraping'].disabled = True
            self.ids['startScraping'].text = trans['waitforconf']
            self.show_popup("confnotok")
            return

        if not self.pathok and not self.pathnokshown:
            if self.config['config']['MountPath']:
                testpath = self.config['config']['MountPath']
            else:
                testpath = self.rompath
            if  self.rompath =='' or not os.path.isdir(testpath):
                #print ('lllllllllllllllllllllllllllllllllllllllllllllllllll')
                self.show_popup("pathnotok")
                self.pathnokshown = True
                self.pathok = False
            else:
                self.pathnokshown = True
                self.pathok = True

        #logox=self.startlogox
        #self.angle += 10
        #logoy=self.startlogoy+int(sin(radians(self.angle))*10)
        #if self.angle==360:
        #    self.angle = 0
        #self.ids['retroscraperimage'].pos=(logox,logoy)
        try:
            event = self.q.get_nowait()
        except:
            event=''
        if event!='':
            if event[1]=='text':
                if event[0].lower()!='errorlabel':
                    #print (event[0])
                    self.ids[event[0]].text=event[2]
                else:
                    try:
                        errGrid = self.ids['errorgrid']
                        errGrid.bind(minimum_height=errGrid.setter('height'))
                        newlabel = Label(text=event[2],size_hint=(None,None),outline_color=(0,0,0),outline_width=1,font_name='font.ttf',font_size= 12,padding_x=5)
                        newlabel._label.refresh()
                        newlabel.size=newlabel._label.texture.size
                        errGrid.add_widget(newlabel)
                    except:
                        logging.error ('###### NO ERROR TAB DEFINED')
            if event[1]=='valueincrease':
                self.ids[event[0]].value += 1
            if event[1]=='max':
                self.ids[event[0]].max = event[2]
            if event[1]=='value':
                self.ids[event[0]].value = event[2]
            if event[1]=='source':
                self.ids[event[0]].source=event[2]
                if event[2] == '':
                    self.ids[event[0]].color=(0,0,0,0)
                else:
                    self.ids[event[0]].color=(1,1,1,1)
                self.ids[event[0]].reload()
            if event[1]=='scandone':
                self.callScanThreadEnd(event[2])
            if event[1]=='popup':
                self.show_info_popup(event[0],event[2])

    def start(self):
        Clock.schedule_interval(self.getQueue, 0.1)


    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        global version
        self.version = version
        self.validversion = False
        self.apikey = globalapikey
        self.uuid = scrapfunctions.getUniqueID()
        self.q = queue.Queue()
        self.confok = self.initializeConfig()
        self.dismissedpopup = False
        self.popupshown = False
        self.pathok = False
        self.pathnokshown = False
        self.icon = 'icon.ico'
        self.scanning = False

class retroscraperApp(App):
    def build(self):
        global version
        self.icon='icon.ico'
        self.title = 'retroScraper ['+str(version)+']'
        picnr = random.randint(1,13)
        self.image_source = AsyncImage (source='http://77.68.23.83/res/back/'+str(picnr)+'.png')
        ms = MainScreen()
        ms.start()
        return ms


def resourcePath():
    '''Returns path containing content - either locally or in pyinstaller tmp file'''
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS)

    return os.path.join(os.path.abspath("."))


Factory.register('Root', cls=MainScreen)

def showrandom(q):
    while True:
        q.put(random.randrange(100))
        sleep(1)

def signal_handler(sig, frame):
    print ('REQUESTED TO END')
    curses.curs_set(1)
    curses.endwin()
    #q.put(True)
    print('SCRAP ABORTED!!! --- Last system might have not been completely scrapped!!\n')
    sys.exit(0)

if __name__ == '__main__':
    logging.basicConfig(filename='retroscraper.log', encoding='utf-8', level=logging.DEBUG)
    parser = argparse.ArgumentParser(description='RetroScraper...supercharge your roms with metadata!')
    parser.add_argument('--cli', help='Run in CLI (Command Line Interface Mode)',action='store_true')
    parser.add_argument('--systemsfile', help='locayion of the es_systems.cfg file)',nargs=1)
    parser.add_argument('--silent', help='Run in SILENT mode, minimum output to console no fancy screen, needs --cli flag also',action='store_true')
    parser.add_argument('--language', help='Select language for descriptions',nargs=1)
    parser.add_argument('--google', help='Use google translate if description not found in your language',action='store_true')
    parser.add_argument('--country', help='Add country decorator from filename [Sonic (es)]',action='store_true')
    parser.add_argument('--disk', help='Add disk decorator fromfilename [Sonic (disk 1/2)]',action='store_true')
    parser.add_argument('--version', help='Add version decorator fromfilename [Sonic V1.10]',action='store_true')
    parser.add_argument('--hack', help='Add hack decorator fromfilename [Sonic (madhedgehog hack)]',action='store_true')
    parser.add_argument('--bezels', help='Download bezels for games',action='store_true')
    parser.add_argument('--sysbezels', help='Download system bezel if game bezel is not found',action='store_true')
    argsvals = vars(parser.parse_args())
    print ('Loading RetroScraper config File')
    logging.info ('###### LOADING RETROSCRAPER CONFIG')
    config = scrapfunctions.loadConfig(logging)
    try:
        cli = argsvals['cli']
    except:
        cli = False    
    try:
        silent = argsvals['silent']
    except:
        silent = False
    try:
        if 'decorators' in config['config'].keys:
            pass
    except:
        config['config']['decorators']=dict()
    try:
        config['config']['decorators']['country']= argsvals['country']
    except:
        config['config']['decorators']['country']= False
    try:
        config['config']['decorators']['disk']= argsvals['disk']
    except:
        config['config']['decorators']['disk']= False
    try:
        config['config']['decorators']['version']= argsvals['version']
    except:
        config['config']['decorators']['version']= False
    try:
        config['config']['decorators']['hack']= argsvals['hack']
    except:
        config['config']['decorators']['hack']= False
    try:
        config['config']['usegoogle']= argsvals['google']
    except:
        config['config']['usegoogle']= False
    try:
        config['config']['bezels']= argsvals['bezels']
    except:
        config['config']['bezels']= False
    try:
        config['config']['sysbezels']= argsvals['sysbezels']
    except:
        config['config']['sysbezels']= False
    try:
        config['config']['language']= argsvals['language'][0].lower()
    except:
        config['config']['language']= 'en'
    try:
        config['config']['SystemsFile']= argsvals['systemsfile'][0]
    except:
        pass
    resource_add_path(resourcePath()) 
    if not cli:
        Config.set('graphics', 'width', '1200')
        Config.set('graphics', 'height', '750')
        Config.set('graphics', 'resizable', True)
        Config.write()
        retroscraperApp().run()    
    else:
        print ('WHAT!')
        apikey =globalapikey
        uuid = scrapfunctions.getUniqueID()
        complete = apicalls.getLanguagesFromAPI(apikey,uuid)
        trans = complete['en']
        scanqueue = queue.Queue()
        try:
            signal.signal(signal.SIGINT,signal_handler) 
        except:
            pass
        try:
            signal.signal(signal.CTRL_C_EVENT,signal_handler) 
        except:
            pass
        try:
            signal.signal(signal.SIGBREAK,signal_handler) 
        except:
            pass
        try:
            signal.signal(signal.CTRL_BREAK_EVENT,signal_handler) 
        except:
            pass
        #signal.signal(signal.SIGINT, lambda signum, frame: signal_handler(signum, frame, scanqueue))
        q=queue.Queue()
        if not scrapfunctions.isValidVersion(version,apikey,uuid):
            print ('SORRY! YOU NEED TO UPGRADE TO THE LATEST VERSION http://77.68.23.83/download.html')
            logging.error('###### THIS IS NOT THE LATEST VERSION OF RETROSCRAPER')
            sys.exit()
        logging.debug('###### CONFIG :'+str(config))
        if not os.path.isfile(config['config']['SystemsFile']):
            ### Try to locate es_systems:
            if os.path.isfile('~/.emulationstation/es_systems.cfg'):
                config['config']['SystemsFile'] = '~/.emulationstation/es_systems.cfg'
            if os.path.isfile('/etc/emulationstation/es_systems.cfg'):
                config['config']['SystemsFile'] = '/etc/emulationstation/es_systems.cfg'
            if not os.path.isfile(config['config']['SystemsFile']):
                print ('There seems to be an error in your retroscraper config file, I cannot find the systems configuration file (usually something like es_systems.cfg)')
                logging.error('###### SYSTEMS FILE CANNOT BE FOUND '+str(config['config']['SystemsFile']))
                sys.exit()
        scrapfunctions.saveConfig(config)
        print ('Loading systems from Backend')
        logging.info ('###### LOADING SYSTEMS FROM BACKEND')
        remoteSystems = apicalls.getSystemsFromAPI(apikey,uuid)
        systems = scrapfunctions.loadSystems(config,apikey,uuid,remoteSystems,q,trans,logging)
        print ('Loading companies from backend')
        logging.info ('###### LOADING COMPANIES FROM BACKEND')
        companies = scrapfunctions.loadCompanies(apikey,uuid)
        rompath = scrapfunctions.getAbsRomPath(systems[0]['path'])
        print ('Starting scraping')
        logging.info ('###### STARTING SCRAPPING ')
        if not silent:
            try:
                stdscr = curses.initscr()
            except Exception as e:
                print (str(e))            
            curses.noecho()
            curses.cbreak()
            curses.curs_set(0)
            curses.echo()
            try:
                stdscr.refresh()
            except Exception as e:
                print ('ERROR '+str(e))
        logging.info ('STARTING THREADS')
        thread = threading.Thread(target= scrapfunctions.scanSystems,args=(q,systems,apikey,uuid,companies,config,logging,remoteSystems,[],scanqueue,rompath,trans))
        thread.start()
        system =''
        game=''
        scrapping = True
        while scrapping:
            if not silent:
                rows, cols = stdscr.getmaxyx()
            else:
                rows = 0
                cols = 0
            if cols > 100:
                ncols = 100
            else:
                ncols = cols
            if rows > 6:
                nlines = 6
            else:
                nlines = rows    
            uly, ulx = int((rows-nlines)/2),int((cols-ncols)/2)
            #try:
            #    if stdscr.getch() == curses.KEY_RESIZE:            
            #        rows,cols = stdscr.getmaxyx()
            #except:
            #    pass
            #stdscr.erase()
            #stdscr.addstr (1,1,'Y:'+str(uly)+' X:'+str(ulx)+' LINES:'+str(nlines)+' COLS:'+str(ncols),curses.A_NORMAL)
            #stdscr.refresh()
            try:
                qu = q.get_nowait()
                if qu[0].lower()=='scrappb' and qu[1].lower()=='max':
                    interval = ncols/qu[2]
                    progress = "-"*ncols
                    pcount = 0
                if qu[0].lower()=='scrappb' and qu[1].lower()=='valueincrease':
                    pcount = pcount + interval
                    progress = "#"*int(pcount)
                    progress = progress +'-'*(ncols-int(pcount))
                if qu[0].lower()=='syslabel':
                    system = qu[2].strip().replace('\n',' ')
                    if silent:
                        print ('SYSTEM '+system)
                if qu[0].lower()=='gamelabel':
                    game = qu[2].strip().replace('\n',' ')
                    if silent:
                        print (game)
                if not silent:
                    stdscr.erase()
                    rectangle(stdscr, uly-1, ulx-1, uly + nlines, ulx + ncols)
                    stdscr.addstr(uly, ulx, system ,curses.A_NORMAL)
                    stdscr.addstr(uly+1, ulx, game ,curses.A_NORMAL)
                    stdscr.addstr(uly+2, ulx, progress ,curses.A_NORMAL)
                    stdscr.refresh()
            except Exception as e:
                pass
            sleep(0.01)
            if not thread.is_alive():
                scrapping= False
        if not silent:
            curses.curs_set(1)
            curses.endwin()
        print('SCRAPPING ENDED --- Thank you for using retroscraper!!\n')
        logging.info ('###### ALL DONE!')
        sys.exit(0)