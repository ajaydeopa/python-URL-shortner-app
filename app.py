from flask import Flask, request, redirect, render_template
from flask_restful import Resource, Api
import json, re, random, string

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db import URLs, Base

# connect to the db
e = create_engine('sqlite:///hackerEarth.db')
Base.metadata.bind = e
app = Flask(__name__)
api = Api(app)

serverName = "deopa.herokuapp.com/"

@app.route('/')
def render_static():
    return render_template('index.html')

# checks whether the long URL is valid or not
def isValidURL(url):
    # regular expression to check if the url is valid or not
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return regex.match(url)

# generates short URL for a valid URL
def generateShortURL():
    # generate 8 characters random string
    randomStr = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])
    # create short url
    return randomStr

# save the pair of actual URL and short URL in DB
def saveURL(longURL, shortURL):
    # start new DB session
    DBSession = sessionmaker(bind = e)
    session = DBSession()
    # create an object of the URLs class
    newURL = URLs(longURL = longURL, shortURL = shortURL, visitCount = 0)
    # add the object to the session
    session.add(newURL)
    # save the new URL data in the DB
    session.commit()

# get data of a short URL
def getURLData(url):
    DBSession = sessionmaker(bind = e)
    session = DBSession()
    return session.query(URLs).filter(URLs.shortURL == url).first()

class createShortURL(Resource):
    def post(self):
        # return request.get_json(force=True)
        reqData = request.form
        longURL = reqData["long_url"]

        # executes when the URL is invalid
        if not isValidURL(longURL):
            res = { "status": "FAILED", "status_codes": ["INVALID_URLS"] }
            return res

        # generates a short URL
        shortURL = generateShortURL()
        # save the URL info in DB
        saveURL(longURL, shortURL)
        res = { "short_url": serverName + shortURL, "status": "OK", "status_codes": [] }
        return res;

class createShortURLs(Resource):
    def post(self):
        reqData = request.form
        longURLs = json.loads(reqData["long_urls"])

        validURLs = []
        invalidURLs = []

        for url in longURLs:
            # executes when long URL is invalid
            if not isValidURL(url):
                invalidURLs.append(url)
                continue

            validURLs.append(url)

        # executes when one or more invalid URLs
        if len(invalidURLs) > 0:
            res = { "invalid_urls": invalidURLs, "status": "FAILED", "status_codes": ["INVALID_URLS"] }
            return res

        short_urls = {}

        # create short URL of all the valid URLs
        for url in validURLs:
            shortURL = generateShortURL()
            # return shortURL
            saveURL(url, shortURL)
            short_urls[url] = serverName + shortURL

        res = { "short_urls": short_urls, "invalid_urls" : [], "status": "OK", "status_codes": [] }
        return res

class getLongURL(Resource):
    def post(self):
        reqData = request.form
        shortURL = reqData["short_url"]

        hashCode = [s for s in shortURL.split("/")][-1]

        # get the data of a short URL from DB
        urlData = getURLData(hashCode)

        # executes when the short URL is invalid
        if urlData is None:
            res = { "status": "FAILED", "status_codes": ["SHORT_URLS_NOT_FOUND"] }
            return res

        res = {"long_url": urlData.longURL, "status": "OK", "status_codes": []}
        return res

class getLongURLs(Resource):
    def post(self):
        reqData = request.form
        shortURLs = json.loads(reqData["short_urls"])

        long_urls = {}
        invalidURLs = []

        for url in shortURLs:
            hashCode = [s for s in url.split("/")][-1]
            urlData = getURLData(hashCode)
            # executes when short URL is invalid
            if urlData is None:
                invalidURLs.append(url)
                continue

            long_urls[url] = urlData.longURL

        # executes when one or more invalid short URLs given
        if len(invalidURLs) > 0:
            res = { "invalid_urls": invalidURLs, "status": "FAILED", "status_codes": ["SHORT_URLS_NOT_FOUND"] }
            return res

        res = { "long_urls": long_urls, "invalid_urls" : [], "status": "OK", "status_codes": [] }
        return res

class accessServer(Resource):
    def get(self, shortURL):

        # get data of the given short URL
        DBSession = sessionmaker(bind=e)
        session = DBSession()
        urlData = session.query(URLs).filter(URLs.shortURL == shortURL).first()

        if urlData is None:
            res = { "status": "FAILED", "status_codes": ["SHORT_URLS_NOT_FOUND"] }
            return res

        longURL = urlData.longURL
        # update visit count of the URL that is being visited
        urlData.visitCount = urlData.visitCount + 1
        session.commit()

        return redirect(longURL, code=302)

class countVisits(Resource):
    def post(self):
        reqData = request.form
        shortURL = reqData["short_url"]

        hashCode = [s for s in shortURL.split("/")][-1]

        urlData = getURLData(hashCode)

        if urlData is None:
            res = {"status": "FAILED", "status_codes": ["SHORT_URLS_NOT_FOUND"]}
            return res

        res = {"count": urlData.visitCount, "status": "OK", "status_codes": []}
        return res

class CleanURLs(Resource):
    def get(self):
        Session = sessionmaker(bind = e)
        session = Session()
        session.query(URLs).delete()
        session.commit()
        session.close()

        res = { "status": 'OK', "status_codes": "[]" }
        return res

# api.add_resource

# create short URL for single URL
api.add_resource(createShortURL, '/fetch/short-url/', methods=['POST'])
# create short URL for Multiple URLs
api.add_resource(createShortURLs, '/fetch/short-urls/', methods=['POST'])
# get actual URL of a single short URL
api.add_resource(getLongURL, '/fetch/long-url/', methods=['POST'])
# get actual URL of Multiple short URLs
api.add_resource(getLongURLs, '/fetch/long-urls/', methods=['POST'])
# get count of number of times a short URL has been accessed
api.add_resource(countVisits, '/fetch/count/')
# truncate all data from DB
api.add_resource(CleanURLs, '/clean-urls/')
# access a short url
api.add_resource(accessServer, '/<shortURL>/')

if __name__ == '__main__':
    app.run(debug=True)