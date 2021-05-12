from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
import webbrowser
import requests
from collections import Counter
from string import punctuation
from difflib import SequenceMatcher
import csv
import pandas as pd

original = "https://en.wikipedia.org/wiki/Special:Random" #Make the original a random Wikipedia page
foundrandom = False

target = "https://en.wikipedia.org/wiki/Special:Random"
#print(original.split("https://en.wikipedia.org/wiki/",1)[1])
snippet = target.split("/wiki/",1)[1]
splitted = snippet.split('_')
splitteddict = {}
splittedsort = []
history = []

with open("10000.txt") as f:
    tenthousand = f.readlines()
tenthousand = [x.strip('\n') for x in tenthousand]

with open("1000.txt") as f:
    thousand = f.readlines()
thousand = [x.strip('\n') for x in thousand]

with open("countries.txt") as f:
    countries = f.readlines()
countries = [x.strip('\n') for x in countries]

with open("names.txt") as f:
    names = f.readlines()
names = [x.strip('\n') for x in names]

df = pd.read_csv("cities.csv")
realdf = df["city"][0:2500]
cities = realdf.values.tolist()

for item in splitted:
    counter = 0
    has = False
    for word in tenthousand:
        counter += 1
        if word in splitted:
            splitteddict[word] = counter
            counter = 0
            has = True
    if has == False:
        splitteddict[item] = 100000

for word in dict(sorted(splitteddict.items(), key=lambda item: item[1], reverse=True)):
    splittedsort.append(word)

#Disambiguation of all the countries and words

def worddistr():
    r = requests.get(target)

    soup = BeautifulSoup(r.content, features="lxml")

    text = (''.join(s.findAll(text=True))for s in soup.findAll('p'))

    c = Counter((x.rstrip(punctuation).lower() for y in text for x in y.split()))

    common = [x for x in c if c.get(x) > 3] # words appearing more than 5 times
    lesscommon = [x for x in c if c.get(x) > 3]
    realcommon = []
    reallesscommon = []

    for word in tenthousand:
        if word in common:
            common.remove(word)

    for word in thousand:
        if word in lesscommon:
            lesscommon.remove(word)

    for word in common:
        if len(re.findall(r'[\d]+',word)) == 0:
            realcommon.append(word)

    for word in lesscommon:
        if len(re.findall(r'[\d]+',word)) == 0:
            reallesscommon.append(word)

    return realcommon, reallesscommon

def similar(word, link):
    return SequenceMatcher(None, word, link).ratio()

def search(page):
    global foundrandom
    req = Request(page)

    html_page = urlopen(req, timeout=5)
    webpage = urlopen(req).read

    soup = BeautifulSoup(html_page, "lxml")

    if foundrandom == False:
        title = soup.find(class_="firstHeading").text
        print(title)
        foundrandom = True

    links = []
    newlinks = []
    no = []
    reallinks = []
    wikishit = ["Special:", "File:", "Talk:", "Wikipedia:", "Template:", "Category:", "Help:", "Portal:", "Wikipedia_talk:", "Template_talk:", "Main_Page", "Geographic_coordinate_system", "Wayback_Machine", "Information_Today", "_(identifier)", "Specials_(Unicode_block)#Replacement_character"] #"ISBN_(identifier)", "Doi_(identifier)", , "LCCN_(identifier)", "OCLC_(identifier)", "Wayback_Machine", "VIAF_(identifier)", "WorldCat_Identities_(identifier)", "VIAF_(identifier)", "Information_Today", "Bibcode_(identifier)", "PMID_(identifier)"]
    dictlinks = {}

    realtitles = []
    for link in soup.findAll('a'):
        #realtitles.append(re.search(">(.*?)</", str(link)))
        links.append(link.get('href'))
        try:
            dictlinks[link.get('href')] = str(link).split("""">""")[1].replace("</a>","")
        except:
            pass

    #print(realtitles)
    for link in links:
        if link != None:
            if "/wiki/" == link[:6]:
                newlinks.append(link[6:])

    for link in newlinks:
        for avoid in wikishit:
            try:
                if (avoid in link) or ((len(re.findall(r'[\d]+',history[-1])) > 0) and (len(re.findall(r'[\d]+',link)) > 0)) or ((similar(history[-1],link) > 0.3) and (similar(history[-1], snippet) < 0.3)):
                    no.append(link)
            except IndexError:
                pass

    for link in newlinks:
        if link not in no:
            reallinks.append(link)

    #Maybe search the new page aswell (?) for its word distribution, or something complicated
    return reallinks, dictlinks

