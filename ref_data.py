import sys, json, time, os, shutil
import requests

from dateutil.parser import parse
from datetime import tzinfo, timedelta, datetime

import boto3
from boto3.session import Session

AWS_ACCESS_KEY_ID=BUILDBOT_SECRET_TOKEN
AWS_SECRET_ACCESS_KEY=BUILDBOT_SECRET_TOKEN


headers = {"User-Agent": "Python script (requests)" ,
            "Content-Type": "application/json" ,
            "Accept": "application/vnd.travis-ci.2+json" ,
            "Travis-API-Version": 3}

def get_builds():
    url = "http://api.travis-ci.org/repo/ioam%2Fholoviews/builds"
    response = requests.get(url, headers=headers)
    json_response = response.json()
    return  json_response['builds']


def get_build_id(builds, number):
    matches =  [build for build  in builds if build['number'] == str(number)]
    if len(matches) == 0:
        print "No builds matching the given build number"
        sys.exit()
    elif len(matches) > 1:
        print "Multiple builds matching the same build number!"
        sys.exit()
    return int(matches[0]['id'])


def wait_for_build(build_id):
    "Returns True on success, False on failure"
    url = "https://api.travis-ci.org/build/%d" % build_id
    pings = 0
    while True:
        time.sleep(5)
        pings += 1
        response = requests.get(url, headers=headers)
        json_response = response.json()
        state = json_response['state']
        if state in ["started", "created"]:
            print "Build status is '%s' [pings %d]" % (state, pings)
        elif state=="failed":
            print "Build failed"
            return False
        elif state=="passed":
            print "Build success."
            return True
        else:
            print "Unhandled status %s" % state
            return False


def restart_build(build_number):
    os.system("travis restart -r ioam/holoviews %d" % build_number)


def restart_master_merge_build(PR_number):
    url = "http://api.travis-ci.org/repos/ioam/holoviews/builds"
    response = requests.get(url, headers={})
    builds = response.json()
    for build in builds:
        if build['branch'] == 'master':
            if build['message'].startswith('Merge pull request #%d' % PR_number):
                build_number = int(build["number"])
                print ("Restarting master merge build %d for #PR%d"
                       % (build_number, PR_number))
                restart_wait(build_number)
                return True
    print "Could not find merge build for #PR%d" % PR_number
    return False


def restart_wait(build_number):
    build_number = int(build_number)
    builds = get_builds()
    build_id =  get_build_id(builds, build_number)
    print "The build ID of build #%d is %d" % (build_number, build_id)
    print ("You can view the status on "
           "https://travis-ci.org/ioam/holoviews/builds/%s" % build_id)
    restart_build(build_number)
    success = wait_for_build(build_id)
    sys.exit(0) if success else sys.exit(1)


def last_build(PR_number, check_available=True):
    # Need to handle None for master
    PR_number = int(PR_number)
    # Branch builds exist too e.g: 'refs/heads/bokeh_improvements'
    if PR_number == 0:
        print "PR number is zero. Looking for latest master build."
        target_ref = "refs/heads/master"
    else:
        target_ref = "refs/pull/%d/merge" % PR_number
    builds = get_builds()
    matches = [(parse(build["commit"]["committed_at"]), build["number"])
               for build in builds if build["commit"]["ref"] == target_ref]

    if matches == []:
        print "No Travis builds found for PR #%d" % PR_number
        sys.exit(1)

    sorted_matches = sorted(matches)
    build_number = int(sorted_matches[-1][1])

    if check_data_available:
        available = check_data_available(build_number)
        if not available:
            print "Test data for build %d is not available on S3." % build_number
            print "Please restart the build to make it available."
            sys.exit(1)
        else:
            print "The test data for build %d is available on S3." % build_number

    return build_number

## S3 Utilities

def check_data_available(build_number):
    session = Session(aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                      region_name='eu-west-1')
    s3 = session.client('s3')
    directories=[]
    paginator = s3.get_paginator('list_objects')
    for result in paginator.paginate(Bucket='preview.holoviews.org', Delimiter='/'):
        for prefix in result.get('CommonPrefixes'):
            directories.append(prefix.get('Prefix')[:-1])
    return str(build_number) in  directories


def copy_from_S3(build_number, destdir, bucket='preview.holoviews.org'):
    destdir = os.path.abspath(destdir)
    if os.path.exists(destdir):
        print "Removing existing directory %s\n" % destdir
        shutil.rmtree(destdir)

    session = Session(aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                      region_name='eu-west-1')

    s3 = session.client('s3')
    s3_resource = session.resource('s3')
    # listing=s3.list_objects(Bucket=bucket)['Contents']
    bucket_obj = s3_resource.Bucket('preview.holoviews.org')
    for s3_key in list(bucket_obj.objects.all()):
        s3_object = str(s3_key.key)
        if s3_object.startswith('%d/' % build_number):
            if s3_object == '%d/' % build_number:
                continue
            print "Downloading %s to %s" % (s3_object, destdir)
            s3_dir='/'.join(s3_object.split('/')[1:-1])
            s3_path = '/'.join(s3_object.split('/')[1:])
            dest = os.path.join(destdir, s3_path)
            target_dir = os.path.join(destdir, s3_dir)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            s3.download_file(bucket, s3_object, dest)



destdir = '/slave/update-PR/travis_build'

if sys.argv[1] == 'restart-wait':
    if sys.argv[2]== 'BUILD_NUMBER_FILE':
        with open('/slave/update-PR/BUILD_NUMBER_FILE', 'r') as f:
            build_number = int(f.read())
    else:
        build_number = int(sys.argv[2])

    restart_build(build_number)
    # restart_wait(build_number)    # Travis API changed. No longer works.

elif sys.argv[1] =='last-build':
    assert int(sys.argv[2]) >= 0
    print last_build(sys.argv[2])
elif sys.argv[1] == 'restart-master-merge':
    restart_master_merge_build(int(sys.argv[2]))
elif sys.argv[1]=='fetch-PR':

    if sys.argv[2] == 'None':
        PR_number = 0
    if int(sys.argv[2]) <= 0:
        print "Please specify the PR number (use 0 for master branch)"
        sys.exit(1)
    else:
        PR_number = int(sys.argv[2])

    build_number = last_build(PR_number)
    print "The last Travis build number for PR #%s is %d" % (PR_number, build_number)
    print "\nFetching data for build number %d from S3\n" % build_number
    copy_from_S3(int(build_number), destdir)
    print "Writing the PR number to BUILD_NUMBER_FILE"
    with open('/slave/update-PR/BUILD_NUMBER_FILE', 'w') as f:
        f.write(str(PR_number))
else:
    print "First argument must be either 'restart-wait', 'restart-master-merge', 'last-PR-build' or 'fetch-PR'"

