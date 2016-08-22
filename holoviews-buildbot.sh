#!/bin/bash

AWS_ACCESS_KEY_ID=BUILDBOT_SECRET_TOKEN
AWS_SECRET_ACCESS_KEY=BUILDBOT_SECRET_TOKEN

echo """

TOKENS
======

As these files are public, some private information has been
censored. Look for the string BUILDBOT_SECRET_TOKEN. These tokens are:

1. The two AWS tokens above.
2. The same two AWS tokens in ref_data.py
3. The Digital Ocean token in run_buildbot_slave.sh
4. The buildbot password in master.cfg


INSTRUCTIONS
============

Terminology

Master - Buildbot master on same EC2 instance. 
Small slave - Buildbot slave on same EC2 instance.
Large slave - Buildbot slave on Digital ocean instance.
Lambda - Amazon Lambda function.

Files:

You can use FileZilla to move these files to a remote node (easiest once
ssh keys are configured).

1. This setup script/instructions (both slaves).
2. The master.cfg for buildbot master. (master)
3. listener.py for web server. (master)
4. ref_data.py which handles REST API access (small slave)
5. run_buildbot_slave.sh to trigger large slave (small slave)
6. slave-monitor (Lambda )
7. Github status (Lambda)

IMPORTANT: Make sure the listener script has DISABLED_START AND
DISABLED_STOP set to correspond to the nightlies in master.cfg!

INFRASTRUCTURE
==============

Base Docker images:

* purism/buildbot-master
* purism/buildbot-slave images.

Mac OS Docker
-------------

On Mac, make sure you allocate enough memory:

docker-machine create -d virtualbox --virtualbox-memory 4096 buildbot

EC2 instance
------------

Currently using free tier with 30GB of disk space.


Large slave (Digital Ocean)
-----------

The machine image called buildbot-slave must be created on a smaller,
cheaper node which can be flexibly scaled up. The best option is to
configure on a 2GB node.

Note that a 3GB swap on a 2GB node currently works fine.  Instructions
for setting up swap can be found here:
https://www.digitalocean.com/community/tutorials/how-to-add-swap-on-ubuntu-14-04

In short, make a 3GB /swapfile, fix the permissions, enable it, set
vm.swappiness=15, vm.vfs_cache_pressure=50 and edit /etc/sysctl.conf and
/etc/fstab to persist across reboots.

Note that an upstart script is needed to automatically start the
container on boot (and keep it running). This is the job of
docker-buildbot.conf also make sure to delete the twisted PID file
before making an image.

MASTER
======

1. Create a new container as follows:

  docker run --name=master -p 8000:8000 -p 8010:8010 -p 10000:9989 -d purism/buildbot-master

2. Copy this file and listener into the container:

  docker cp holoviews-buildbot.sh master:/master/holoviews-buildbot.sh
  docker cp listener.py master:/master/listener.py

3. Copy master.cfg into the container and jump into it:

  docker cp master.cfg master:/master/master.cfg
  docker exec -it master bash

4. Run this script for master and exit:

  chmod +x holoviews-buildbot.sh
  ./holoviews-buildbot.sh master
  pip install bottle; exit

5. Stop and start master:

  docker stop master; docker start master

6. Start the listener:

   docker exec -d master python /master/listener.py

You can check the listener script is running by jumping into the
container and running ``ps aux``. If you want to update the listener
kill any existing listeners as only one should be running at a time.

If re-imaging (e.g to update bokeh), remember to rm /slave/twistd.pid
before shutting down and creating the image. Only one image called
buildbot-slave should be used.


SMALL SLAVE
===========

1. Use ifconfig to get the IP address (eth0) of the EC2 instance:

   MASTER_IP=xxx.xx.xx.xxx

2. Launch the container:

docker run -p 9989:10000 --name=minislave --privileged -d \
  -e MASTER=$MASTER_IP:10000 -e SLAVE_NAME=minibuilder \
  -e SLAVE_PASSWORD=pass purism/buildbot-slave

3. Copy the start/stop script and fetch script into the container:

  docker cp run_buildbot_slave.sh minislave:/slave/run_buildbot_slave.sh
  docker cp ref_data.py minislave:/slave/ref_data.py
  docker cp holoviews-buildbot.sh minislave:/slave/holoviews-buildbot.sh

4. Jump into the container:

   docker exec -it minislave bash

5. Run this script, make slave running script executable:

   chmod +x /slave/run_buildbot_slave.sh
   chmod +x /slave/holoviews-buildbot.sh
   /slave/holoviews-buildbot.sh small-slave

6. Install the following:

   pip install awscli boto3 flake8 pylint
   sudo apt-get update
   sudo apt-get install curl jq rubygems-integration ruby-dev unzip

7. Install ruby2 from source (now needed by the travis command):

   sudo apt-get -y update
   sudo apt-get -y install build-essential zlib1g-dev libssl-dev \
                           libreadline6-dev libyaml-dev
   cd /tmp
   wget http://cache.ruby-lang.org/pub/ruby/2.0/ruby-2.0.0-p481.tar.gz
   tar -xvzf ruby-2.0.0-p481.tar.gz
   cd ruby-2.0.0-p481/
   ./configure --prefix=/usr/local
   make
   sudo make install
   /usr/local/bin/ruby /usr/local/bin/gem install travis

8. Get the hub tool:

   cd /slave
   wget https://github.com/github/hub/releases/download/v2.2.3/hub-linux-amd64-2.2.3.tgz
   tar zxvf hub-linux-amd64-2.2.3.tgz; mv hub-linux-amd64-2.2.3 hub

9. Configure git and travis credentials. Make sure sf-issues is
   authorized to access travis:

   su buildbot
   git config --global user.email 'holoviews@gmail.com'
   git config --global user.name 'Buildbot'
   travis login --org

10. Remaining as the buildbot user, create an ssh key (no passphrase) and
   add to ssh-agent (visit
   https://help.github.com/articles/generating-a-new-ssh-key/ for more
   info)

   ssh-keygen -t rsa -b 4096 -C 'holoviews@gmail.com'
   eval "$(ssh-agent -s)"
   ssh-add ~/.ssh/id_rsa

11. Add public key to sf-issues user on github and add to hosts:

   cat ~/.ssh/id_rsa.pub
   git clone git@github.com:ioam/holoviews-data.git # Just to add to hosts
   rm -rf holoviews-data
 
10. Exit out of container and restart the slave:

  exit; exit
  docker stop minislave; docker start minislave


LARGE SLAVE
===========

Note that due to the SSH key setup, the login is via ssh root@$DROPLET_IP.

1. Set the MASTER IP:

  # Might want to make sure the port is open
  # e.g using cat < /dev/tcp/52.48.45.34/10000
  MASTER_IP=buildbot.holoviews.org

2. Start the slave container:

   docker run --name=slave-container -p 9989:10000 --privileged \
   -d -e MASTER=$MASTER_IP:10000 -e SLAVE_NAME=docbuilder \
   -e SLAVE_PASSWORD=pass purism/buildbot-slave

3. Copy this file and the S3 script into the container and jump into it:

  docker cp holoviews-buildbot.sh slave-container:/slave/holoviews-buildbot.sh
  docker cp sync_with_S3.sh slave-container:/slave/sync_with_S3.sh
  docker exec -it slave-container bash

4. Get the hub tool:
 
   cd /slave
   wget https://github.com/github/hub/releases/download/v2.2.3/hub-linux-amd64-2.2.3.tgz
   tar zxvf hub-linux-amd64-2.2.3.tgz; mv hub-linux-amd64-2.2.3 hub


5. Install these dependencies:
  sudo apt-get update
  sudo apt-get install curl libsm6 libxrender1 graphviz libav-tools imagemagick # Will fail without libsm and xrender

6. Run this script inside the /slave directory twice and exit:

  rm /slave/twistd.pid
  cd slave; chmod +x holoviews-buildbot.sh;./holoviews-buildbot.sh slave-root
  chmod +x /slave/sync_with_S3.sh
  gosu buildbot ./holoviews-buildbot.sh slave-buildbot; exit
 
7. Start and stop the slave:

 docker stop slave-container; docker start slave-container


WORKFLOW
========

Updating master.cfg
-------------------

1. Edit master.cfg either locally (then upload) or use Emacs tramp mode.

2. Copy into the container:

  docker cp master.cfg master:/master/master.cfg
  docker exec -it master bash

3. Set ownership to buildbot:

  chown buildbot master.cfg
  exit

3. Start and stop the container:

  docker stop master; docker start master

4. Restart the listener:

   docker exec -d master python /master/listener.py


Debugging the slave
-------------------

Switch to the slave container and activate the conda environment:

   docker exec -it slave-container bash
   su buildbot
   source /slave/miniconda/bin/activate buildbot-env

Note that conda packages should be listed in this script.

"""

