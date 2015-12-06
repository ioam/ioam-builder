"""
Script to move and commit static html notebooks to media directory
on ioam.github.com:master.

This script also fixes html links between notebooks.
"""

import subprocess, os, sys, glob

try: input = raw_input
except NameError: pass

IOAM_REPO = os.path.abspath(os.path.join(__file__, '..', '..', 'reference_data'))
HTML_GLOB = os.path.abspath(os.path.join(__file__, '..', '..', '_build', 'html', 'Tutorials', '*.html'))


def switch_branch(repo, branch):
    proc = subprocess.Popen(["git", "checkout", branch], cwd=repo)
    proc.communicate()
    return proc.returncode

def add_files(repo, files):
    proc = subprocess.Popen(["git", "add"] + files, cwd=repo)
    proc.communicate()
    return proc.returncode

def commit(repo, msg):
    proc = subprocess.Popen(["git", "commit", "-m", msg], cwd=repo)
    proc.communicate()
    return proc.returncode

def push(repo):
    proc = subprocess.Popen(["git", "push", "origin", "master"], cwd=repo)
    proc.communicate()
    return proc.returncode



if __name__ == "__main__":
    project = sys.argv[1]
    prompt = True if len(sys.argv) == 2 else False
    if project.lower() == 'holoviews':
        branch = 'tutorials'
        data_branch = 'reference_data'
    else:
        branch = project.lower()+"-tutorials"
        data_branch = project + "-data"
    html_files = [f for f in glob.glob(HTML_GLOB)]

    if prompt:
        msg = input('Are you ready to push static notebooks? [y, N]: ')
        if msg.strip().lower() != 'y':
            sys.exit(0)

    switch_branch(IOAM_REPO, branch)
    dest_files = [os.path.join(IOAM_REPO, os.path.basename(f)) for f in html_files]

    for f, dest_f in zip(html_files, dest_files):
        os.rename(f, dest_f)

    add_files(IOAM_REPO, dest_files)
    commit(IOAM_REPO, "Updated static notebooks for %s." % project)
    push(IOAM_REPO)
    switch_branch(IOAM_REPO, data_branch)
