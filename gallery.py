import os
import glob
import shutil
import requests
from nbpublisher.thumbnailer import notebook_thumbnail, execute

# Try Python 3 first, otherwise load from Python 2
try:
    from html import escape
except ImportError:
    from functools import partial
    from xml.sax.saxutils import escape
    escape = partial(escape, entities={'"': '&quot;'})

THUMBNAIL_URL = 'http://assets.holoviews.org'

# CONFIGURATION
gallery_conf = {
    'Gallery':   {'Demos': 'demos'},
    'Reference': {'Containers': 'containers',
                  'Elements': 'elements',
                  'Streams': {'path': 'streams', 'skip': True}}
}
backends = ['bokeh', 'matplotlib', 'plotly']

PREFIX = """
# -*- coding: utf-8 -*-
import holoviews
from holoviews.plotting.widgets import NdWidget
from holoviews.plotting.comms import Comm

try:
    import holoviews.plotting.mpl
    holoviews.Store.renderers['matplotlib'].comms['default'] = (Comm, '')
except:
    pass

try:
    import holoviews.plotting.bokeh
    holoviews.Store.renderers['bokeh'].comms['default'] = (Comm, '')
except:
    pass

NdWidget.export_json=True
NdWidget.json_load_path = '/json'
NdWidget.json_save_path = './'

holoviews.plotting.mpl.MPLPlot.fig_alpha = 0
holoviews.plotting.bokeh.callbacks.Callback._comm_type = Comm
"""

# TEMPLATES
TOC_TEMPLATE  = """
.. toctree::
    :hidden:

    /%s

"""

THUMBNAIL_TEMPLATE = """
.. raw:: html

    <div class="sphx-glr-thumbcontainer {backend}_example" tooltip="{snippet}">

.. figure:: /{thumbnail}

    :ref:`{ref_name} <{backend}_gallery_{ref_name}>`

.. raw:: html

    </div>

"""

BUTTON_GROUP_TEMPLATE = """
.. raw:: html

    <script>
    function gallery_toggle(input) {{
        backends = {backends};
        for (i in backends) {{
            entries = $('.'+backends[i]+'_example');
            if (backends[i] == input) {{
                entries.show();
            }} else {{
                entries.hide()
            }}
        }}
    }}
    </script>

    <ul class="tab">
    {buttons}
    </ul>

"""

BUTTON_TEMPLATE = """
        <li>
            <input id="tab{N}" {checked} type="radio" name="tab" onclick="gallery_toggle('{label}'.toLowerCase())" />
            <label for="tab{N}">{label}</label>
        </li>
"""

HIDE_JS = """
.. raw:: html

    <script>
        $(document).ready(function () {{
            $('.'+'{backend}'+'_example').hide();
        }});
    </script>
"""


def generate_file_rst(src_dir, backend, skip):
    files = glob.glob(os.path.join(src_dir, '*.ipynb'))
    for f in files:
        basename = os.path.basename(f)
        rst_path = f[:-len('ipynb')].replace(' ', '_') + 'rst'
        title = basename[:-6].replace('_', ' ').capitalize()
        with open(rst_path, 'w') as rst_file:
            rst_file.write('.. _%s_gallery_%s:\n\n' % (backend, basename[:-6]))
            rst_file.write(title+'\n')
            rst_file.write('_'*len(title)+'\n\n')
            rst_file.write(".. notebook:: %s %s" % ('holoviews', basename))
            if skip:
                rst_file.write('\n    :skip_execute: True\n')
            rst_file.write('\n\n-------\n\n')
            rst_file.write('`Download this notebook from GitHub (right-click to download).'
                           ' <https://raw.githubusercontent.com/ioam/holoviews/master/%s/%s>`_' % (src_dir[2:], basename))

def _thumbnail_div(full_dir, fname, snippet, backend):
    """Generates RST to place a thumbnail in a gallery"""
    thumb = os.path.join(full_dir, 'thumbnails',
                         '%s.png' % fname[:-6])

    # Inside rst files forward slash defines paths
    thumb = thumb.replace(os.sep, "/")
    template = THUMBNAIL_TEMPLATE
    return template.format(snippet=escape(snippet), backend=backend,
                           thumbnail=thumb[2:], ref_name=fname[:-6])



