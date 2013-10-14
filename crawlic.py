#!/usr/bin/python

from lib.pholcidae import Pholcidae
import argparse
import random
import requests
import string
import json
from urlparse import urlparse
import socket
import time
import re

user_agent_list = []

"""
Crawler definition
"""

class Crawlic(Pholcidae):
    """ Base Class for crawler """

    def crawl(self, data):
        """ called every link fetched """
        url = data.url.split("?")[0].split("#")[0]
        for extension in Crawlic.extension_list:
            try:
                response = requests.get(url + extension, verify=False)
                if response.status_code == 200 and Crawlic.page_not_found_pattern not in response.text:
                    print "   [+] %s" % url + extension
            except requests.exceptions.ConnectionError as e:
                print "[!] %s : %s" % (url, e)

"""
Load configuration files
"""


def loadList(filepath, callback=lambda s: s):
    """Load a list file. Apply a callback on each value if more processing
    is needed.
    """
    return [callback(l.strip()) for l in open(filepath)]

"""
Usefull methods
"""

def getPageNotFoundPattern(url):
    """ Get a pattern for 404 page (if server return 200 on 404) """
    if url[:-1] != "/":
        url = url + "/"
    pattern = ""
    random_string = ''.join([random.choice(string.letters) for c in xrange(0, random.randint(5,30))])
    url = url + random_string
    response = requests.get(url, headers={"referer" : url, "User-Agent" : getRandomUserAgent()}, verify=False)
    if "404" in response.text:
        pattern = "404"
    elif "not found" in response.text:
        pattern = "not found"
    return pattern

def getRandomUserAgent():
    """ return a random user agent from the list loaded in previous method """
    return random.choice(user_agent_list)

def printBanner(banner_file):
    """ Print a fucking awesome ascii art banner """
    banner_length = 0
    for line in [line.rstrip() for line in open(banner_file)]:
        print line
        if len(line) > banner_length:
            banner_length = len(line)

    print "\n" + "#" * banner_length + "\n"

"""
Recon methods
"""

def robotsExtract(url, pattern):
    """ Parse robots.txt file """
    if url[:-1] != "/":
        url = url + "/"
    url = url + "robots.txt"
    response = requests.get(url, headers={"referer" : url, "User-Agent" : getRandomUserAgent()}, verify=False)
    if response.status_code == 200 and pattern not in response.text:
        for line in response.text.split("\n"):
            if not line.strip().startswith("#") and not line.strip().lower().startswith("sitemap") and not line.strip().lower().startswith("user") and line.strip() != "":
                line = line.split("#")[0]
                (rule, path) = line.split(":")
                if rule.lower() == "disallow":
                    print "   [+] %s" % path

def searchFolders(url, folders_file, pattern):
    """ Search for interresting folders like /private, /admin etc... """
    if url[:-1] != "/":
        url = url + "/"

    for line in [line.strip() for line in open(folders_file)]:
        response = requests.get(url + line, headers={"referer" : url, "User-Agent" : getRandomUserAgent()}, verify=False)
        if response.status_code == 200 and pattern not in response.text:
            print "   [+] /%s" % line

def googleDorks(url, google_dorks):
    """ Use google dorks to retrieve informations on target """
    for google_dork in google_dorks:
        dork = google_dork % url
        google_url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=%s' % dork
        response = requests.get(google_url, headers={"referer" : "http://google.com/", "User-Agent" : getRandomUserAgent()}, verify=False)
        parsed_response = json.loads(response.text)
        for result in parsed_response['responseData']['results']:
            print "   [+] %s" % result['url']

def reverseDns(ip, query_numbers):
        page_counter = 1
        domains = []
        while page_counter < query_numbers:
            try:
                bing_url = 'http://www.bing.com/search?q=ip%3a'+str(ip)+'&go=&filt=all&first=' + repr(page_counter) + '&FORM=PERE'
                response = requests.get(bing_url, headers={"User-Agent" : getRandomUserAgent()})
                names = (re.findall('\/\/\w+\.\w+\-{0,2}\w+\.\w{2,4}',response.text))
                for name in names:
                    get_ip = socket.gethostbyname_ex(name[2:])
                    if get_ip[2][0] == ip and name[2:] not in domains:
                        domains.append(name[2:])
            except:
                pass
            page_counter += 10
            time.sleep(0.5)
        return domains

"""
Scannings methods
"""

def scanRobots(url, page_not_found_pattern):
    """ Start scan using robots.txt """
    print "[*] Starting robots.txt search"
    try:
        robotsExtract(url, page_not_found_pattern)
    except KeyboardInterrupt:
        print "[!] Skip robots.txt parsing"

