# RetroScraper
RetroScraper - Metadata &amp; Media scraper for your rom collection 

Runs and has been tested under python 3.9, I've tested it under windows, linux and rpi distrubutions.

You need to install the requirements for you platform before being able to run it.

This scraper uses its own database, which has been compiled from many sources on the net and keeps extending. If this is a problem for you, do not run this software.

## Running the software:

### From source:

Excute as 'python retroscraper.py'.

### From precompiled binaries:

Simply download the pre-compiled binaries for your system from the dist directory. Currently windows, rpi and linux_x64 exist.

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



