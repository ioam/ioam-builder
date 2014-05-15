"""
Script to move and commit static html notebooks to media directory
on ioam.github.com:master.

This script also fixes html links between notebooks.
"""

import subprocess, os, sys, glob, re

try: input = raw_input
except NameError: pass

IOAM_REPO = os.path.abspath(os.path.join(__file__, '..', '..', 'reference_data'))
HTML_GLOB = os.path.abspath(os.path.join(__file__, '..', '..', '_build', 'html', 'Tutorials', '*.html'))
STATIC_DIR = os.path.abspath(os.path.join(__file__, '..', '..', 'reference_data', 'media'))


def fix_notebook_links(project, files):
    for f in files:
        with open(f, 'r') as html_file:
            html = html_file.read()
        fixed_html = re.sub(r"<a\ href=\"([\w ]+).ipynb\">", r'<a href="http://ioam.github.com/media/%s/\1.html">' % project, html)
        with open(f, 'w') as html_file:
            html_file.write(fixed_html)


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
    data_branch = project + "-data"
    html_files = [f for f in glob.glob(HTML_GLOB) if os.path.basename(f) != 'index.html']
    fix_notebook_links(project, html_files)

    if prompt:
        msg = input('Are you ready to push static notebooks? [y, N]: ')
        if msg.strip().lower() != 'y':
            sys.exit(0)

    switch_branch(IOAM_REPO, "master")
    dest_dir = os.path.join(STATIC_DIR, project)
    if not os.path.isdir(dest_dir):
        os.mkdir(dest_dir)

    dest_files = [os.path.join(dest_dir, os.path.basename(f)) for f in html_files]

    for f, dest_f in zip(html_files, dest_files):
        os.rename(f, dest_f)

    add_files(IOAM_REPO, dest_files)
    commit(IOAM_REPO, "Updated static notebooks for %s." % project)
    push(IOAM_REPO)
    switch_branch(IOAM_REPO, data_branch)