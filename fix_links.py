#! /usr/bin/env python
"""
Cleans up relative cross-notebook links by replacing them with .html
extension.
"""

import os
from bs4 import BeautifulSoup

BOKEH_REPLACEMENTS = {'cell.output_area.append_execute_result':
                      '//cell.output_area.append_execute_result',
                      '}(this));\n</div>': '}(this));\n</script></div>',
                      '\n(function(global) {': '<script>\n(function(global) {'}

# Fix gallery links (e.g to the element gallery)
LINK_REPLACEMENTS = {'../../examples/elements/':'../gallery/elements/',
                     '../../examples/demos/':'../gallery/demos/',
                     '../../examples/streams/':'../gallery/streams/'}

def cleanup_links(path):
    with open(path) as f:
        text = f.read()
    if 'BokehJS does not appear to have successfully loaded' in text:
        for k, v in BOKEH_REPLACEMENTS.items():
            text = text.replace(k, v)
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