function sync_script {
    cat > /slave/sync_with_S3.sh <<- EOM
#!/bin/bash

# Trivial script to hide environment variables from buildbot logs and
# select appropriate bucket based on the branch.  Environment variables
# must be used as aws configure is broken for some unknown reason.
case \$2 in
    0)
        BUCKET="s3://dev.holoviews.org";;
    None)
        BUCKET="s3://dev.holoviews.org";;
    *)
        BUCKET="s3://build.holoviews.org";;
esac

AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY aws s3 sync \$1 \$BUCKET
EOM
    chmod +x /slave/sync_with_S3.sh
}


function pylint_rc {
    # Run with pylint --disable=R,C --rcfile=/slave/pylintrc  .
    cat > /slave/pylintrc <<- EOM
[TYPECHECK]

ignored-modules = numpy,param
EOM
}


function docker_conf {
    # Create the docker conf
    cat > /etc/init/docker-buildbot.conf <<- EOM
description "Start docker containers for buildbot master and slave"
author  "holoviews@gmail.com"

start on runlevel [2345]
stop on runlevel [!2345]

respawn

script
    exec docker start slave-container
end script

EOM
}

function git_PR_init {
    # Create the script to checkout PRs with git
    cat > /slave/git_PR_init.sh <<- 'EOM'
#!/bin/bash

# Script to handle checkout/creation of PR branch:

cd /slave/update-PR/build/doc/reference_data;
if [ $(git branch -a --list *origin/$1 | wc -l) -eq 1 ] ; then
    git checkout $1;
    git rm -rf *;
else
    git checkout reference_data;
    git branch $1;
    git checkout $1;
    git rm -rf *;
fi
cd -
EOM
    chmod +x /slave/git_PR_init.sh
}



