"""Generates ReST for the Reference Manual pages"""

import os, sys

path = sys.argv[1]

sys.path.insert(0, os.path.abspath(os.path.join("..", "..", path)))
sys.path.insert(0, os.path.abspath(os.path.join("..", "..")))

refman = "Reference_Manual"

module_template = """\
***************
__module_name__
***************

.. inheritance-diagram:: __module_name__

__submodules__

Module
======

.. automodule:: __module_name__
   :members:
   :show-inheritance:
"""

submodule_heading = """\
Submodules
==========
"""

def submodules(module, modules):
    ms = []
    for m in modules:
        if m != module and m[:len(module+".")] == module+".":
            ms.extend([m])
    return ms


def analyse_modules(module_path):
    modules = []
    for dirpath, dirnames, filenames in os.walk((os.path.join("..", module_path))):
        filenames = [fn[:-3] for fn in filenames if fn[-3:] == '.py' and fn[-3:] != "setup.py"]
        for filename in filenames:
            if filename == "__init__": filename = ""
            modules.extend([str.replace(os.path.join(dirpath[len("../"):], filename).rstrip("/"), "/", ".")])
    return modules

def generate_module_rst(module, submodules):
    text = str.replace(module_template, "__module_name__", module)
    sub_text = ""
    if submodules:
        sub_text = submodule_heading
        for submodule in submodules:
            sub_text += "* `%s <%s-module.html>`_\n" % (submodule, submodule)
    text = str.replace(text, "__submodules__", sub_text)
    rst_path = os.path.join(refman, module + "-module.rst")
    with open(rst_path, "w") as f:
        f.write(text)

if __name__ == "__main__":
    modules = [m for m in analyse_modules(path)]
    generate_module_rst(path, [])
    for m in modules:
        generate_module_rst(m, submodules(m, modules))
