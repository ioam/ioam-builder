#! /usr/bin/env python
import os, sys
import shutil
import subprocess
import json, glob

try:
    import cyorderedict  # noqa (Test import)
    raise Exception("Please generate tests in an environment"
                    "without cyorderedict.")
except:
    pass


class NotebookFinder(object):
    """
    Given the path to a notebook.json file, locate the notebooks
    given the supplied command-line options (projects and suites).
    """

    def __init__(self, spec_path, projects=[], suites=[]):
        spec = json.load(open(spec_path, 'r'))
        # Assuming file in doc/nbpublisher
        root = os.path.abspath(os.path.join(__file__, '..', '..', '..'))
        # Get current project name from spec
        project = [k for k in spec.keys() if k != 'links'][0]
        # If not projects specified, test current project
        projects = [project] if not projects else projects
        # Dictionary of root directories by project
        root_dirs = self.root_directories(root, spec, projects)

        # Relative to top level of each project
        self.spec = self.expand_spec(spec, root_dirs)
        self.files = self.expand_paths(self.spec, root_dirs, suites)


    def root_directories(self, root, spec, projects):
        """
        Return a dictionary of root directories for the required
        projects.
        """
        root_dirs = {}
        for project in projects:
            relpath =  spec['links'].get(project, False)
            if relpath:
                link_path = os.path.abspath(os.path.join(root, relpath))
                path = link_path
            elif project in spec:
                path = root
            elif relpath is False:
                continue

            if not os.path.isdir(path):
                raise Exception("Invalid link path: %s" % link_path)
            root_dirs[project] = path

        return root_dirs


    def expand_spec(self, spec, root_dirs, location=['doc', 'notebook.json']):
        """
        Follow the links to other notebook.json files to create an
        expanded specification dictionary with all the projects to
        test.
        """
        spec = dict((k,v) for (k,v) in spec.items() if k != 'links')
        for name, root in root_dirs.items():
            specpath = os.path.join(root,  *location)
            if (name not in spec) and not os.path.isfile(specpath):
                print("Could not find %r in %s" % (os.path.sep.join(location), root))
            elif (name not in spec):
                spec[name] = json.load(open(specpath, 'r'))[name]
        return spec


    def expand_paths(self, spec, root_dirs, suites=[]):
        """
        Using the expanded spec, find all the specified notebooks,
        filtering by the specified suites (if specified).
        """
        files = []
        for project, group in spec.items():
            selection = [s for s in suites if s in group]
            selection = selection if suites else group.keys()
            for suite in selection:
                key = (str(project), str(suite))
                group_list = []
                for relpath in group[suite]:
                    pattern = os.path.join(root_dirs[project], relpath)
                    for match in glob.glob(pattern):
                        group_list.append(str(match))
                files.append((key, group_list))
        return files



def switch_reference_branch(ref_dir, project):
    # Not yet implemented...
    pass

def run_notebook_test(notebook, project, suite, ref_dir, test_dir, regen=False):
    path, filename = os.path.split(__file__)
    test_script = os.path.abspath(os.path.join(path, 'nbtest.py'))

    notebook_name =  os.path.split(notebook)[1]
    if not notebook_name.endswith('.ipynb'):
        print("Not an IPython notebook (%s)...skipping." % notebook_name)
        return 0

    py_version =  "_py%d" % sys.version_info[0]
    ref_dir = os.path.join(ref_dir, project + '_' + notebook_name[:-6] + py_version)
    test_dir = os.path.join(test_dir, project + '_' + notebook_name[:-6] + py_version)
    if regen and os.path.isdir(ref_dir):  shutil.rmtree(ref_dir)
    ncomparisons = sum(len(glob.glob(os.path.join(ref_dir, '*.%s' % ft)))
                       for ft in ['pkl', 'html'])
    if not regen and ncomparisons == 0:
        return 0
    cmds = ['ipython', test_script, project, notebook, ref_dir, test_dir, str(regen)]
    proc = subprocess.Popen(cmds,
                            stderr=subprocess.PIPE,
                            cwd=os.path.split(notebook)[0])
    _,stderr = proc.communicate()
    print(str(stderr.decode()))
    for idx, line in enumerate(stderr.splitlines()[-10:]):
        error = 'FAILED (errors=' in str(line)
        failure = 'FAILED (failures=' in str(line)
        if error or failure:
            return 1
    return proc.returncode

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('projects', nargs='*', default=[])
    parser.add_argument('-s', '--suites', nargs='*', default=[])
    parser.add_argument('-p', '--paths', nargs='*')
    parser.add_argument('-r', '--regen', action="store_true")
    args = parser.parse_args()

    if args.paths is not None:
        assert len(args.projects) == 1
        file_list = [((args.projects[0], "custom"), args.paths)]
    else:
        file_list = NotebookFinder('../notebook.json', projects=args.projects,
                                   suites=args.suites).files

    ref_dir = os.path.abspath(os.path.join(__file__, '..', '..','reference_data'))
    test_dir = os.path.abspath(os.path.join(__file__, '..', '..','test_data'))

    if not os.path.isdir(ref_dir):
        raise Exception("No reference directory: %s" % ref_dir)
    if not os.path.isdir(test_dir):
        raise Exception("No test directory: %s" % test_dir)

    retcode = 0
    for (project, suite), paths in sorted(file_list):
        for path in paths:
            switch_reference_branch(ref_dir, project)
            retcode |= run_notebook_test(path, project, suite, ref_dir, test_dir, regen=args.regen)
    sys.exit(retcode)
