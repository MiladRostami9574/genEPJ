"""
Python package `genEPJ` provides templates for EnergyPlus using a variety of approaches (IDF templates, epJSON, eppy, OpenStudio, etc).
Templates are instantiated using a well structured approach where the impact of incremental changes to a model can be made.
Various performance metrics such as energy/peak load reduction, GHGs savings, daylight performance, and life-cycle cost (and more) are available.
An optimization and parametric framework allows for directed searches to find optimal combinations of parameters for search spaces up to 10<sup>150</sup> [cite paper].

.. include:: ./doc/documentation.md
"""

## TODO- Be smarter in how you import
#from genEPJ_pkg.generate_EPJ import *
#from genEPJ_pkg.pylib.genEPJ_lib import *
#from genEPJ_pkg.pylib.templater import *
#from genEPJ_pkg.pylib.epJSON_templater import *
#from genEPJ_pkg.Modelkit.modelkit_wrapper import *
#from genEPJ_pkg.pylib import templates_v9_0 as templ

#import os
import sys
from os.path import join

sys.path.append( join( 'genEPJ', 'pylib') )
sys.path.append('pylib')
sys.path.append('Modelkit')
#sys.path.append('EPSchematic')
#sys.path.append('templateGenerator_epJSON')

from .generate_EPJ import *
from .opti_EPJ import *
from .pylib.genEPJ_lib import *
from .pylib.templater import *
from .pylib import templates_v9_0 as templ

from .pylib.epJSON_templater import *
from .Modelkit.modelkit_wrapper import *

#name = "genEPJ"
#


#sys.path.append(os.path.dirname(os.path.realpath(__file__)))

#__all__ = [
#  'generate_EPJ',
#  'pylib.genEPJ_lib',
#  'pylib.templater',
#  'pylib.epJSON_templater'
#        ]
