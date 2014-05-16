import os, sys, shutil, glob, re

STATIC_DIR = '_static'
MAKEFILE = 'Makefile'

def get_project_doc(project):
    # Write project specific Makefile
    src_path = os.path.abspath(os.path.join(__file__, '..'))
    dest_path = os.path.abspath(os.path.join(__file__, '..', '..'))

    makefile_path = os.path.abspath(os.path.join(src_path, MAKEFILE))
    with open(makefile_path, 'r') as makefile:
        make = makefile.read()
    make = make.replace('IOAMPROJECT_lower', project.lower())
    makefile_dest = os.path.abspath(os.path.join(dest_path, MAKEFILE))
    with open(makefile_dest, 'w') as mf:
        mf.write(make)

    static_dest = os.path.join(dest_path, '_static')
    if not os.path.isdir(static_dest): os.mkdir(static_dest)
    for sfile in glob.glob(os.path.join(src_path, STATIC_DIR, '*')):
        sfilepath, sfilename = os.path.split(sfile)
        shutil.copy(sfile, os.path.join(static_dest, sfilename))

if __name__ == "__main__":
    project = sys.argv[1]
    get_project_doc(project)
