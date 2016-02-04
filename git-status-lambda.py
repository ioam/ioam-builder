from __future__ import print_function

import json, codecs
import requests
import github
import boto3

GITHUB_TOKEN  = 'HIDDEN'
CACHE_SIZE    = 12
STATUS        = {'context': 's3-reference-data-cache'}
BUCKET        = 'preview.holoviews.org'
TRAVIS_API    = 'https://api.travis-ci.org/repos/ioam/holoviews/builds'
GITHUB_PR_API = 'https://api.github.com/repos/ioam/holoviews/pulls/'
CACHED_MSG    = 'Test data is cached.'
FAIL_MSG      = 'Test data not cached, see details to rebuild.'
PASSED_MSG    = 'Tests passing no test data changes required.'
PENDING_MSG   = 'Tests still building.'

s3 = boto3.resource('s3')
s3_client = boto3.client('s3')

g = github.Github(GITHUB_TOKEN)
repo = g.get_repo('ioam/holoviews')

def delete_folder(number):
    bucket = s3.Bucket(BUCKET)
    for obj in bucket.objects.filter(Prefix=number+'/'):
        s3.Object(bucket.name, obj.key).delete()

def get_build(number):
    data = json.loads(requests.get(TRAVIS_API+'?number=%s' % number).text)
    return data[0] if data else None

def get_build_detail(number):
    data = json.loads(requests.get(TRAVIS_API+'/%s' % number).text)
    return data if data else None

def get_commit(number):
    return json.loads(requests.get(GITHUB_PR_API+number).text)['head']['sha']

def update_status(build_number, cached):
    details = dict(STATUS)
    build = get_build(build_number)
    pr = get_build_detail(build['id'])
    pr_number = pr['compare_url'].split('/')[-1]
    commit_sha = get_commit(pr_number)
    if pr['state'] != 'finished' and pr['number'] not in cached:
        details['state'] = 'pending'
        details['description'] = PENDING_MSG
    elif pr['result'] == 0:
        details['state'] = 'success'
        details['description'] = PASSED_MSG
    elif pr['number'] in cached:
        details['state'] = 'success'
        details['description'] = CACHED_MSG
    else:
        details['state'] = 'failure'
        details['description'] = FAIL_MSG
    commit = repo.get_commit(commit_sha)

    details["target_url"] = "http://buildbot.holoviews.org:8000/%s" % pr_number 
    commit.create_status(**details)

def handler(build_number, context):
    paginator = s3_client.get_paginator('list_objects')
    cached = [b['Prefix'][:-1] for b in list(paginator.paginate(Bucket=BUCKET, Delimiter='/'))[0]['CommonPrefixes']]
    cached = sorted(cached)
    removed = cached[:-12]
    cached = cached[-12:]
    for build in removed:
        delete_folder(build)
        update_status(build, cached)
    update_status(build_number, cached)
