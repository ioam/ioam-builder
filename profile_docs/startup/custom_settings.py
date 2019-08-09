# Example of how to change the default imagen video format via profile

import warnings

import holoviews # noqa (API import)
import numpy     # noqa (API import)
import matplotlib as mpl
import holoviews.plotting.mpl # noqa (API import)

from panel import config
from pyviz_comms import Comm

mpl.use('agg')

warnings.filterwarnings("ignore")

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

config.embed = True
config.embed_json = True
config.embed_load_path = '/json'
config.embed_save_path = './'

holoviews.plotting.mpl.MPLPlot.fig_alpha = 0
