#!/usr/bin/python3  

import urllib.request
import os, os.path
import json
from datetime import datetime
from bs4 import BeautifulSoup
import re

TYPE_BOULDERADO = 'boulderado'
TYPE_WEBCLIMBER = 'webclimber'
TYPE_ROCKGYMPRO = 'rock-gym-pro'
defaultConfig = {
    'targets': [
        {
            'name': 'greifhaus',
            'url': 'https://www.boulderado.de/boulderadoweb/gym-clientcounter/index.php?mode=get&token=eyJhbGciOiJIUzI1NiIsICJ0eXAiOiJKV1QifQ.eyJjdXN0b21lciI6IkdyZWlmaGF1cyJ9.3Nen_IU5N2sVtJbP44CGCFfdKY93zQx2FRczY4z9Jy0',
            'type': TYPE_BOULDERADO
        },
        {
            'name': 'fliegerhalle',
            'url': 'https://158.webclimber.de/de/trafficlight?callback=WebclimberTrafficlight.insertTrafficlight&key=yspPh6Mr2KdST3br8WC7X8p6BdETgmPn&hid=158&container=trafficlightContainer&type=&area=',
            'type': TYPE_WEBCLIMBER
        },
        {
            'name': 'the-spot-boulder',
            'url': 'https://portal.rockgympro.com/portal/public/415a34a23151c6546419c1415d122b61/occupancy?&iframeid=occupancyCounter&fId=',
            'type': TYPE_ROCKGYMPRO,
            'location': 'BLD'
        },
        {
            'name': 'the-spot-denver',
            'url': 'https://portal.rockgympro.com/portal/public/415a34a23151c6546419c1415d122b61/occupancy?&iframeid=occupancyCounter&fId=',
            'type': TYPE_ROCKGYMPRO,
            'location': 'DEN'
        }
    ],
    'outputDir': os.path.dirname(__file__)
}

def main():
    config = loadConfig()
    if not config:
        exit(-1)
    outputDir = config['outputDir']
    targets = config['targets']
    for target in targets:
        parseTarget(target, outputDir)
    

def parseTarget(target, outputDir):
    currentVisitors, currentFree = getClientCount(target)
    if currentVisitors is None or currentFree is None:
        Log.log(Log.error, 'Failed to parse: currentVisitors = {}, currentFree = {}'.format(currentVisitors, currentFree))
        exit(-1)

    counterFile = os.path.join(outputDir, '{}-counter.csv'.format(target['name']))
    latestDataFile = os.path.join(outputDir, '{}-latest.csv'.format(target['name']))
    csvExists = os.path.exists(counterFile)
    lastEntry = None
    currentTime = datetime.now().replace(microsecond=0).isoformat()
    newEntry = '{},{},{}\n'.format(currentTime, currentVisitors, currentFree)

    if csvExists:
        with open(counterFile, 'r') as outputCSV:
            for line in outputCSV:
                pass
            lastEntry = line

    with open(counterFile, 'a') as outputCSV:
        if not csvExists:
            outputCSV.write('time,visitors,available\n')
        if not lastEntry or not lastEntry.partition(',')[2] == newEntry.partition(',')[2]:
            outputCSV.write(newEntry)
    
    with open(latestDataFile, 'w') as latestDataCSV:
        latestDataCSV.write('time,visitors,available\n')
        latestDataCSV.write(newEntry)

def getClientCount(target):
    url = target['url']
    html = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(html, features='lxml')
    if target['type'] == TYPE_BOULDERADO:
        return parseBoulderado(soup)
    elif target['type'] == TYPE_WEBCLIMBER:
        return parseWebclimber(soup)
    elif target['type'] == TYPE_ROCKGYMPRO:
        return parseRockGymPro(soup, target['location'])

def parseBoulderado(soup):
    currentVisitors = None
    currentFree = None
    for div in soup.find_all('div'):
        if div['class'] == ['actcounter', 'zoom']:
            currentVisitors = div['data-value']
        if div['class'] == ['freecounter', 'zoom']:
            currentFree = div['data-value']
    return (currentVisitors, currentFree)

def parseWebclimber(soup):
    currentVisitors = None
    currentFree = None
    for div in soup.find_all('div'):
        if 'style' in div.attrs:
            currentVisitors = int(re.search(r'width: (\d+?)%;', div['style']).group(1))
            currentFree = 100 - currentVisitors
    return (currentVisitors, currentFree)

def parseRockGymPro(soup, location):
    currentVisitors = None
    currentFree = None
    for script in soup.find_all('script'):
        contents = script.contents
        if contents and 'capacity' in contents[0] and 'count' in contents[0]:
            script = contents[0].replace('\n', '').replace(' ', '')
            filteredScript = re.search(rf'\'{location}\':{{(.+?)}}', script).group(1)
            capacity = int(re.search(r'\'capacity\':(\d+?),', filteredScript).group(1))
            currentVisitors = int(re.search(r'\'count\':(\d+?),', filteredScript).group(1))
            currentFree = capacity - currentVisitors
    return (currentVisitors, currentFree)


def loadConfig():
    # constants
    configDir = os.path.dirname(__file__)
    configFilename = os.path.join(configDir, 'config.json')
    # check if file exists
    if not os.path.isfile(configFilename):
        Log.log(Log.error, 'File "{0}" not found. Creating empty config file, please fill in the empty fields'.format(configFilename))
        createEmptyConfig(configFilename, defaultConfig)
        return None
    # try loading the config
    with open(configFilename, 'r') as configFile:
        try:
            config = json.load(configFile)
        except json.decoder.JSONDecodeError:
            Log.log(Log.error, 'Corrupt config. Creating empty config file, please fill in the empty fiels')
            createEmptyConfig(configFilename, defaultConfig)
            return None
    # check all fields exists
    for key in defaultConfig:
        if not key in config or type(defaultConfig[key]) is not type(config[key]):
            Log.log(Log.error, 'File "mail.config" incomplete. {0} is missing or invalid. Renaming old config file and generating new config'.format(key))
            createEmptyConfig(configFilename, defaultConfig)
            return None
    # return valid config
    return config

def createEmptyConfig(filename, defaultConfig):
    saveOldConfig(filename)
    with open(filename, 'w') as configFile:
        json.dump(defaultConfig, configFile)

def saveOldConfig(filename):
    if not os.path.exists(filename):
        return
    targetFileName = '{0}_{1}.json'.format(os.path.splitext(filename)[0], getTimeForFilename())
    if os.path.exists(targetFileName):
        os.remove(targetFileName)
    os.rename(filename, targetFileName)

def getLogTime():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def getTimeForFilename():
    return datetime.now().strftime("%Y-%m-%d-%H%M%S")

class Log:
    error = 'ERROR'
    info = 'INFO'
    debug = 'DEBUG'

    @staticmethod
    def log(tag, message):
        print('[{time}] [{tag}] {message}'.format(time = getLogTime(), tag = tag, message = message))

if __name__ == "__main__":
    main()
