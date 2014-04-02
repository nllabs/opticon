import ConfigParser
from datetime import datetime
from functools import wraps

from flask import Flask
from flask import request, Response

from s3 import S3

from email_interface import EmailHandler

config = ConfigParser.RawConfigParser()
config.read('opticon.cfg')

app = Flask(__name__)
s = S3(config)
s.connect_to_s3()
e = EmailHandler(config)

def check_auth(username, password):
    return username == config.get('App', 'username') and password == config.get('App', 'password')

def authenticate():
    return Response(
            'Could not verify your access level for that URL.\n'
            'You have to login with proper credentials', 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth= request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/about')
def description():
    return 'Welcome to opticon'


@app.route('/captures/', defaults={'ch' : None, 'year' : None, 'month' : None, 'day' : None, 'hour' : None})
@app.route('/captures/<year>/<month>/<day>/<hour>/<ch>')
@requires_auth
def captures(ch, year, month, day, hour):
    header = '<html><head></head><body>'
    footer = '</body></html>'
    dt = datetime.today()
    if hour is None:
        hour = str(dt.hour)
        if len(hour) == 1: hour = '0' + hour
    else: hour = str(hour)
    if day is None:
        day = str(dt.day)
        if len(day) == 1: day = '0' + day
    else: day = str(day)
    if month is None:
        month = str(dt.month)
        if len(month) == 1: month = '0' + month
    else: month = str(month)
    if year is None:
        year = str(dt.year)[-2:]
    else: year = str(year)
    html = '' + header
    if (ch is None) or (ch == '*'):
        for i in range(1,5):
            for (key, url) in s.get_captures_from_prefix('CH0%d_%s_%s_%s_%s' % (i, year, month, day, hour)):
                html = html + '<h2>%s</h2><img src="%s" /><br />' % (key, url)
    else:
        for (key, url) in s.get_captures_from_prefix('CH%s_%s_%s_%s_%s' % (ch, year, month, day, hour)):
            html = html + '<h2>%s</h2><img src="%s" /><br />' % (key, url)

    html = html + footer
    return html


@app.route('/update_captures')
@requires_auth
def update_captures():
    e.connect_to_server()
    complete_messages = []
    try:
        for message in e.get_messages():
            try:
                for (i, filename, attachment) in e.get_attachments(message):
                    s.save_to_key(filename, attachment)
                    complete_messages.append(i)
            except Exception as er:
                print er
                pass
        e.delete_messages(set(complete_messages))
        e.disconnect_from_server()
    except Exception as er:
        print er
    result = 'Updated %d captures' % len(complete_messages)
    print result
    return result

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
