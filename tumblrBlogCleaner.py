import oauth2
import pprint
import pytumblr
import sys
import time
import urllib
import urlparse

import ConfigParser

access_token_url = 'https://www.tumblr.com/oauth/access_token'
authorize_url = 'http://www.tumblr.com/oauth/authorize'
request_token_url = 'http://www.tumblr.com/oauth/request_token'

g_request = None

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
        self.__position = self.__limit
        self.__following = None

    def __iter__(self):
        return self

    def next(self):
        if self.__position >= self.__limit:
            self.__offset += self.__limit
            self.__position = 0
            self.__following = self.__client.following(limit=self.__limit, offset=self.__offset)

        if not self.__following.has_key('blogs') or len(self.__following['blogs']) == 0 or self.__position == len(self.__following['blogs']):
            raise StopIteration()

        value = self.__following['blogs'][self.__position]
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

    def __get_date(self):
        return time.ctime(self.__get_timestamp())
    date = property(__get_date)

    def __get_timestamp(self):
        return int(self._post['timestamp'])
    timestamp = property(__get_date)

    def __get_age(self):
        return time.time() - self.__get_timestamp()
    age = property(__get_age)

    def __get_format(self):
        return self._post['format']
    format = property(__get_format)

    def __get_type(self):
        return self._post['type']
    type = property(__get_type)

if __name__ == '__main__':
    config = Config()

    print config.tumblr_consumer_key
    print config.tumblr_consumer_secret

    if len(sys.argv) == 3:
        auth = SavedAuth(*sys.argv[1:])
    elif config.tumblr_oauth_token is not None and config.tumblr_oauth_token_secret is not None:
        auth = SavedAuth(config.tumblr_oauth_token, config.tumblr_oauth_token_secret)
    else:
        auth = TumblrAuth(
            config.tumblr_consumer_key,
            config.tumblr_consumer_secret
        )

    print auth.response
    print auth.access_token

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

    print client.info()

    for blog in IterFollowing(client):
        print
        print
        print blog['name']

        posts = client.posts(blog['name'], limit=10)
        for post in posts['posts']:
            post = PostScanner(post)
            print
            print 'type: %s' % (post.type,)
            print 'date: %s' % (post.date,)