def findPage(originalpage):
    if snippet in history:
        quit()
    links, dictlinks = search(originalpage)
    targetlinks, worthless = search(target)
    dicttargetlinks = {}
    for link in targetlinks:
        if link in dicttargetlinks:
            dicttargetlinks[link] += 1
        else:
            dicttargetlinks[link] = 0
    sortdicttargetlinks = dict(sorted(dicttargetlinks.items(), key=lambda item: item[1], reverse=True))


    for link in links:
        if snippet == link:
            print(link + "  |  " + dictlinks["/wiki/"+link] + "  |  " + str(len(links)))
            quit()
            return True

    for link in links:
        for targetlink in sortdicttargetlinks:
            if link == targetlink and (link not in history) and (sortdicttargetlinks[targetlink] > 0):
                print(link + " |  LINK  |  " + str(sortdicttargetlinks[targetlink]) + "  |  " + dictlinks["/wiki/"+link] + "  |  " + str(len(links)))
                history.append(link)
                findPage('https://en.wikipedia.org/wiki/' + link)
                return False

    for word in splittedsort:
        for link in links:
            if (word in link) and (link not in history) and (word not in names):
                print(link + "  |  DIRECT  |  " + word + "  |  " + dictlinks["/wiki/"+link] + "  |  " + str(len(links)))
                history.append(link)
                if ('https://en.wikipedia.org/wiki/' + link) == target:
                    return True
                else:
                    findPage('https://en.wikipedia.org/wiki/' + link)

    for link in links:
        for country in countries:
            if (country == link) and (link not in history):
                print(link + "  |  COUNTRY" + "  |  " + dictlinks["/wiki/"+link] + "  |  " + str(len(links)))
                history.append(link)
                findPage('https://en.wikipedia.org/wiki/' + link)
                return False

    for link in links:
        for city in cities:
            if (city.replace(" ", "_") == link) and (link not in history):
                print(link + "  |  CITY" + "  |  " + dictlinks["/wiki/"+link] + "  |  " + str(len(links)))
                history.append(link)
                findPage('https://en.wikipedia.org/wiki/' + link)
                return False

    # (similar(history[-1],link) > 0.3)
    for word in common:
        for link in links: #regex here
            if (word in [x.lower() for x in link.split("_")]) and (link not in history):
                print(link + "  |  COMMON  |  " + word + "  |  " + dictlinks["/wiki/"+link] + "  |  " + str(len(links)))
                history.append(link)
                findPage('https://en.wikipedia.org/wiki/' + link)
                return False

    for link in links:
        for targetlink in sortdicttargetlinks:
            if link == targetlink and (link not in history):
                print(link + "  |  LINK  |  " + str(sortdicttargetlinks[targetlink]) + "  |  " + dictlinks["/wiki/"+link] + "  |  " + str(len(links)))
                history.append(link)
                findPage('https://en.wikipedia.org/wiki/' + link)
                return False

    for word in lesscommon:
        for link in links:
            if (word in [x.lower() for x in link.split("_")]) and (link not in history):
                history.append(link)
                print(link + "  |  LESSCOMMON  |  " + word + "  |  " + dictlinks["/wiki/"+link] + "  |  " + str(len(links)))
                findPage('https://en.wikipedia.org/wiki/' + link)
                return False

    for link in links:
        if link not in history:
            history.append(link)
            print(link + "  |  RANDOM" + "  |  " + dictlinks["/wiki/"+link] + "  |  " + str(len(links)))
            findPage('https://en.wikipedia.org/wiki/' + link)
            return False

common, lesscommon = worddistr()
findPage(original)
