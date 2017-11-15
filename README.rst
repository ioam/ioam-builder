============
IOAM builder
============

WIP!

Installation
============

0. Assumptions:

  * You have getting started guide notebooks in
    examples/getting_started
    
  * You have user guide notebooks in examples/user_guide
    
  * You have gallery notebooks in examples/gallery


1. Add sphinx to your project in `doc/`

2. Edit PROJECT and MODULE in doc/Makefile
   
2. Add ioam builder as submodule of your project at `doc/builder`.

0. ``conda env create --file doc/builder/docenv.yml`` (TODO: conda package coming
   instead)

3. Install theme: ``cd doc/builder/ioam_theme && python setup.py install``

3. 
   
3. FAQ.rst
   getting_started/index.rst
   user_guide/index.rst
   index.rst
   about.rst
   latest_news.html
   Reference_Manual/index.rst

   
3. At this point you should be able to build site (see usage, below).


Extras
------
   
1. Either edit these files or comment out references to them in conf.py

  * about.rst: 
  * latest_news.html: twitter account
  * Reference_Manual/index.rst
  * holoviews_theme/includes/ga.html: google analytics


Usage
=====

1. export PYTHONPATH=$PWD/doc
2. cd doc
3. make ipynb-rst (optional: commit result and skip step in future)
3. (optional) make gallery
4. (optional) make refmanual
5. make html
6. make fix-links
7. pushd _build/html && python -m http.server


Contents
========

Config
------

shared_conf.py
______________


Commands
--------

make clean
make ...


Code
----

fix_links.py
____________

something


gallery.py
__________

something


thumbnailer.py
______________


nbbuild.py
__________

something

nbpagebuild.py
______________

Generates rst containers for all notebooks in examples/


generate_modules.py
___________________

something


paramdoc.py
___________

The ioam-builder docextensions branch provides extensions for Sphinx
to document Parameterized classes and generate autodocs for the
modules and submodules in each project.
