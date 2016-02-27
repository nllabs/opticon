import ConfigParser
from datetime import datetime
from functools import wraps
from collections import defaultdict

from flask import Flask
from flask import request, Response

from s3 import S3

from email_interface import EmailHandler
import lnetatmo
from fb import Fb

config = ConfigParser.RawConfigParser()
config.read('opticon.cfg')

app = Flask(__name__)
s = S3(config)
s.connect_to_s3()
e = EmailHandler(config)
f = Fb(config)

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


@app.route('/stats/<year>/<month>')
@requires_auth
def stats(year, month):
    header = '<html><head></head><body>'
    footer = '</body></html>'
    captures = []
    stats_dict = {}
    stats_dict['channel'] = defaultdict(int)
    #stats_dict['year'] = defaultdict(int)
    stats_dict['month'] = defaultdict(int)
    stats_dict['day'] = defaultdict(int)
    stats_dict['hour'] = defaultdict(int)
    #stats_dict['minute'] = defaultdict(int)
    #stats_dict['second'] = defaultdict(int)
    #stats_dict['total'] = defaultdict(int)
    
    for i in range(1,3):
        captures.extend(s.get_captures_from_prefix('CH0%d_%s_%s' % (i, year, month)))
    for (key, url) in captures:
        key = key.replace('.jpg', '')
        key = key.replace('CH', '')
        key_split = key.split('_')
        stats_dict['channel'][key_split[0]] += 1
        #stats_dict['year'][key_split[1]] += 1
        stats_dict['month'][key_split[2]] += 1
        stats_dict['day'][key_split[3]] += 1
        stats_dict['hour'][key_split[4]] += 1
        #stats_dict['minute'][key_split[5]] += 1
        #stats_dict['second'][key_split[6]] += 1
        #stats_dict['total']['total'] += 1

    html = '' + header
    for (group, count_dict) in stats_dict.iteritems():
        html = html + '<h2>%s</h2><br />' % (group)
        for (value, count) in sorted(count_dict.iteritems()):
            html = html + '%s : %d' % (value, count)
            html = html + '|' * (count)
            html = html + '<br />'
    html = html + footer
    return html

@app.route('/weather')
@requires_auth
def weather():
    header = '<html><head></head><body>'
    footer = '</body></html>'
    html = header
    html = html + """
    <iframe id="forecast_embed" type="text/html" frameborder="0" height="210" width="720" src="http://forecast.io/embed/#lat=37.4634447&lon=-122.22568030000002&name=Redwood City"> </iframe> <br />
            <iframe src="http://www.wrh.noaa.gov/mtr/getzfpzone.php?sid=mtr&zone=caz508" style="border:none"> </iframe><br />
            <iframe src="http://forecast.weather.gov/MapClick.php?lat=37.4634447&lon=-122.22568030000002&unit=0&lg=english&FcstType=text&TextType=1" width="720" height="800" style="border:none"> </iframe><br />
        """
    html = html + '<img src="http://www.ssd.noaa.gov/goes/west/wfo/mtr/vis.jpg" width="720" height="480"> <br />'
    html = html + '<img src="http://www.ssd.noaa.gov/goes/west/wfo/mtr/rgb.jpg" width="720" height="480"> <br />'
    html = html + '<img src="http://www.ssd.noaa.gov/goes/west/wfo/mtr/ir2.jpg" width="720" height="480"> <br />'
    html = html + '<img src="http://radar.weather.gov/ridge/Conus/Loop/pacsouthwest_loop.gif"> <br />'
    authorization = lnetatmo.ClientAuth()
    dev_list = lnetatmo.DeviceList(authorization)
    for (device, measures) in dev_list.lastData().iteritems():
        html = html + '<h2>%s</h2><br />' % (device)
        for (measure, value) in measures.iteritems():
            html = html + '%s : %d<br />' % (measure, value)
    html = html + footer
    return html

@app.route('/goals')
@requires_auth
def goals():
    f.connect_to_fitbit()
    f.get_data()
    header = '<html><head></head><body>'
    footer = '</body></html>'
    html = header
    html = html + """
    <iframe height='160' width='300' frameborder='0' allowtransparency='true' scrolling='no' src='https://www.strava.com/athletes/7495548/activity-summary/f40ddafd975b5c8d1d2d6d1d7ed962d8ae93fa4b'></iframe> <br />
    """
    html = html + f.get_html()
    html = html + footer
    return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
