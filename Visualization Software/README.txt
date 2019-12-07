
###################
#File Descriptions#
###################
animator.py - The main scrip. This is where the layout and 
    interactions are done for the main window and its dialog windows.

animator_utils.py - Holds the classes for the bones, skeletons, and recordings.
    Also has some helper functions.

sensor_config.py - The script for the Sensor Configuration window. 

node_graph.py - The script for the Node Graph window. This is where the layout
    and interactions are done for the window.

base_node_graph.py - Holds the classes for the nodes. 

gl_scene_graph.py - Holds the classes for the OpenGl objects.

math_lib.py - Holds the classes for the math objects.

export_tsh.py - The script for exporting the recorded data as a tsh file.

import_tsh.py - The script for importing a tsh file.

export_bvh.py - The script for exporting the recorded data as a bvh file.

import_bvh.py - The script for importing a bvh file.

tsh_to_xml.py - The script for converting a tsh file into an xml file.

##############
#Dependencies#
##############
Python 2.7
wxPython 2.8
PyOpenGL 3.0.2
numpy 1.7.0
PIL 1.1.7
