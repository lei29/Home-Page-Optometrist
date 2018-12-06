#!/usr/local/bin/python3.4
import flask
import os
import validators
import urllib.request
from urllib.parse import urlparse
from wpo import get_html_at_url, make_etree,make_outline, copy_profile_photo_static
app = flask.Flask(__name__)


@app.route('/')
def root_page():
    return flask.render_template('root.html')

@app.route('/outline')
def outline_view():
    value = flask.request.args.get("url")
    html = get_html_at_url(value)
    etree = make_etree(html,value)
    outline = make_outline(etree)
    return outline
'''
@app.route('/view')
def view_page():

	#testing purpose test svn test svn
    usrarg = flask.request.args.get("url")
    print(usrarg)
    urlvalidity = validators.url(usrarg)
    if(urlvalidity != True):
        return "Wrong url, please go back"

    social_list = ["www.facebook.com","www.qzone.qq.com","www.tumblr.com","www.instagram.com","www.twitter.com","www.skype.com","www.vk.com","www.linkedin.com","www.reddit.com"]
    urlobj = urlparse(usrarg)
    print(urlobj.netloc)
    if(urlobj.netloc in social_list):
        print("URL should not be social network.")
        return "URL should not be social network, please go back"
    req = urllib.request.Request(usrarg)
    req.add_header('Referer', 'http://www.python.org/')
    # Customize the default User-Agent header value:
    req.add_header('User-Agent', 'PurdueUniversityClassProject/1.0 (lei29@purdue.edu https://goo.gl/dk8u5s)')
    open = get_html_at_url(usrarg)
    return "<base href="+usrarg+">"+open
    # Credit: Adapted from example in Python 3.4 Documentation, urllib.request
    #         License: PSFL https://www.python.org/download/releases/3.4.1/license/
    #                  https://docs.python.org/3.4/library/urllib.request.html
'''
@app.route('/view')
def view_page():
    global usrarg
	#testing purpose test svn test svn
    usrarg = flask.request.args.get("url")
    #print(usrarg)
    urlvalidity = validators.url(usrarg)
    if(urlvalidity != True):
        return "Wrong url, please go back"

    social_list = ["www.facebook.com","www.qzone.qq.com","www.tumblr.com","www.instagram.com","www.twitter.com","www.skype.com","www.vk.com","www.linkedin.com","www.reddit.com"]
    urlobj = urlparse(usrarg)
    #print(urlobj.netloc)
    if(urlobj.netloc in social_list):
        #print("URL should not be social network.")
        return "URL should not be social network, please go back"
    if(usrarg[-1]!="/"):
        usrarg = usrarg+"/"
    req = urllib.request.Request(usrarg)
    req.add_header('Referer', 'http://www.python.org/')
    # Customize the default User-Agent header value:
    req.add_header('User-Agent', 'PurdueUniversityClassProject/1.0 (lei29@purdue.edu https://goo.gl/dk8u5s)')
    open = get_html_at_url(usrarg)
    #print(usrarg)
    html = "<base href="+usrarg+">"+open
    etree1 = make_etree(html,usrarg)

    #print(html)
    #print(etree1)
    #print("UTIL copy is fine")
    path = copy_profile_photo_static(etree1)
    #filename = path[len(os.getcwd()):]

    filename = os.path.basename(path)

    #print(filename)
    static_url = flask.url_for('static', filename = filename)
    #print(static_url)
    return flask.redirect(static_url)

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=os.environ.get("ECE364_HTTP_PORT", 8000),use_reloader=True, use_evalex=False, debug=True, use_debugger=False)
    # Each student has their own port, which is set in an environment variable.
    # When not on ecegrid, the port defaults to 8000.  Do not change the host,
    # use_evalex, and use_debugger parameters.  They are required for security.
    #
    # Credit:  Alex Quinn.  Used with permission.  Preceding line only.
