# Example of how to change the default imagen video format via profile

import holoviews # pyflakes:ignore (API import)
import numpy     # pyflakes:ignore (API import)

ip = get_ipython()  # pyflakes:ignore (IPython namespace)
ip.extension_manager.load_extension('holoviews.ipython')
ip.run_line_magic('view', " holomap='widgets'")
