import os, sys
from nbconvert.preprocessors import Preprocessor

from holoviews.ipython.preprocessors import OptsMagicProcessor, OutputMagicProcessor
from holoviews.ipython.preprocessors import StripMagicsProcessor, wrap_cell_expression
from holoviews.util.command import main
import holoviews as hv
from holoviews import Store, Dimensioned


import matplotlib
matplotlib.use('agg')

def thumbnail(obj, basename):
    import os
    if isinstance(obj, Dimensioned) and not os.path.isfile(basename+'.png'):
        Store.renderers[Store.current_backend].save(obj, basename, fmt='png')
    return obj


class ThumbnailProcessor(Preprocessor):

    def __init__(self, basename, **kwargs):
        self.basename = basename
        super(ThumbnailProcessor, self).__init__(**kwargs)

    def preprocess_cell(self, cell, resources, index):
        if cell['cell_type'] == 'code':
            template = 'thumbnail({{expr}}, {basename!r})'
            cell['source'] = wrap_cell_expression(cell['source'],
                                                  template.format(
                                                      basename=self.basename))
        return cell, resources

    def __call__(self, nb, resources): return self.preprocess(nb,resources)


def execute(code):
    namespace = {'thumbnail':thumbnail, 'matplotlib':matplotlib}
    if sys.version_info.major==3:
        exec(code, namespace)
    else:
        exec(code) in namespace


def notebook_thumbnail(filename, subpath):
    basename = os.path.splitext(os.path.basename(filename))[0]
    dir_path = os.path.join('gallery', subpath, 'thumbnails')
    absdirpath= os.path.abspath(os.path.join('.', dir_path))
    if not os.path.exists(absdirpath):
        os.makedirs(absdirpath)

    preprocessors = [OptsMagicProcessor(),
                     OutputMagicProcessor(),
                     StripMagicsProcessor(),
                     ThumbnailProcessor(os.path.join(dir_path, basename))]
    return main(filename, preprocessors)

if __name__ == '__main__':
    files = []
    abspath = os.path.abspath(sys.argv[1])
    if os.path.isdir(abspath):
        split_path = abspath.split(os.path.sep)
        if 'examples' not in split_path:
            print('Can only thumbnail notebooks in examples/')
            sys.exit()
        subpath = os.path.sep.join(split_path[split_path.index('examples')+1:])
        files = [os.path.join(abspath, f) for f in os.listdir(abspath)
                 if f.endswith('.ipynb')]
    elif os.path.isfile(abspath):
        print('Please supply a directory to thumbnail, not a single notebook')
        sys.exit()
    else:
        print('Path {path} does not exist'.format(path=abspath))

    for f in files:
        print('Generating thumbnail for file {filename}'.format(filename=f))
        code = notebook_thumbnail(f, subpath)
        try:
            execute(code.encode('utf8'))
        except Exception as e:
            print('Failed to generate thumbnail for {filename}'.format(filename=f))
            print(str(e))
