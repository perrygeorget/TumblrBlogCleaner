import getpass
import oauth2
import pytumblr
import urllib
import urlparse

import ConfigParser

access_token_url = 'https://www.tumblr.com/oauth/access_token'

class Credentials:
    def __init__(self):
        self.__username = None
        self.__password = None

    def ask_credentials(self):
        self.__username = raw_input("Username: ")
        self.__password = getpass.getpass("Password: ")

    def __get_username(self):
        return self.__username

    username = property(__get_username)

    def __get_password(self):
        return self.__password

    password = property(__get_password)

class Config:
    def __init__(self):
        self.__config = ConfigParser.ConfigParser()
        self.__config.read('config.ini')

    def __get_tumblr_consumer_key(self):
        return self.__config.get('tumblr', 'consumer_key')

    tumblr_consumer_key = property(__get_tumblr_consumer_key)

    def __get_tumblr_consumer_secret(self):
        return self.__config.get('tumblr', 'consumer_secret')

    tumblr_consumer_secret = property(__get_tumblr_consumer_secret)

class TumblrXAuth:
    def __init__(self, consumer_key, consumer_secret, username, password):
        self.__consumer_key = consumer_key
        self.__consumer_secret = consumer_secret
        self.__username = username
        self.__password = password
        self.__access_token = None

    def __get_params(self):
        return {
            'x_auth_username': self.__username,
            'x_auth_password': self.__password,
            'x_auth_mode': 'client_auth'
        }

    def __get_client(self, consumer):
        client = oauth2.Client(consumer)                                                                                                                                                      
        client.add_credentials(self.__username, self.__password)
        client.authorizations  

        client.set_signature_method = oauth2.SignatureMethod_HMAC_SHA1()
        return client

    def __get_access_token(self):
        if self.__access_token == None:
            consumer = oauth2.Consumer(self.__consumer_key, self.__consumer_secret)
            client = self.__get_client(consumer)

            params = self.__get_params()
            resp, token = client.request(access_token_url, method="POST", body=urllib.urlencode(params))
            self.__access_token = dict(urlparse.parse_qsl(token))

        return self.__access_token

    access_token = property(__get_access_token)

    def clear(self):
        self.access_token = None

if __name__ == '__main__':
    credentials = Credentials()
    credentials.ask_credentials()

    config = Config()

    print credentials.username
    print '*' * len(credentials.password)

    print config.tumblr_consumer_key
    print config.tumblr_consumer_secret

    xauth = TumblrXAuth(config.tumblr_consumer_key, config.tumblr_consumer_secret, credentials.username, credentials.password)
    print xauth.access_token
    print xauth.access_token
