FROM python:2

RUN apt-get update
RUN apt-get install -y zip

RUN mkdir pytumblr
ADD https://github.com/tumblr/pytumblr/archive/master.zip pytumblr/.
RUN cd pytumblr && unzip master.zip && cd pytumblr-master && python setup.py install && cd ../..

ADD config.ini .
ADD tumblrBlogCleaner.py .

CMD python tumblrBlogCleaner.py
