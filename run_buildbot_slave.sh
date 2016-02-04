#!/bin/bash

# Script to start and stop a digital ocean slave node for the holoviews
# buildbot.
#
# USAGE:
#
# ./run_buildbot_slave.sh
#
# This will start the slave and hang. The slave will be shutdown and
# deleted when the script exits (use Ctrl+C).
#
# Requires the TOKEN to be set. Developers can log into
# holoviews@gmail.com and look for the e-mail 'DIGITAL OCEAN TOKEN' and
# anyone else using this script can contact us on Gitter to request one:
#
# https://gitter.im/ioam/holoviews
 

TOKEN=BUILDBOT_SECRET_TOKEN
SIZE="2"  # Size in GB of the node.

function start_slave {

    echo "Starting slave..."
    images=$(curl -s -X GET -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" "https://api.digitalocean.com/v2/images?page=3") 
    snapshot_id=$(echo $images | jq '.images[] | select(.name == "buildbot-slave") | .id')


    # Should check that there is no droplet already called buildbot-slave...
    started=$(curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{"name":"buildbot-slave","region":"lon1","size":"'$SIZE'gb","image":'$snapshot_id',"ssh_keys":["e6:28:e6:95:c3:1a:3a:5e:b5:f0:e6:f9:e9:98:90:f7"],"backups":false,"ipv6":true,"user_data":null,"private_networking":null}' "https://api.digitalocean.com/v2/droplets" % 'MacBook')
    echo
    echo "Note, it may take a few minutes for the slave to boot up and connect to buildbot. Please be patient!"
}

function start_wait_slave {
    start_slave
    echo "Retrieving droplet IP..."
    sleep 10
    # Find the droplet IP
    droplets=$(curl -s -X GET -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" "https://api.digitalocean.com/v2/droplets?page=1")

    droplet_IP=$(echo $droplets | jq '.droplets[] 
                                     | select(.name == "buildbot-slave")
                                     | .networks.v4[0].ip_address')
    running=$(echo "$droplet_IP" | wc -w)
    if (( $running > 1 )); then echo 'More than one buildbot-slave droplet already running' && exit 1; fi
    echo "The IP of the droplet is" $droplet_IP

    count=0
    while [ 1 ]
    do
        sleep 2
        count=$((count + 1))
        ping -q -c 1 $(echo "$droplet_IP" | tr -d '"')  && echo 'Slave responded to ping. Wait a minute for the slave to connect to buildbot.' && exit
        echo "No response after $count tries (can take up to 50 tries)"
    done
    }

function stop_slave {
    # Find the droplet ID
    droplets=$(curl -s -X GET -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" "https://api.digitalocean.com/v2/droplets?page=1")
    droplet_id=$(echo $droplets | jq '.droplets[] | select(.name == "buildbot-slave") | .id')
    # Shutdown
    echo
    echo "Sending shutdown command... (60 second wait)"
    shutdown=$(curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{"type":"shutdown"}' "https://api.digitalocean.com/v2/droplets/$droplet_id/actions")
    sleep 60
    echo "Shutdown should have happened by now."
    echo "Deleting droplet..."
    curl -s -X DELETE -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" "https://api.digitalocean.com/v2/droplets/$droplet_id"
    echo "Droplet deleted."
}


[ -z "$TOKEN" ] && echo "Need to set the TOKEN environment variable. See inside script for details." && exit 1;



case $1 in
    start)
        start_slave;exit;;
     stop)
         stop_slave;exit;;
     start-wait)
         start_wait_slave; exit;;
     *)
        echo "Options are start, start-wait or stop";;
esac



trap stop_slave EXIT
echo
echo "This script will hang while the slave is running; quit script with Ctrl+C to shutdown slave."
start_slave
echo
echo "PLEASE SHUTDOWN THIS SCRIPT ONCE YOU ARE DONE FORCING A BUILD!"
echo
echo "LINKS"
echo
echo "Website builder:    http://buildbot.holoviews.org:8010/builders/website"
echo "Main buildbot page: http://buildbot.holoviews.org:8010/"
echo "Preview site:       http://test.holoviews.org.s3-website-eu-west-1.amazonaws.com/"


while true; do
    sleep 1
done
