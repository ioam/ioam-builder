# Example of how to change the default imagen video format via profile

import holoviews # noqa (API import)
import numpy     # noqa (API import)
import warnings

import matplotlib as mpl
mpl.use('agg')

import holoviews.plotting.mpl

warnings.filterwarnings("ignore")

ip = get_ipython()  # pyflakes:ignore (IPython namespace)
ip.extension_manager.load_extension('holoviews.ipython')

from holoviews.plotting.widgets import NdWidget
NdWidget.export_json=True
NdWidget.json_load_path = '/json'
NdWidget.json_save_path = './'

holoviews.plotting.mpl.MPLPlot.fig_alpha = 0
