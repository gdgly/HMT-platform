#!/usr/bin/env python2.7

""" Creates the main window for the Node Graph.
    
    Is able to save out the layout of the window as a XML file.
"""

__version__ = "2.0.2.2"


import os
_dir_path = os.getcwd()
_file_path = os.path.join(_dir_path, "demos")

import wx
import wx.lib.ogl as ogl
import base_node_graph as base_ng
import sensor_config as sc
import xml.etree.ElementTree as et
import wx.lib.scrolledpanel as scrolled

from math_lib import *


### Static Globals ###
VERSION = "YEI Node Graph %s" % (__version__)


### Classes ###
class ParseXML(object):
    
    """ An object that is used for saving and loading XML files.
        
        Attributes:
            canvas: A reference to an OGL ShapeCanvas.
            id_max: A list of IDs used in the ShapeCanvas.
            last_node: A reference to one of the base_node_graph.py objects.
            last_tag: A string to one of the base_node_graph.py object's class
                name.
    """
    def __init__(self, canvas):
        """ Initializes the ParseXML class.
            
            Args:
                canvas: A reference to an OGL ShapeCanvas.
        """
        self.canvas = canvas
        self.id_max = [0]
        self.last_node = None
        self.last_tag = None
    
    def start(self, tag, attrib):
        """ Called for each opening tag.
            
            Args:
                tag: A string.
                attrib: A dictionary of attributes that was loaded in.
        """
        if hasattr(base_ng, tag):
            self.last_node = getattr(base_ng, tag)(self.canvas, float(attrib["X"]), float(attrib["Y"]), int(attrib["ID"]))
            self.last_tag = tag
            self.id_max.append(int(attrib["ID"]))
        elif tag == "Con":
            self.last_node.previous_connections.append(attrib)
        elif self.last_tag:
            self.last_node.additional_attributes[tag] = attrib
    
    def end(self, tag):
        """ Called for each closing tag.
            
            Args:
                tag: A string.
        """
        if tag == self.last_tag:
            self.last_node.loads()
    
    def data(self, stuff):
        """ We do not need to do anything with data, but need it to work.
            
            Args:
                stuff: Anything.
        """
        pass
    
    def close(self):
        """Called when all data has been parsed."""
        for shape in self.canvas.shapes:
            shape.makeConnections()
        for shape in self.canvas.shapes:
            shape.performOperation()
        return max(self.id_max) + 1