def generate_gallery(basepath, title, folders):
    """
    Generates a gallery for all example directories specified in
    the gallery_conf. Generates rst files for all found notebooks
    and copies the notebooks to doc/gallery/ relative to the supplied
    basepath. Also generates thumbnails and an overall index.
    """

    gallery_rst = title + '\n' + '_'*len(title)
    buttons = []
    for n, backend in enumerate(backends):
        buttons.append(BUTTON_TEMPLATE.format(N=n+1, checked='' if n else 'checked="checked"',
                                              label=backend.capitalize()))

    gallery_rst += BUTTON_GROUP_TEMPLATE.format(buttons=''.join(buttons), backends=backends)

    page = title.lower()
    for heading, folder in sorted(folders.items()):
        if isinstance(folder, dict):
            skip = folder.get('skip', False)
            folder = folder['path']
        else:
            skip = False
        gallery_rst += heading + '\n' + '='*len(heading) + '\n\n'
        asset_dir = os.path.join(basepath, 'examples', page, folder, 'assets')
        asset_dest = os.path.join('.', page, folder, 'assets')
        if os.path.isdir(asset_dir) and not os.path.isdir(asset_dest):
            shutil.copytree(asset_dir, asset_dest)
        for backend in backends:
            path = os.path.join(basepath, 'examples', page, folder, backend)
            dest_dir = os.path.join('.', page, folder, backend)
            try:
                os.makedirs(dest_dir)
            except:
                pass
            notebooks = glob.glob(path+'/*.ipynb')
            if notebooks:
                print("\n\nGenerating %d %s %s examples for %s backend\n"
                      "__________________________________________________"
                      % (len(notebooks), heading, title, backend))
            for f in notebooks:
                # Get ipynb file and copy it to doc
                basename = os.path.basename(f)
                title = basename[:-6].replace('_', ' ').capitalize()
                dest = os.path.join(dest_dir, os.path.basename(f))

                shutil.copyfile(f, dest)
                # Try to fetch thumbnail otherwise regenerate it
                thumb_url = '/'.join([THUMBNAIL_URL, 'thumbnails', page, folder,
                                      backend, '%s.png' % basename[:-6]])
                thumb = os.path.join(dest_dir, 'thumbnails',
                                     '%s.png' % basename[:-6])
                thumb_req = requests.get(thumb_url)
                if os.path.isfile(thumb):
                    verb = 'Used existing'
                    retcode = 0
                elif thumb_req.status_code == 200:
                    verb = 'Successfully downloaded'
                    thumb_dir = os.path.dirname(thumb)
                    if not os.path.isdir(thumb_dir):
                        os.makedirs(thumb_dir)
                    with open(thumb, 'wb') as thumb_f:
                        thumb_f.write(thumb_req.content)
                    retcode = 0
                else:
                    verb = 'Successfully generated'
                    code = notebook_thumbnail(f, os.path.join(page, folder, backend))
                    code = PREFIX + code
                    retcode = execute(code.encode('utf8'), cwd=os.path.split(f)[0])
                if retcode:
                    print('%s thumbnail export failed' % basename)
                    this_entry = THUMBNAIL_TEMPLATE.format(
                        snippet=escape(title), backend=backend,
                        thumbnail='../_static/images/logo.png',
                        ref_name=basename[:-6])
                else:
                    print('%s %s thumbnail' % (verb, basename))
                    this_entry = _thumbnail_div(dest_dir, basename, title, backend)
                this_entry += TOC_TEMPLATE % os.path.join(dest_dir, basename[:-6])[2:].replace(os.sep, '/')
                gallery_rst += this_entry
            generate_file_rst(dest_dir, backend, skip)
        # clear at the end of the section
        gallery_rst += """.. raw:: html\n\n
        <div style='clear:both'></div>\n\n"""
    gallery_rst += HIDE_JS.format(backend=backend)
    with open(os.path.join(basepath, 'doc', page, 'index.rst'), 'w') as f:
        f.write(gallery_rst)


if __name__ == '__main__':
    basepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    for title, folders in sorted(gallery_conf.items()):
        generate_gallery(basepath, title, folders)
