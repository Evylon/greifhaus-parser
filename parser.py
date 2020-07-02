#!/usr/bin/python3  

import urllib.request
import os, os.path
import json
from datetime import datetime
from bs4 import BeautifulSoup

defaultConfig = {
    'outputCSV': 'greifhaus-counter.csv',
    'targetUrl': 'https://www.boulderado.de/boulderadoweb/gym-clientcounter/index.php?mode=get&token=eyJhbGciOiJIUzI1NiIsICJ0eXAiOiJKV1QifQ.eyJjdXN0b21lciI6IkdyZWlmaGF1cyJ9.3Nen_IU5N2sVtJbP44CGCFfdKY93zQx2FRczY4z9Jy0'
}

def main():
    config = loadConfig()
    if not config:
        exit(-1)
    currentVisitors, currentFree = getClientCount(config['targetUrl'])
    if currentVisitors is None or currentFree is None:
        Log.log(Log.error, 'Failed to parse: currentVisitors = {}, currentFree = {}'.format(currentVisitors, currentFree))
        exit(-1)
    csvExists = os.path.exists(config['outputCSV'])
    with open(config['outputCSV'], 'a') as outputCSV:
        if not csvExists:
            outputCSV.write('time,visitors,available\n')
        currentTime = datetime.now().replace(microsecond=0).isoformat()
        outputCSV.write('{},{},{}\n'.format(currentTime, currentVisitors, currentFree))

def getClientCount(url):
    html = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(html, features='lxml')
    currentVisitors = None
    currentFree = None
    for div in soup.find_all('div'):
        if div['class'] == ['actcounter', 'zoom']:
            currentVisitors = div['data-value']
        if div['class'] == ['freecounter', 'zoom']:
            currentFree = div['data-value']
    return (currentVisitors, currentFree)

def loadConfig():
    # constants
    configPath = os.path.dirname(__file__)
    configFilename = os.path.join(configPath, 'config.json')
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
