# RetroScraper
RetroScraper - Metadata &amp; Media scraper for your rom collection 

Runs and has been tested under python 3.9 & 3.7, I've tested it under windows, linux and rpi distrubutions, but of course, errors will still occur.

RPI binary has been compiled on an actual retropie image (latest version).

You need to install the requirements for you platform before being able to run it from source.

This scraper uses its own backend, which has been compiled from many sources on the net and keeps extending. If this is a problem for you, do not run this software.

This scraper will create a local DB with the checksum of your roms, for purposes of speed if you have large files. If this is a problem for you, use the --nodb modifier.

It will create a backup of the gamelist.xml files by default, use the --nobackup modifier to overwrite them directly.

## Running the software:

### From source:

Excute as 'python retroscraper.py'.

**In order to run from the source, you will need an API key, pls reuest this to retroscraper[at]gmail.com**

### From precompiled binaries:

Simply download the pre-compiled binaries for your system from the [releases page](https://github.com/zayamatias/retroscraper/releases). Currently windows, rpi and linux_x64 exist. For linux version you need to do 'chmod +rwx retroscraper.linux' and for rpi 'chmod +rwx retroscraper.rpi' to be able to execute it.

At first run it will create an empty retroscraper.cfg file, which will be used to keep the configuration as you edit it.

In every run, it will verify with the backend if the version you're running is the latest one. It will also download te resources needed (images/translations). If you have a problem wuth this, please do not use it.

## GUI Mode

GUI mode is executed if you run the program without any commands (python retroscraper.py) and opens a windows such as this:

![image](https://user-images.githubusercontent.com/32246591/162161430-0f74ff42-00d2-4e27-82df-4fa56c3a0bee.png)

This is the main screen. 

There are 4 tabs, =Games=, =Systems=, =Configuration= and =Errors=

The =Errors= tab shows you a log with the erros during scraping, which may help you troubleshoot the execution.

![image](https://user-images.githubusercontent.com/32246591/162163083-8b0f0da6-b30d-4988-aed4-862015e0dfd8.png)

The =Games= tab show the actual scraping status of every rom.

![image](https://user-images.githubusercontent.com/32246591/162163298-8414220d-5299-4ad6-852c-897c9ca92063.png)

The blue bar on the lower part of the screen shows the progress of the current system.

The =Systems= tab allows you to select which systems you want to scrape, either all, or individually sleected ones.

![image](https://user-images.githubusercontent.com/32246591/162163527-4171a0db-523d-4c71-86ab-d4f421358313.png)

It also shows the current system being scraped (if you started scraping) and te number of files to be scraped for that system.

last but not least, the =Configuration= tab, allows you to configure the tool to suit your needs.

![image](https://user-images.githubusercontent.com/32246591/162164152-a4cfd3bf-bdf8-4005-bcf0-132c5f2a9eb7.png)

### Configuatrion items:

#### Systems File: 

Location of the, usually called, es_systems.cfg file, this is the emulation station file that holds the information for the systems ands roms directories you have set up. it is similar to the _ _'--systemsfile'_ _ option in the _ _'--cli'_ _ version. By default Retroscraper will try to locate it in the usual directories, if unsuccesfull it will be left blank.

#### Systems Roms Path:

This will tell you where your roms are located according to your _ _es_systems.cfg_ _ file. If you're importing this file from a machine in your network, it will actually show wwhere they are in that machine.

#### Map To Path:

This will allow you to map the previous path to a path in your local machine, so if you mount the remote machine rom's directory into the machine executing retroscraper, retroscraper will be able to access the roms on the remote machine as if they were local.

#### Name Decorators:

The following options allow you to add 'decorators' to the name taht is going to be displayed in your system, for example:

#### Add Version: 

Will get any string that matches (Vxxxxx) in the rom filename and insert it in the final name for the game. If your rom is called _ _'My Super Game (v3).zip'_ _ , your game name will be displayed as _ _'My Super Game (v3)'_ _ 

This is similar to the _ _--version_ _ command

#### Add Hack/Beta:

Similar to previous option, but searching for matches of _ _(xxxx Beta xxxx)_ _ or _ _(xxxx Hack xxxx)_ _

This is similar to the _ _--hack_ _ command

#### Add Country/Language:

Simiular to previous option, but searching for matches of _ _(xx)_ _ where xx is an identified country/language shortname, such as usa,fr, en, es, etc..

This is similar to the _ _--country_ _ command

#### Add Disk/Tape:

Simiular to previous option, but searching for matches of _ _(Tape xx of yy)_ _ or _ _(Disk xx of yy)_ _ where xx and yy are numbers or letters such as _ _(Tape A)_ _ or _ _(Disk 1 of 2)_ _

This is similar to the _ _--disk_ _ command

All previous options will relay on the filename, so if the information is not in the filename, it will not show in the final name.

#### Bezels

This two options allow you to download the game bezels (this is usually a pciture surrounding the playing area) and will allow you to decide if you want to download the generic system bezel if the game bezel is not found.

This is similar to the _ _--bezels_ _ command and _ _--sysbezels_ _

#### Media Download preferences.

Do you prefer to have the game box instead of the screenshot? Select it here. Do you prefer not to download videos? You can also do it here.

#### Preferred Language:

Select your preferred language form the drop down list. If supported the interface will change to that language (currently en, fr & es are supported).

If you select to use google translate, the games desciptions which are not available in the selected language, will be translated by google.

This is similar to the _ _--language xx_ _ command and _ _--google_ _

#### No DB

Retroscraper creates a local retroscraper.db file, where it will store all the checksums for yoru files. This is done to avoid losing extra time in subsequent runs, specially fro large files. If you prefer to calculate the hashes on teh fly, use the _ _--nodb_ _ modifier

#### No Backup:

Since latest version, RetroScraper will autoamtically generate a backup of your gamelist.xml file for each system, by adding a number to it (gamelist.xml.1, gamelist.xml.2 and so forth). If you want to avoid having these backups created, use the _ _--nobackup_ _ modifier.



