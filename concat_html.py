#! /usr/bin/env python
"""
Concatenates visual test or reference data into single
HTML files for each notebook.
"""

import glob, os

def concatenate_files(input_dir, output_dir):
    test_glob = glob.glob(os.path.join(input_dir, '*'))
    test_dirs = (path for path in test_glob if os.path.isdir(path))
    for tdir in test_dirs:
        out_path = os.path.join(output_dir, '%s.html' %
                                tdir.split('/')[-1])
        html_files = glob.glob(os.path.join(tdir, '*.html'))
        with open(out_path, 'w') as outfile:
            for fname in html_files:
                with open(fname) as infile:
                    outfile.write(infile.read())


def extant_folder(x):
    """
    'Type' for argparse - create output folder if none exists.
    """
    if not os.path.isdir(x): os.mkdir(x)
    return x


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=extant_folder,
                        help="Input folder")
    parser.add_argument('output', type=extant_folder,
                        help="Output folder")
    args = parser.parse_args()
    concatenate_files(args.input, args.output)
