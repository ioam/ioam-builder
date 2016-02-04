========
Overview
========

This branch contains the files necessary to configure website and
notebook building. The detailed installation instructions may be found
in ``holoviews-buildbot.sh``.

Architecture
~~~~~~~~~~~~

The overall architecture is designed around the premise that you want a
cheap machine (little RAM, few cores) that you can leave on constantly
which boots up a more powerful remote slave machine when needed.

* ``holoviews-buildbot.sh``: Script to configure the infrastructure
  including detailed instructions.
* ``master.cfg``: Defines buildbot configuration.
* ``git-status-lambda.py``: An AWS Lambda function that provides status
  updates in pull requests. Offers a link to a page that can be used to
  control buildbot.
* ``listener.py``: Server that serves th page linked to from the status
  information. Also a target for a GitHub webhook for pull requests (to detect a merge)
* ``run_buildbot_slave.sh``: Used by buildbot to start and stop the more
  powerful remote slave.
* ``ref_data.py``: Tools for handling the reference data, including
  utilities to query travis, restart travis builds and download
  reference data from S3.

Test data is processed as follows:

* Travis builds generates test data (even if the tests fail) and pushes
  this test data to an S3 bucket (preview.holoviews.org)
* PR authors can make sure the data is correct at `travis.holoviews.org
  <http://travis.holoviews.org>`_.
* From the PR status, buildbot can be triggered to update the test
  data. This creates a branch on the ``holoviews-data`` repository using
  the PR number. The original Travis builds are restarted and this time
  they should be able to find the test data (no reference data). These
  builds should now pass.


Constraints
~~~~~~~~~~~

* A time-limit is enforced between reference data update builds and
  between website builds.
* Website builds are disabled via the listener webpage around the time
  of the regularly scheduled nightly builds.
* Only developers with access to buildbot credentials can force start
  the large slave.

Miscellaneous
~~~~~~~~~~~~~

* Master builds are pushed to `dev.holoviews.org
  <http://dev.holoviews.org>`_ and PR builds are pushed to
  `build.holoviews.org <http://build.holoviews.org>`_.
* The official website can be updated as follows::

   aws s3 rm s3://holoviews.org/ --recursive; aws s3 sync s3://dev.holoviews.org/ s3://holoviews.org/ 
