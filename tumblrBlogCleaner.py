import oauth2
import pprint
import pytumblr
import re
import surblclient
import sys
import time
import urllib
import urlparse

import ConfigParser

access_token_url = 'https://www.tumblr.com/oauth/access_token'
authorize_url = 'http://www.tumblr.com/oauth/authorize'
request_token_url = 'http://www.tumblr.com/oauth/request_token'

g_request = None
g_whitelist = []

class Config:
    def __init__(self):
        self.__config = ConfigParser.ConfigParser()
        self.__config.read('config.ini')

    def __safe_get(self, section, option):
        if not self.__config.has_section(section):
            return None
        if not self.__config.has_option(section, option):
            return None
        else:
            return self.__config.get(section, option)

    def __get_tumblr_consumer_key(self):
        return self.__safe_get('tumblr', 'consumer_key')
    tumblr_consumer_key = property(__get_tumblr_consumer_key)

    def __get_tumblr_consumer_secret(self):
        return self.__safe_get('tumblr', 'consumer_secret')
    tumblr_consumer_secret = property(__get_tumblr_consumer_secret)

    def __get_tumblr_oauth_token(self):
        return self.__safe_get('tumblr', 'oauth_token')
    tumblr_oauth_token = property(__get_tumblr_oauth_token)

    def __get_tumblr_oauth_token_secret(self):
        return self.__safe_get('tumblr', 'oauth_token_secret')
    tumblr_oauth_token_secret = property(__get_tumblr_oauth_token_secret)

class TumblrAuth:
    def __init__(self, consumer_key, consumer_secret):
        global g_request

        self.__consumer_key = consumer_key
        self.__consumer_secret = consumer_secret

        consumer = oauth2.Consumer(self.__consumer_key, self.__consumer_secret)
        client = oauth2.Client(consumer)                                                                                                                                                      

        # Get request token
        resp, content = client.request(request_token_url, method="POST")
        request_token =  urlparse.parse_qs(content)

        # Redirect to authentication page
        print '\nPlease go here and authorize:\n%s?oauth_token=%s' % (authorize_url, request_token['oauth_token'][0])
        redirect_response = raw_input('Allow then paste the full redirect URL here:\n')

        # Retrieve oauth verifier
        url = urlparse.urlparse(redirect_response)
        query_dict = urlparse.parse_qs(url.query)
        oauth_verifier = query_dict['oauth_verifier'][0]

        # Request access token
        token = oauth2.Token(request_token['oauth_token'], request_token['oauth_token_secret'][0])
        token.set_verifier(oauth_verifier)
        client = oauth2.Client(consumer, token)

        resp, content = client.request(access_token_url, "POST")
        self.__access_token = dict(urlparse.parse_qsl(content))
        self.__response = resp

    def __get_access_token(self):
        return self.__access_token

    access_token = property(__get_access_token)

    def __get_response(self):
        return self.__response

    response = property(__get_response)

class IterFollowing:
    def __init__(self, client):
        self.__client = client
        self.__offset = 0
        self.__limit = 20
        self.__position = 0
        self.__following = None

    def __iter__(self):
        return self

    def next(self):
        position = self.__position % self.__limit

        if position == 0:
            #print 'position %d, offset %d' % (self.__position, self.__offset,)

            self.__offset += self.__limit
            self.__following = self.__client.following(limit=self.__limit, offset=self.__offset)
            #print 'got %d blogs' % (len(self.__following['blogs']),)

        if not self.__following.has_key('blogs') or len(self.__following['blogs']) == 0 or position >= len(self.__following['blogs']):
            #print 'last at position %d' % (self.__position,)
            raise StopIteration()

        value = self.__following['blogs'][position]
        self.__position += 1
        return value

class SavedAuth:
    def __init__(self, oauth_token, oauth_token_secret):
        self.__oauth_token = oauth_token
        self.__oauth_token_secret = oauth_token_secret

    def __get_access_token(self):
        return {'oauth_token': self.__oauth_token, 'oauth_token_secret': self.__oauth_token_secret}
    access_token = property(__get_access_token)

    def __get_response(self):
        return {'status': '200'}
    response = property(__get_response)

class PostScanner:
    def __init__ (self, post):
         self._post = post

    def __get_id(self):
        return int(self._post['id'])
    id = property(__get_id)

    def __get_date(self):
        return time.ctime(self.__get_timestamp())
    date = property(__get_date)

    def __get_timestamp(self):
        return int(self._post['timestamp'])
    timestamp = property(__get_timestamp)

    def __get_age(self):
        return time.time() - self.__get_timestamp()
    age = property(__get_age)

    def __get_format(self):
        return self._post['format']
    format = property(__get_format)

    def __get_type(self):
        return self._post['type']
    type = property(__get_type)

    def __get_domains(self):
        urls = []
        for text in self.__deep_values(self._post, 7):
            try:
                extracted = re.search("(?P<url>https?://[^\s\"']+)", text).groups("url")
                urls.extend(extracted)
            except:
                pass

        domains = {}
        for url in urls:
            domain = re.search("://(?P<domain>[^/]+)", url).group("domain")
            domains[domain] = True
        return domains.keys()
    domains = property(__get_domains)

    def __is_spammy(self):
        global g_whitelist

        for domain in self.__get_domains():
            if domain in g_whitelist:
                continue
            if domain in surblclient.surbl:
                return True
            else:
                g_whitelist.append(domain)
		return False
    spammy = property(__is_spammy)

    def __deep_values(self, d, depth):
        if depth == 1:
            for i in d.values():
                yield i
        else:
            for v in d.values():
                if isinstance(v, dict):
                    for i in self.__deep_values(v, depth-1):
                        yield i
                yield v

if __name__ == '__main__':
    config = Config()

    #print config.tumblr_consumer_key
    #print config.tumblr_consumer_secret

    if len(sys.argv) == 3:
        auth = SavedAuth(*sys.argv[1:])
    elif config.tumblr_oauth_token is not None and config.tumblr_oauth_token_secret is not None:
        auth = SavedAuth(config.tumblr_oauth_token, config.tumblr_oauth_token_secret)
    else:
        auth = TumblrAuth(
            config.tumblr_consumer_key,
            config.tumblr_consumer_secret
        )

    #print auth.response
    #print auth.access_token

    if auth.response['status'] != '200':
        print 'Error! Authentication failed.'
        sys.exit(1)

    # See https://github.com/tumblr/pytumblr
    client = pytumblr.TumblrRestClient(
        config.tumblr_consumer_key,
        config.tumblr_consumer_secret,
        auth.access_token['oauth_token'],
        auth.access_token['oauth_token_secret']
    )

    #print client.info()

    now = time.time()

    blogs_to_unfollow = list()
    for blog in IterFollowing(client):
        print
        print blog['name']

        spammy = False
        old = False
        timestamp = 0

        time.sleep(1)
        posts = client.posts(blog['name'], limit=50)

        for post in posts['posts']:
            time.sleep(1)
            post = PostScanner(post)
            timestamp = max(timestamp, post.timestamp)
            if not spammy and post.spammy:
                spammy = True

        if timestamp < (now - 60 * 60 * 24 * 365):
            old = True
        print 'spammy: %s' % (spammy,)
        print 'old: %s' % (old,)

        if spammy or old:
            blogs_to_unfollow.append(blog)

    print
    print '* Unfollow'
    for blog in blogs_to_unfollow:
        print blog['name']
        time.sleep(1)
        response = client.unfollow(blog['name'])
