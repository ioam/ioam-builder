#! /usr/bin/env python
"""
Cleans up relative cross-notebook links by replacing them with
.html extension. 
"""

import os
from bs4 import BeautifulSoup

BOKEH_REPLACEMENTS = {'">\n\n(function(global) {\n  function now()':
                      '">\n<script>\n(function(global) {\n  function now()',
                      'run_inline_js();\n    });\n  }\n}(this));\n</div>':
                      'run_inline_js();\n    });\n  }\n}(this));\n</script>\n</div>'}

def cleanup_links(path):
    with open(path) as f:
        text = f.read()
    if 'BokehJS successfully loaded.' in text:
        for k, v in BOKEH_REPLACEMENTS.items():
            text = text.replace(k, v)
    soup = BeautifulSoup(text)
    for a in soup.findAll('a'):
        href = a.get('href', '')
        if '.ipynb' in href and 'http' not in href:
            a['href'] = href.replace('.ipynb', '.html')
    html = soup.prettify("utf-8")
    with open(path, 'wb') as f:
        f.write(html)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('build_dir', help="Build Directory")
    args = parser.parse_args()

    for root, dirs, files in os.walk(args.build_dir):
        for file_path in files:
            if file_path.endswith(".html"):
                soup = cleanup_links(os.path.join(root, file_path))
