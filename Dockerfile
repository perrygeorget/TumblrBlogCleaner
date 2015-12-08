FROM python:2

RUN apt-get update
RUN apt-get install -y zip
# RUN apt-get install -y zip \
# libtiff5-dev libjpeg-dev zlib1g-dev \
# libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python-tk

RUN mkdir pytumblr
ADD https://github.com/tumblr/pytumblr/archive/master.zip pytumblr/.
RUN cd pytumblr && unzip master.zip && cd pytumblr-master && python setup.py install && cd ../..

RUN mkdir surblclient
ADD https://github.com/byfilip/surblclient/archive/master.zip surblclient/.
RUN cd surblclient && unzip master.zip && cd surblclient-master && python setup.py install && cd ../..

# RUN mkdir Pillow
# ADD https://github.com/python-pillow/Pillow/archive/master.zip Pillow/.
# RUN cd Pillow && unzip master.zip && cd Pillow-master && python setup.py install && cd ../..

ADD config.ini .
ADD tumblrBlogCleaner.py .

CMD python tumblrBlogCleaner.py
