"""
Auto-generates the rst files corresponding to the Notebooks in Tutorials.
"""
import os
from test_notebooks import NotebookFinder

doc_path = os.path.abspath(os.path.join(__file__, '..', '..'))
file_list = NotebookFinder(os.path.join(doc_path, 'notebook.json'),
                           projects=[], suites=[]).files


for (project, _), files in file_list:
    for f in files:
        if not f.startswith(doc_path):
            continue
        basename = os.path.basename(f)
        rst_path = f[:-len('ipynb')].replace(' ', '_') + 'rst'
        title = basename[:-6].replace('_', ' ')
        with open(rst_path, 'w') as rst_file:
            rst_file.write(title+'\n')
            rst_file.write('_'*len(title)+'\n')
            rst_file.write(".. notebook:: %s %s" % (project, basename))