def scanFolders(url, folders, page_not_found_pattern):
    """ Start scan using folder list """
    print "[*] Starting folder search"
    try:
        searchFolders(url, folders, page_not_found_pattern)
    except KeyboardInterrupt:
        print "[!] Skip folder search"

def scanTemporaryFiles(url):
    """ Start scan using temporary files extensions """
    print "[*] Starting temp file search"
    try:
        crawlic = Crawlic()
        crawlic.start()
    except KeyboardInterrupt:
        print "[!] Skip temp file search"

def scanGoogleDorks(url, google_dorks):
    """ Start scan using google dorks """
    print "[*] Starting Google dorking"
    try:
        googleDorks(url, google_dorks)
    except KeyboardInterrupt:
        print "[!] Skip Google dorking"

def scanReverseDns(url):
    """ Start reverse DNS search by bing """
    print "[*] Searching domains on same server"
    try:
        ip = socket.gethostbyname(urlparse(url).netloc)
        for domain in reverseDns(ip, 50):
            print "   [+] %s" % domain
    except KeyboardInterrupt:
        print "[!] Skip reverse dns search"

"""
Entry point
"""

def main():
    printBanner("./banner.txt")
    parser = argparse.ArgumentParser(description='Crawl website for temporary files')
    parser.add_argument('-u', '--url', action="store", dest="url", required=True, help='url')
    parser.add_argument('-e', '--extensions', action="store", dest="extensions", default="lists/extensions.lst", help='extensions')
    parser.add_argument('-d', '--dorks', action="store", dest="dorks", default="lists/dorks.lst", help='dorks')
    parser.add_argument('-f', '--folders', action="store", dest="folders", default="lists/folders.lst", help='folders')
    parser.add_argument('-a', '--agent', action="store", dest="user_agent", default="lists/user_agent.lst", help='user agent file')
    parser.add_argument('-g', '--google', action="store", dest="google_dorks", default="lists/google_dorks.lst", help='google dorks file')
    parser.add_argument('-t', '--techniques', action="store", dest="techniques", default="rtfgd", help='scan techniques (r: robots.txt t: temp files, f: folders, g: google dorksi, d: reverse dns)')
    args = parser.parse_args()

    print "[*] Scan %s using techniques %s" % (args.url, args.techniques)

    url = urlparse(args.url)
    if not url.scheme:
        args.url = 'http://' + args.url
        url = urlparse(args.url)

    protocol, domain = url.scheme, url.netloc

    # Make sure the host is up
    print "[*] Probe host %s" % args.url

    try:
        requests.head(args.url)
    except requests.exceptions.ConnectionError:
        print '[!] Url %s not reachable or is down. Aborting' % args.url
        return

    # Load configuration from files
    try:
        user_agent_list.extend(loadList(args.user_agent))
    except IOError():
        print '[!] User agent list %s doesn\'t exist' % args.user_agent
        return

    try:
        Crawlic.extension_list = loadList(args.dorks)
    except IOError():
        print '[!] Dorks list %s doesn\'t exist' % args.dorks
        return

    page_not_found_pattern = getPageNotFoundPattern(args.url)

    try:
        google_dorks = loadList(args.google_dorks)
    except IOError():
        print '[!] Google dorks list %s doesn\'t exist' % args.google_dorks
        return

    # Configure crawler
    Crawlic.page_not_found_pattern = page_not_found_pattern
    try:
        valid_links = loadList(args.extensions, lambda s: '(.*%s)' % s)
    except IOError():
        print '[!] Extension list %s doesn\'t exists' % args.extensions
        return

    Crawlic.settings = {
            'domain': domain,
            'start_page': '/',
            'stay_in_domain' : True,
            'protocol': protocol + "://",
            'valid_links': valid_links,
            'headers' : {
                'Referer': domain,
                'User-Agent': getRandomUserAgent()
                }
            }

    # Start recon here
    for technique in args.techniques:
        if technique == "r":
            scanRobots(args.url, page_not_found_pattern)
        elif technique == "f":
            scanFolders(args.url, args.folders, page_not_found_pattern)
        elif technique == "t":
            scanTemporaryFiles(args.url)
        elif technique == "g":
            scanGoogleDorks(args.url, google_dorks)
        elif technique == "d":
            scanReverseDns(args.url)
        else :
            print "[*] unknown technique : %s" % technique
    print "[*] Crawling finished"


if __name__ == "__main__":
    main()
