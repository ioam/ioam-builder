# Website served to trigger buildbot builders
#
# Make sure to pip install bottle and that port 8000 is open, i.e:
#
#   docker run --name=master -p 8000:8000 -p 8010:8010 -p 10000:9989 -d purism/buildbot-master
#
# Copy this file into the container:
#
#    docker cp listener.py master:/master/listener.py
#
# Run as follows (i.e as a deamon):
#
#   docker exec -d master python /master/listener.py
#
# In the container, it will be listed using px aux:
#
# GitHub webhook target:
#
#  http://buildbot.holoviews.org/merge


import logging
import socket
import threading
from bottle import route, run, request, template
import pprint, json, os
from datetime import datetime, time
from time import time as unix_time
from time import sleep, ctime
import requests


logging.basicConfig(filename='listener.log',level=logging.DEBUG)

# IN MINUTES
START_WAIT = 5    # Time to wait after slave-start
WEBSITE_WAIT= 30  # Time to let website build run

# Time to disable website trigger due to nightlies. (hours, mins)
DISABLED_START=(00,30)
DISABLED_STOP=(01,40)


PREFIX = "buildbot sendchange -m localhost:9999 -a script:pass -W scriptbot"
BUILD_WEBSITE =  PREFIX + " -C website"
STOP_SLAVE =  PREFIX + " -C stop"
START_SLAVE =  PREFIX + " -C start"
UPDATE_TEST_DATA = PREFIX + " -C update"
TRIGGER_MERGE = PREFIX + " -C merge"

IP = socket.gethostbyname(socket.gethostname())
START_WAIT_S = int(START_WAIT*60)
WEBSITE_WAIT_S = int(WEBSITE_WAIT*60)

# Validation

def insufficient_elapsed_build_time(builder, limit=120, url="http://buildbot.holoviews.org:8010"):
    query = "/json/builders/%s/builds?select=-1" % builder
    url = url + query
    try:
        response = requests.get(url, headers={})
        json_response = response.json()
        # No builds exist yet
        if json_response['-1'].get('error') == 'Not available':
            return False
        last_build_time = int(json_response['-1']['steps'][0]['times'][0])
    except:
        return "Could not find last build from buildbot."
    elapsed = (unix_time() - last_build_time) / 60.0
    logging.info("Time since last build (minutes): %d" % elapsed)
    if elapsed < limit:
        return (("Please wait %.2f minutes before triggering %r builder again."
                "<br>The time limit is %s. Please try again later.")
                % (limit-elapsed, builder, limit))
    return False


def website_build_disabled(start=DISABLED_START, stop=DISABLED_STOP):
    now = datetime.now()
    now_time = now.time()
    if now_time >= time(*start) and now_time <= time(*stop):
        message="Currently disabled due to scheduled nightly build."
        return message
    else:
        # From the time of start-slave NOT website!
        insufficient_time = insufficient_elapsed_build_time("start-slave")
        logging.info(insufficient_time)
        if insufficient_time:
            return insufficient_time
        return False

# Triggers

def build_website(PR_number):
    logging.info("Running the website task on buildbot.")
    logging.info("Building website for #PR%d" % PR_number)
    os.system(BUILD_WEBSITE + " -p PR_number:%d" % PR_number)
    threading.Timer(WEBSITE_WAIT_S, stop_slave).start()

def stop_slave():
    logging.info( "Running the stop-slave task on buildbot.")
    os.system(STOP_SLAVE)

def start_slave():
    logging.info( "Running the start-slave task on buildbot.")
    os.system(START_SLAVE)
    sleep(3) # To allow buildbot to trigger and register a new build.

def update_test_data(PR_number):
    logging.info( "Running the update-PR task on buildbot for #PR%d." % PR_number)
    os.system(UPDATE_TEST_DATA + " -p PR_number:%d" % PR_number)


def trigger_merge(PR_number):
    logging.info( "Running the merge task on buildbot for #PR%d." % PR_number)
    os.system(TRIGGER_MERGE + " -p PR_number:%d" % PR_number)

# Bottle server

@route('/merge', method='POST')
def merge_webhook():
    postdata = request.body.read()
    json_data = json.loads(postdata)
    # logging.info(pprint.pformat(json_data))
    if 'pull_request' in json_data and 'action' in json_data:
        if json_data['pull_request'].get('merged')==True:
            if json_data['action']=='closed':
                try:
                    PR_number = int(json_data['number'])
                except:
                    logging.info("ERROR EXTRACTING PR NUMBER")
                    return 'Server ERROR (Data received)\n'

                logging.info("**MERGE DETECTED. TRIGGERING MERGE. #PR%d**" % PR_number)
                trigger_merge(PR_number)
    return 'Data received\n'


@route('/<PR_number:int>')
def page(PR_number):
    update_info = ( "Before running a test data update, ensure the build is cached "
                    "and check the testa dat is correct at travis.holoviews.org")
    website_info = "Trigger a website build to update http://build.holoviews.org/"
    stop_info = "Stop the website builder slave."

    return ("<h2>Buildbot commands #PR%s</h2>" % PR_number
            + """<form method="POST" action="/%s">""" % PR_number
            + website_info + "<br/>"
            + """<input name="website" value="Update Website" type="submit" /> <br/>"""
            + update_info + "<br/>"
            + """<input name="update" value="Update Test Data" type="submit"/> <br/>"""
            + stop_info + "<br/>"
            + """<input name="stop" value="Stop Slave" type="submit"/> <br/>"""
            +"""</form>""")


@route('/<PR_number:int>', method='POST')
def submit(PR_number):
    PR_number = int(PR_number)
    update = request.forms.get('update') == 'Update Test Data'
    website = request.forms.get('website') == 'Update Website'
    stop = request.forms.get('stop') == 'Stop Slave'
    if stop:
        stop_slave()
        return "%s</br>Stopped the slave" % ctime()
    if website:
        disabled =  website_build_disabled()
        if disabled: return disabled
        start_slave()
        threading.Timer(START_WAIT_S, build_website, args=(PR_number,)).start()
        return ("%s</br>" % ctime()
                + "Started website building process for the <a href='http://build.holoviews.org/'>preview website</a> </br>"
                + "Time till website build starts: %s minutes, Time given to website builder: %s minutes" % (START_WAIT, WEBSITE_WAIT)
                + "Please visit <a href='http://buildbot.holoviews.org:8010/waterfall'>HoloViews Buildbot</a> to follow the build process.")
    elif update:
        disabled = insufficient_elapsed_build_time('update-PR', limit=7)
        if disabled: return disabled

        update_test_data(PR_number)
        return ("%s</br>" % ctime()
                + "Started the test data updating process for #PR%d </br>" % PR_number
                + "Please visit http://buildbot.holoviews.org:8010/waterfall to follow the build process.")


run(host=IP, port=8000, debug=True)