function slave_root_cmds {
    # Configure root environment for slave
    
    pip install awscli wget coveralls
    rm /slave/twistd.pid # Can break images otherwise
    # AWS credentials
    gosu buildbot aws configure set default.region eu-west-1
    # Modify run script to use conda
    echo -e "$(head -n -1 /run.sh)\ngosu buildbot /slave/miniconda/bin/conda run -n buildbot-env 'buildslave start --nodaemon $SLAVE_ARGS'" > /run.sh
}


function buildbot_cmds {
    sync_script
    # Configure the conda environment for buildbot user (slave)
    INSTALL="buildbot-env python nose numpy=1.9.1 matplotlib bokeh pandas scipy jupyter ipython param runipy sphinx matplotlib seaborn requests beautiful-soup freetype=2.5.2 xarray"

    # Download and install miniconda
    python -c 'import wget; wget.download("https://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh", out="miniconda.sh")'
    bash miniconda.sh -b -p $HOME/miniconda
    export PATH="$HOME/miniconda/bin:$PATH"
    hash -r # Bash builtin: causes the shell to forget all remembered locations. May not be needed.

    # Configure conda, create conda environment buildbot-env
    conda config --set always_yes yes --set changeps1 no
    conda update -q conda
    conda create -q -n $INSTALL
}



function master_cmds {
    # Set ownership of master.cfg and customize buildbot webpage
    chown buildbot master.cfg
    # Modify the welcome page
    cp /usr/local/lib/python2.7/dist-packages/buildbot/status/web/templates/root.html /master/templates/
    cat > ./templates/root_page_diff <<- EOM
  This buildbot interface is designed to allow developers and users to
  update the HoloViews website and notebook test data. The website is
  built nightly and can be previewed for PRs::

  <h3>Previewing a PR change</h3>
  <ol>
    <li>Create a pull request for a documentation change on <a href="https://github.com/ioam/holoviews">GitHub</a>.</li>
    <li>When the PR is ready, ask for the buildbot credentials there.</li>
    <li>Log in to <a href="builders/start-slave">/builders/start-slave</a> to start a slave</li>
    <li>Wait a few minutes for the slave to connect then force a <a
    href="builders/website">/builders/website</a> build, <br> making sure to
    set <b>Target Branch</b> field to the PR branch name and specifying
    your fork (if any).</li>
    <li><b>Please make sure to force a <a
    href="builders/stop-slave">stop slave build</a> when the main build is complete</b></li>
    <li>Once the build is done visit <a
    href="http://build.holoviews.org.s3-website-eu-west-1.amazonaws.com/">preview
    website</a> to view your changes.</li>
  </ol>

 <h3>Updating reference data and merging</h3>

  <ol>
    <li>Create a pull request for a notebook change on <a href="https://github.com/ioam/holoviews">GitHub</a>.</li>
    <li>When the PR is ready, ask for the buildbot credentials there.</li>
    <li>Find the build you want to update that corresponds to the
    <b>last</b> commit on your PR on <a
    href="https://travis-ci.org/ioam/holoviews/">our Travis page</a></li>
    <li>Review the <a href="http://travis.holoviews.org/">display
        changes</a> for this build to make sure the output is
        correct. Note that the build must marked in green as
        [Cached]. <br> If not, you will need restart the build yourself to
        make the test data available.
   <li> If the changes are correct, force an <a
    href="builders/update-merge">/builders/update-merge</a> build,
    making sure you enter both the PR number.</li>
   <li> Buildbot will update the reference data and restart the
   specified build. If it passes, Buildbot will automatically merge the
   PR if the merge checkbox is checked.</li>
</ol>

 <h3>Updating main website after release</h3>

 Requires AWS credentials (developers only):<br></br>

 <code>aws s3 rm s3://holoviews.org/ --recursive; aws s3 sync s3://dev.holoviews.org/ s3://holoviews.org/</code> </br>


<br>Now here is the normal buildbot options panel:

EOM

    sed -i.bak '/request) %}/r /master/templates/root_page_diff' ./templates/root.html
    rm ./templates/root_page_diff
}


case $1 in
    master)
        master_cmds;;
     slave-root)
        slave_root_cmds;;
     slave-buildbot)
         buildbot_cmds;;
     small-slave)
         git_PR_init;
         pylint_rc;;
     upstart-script)
        docker_conf;;
     *)
        echo "Options are master, small-slave, upstart-script, slave-root or slave-buildbot";;
esac