### wxShapeCanvas ###
class NodeScriptWindow(ogl.ShapeCanvas):
    
    """ An OGL ShapeCanvas.
        
        Attributes:
            diagram: An OGL Diagram instance.
            id_counter: An integer that keeps track of the current ID to use.
            max_height: A float denoting the maximum height of the canvas.
            max_width: A float denoting the maximum width of the canvas.
            parent: A reference to a wxPython object.
            pos: A tuple with x an y coordinate position.
            shapes: A list of references to objects in the canvas.
    """
    def __init__(self, parent):
        """ Initializes the NodeScriptWindow class.
            
            Args:
                parent: A reference to another wxPython object.
        """
        ogl.ShapeCanvas.__init__(self, parent)
        self.max_width = 0
        self.max_height = 0
        self.SetScrollbars(20, 20, self.max_width / 20, self.max_height / 20)
        
        self.SetBackgroundColour("LIGHT BLUE")
        self.diagram = ogl.Diagram()
        self.SetDiagram(self.diagram)
        self.diagram.SetCanvas(self)
        self.shapes = []
        self.id_counter = 0
        self.pos = (0, 0)
        self.parent = parent
    
    def makeMenuItem(self, menu, name, function_to_call):
        compacted_name = name.replace(' ', '')
        if not hasattr(self, "menu_item" + compacted_name):
            setattr(self, "menu_item" + compacted_name, wx.NewId())
            new_id = getattr(self, "menu_item" + compacted_name)
            self.Bind(wx.EVT_MENU, function_to_call, id=new_id)
        menu_id = getattr(self, "menu_item" + compacted_name)
        menu.Append(menu_id, name)
    
    def resizeWindow(self, x, y):
        if self.max_width < x:
            self.max_width = max(self.max_width, x + 50)
            w_pos, h_pos = self.GetViewStart()
            self.SetScrollbars(20, 20, self.max_width / 20, self.max_height / 20, w_pos + 30, h_pos)
        if self.max_height < y:
            self.max_height = max(self.max_height, y + 50)
            w_pos, h_pos = self.GetViewStart()
            self.SetScrollbars(20, 20, self.max_width / 20, self.max_height / 20, w_pos, h_pos + 30)
    
    def autoGenerateNodes(self, event=None):
        if len(self.shapes):
            message = "Generation will remove current nodes!!"
            caption = "Auto Generate Nodes"
            
            if wx.MessageBox(message, caption, wx.OK | wx.CANCEL) == wx.OK:
                for i in range(len(self.shapes) - 1, -1, -1):
                    self.shapes[i].Remove()
            else:
                return
        mX = 80
        mY = 60
        for id in base_ng.global_sensor_list.keys():
            id_hex = "{0:08X}".format(id)
            tss_node = base_ng.TSSNode(self, mX, mY, self.id_counter)
            tss_node.additional_attributes["TSS_Sensor"] = {"SERIAL": id_hex}
            node_connection = {
                "DATATYPE": "Q",
                "FROMPORT": "0",
                "ID": str(self.id_counter),
                "TOPORT": "0"
            }
            tss_node.previous_connections.append(node_connection)
            virt_node = base_ng.VirtualSensorNode(self, mX + 180, mY, self.id_counter)
            virt_node.additional_attributes["NodeName"] = {"NAME": id_hex}
            virt_node.loads()
            tss_node.loads()
            tss_node.makeConnections()
            tss_node.performOperation()
            mY += 60
    
    def onContextMenu(self, event):
        # Make a menu
        menu = wx.Menu()
        self.makeMenuItem(menu, "Virtual Sensor", self.onPopupVirtualSensorNode)
        self.makeMenuItem(menu, "TSS Node", self.onPopupTSSNode)
        self.makeMenuItem(menu, "Clone Node", self.onPopupCloneNode)
        self.makeMenuItem(menu, "Constraint Node", self.onPopupConstraintNode)
        self.makeMenuItem(menu, "Invert Node", self.onPopupInvertNode)
        self.makeMenuItem(menu, "Mirror Node", self.onPopupMirrorNode)
        self.makeMenuItem(menu, "Output Node", self.onPopupOutputNode)
        self.makeMenuItem(menu, "Interpolate Node",
            self.onPopupInterpolationNode)
        
        convert_menu = wx.Menu()
        menu.AppendMenu(-1, "Convert To..", convert_menu)
        self.makeMenuItem(convert_menu, "Convert To Quaternion", self.onPopupConvert2QuaternionNode)
        self.makeMenuItem(convert_menu, "Convert To Euler", self.onPopupConvert2EulerNode)
        self.makeMenuItem(convert_menu, "Convert To Axis Angle", self.onPopupConvert2AxisAngleNode)
        self.makeMenuItem(convert_menu, "Convert To Matrix", self.onPopupConvert2MatrixNode)
        self.makeMenuItem(convert_menu, "Degree To Radian", self.onPopupDegree2RadianNode)
        self.makeMenuItem(convert_menu, "Radian To Degree", self.onPopupRadian2DegreeNode)
        
        self.makeMenuItem(menu, "Rotational Offset", self.onPopupRotationalOffsetNode)
        self.makeMenuItem(menu, "Multiply Rotation", self.onPopupMultiplyRotationNode)
        
        static_menu = wx.Menu()
        menu.AppendMenu(-1, "Static Value Node...", static_menu)
        self.makeMenuItem(static_menu, "Static Float", self.onPopupStaticFloatNode)
        self.makeMenuItem(static_menu, "Static Vector", self.onPopupStaticVectorNode)
        self.makeMenuItem(static_menu, "Static Quaternion", self.onPopupStaticQuaternionNode)
        self.makeMenuItem(static_menu, "Static Euler", self.onPopupStaticEulerNode)
        self.makeMenuItem(static_menu, "Static Axis Angle", self.onPopupStaticAxisAngleNode)
        self.makeMenuItem(static_menu, "Static Matrix", self.onPopupStaticMatrixNode)
        
        compose_menu = wx.Menu()
        menu.AppendMenu(-1, "Compose Value Node...", compose_menu)
        self.makeMenuItem(compose_menu, "Compose Quaternion", self.onPopupComposeQuaternionNode)
        self.makeMenuItem(compose_menu, "Compose Euler", self.onPopupComposeEulerNode)
        self.makeMenuItem(compose_menu, "Compose Axis Angle", self.onPopupComposeAxisAngleNode)
        self.makeMenuItem(compose_menu, "Compose Matrix", self.onPopupComposeMatrixNode)
        self.makeMenuItem(compose_menu, "Compose Vector", self.onPopupComposeVectorNode)
        
        decompose_menu = wx.Menu()
        menu.AppendMenu(-1, "Decompose Value Node...", decompose_menu)
        self.makeMenuItem(decompose_menu, "Decompose Quaternion", self.onPopupDecomposeQuaternionNode)
        self.makeMenuItem(decompose_menu, "Decompose Euler [Degrees]", self.onPopupDecomposeEulerDegreesNode)
        self.makeMenuItem(decompose_menu, "Decompose Euler [Radians]", self.onPopupDecomposeEulerRadiansNode)
        self.makeMenuItem(decompose_menu, "Decompose Axis Angle [Degrees]", self.onPopupDecomposeAxisAngleDegreesNode)
        self.makeMenuItem(decompose_menu, "Decompose Axis Angle [Radians]", self.onPopupDecomposeAxisAngleRadiansNode)
        self.makeMenuItem(decompose_menu, "Decompose Matrix", self.onPopupDecomposeMatrixNode)
        self.makeMenuItem(decompose_menu, "Decompose Vector", self.onPopupDecomposeVectorNode)
        
        scale_menu = wx.Menu()
        menu.AppendMenu(-1, "Scale Value Node...", scale_menu)
        self.makeMenuItem(scale_menu, "Scale Vector", self.onPopupScaleVectorNode)
        self.makeMenuItem(scale_menu, "Scale Float", self.onPopupScaleFloatNode)
        
        difference_menu = wx.Menu()
        menu.AppendMenu(-1, "Difference Angle...", difference_menu)
        self.makeMenuItem(difference_menu, "Difference Orientation", self.onPopupDifferanceOrientNode)
        self.makeMenuItem(difference_menu, "Difference Angle Quat", self.onPopupDifferenceAngleQuatNode)
        
        vector_menu = wx.Menu()
        menu.AppendMenu(-1, "Vector Operations...", vector_menu)
        self.makeMenuItem(vector_menu, "Dot Product", self.onPopupDotProductNode)
        self.makeMenuItem(vector_menu, "Cross Product", self.onPopupCrossProductNode)
        self.makeMenuItem(vector_menu, "Angle Between", self.onPopupAngleBetweenNode)
        self.makeMenuItem(vector_menu, "Normalize Vector", self.onPopupNormalizeVectorNode)
        self.makeMenuItem(vector_menu, "Sum Vectors", self.onPopupSumVectorNode)
        
        self.PopupMenu(menu)
        menu.Destroy()
    
    def onPopupTSSNode(self, event):
        base_ng.TSSNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupMirrorNode(self, event):
        base_ng.MirrorNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupDifferanceOrientNode(self, event):
        base_ng.DifferanceOrientNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupDifferenceAngleQuatNode(self, event):
        base_ng.DifferanceAngleQuatNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupDegree2RadianNode(self, event):
        base_ng.Degree2RadianNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupRotationalOffsetNode(self, event):
        base_ng.RotationalOffsetNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupRadian2DegreeNode(self, event):
        base_ng.Radian2DegreeNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupOutputNode(self, event):
        base_ng.OutputNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupInterpolationNode(self, event):
        base_ng.InterpolationNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupVirtualSensorNode(self, event):
        base_ng.VirtualSensorNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupStaticQuaternionNode(self, event):
        base_ng.StaticQuaternionNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupConvertToEulerNode(self, event):
        base_ng.ConvertToEulerNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupCloneNode(self, event):
        base_ng.CloneNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupInvertNode(self, event):
        base_ng.InvertNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupConvert2EulerNode(self, event):
        node = base_ng.ConvertXNode(self, self.pos[0], self.pos[1], self.id_counter)
        node.setConversion("Euler")
    
    def onPopupConvert2QuaternionNode(self, event):
        node = base_ng.ConvertXNode(self, self.pos[0], self.pos[1], self.id_counter)
        node.setConversion("Quaternion")
    
    def onPopupConvert2AxisAngleNode(self, event):
        node = base_ng.ConvertXNode(self, self.pos[0], self.pos[1], self.id_counter)
        node.setConversion("AxisAngle")
    
    def onPopupConvert2MatrixNode(self, event):
        node = base_ng.ConvertXNode(self, self.pos[0], self.pos[1], self.id_counter)
        node.setConversion("Matrix")
    
    def onPopupConstraintNode(self, event):
        base_ng.ConstraintNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupStaticFloatNode(self, event):
        base_ng.StaticFloatNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupStaticVectorNode(self, event):
        base_ng.StaticVectorNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupStaticEulerNode(self, event):
        base_ng.StaticEulerNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupStaticAxisAngleNode(self, event):
        base_ng.StaticAxisAngleNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupStaticMatrixNode(self, event):
        base_ng.StaticMatrixNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupComposeQuaternionNode(self, event):
        base_ng.ComposeXNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupComposeEulerNode(self, event):
        node = base_ng.ComposeXNode(self, self.pos[0], self.pos[1], self.id_counter)
        node.setType("Euler")
    
    def onPopupComposeAxisAngleNode(self, event):
        node = base_ng.ComposeXNode(self, self.pos[0], self.pos[1], self.id_counter)
        node.setType("AxisAngle")
    
    def onPopupComposeMatrixNode(self, event):
        node = base_ng.ComposeXNode(self, self.pos[0], self.pos[1], self.id_counter)
        node.setType("Matrix")
    
    def onPopupComposeVectorNode(self, event):
        node = base_ng.ComposeXNode(self, self.pos[0], self.pos[1],self.id_counter)
        node.setType("Vector")
    
    def onPopupDecomposeQuaternionNode(self, event):
        base_ng.DecomposeXNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupDecomposeEulerDegreesNode(self, event):
        node = base_ng.DecomposeXNode(self, self.pos[0], self.pos[1], self.id_counter)
        node.setType("Euler[Degrees]")
    
    def onPopupDecomposeEulerRadiansNode(self, event):
        node = base_ng.DecomposeXNode(self, self.pos[0], self.pos[1], self.id_counter)
        node.setType("Euler[Radians]")
    
    def onPopupDecomposeAxisAngleDegreesNode(self, event):
        node = base_ng.DecomposeXNode(self, self.pos[0], self.pos[1], self.id_counter)
        node.setType("AxisAngle[Degrees]")
    
    def onPopupDecomposeAxisAngleRadiansNode(self, event):
        node = base_ng.DecomposeXNode(self, self.pos[0], self.pos[1], self.id_counter)
        node.setType("AxisAngle[Radians]")
    
    def onPopupDecomposeMatrixNode(self, event):
        node = base_ng.DecomposeXNode(self, self.pos[0], self.pos[1], self.id_counter)
        node.setType("Matrix")
    
    def onPopupDecomposeVectorNode(self, event):
        node = base_ng.DecomposeXNode(self, self.pos[0], self.pos[1], self.id_counter)
        node.setType("Vector")
    
    def onPopupScaleVectorNode(self, event):
        node = base_ng.ScaleNode(self, self.pos[0], self.pos[1], self.id_counter)
        node.setType("Vector")
    
    def onPopupScaleFloatNode(self, event):
        base_ng.ScaleNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupDotProductNode(self, event):
        base_ng.DotProductNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupCrossProductNode(self, event):
        base_ng.CrossProductNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupAngleBetweenNode(self, event):
        base_ng.AngleBetweenNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupNormalizeVectorNode(self, event):
        base_ng.NormalizeVectorNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupMultiplyRotationNode(self, event):
        base_ng.MultiplyRotationNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    def onPopupSumVectorNode(self, event):
        base_ng.SumVectorNode(self, self.pos[0], self.pos[1], self.id_counter)
    
    ## OGL Functions
    def OnMouseEvent(self, event):
        # Hides the right click move bug on composite shapes
        if self._dragState == ogl.ContinueDraggingRight:
            self._dragState = ogl.NoDragging
            return
        ogl.ShapeCanvas.OnMouseEvent(self, event)
    
    def OnRightClick(self, x, y, keys=0, attachment=0):
        self.pos = (x, y)
        self.onContextMenu(None)


