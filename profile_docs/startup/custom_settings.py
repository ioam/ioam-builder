# Example of how to change the default imagen video format via profile

import holoviews # pyflakes:ignore (API import)
import numpy     # pyflakes:ignore (API import)

ip = get_ipython()  # pyflakes:ignore (IPython namespace)
ip.extension_manager.load_extension('holoviews.ipython')

from holoviews.plotting.widgets import NdWidget
NdWidget.export_json=True
NdWidget.json_load_path = ''
NdWidget.json_save_path = './'

holoviews.plotting.MPLPlot.fig_alpha = 0
