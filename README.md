# TumblrBlogCleaner
Cleans inactive and hacked tumblr blogs that you follow.

## Requires Tumblr xAuth
Web apps should use the standard OAuth flow, reserving xAuth for apps in which the web authorization process is impractical or impossible, such as native desktop or mobile apps. 

xAuth is not enabled by default. To request xAuth permission for your app, please use the Request xAuth link on an app above.
xAuth access-token URL:

    POST https://www.tumblr.com/oauth/access_token

Accepts `x_auth_username` (the user's email address), `x_auth_password`, and `x_auth_mode=client_auth`, just like Twitter's implementation.

## Configuration

You will need to create `config.ini` at the root of this repository:

    [tumblr]
    consumer_key=<consumer_key>
    consumer_secret=<consumer_secret>

## Building Docker Image

Execute:

    docker build -t tumblr-cleaner .

## Running 

Execute:

    docker run -it --rm --name my-tumblr-cleaner tumblr-cleaner
