#! /usr/bin/env python
"""
Cleans up relative cross-notebook links by replacing them with .html
extension.
"""
import os
import re
from bs4 import BeautifulSoup

import holoviews as hv
import param


BOKEH_REPLACEMENTS = {'cell.output_area.append_execute_result':
                      '//cell.output_area.append_execute_result',
                      '}(this));\n</div>': '}(this));\n</script></div>',
                      '\n(function(global) {': '<script>\n(function(global) {'}

# Fix gallery links (e.g to the element gallery)
LINK_REPLACEMENTS = {'../../examples/elements/':'../gallery/elements/',
                     '../../examples/demos/':'../gallery/demos/',
                     '../../examples/streams/':'../gallery/streams/'}


# Class names for auto-linking
excluded_names = { 'UniformNdMapping', 'NdMapping', 'MultiDimensionalMapping',
                   'Empty', 'CompositeOverlay', 'Collator', 'AdjointLayout'}
dimensioned = set(param.concrete_descendents(hv.Dimensioned).keys())

class_names = {'elements': set(param.concrete_descendents(hv.Element).keys()),
               'streams': set(param.concrete_descendents(hv.streams.Stream).keys())}
class_names['containers'] = set((dimensioned - class_names['elements']) - excluded_names)


def component_links(text, path):
    if ('user_guide' in path) or ('getting_started' in path):
        for clstype, listing in class_names.items():
            for clsname in list(listing):
                replacement_tpl = """<a href='../reference/{clstype}/bokeh/{clsname}.html'>
                <code>{clsname}</code></a>"""
                replacement = replacement_tpl.format(clstype=clstype, clsname=clsname)
                try:
                    text, count = re.subn('<code>\s*{clsname}\s*</code>*'.format(clsname=clsname),
                                          replacement, text)
                except Exception as e:
                    print(str(e))
    return text


def cleanup_links(path):
    with open(path) as f:
        text = f.read()
    if 'BokehJS does not appear to have successfully loaded' in text:
        for k, v in BOKEH_REPLACEMENTS.items():
            text = text.replace(k, v)

    text = component_links(text, path)
    soup = BeautifulSoup(text)
    for a in soup.findAll('a'):
        href = a.get('href', '')
        if '.ipynb' in href and 'http' not in href:
            for k, v in LINK_REPLACEMENTS.items():
                href = href.replace(k, v)
            a['href'] = href.replace('.ipynb', '.html')
    html = soup.prettify("utf-8")
    with open(path, 'w') as f:
        f.write(html)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('build_dir', help="Build Directory")
    args = parser.parse_args()

    for root, dirs, files in os.walk(args.build_dir):
        for file_path in files:
            if file_path.endswith(".html"):
                try:
                    soup = cleanup_links(os.path.join(root, file_path))
                except:
                    pass