### wxScrolledPanel ###
class SidePanel(scrolled.ScrolledPanel):
    
    """ A wxPython ScrolledPanel.
        
        Attributes:
            parent: A reference to another wxPython object.
            panel_nodes: A list of tuples of 2 wxPython objects.
            sizer: A wx.BoxSizer instance.
            update_timer: A wx.Timer instance that is used to update the Panel.
    """
    def __init__(self, parent):
        """ Initializes the SidePanel class.
            
            Args:
                parent: A reference to another wxPython object.
        """
        scrolled.ScrolledPanel.__init__(self, parent, -1)
        self.panel_nodes = None
        self.parent = parent
        base_ng.global_side_panel = self # Change name later
        self.update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, base_ng.pollRefreshOutputs, self.update_timer)
        
        button_sizer = wx.BoxSizer(wx.VERTICAL)
        
        button = wx.Button(self, wx.NewId(), "Tare All Sensors", (10, 150))
        button.Bind(wx.EVT_BUTTON, base_ng.tareAll)
        button_sizer.Add(button, 0, wx.ALIGN_CENTRE | wx.RIGHT | wx.TOP, 5)
        
        button = wx.Button(self, wx.NewId(), "Generate Sensor Nodes", (10, 150))
        button.Bind(wx.EVT_BUTTON, self.parent.script_win.autoGenerateNodes)
        button_sizer.Add(button, 0, wx.ALIGN_CENTRE | wx.RIGHT | wx.TOP, 5)
        
        stream_grid = wx.GridSizer(1, 2)
        label = wx.StaticText(self, -1, "Streaming: ")
        self.status = wx.StaticText(self, wx.NewId(), "OFF")
        stream_grid.Add(label, 0, wx.ALIGN_CENTRE | wx.FIXED_MINSIZE)
        stream_grid.Add(self.status, 0, wx.ALIGN_CENTRE | wx.FIXED_MINSIZE)
        button_sizer.Add(stream_grid, 0, wx.ALIGN_CENTRE | wx.RIGHT | wx.TOP, 5)
        
        line = wx.StaticLine(self, wx.NewId(), size=(250, -1))
        button_sizer.Add(line, 0, wx.ALL, 5)
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        button_sizer.Add(self.sizer, 0)
        
        self.SetSizerAndFit(button_sizer)
        
        self.SetAutoLayout(1)
        self.SetupScrolling()
    
    def destroy(self):
        self.update_timer.Stop()
        self.Unbind(wx.EVT_TIMER)
    
    def updatePanel(self):
        """Updates the SidePanel."""
        if not self.parent.IsShown():
            return
        output_nodes = base_ng.global_output_nodes
        if self.panel_nodes is None or (len(self.panel_nodes) != len(output_nodes)):
            self.sizer.Clear(True)
            self.panel_nodes = []
            
            for out in output_nodes:
                type_str = ""
                if out.input_ports[0].data_type == "F":
                    type_str = "Float:\n"
                elif out.input_ports[0].data_type == "V":
                    type_str = "Vector 3:\n"
                elif out.input_ports[0].data_type == "A":
                    type_str = "Axis Angle:\n"
                elif out.input_ports[0].data_type == "Q":
                    type_str = "Quaternion:\n"
                elif out.input_ports[0].data_type == "E":
                    type_str = "Euler: \n"
                elif out.input_ports[0].data_type == "M":
                    type_str = "Matrix 3: \n"
                
                tmp_box = wx.BoxSizer(wx.HORIZONTAL)
                title = wx.StaticText(self, -1, "Name:")
                node_name =  wx.StaticText(self, -1, out.name)
                tmp_box.Add(title, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
                tmp_box.Add(node_name, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
                self.sizer.Add(tmp_box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
                
                tmp_box = wx.BoxSizer(wx.HORIZONTAL)
                data = out.input_ports[0].data
                label = wx.StaticText(self, -1, type_str + str(data))
                tmp_box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
                self.sizer.Add(tmp_box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
                
                self.panel_nodes.append((node_name, label))
                
                line = wx.StaticLine(self, wx.NewId(), size=(250, -1))
                self.sizer.Add(line, 0, wx.ALL, 5)
            
            self.sizer.Layout()
            self.SetupScrolling(self, True, True, 20, 20, False)
        
        else:
            for i in range(len(self.panel_nodes)):
                out = output_nodes[i]
                self.panel_nodes[i][0].SetLabel(out.name)
                type_str = ""
                if out.input_ports[0].data_type == "F":
                    type_str = "Float:\n"
                elif out.input_ports[0].data_type == "V":
                    type_str = "Vector 3:\n"
                elif out.input_ports[0].data_type == "A":
                    type_str = "Axis Angle:\n"
                elif out.input_ports[0].data_type == "Q":
                    type_str = "Quaternion:\n"
                elif out.input_ports[0].data_type == "E":
                    type_str = "Euler: \n"
                elif out.input_ports[0].data_type == "M":
                    type_str = "Matrix 3: \n"
                
                data = out.input_ports.end_list[0].data
                self.panel_nodes[i][1].SetLabel(type_str + str(data))
        
        self.SetAutoLayout(1)
    
    def disableSliders(self, event):
        if event.GetInt() == 1:
            self.slider.Enable(False)
            self.slider2.Enable(False)
            self.slider3.Enable(False)
        
        if event.GetInt() == 0:
            self.slider.Enable(True)
            self.slider2.Enable(True)
            self.slider3.Enable(True)


### wxDialog ###
class CustomAboutDialog(wx.Dialog):
    
    """A wxPython Dialog that creates a custom about dialog."""
    def __init__(self, parent, id, title, version, size=wx.DefaultSize, pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):
        """ Initializes the CustomAboutDialog class.
            
            Args:
                parent: A reference to another wxPython object.
                id: An integer used as an identifier for the object by wxPython.
                title: A string used for the title of the dialog.
                size: A tuple denoting the size of the dialog
                    (default is wx.DefaultSize)
                pos: A tuple denoting the position of the dialog
                    (default is wx.DefaultPosition)
                style: An integer used for determining a style for the dialog to
                    use (default is wx.DEFAULT_DIALOG_STYLE)
        """
        wx.Dialog.__init__(self, parent, id, title, pos, size, style)
        
        self.SetIcon(parent.GetIcon())
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create a banner for the dialog
        banner = wx.Image(os.path.join(_dir_path, "media\\YEI_Banner.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        
        # Add the bitmap banner
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(wx.StaticBitmap(self, -1, banner), 0, wx.EXPAND | wx.ALL)
        
        # Add other support text/links
        label = wx.StaticText(self, -1, version)
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        label = wx.StaticText(self, -1, "\xa9 2014 YEI Corporation")
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        page_url = wx.HyperlinkCtrl(self, -1, "YEI Technology Community Forum", "http://forum.yeitechnology.com/")
        box.Add(page_url, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        page_url = wx.HyperlinkCtrl(self, -1, "YEI Technology Home Page", "http://www.yeitechnology.com/")
        box.Add(page_url, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        page_url = wx.HyperlinkCtrl(self, -1, "3-Space Open Source License", "http://www.yeitechnology.com/yei-3-space-open-source-license")
        box.Add(page_url, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        
        btnsizer = wx.StdDialogButtonSizer()
        
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)
        btnsizer.Realize()
        
        sizer.Add(btnsizer, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.SetSizer(sizer)
        sizer.Fit(self)


### wxFrame ###
class MainWindow(wx.Frame):
    
    """ A wxPython Frame.
        
        Attributes:
            config_win: An instance of SensorConfigurationWindow.
            script_win: An instance of NodeScriptWindow.
            side_panel: An instance of SidePanel.
    """
    def __init__(self, parent=None, id=-1, title="YEI Node Graph"):
        """ Initializes the MainWindow class.
            
            Args:
                parent: A reference to another wxPython object (default is None)
                id: An integer denoting an ID for the window (default is -1)
                title: A string denoting the title of the window
                    (default is "Node Graph")
        """
        wx.Frame.__init__(self, parent, id, title, size=(800, 600), style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)
        self.SetMinSize((800, 600))
        if parent is not None:
            self.SetIcon(parent.GetIcon())
        else:
            self.SetIcon(wx.Icon(os.path.join(_dir_path, "media\\3Space_Icon.ico"), wx.BITMAP_TYPE_ICO))
        
        ogl.OGLInitialize()
        self.script_win = NodeScriptWindow(self)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.script_win, 4, wx.EXPAND)
        self.side_panel = SidePanel(self)
        self.timer_interval = None
        box.Add(self.side_panel, 0, wx.EXPAND | wx.FIXED_MINSIZE)
        self.config_win = sc.SensorConfigurationWindow(self, sc.SENS_CONF_SIZE)
        base_ng.global_config_win = self.config_win
        
        self.SetAutoLayout(True)
        self.SetSizer(box)
        self.Layout()
        
        # Binds
        if parent is None:
            self.Bind(wx.EVT_CLOSE, self.onAppClose)

        # StatusBar
        self.CreateStatusBar()

        # Filemenu
        file_menu = wx.Menu()
        
        # Filemenu - New
        menu_item = file_menu.Append(-1, "&New", "Creates a new layout for the Node Graph")
        self.Bind(wx.EVT_MENU, self.onNew, menu_item)
        
        # Filemenu - Separator
        file_menu.AppendSeparator()
        
        # Filemenu - Save
        menu_item = file_menu.Append(-1, "&Save", "Save the current layout of the Node Graph")
        self.Bind(wx.EVT_MENU, self.onSave, menu_item)
        
        # Filemenu - Load
        menu_item = file_menu.Append(-1, "&Load", "Loads a new layout from file into the Node Graph")
        self.Bind(wx.EVT_MENU, self.onLoad, menu_item)
        
        # Filemenu - Separator
        file_menu.AppendSeparator()
        
        # Filemenu - About
        menu_item = file_menu.Append(-1, "&About", "Information about this program")
        self.Bind(wx.EVT_MENU, self.onAbout, menu_item)
        
        # Filemenu - Separator
        file_menu.AppendSeparator()
        
        # Filemenu - Exit
        menu_item = file_menu.Append(-1, "E&xit", "Terminate the program")
        self.Bind(wx.EVT_MENU, self.onExit, menu_item)
        
        # 3Spacemenu
        ts_menu = wx.Menu()
        
        # 3Spacemenu - Find & Configure
        menu_item = ts_menu.Append(-1, "&Find && Configure", "Finds and configures the 3-Space Sensor devices")
        self.Bind(wx.EVT_MENU, self.onConfigureOpen, menu_item)
        
        # Menubar
        menu_bar = wx.MenuBar()
        menu_bar.Append(file_menu, "&File")
        menu_bar.Append(ts_menu, "&Device Settings")
        
        if parent is None:
            # Streammenu
            stream_menu = wx.Menu()
            
            # Streammenu - Find & Configure
            menu_item = stream_menu.AppendCheckItem(-1, "&Start Streaming", "Starts streaming data for the 3-Space Sensors")
            self.Bind(wx.EVT_MENU, self.onStream, menu_item)
            
            menu_bar.Append(stream_menu, "&Streaming Settings")
        
        self.SetMenuBar(menu_bar)
    
    def onAbout(self, event):
        about_dialog = CustomAboutDialog(self, -1, "About YEI Node Graph", VERSION, (350, 200))
        about_dialog.CenterOnScreen()
        about_dialog.ShowModal()
        about_dialog.Destroy()
    
    def onExit(self, event):
        self.Show(False)  # Close the frame.
        if self.GetParent() is None:
            self.onAppClose(event)
    
    def onSave(self, event):
        """ Saves what is currently in the NodeScriptWindow's canvas as an XML
            file.
            
            Args:
                event: A wxPython event.
        """
        if type(event) is str:
            root = et.Element("Root")
            for shape in self.script_win.shapes:
                root.append(shape.dumps())
            indent(root)
            xmlTree = et.ElementTree(root)
            xmlTree.write(event, "us-ascii", True)
        else:
            wild_card = "XML files (*.xml)|*.xml"
            fileOpen = wx.FileDialog(self, message="Save file as ...", defaultDir=_file_path,defaultFile="node_data", wildcard=wild_card, style=wx.SAVE | wx.CHANGE_DIR | wx.OVERWRITE_PROMPT)
            if fileOpen.ShowModal() == wx.ID_OK:
                path = fileOpen.GetPath()
                root = et.Element("Root")
                for shape in self.script_win.shapes:
                    root.append(shape.dumps())
                indent(root)
                xmlTree = et.ElementTree(root)
                xmlTree.write(path, "us-ascii", True)
            fileOpen.Destroy()
    
    def onLoad(self, event):
        """ Loads a previously saved XML file to the NodeScriptWindow's canvas.
            
            Args:
                event: A wxPython event.
        """
        if type(event) is str:
            try:
                data = open(event).read()
                for i in range(len(self.script_win.shapes) - 1, -1, -1):
                    self.script_win.shapes[i].Remove()
                parser = et.XMLParser(target=ParseXML(self.script_win))
                parser.feed(data)
                self.script_win.id_counter = parser.close()
            except:
                print ("Could not open file " + event + ", or file " + event + " does not exist.")
        else:
            wild_card = "XML files (*.xml)|*.xml"
            fileOpen = wx.FileDialog(self, message="Choose a *.xml file", defaultDir=_file_path, wildcard=wild_card, style=wx.OPEN | wx.CHANGE_DIR)
            if fileOpen.ShowModal() == wx.ID_OK:
                path = fileOpen.GetPath()
                for i in range(len(self.script_win.shapes) - 1, -1, -1):
                    self.script_win.shapes[i].Remove()
                parser = et.XMLParser(target=ParseXML(self.script_win))
                try:
                    data = open(path).read()
                except:
                    data = "<Root></Root>"
                parser.feed(data)
                self.script_win.id_counter = parser.close()
            fileOpen.Destroy()
    
    def onNew(self, event):
        for i in range(len(self.script_win.shapes) - 1, -1, -1):
            self.script_win.shapes[i].Remove()
    
    def onStartRecording(self):
        self.timer_interval = self.side_panel.update_timer.GetInterval()
        self.side_panel.update_timer.Stop()
        self.side_panel.Disable()
    
    def onStopRecording(self):
        self.side_panel.Enable()
        self.side_panel.update_timer.Start(self.timer_interval)
    
    def onConfigureOpen(self, event):
        """ Shows the SensorConfigurationWindow to configure the sensors.
            
             Args:
                event: A wxPython event.
        """
        if base_ng.global_poll_bool:
            base_ng.stopStream()
        
        self.config_win.counter = 0
        self.config_win.update_timer.Start()
        self.config_win.Show()
        self.config_win.SetFocus()
        if not self.config_win.IsActive():
            self.config_win.Restore()
    
    def onConfigureClose(self):
        """Closes the SensorConfigurationWindow."""
        if base_ng.global_poll_bool:
            base_ng.startStream()
    
    def onStream(self, event):
        """ Starts the streaming session for the sensors bound to a TSSNode.
            
             Args:
                event: A wxPython event.
        """
        if event.IsChecked():
            sens_list = []
            for node in base_ng.global_input_nodes:
                dev = node.getInputDevice()
                if dev is not None:
                    sens_list.append(dev)
            if base_ng.startStream(sensor_filter=sens_list):
                base_ng.pollToggle()
            else:
                id = event.GetEventObject().GetMenuBar().FindMenuItem("&Streaming Settings", "&Start Streaming")
                event.GetEventObject().GetMenuBar().Check(id, False)
        else:
            if base_ng.stopStream():
                base_ng.pollToggle()
            else:
                id = event.GetEventObject().GetMenuBar().FindMenuItem("&Streaming Settings", "&Start Streaming")
                event.GetEventObject().GetMenuBar().Check(id, True)
    
    def onAppClose(self, event):
        self.side_panel.update_timer.Stop()
        self.side_panel.destroy()
        if base_ng.global_poll_bool:
            base_ng.stopStream()
        self.Unbind(wx.EVT_TIMER)
        self.config_win.onAppClose(event)
        self.Destroy()


### Helper Functions ###
def indent(elem, level=0):
    """ A function that makes a hierarchy out of the parsed xmlTree.
        
        Args:
            elem: A reference to an object in the xmlTree.
            level: An integer indicating what level of the hierarchy is
                currently being looked at.
    """
    i = "\n" + level * "    "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "    "
        for e in elem:
            indent(e, level + 1)
            if not e.tail or not e.tail.strip():
                e.tail = i + "    "
        if not e.tail or not e.tail.strip():
            e.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


if __name__ == "__main__":
    # from multiprocessing import freeze_support
    # freeze_support()
    ## Main Code
    # Create an "Application" (initializes the WX system)
    app = wx.PySimpleApp()
    
    # Check for 3 Space Sensors and Dongles
    base_ng.initBaseScript()
    
    # Create a frame for use in our application
    frame = MainWindow()
    frame.Show()
    frame.side_panel.update_timer.Start()
    
    # Run the application's loop
    app.MainLoop()
    
    # Destroying the objects
    print "Destroying Frame"
    del frame
    print "Destroying App"
    del app
    print "Destroyed!!!"





