#!/usr/bin/env python2.7

"""Is a script that holds the classes used by the node_graph.py script."""


import os
import sys
_dir_path = os.getcwd()
_idx = _dir_path.rfind("\\")

import wx
import wx.lib.ogl as ogl
import wx.lib.agw.floatspin as float_spin
import random
import math
import sensor_config as sc
import xml.etree.ElementTree as et
import threading
import time
from math_lib import *
import copy
sys.path.insert(0, os.path.join(_dir_path[:_idx], "3SpaceAPI\\stable"))
import threespace_api as ts_api


### Static Globals ###
ALL_DATA_TYPES = '*'
ALL_ORIENTATIONS = '#'
CONNECTION_INPUT = 1
CONNECTION_OUTPUT = 0
# Q = Quaternion, E = Euler Angles, A = Axis Angle, M = Matrix 3
ORIENT_TYPES = ('Q', 'E', 'A', 'M')
DATA_TYPES = ('F', 'V') # F = Float, V = Vector 3
WILD_TYPES = ('#', '*') # # = All Orientation Types, * = All Types
# AXIS_DIR_MAP = {}

### Globals ###
global_poll_map = {}
global_sensor_list = sc.global_sensor_list
global_dongle_list = sc.global_dongle_list
global_output_nodes = []
global_input_nodes = []
global_static_nodes = []
global_poll_bool = False
global_manual_refresh = False
global_side_panel = None
global_config_win = None
global_stream_wait = None
global_timer_interval = None
global_sensor_filter = []


### Classes ###
### Base Classes ###
class PropertiesDialogDefault(wx.Dialog):
    
    """ The default dialoge for all nodes.
        
        Meant for inheritence for extending functionality for an individual
        node's application. Creates the boilerplate form and buttons for the
        dialogue.
    """
    def __init__(self, parent, id, title, size=wx.DefaultSize, pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE, ex_style=None):
        """ Initializes the PropertiesDialogDefault class.
            
            Args:
                parent: A reference to an object.
                id: An integer used as an identifier for the object by wxPython.
                title: A string denoting the title of the window.
                size: A tuple that stores a width and height for the window.
                pos: A tuple with x an y coordinate position for the window.
                style: An integer denoting the style of the window.
                ex_style: An integer denoting an extra style for the window.
        """
        if ex_style is None:
            wx.Dialog.__init__(self, parent.GetCanvas().GetParent(), id, title, pos, size, style)
        else:
            # Instead of calling wx.Dialog.__init__ we precreate the dialog so we
            # can set an extra style that must be set before creation, and then we
            # create the GUI object using the Create method.
            pre = wx.PreDialog()
            pre.SetExtraStyle(ex_style)
            pre.Create(parent.GetCanvas().GetParent(), id, title, pos, size, style)
            # This next step is the most important, it turns this Python object into
            # the real wrapper of the dialog (instead of pre) as far as the wxPython
            # extension is concerned.
            self.PostCreate(pre)
        
        self.SetIcon(parent.GetCanvas().GetParent().GetIcon())
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.addProperties(sizer, parent)
        line = wx.StaticLine(self, wx.NewId())
        sizer.Add(line, 0, wx.EXPAND, 5)
        
        btn_sizer = wx.StdDialogButtonSizer()
        
        btn = wx.Button(self, wx.ID_OK)
        btn_sizer.AddButton(btn)
        
        btn = wx.Button(self, wx.ID_CANCEL)
        btn_sizer.AddButton(btn)
        btn_sizer.Realize()
        
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        
        self.SetSizer(sizer)
        sizer.Fit(self)
    
    # Overwritten for adding options and features to child classes.
    def addProperties(self, sizer, parent):
        label = wx.StaticText(self, -1, "This has no Properties")
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)


class Node(ogl.CompositeShape):
    
    """ A base class that creates the OGL node.
        
        Handles boilerplate intitialization, and sets up event handling
        behavior.
        Meant for inheritence to create custom functionality for an individual
        node.
        
        Attributes:
            additional_attributes: A dictionary of attributes.
            id: An integer denoting an ID for the object.
            input_ports: A list of Node objects.
            label: An instance of OGL RectangleShape for the label of the Node.
            main_window: A reference to the MainWindow object created in the
                node_graph.py.
            node_selected: A boolean that indicates whether the object has been
                selected.
            node_shape: An instance of OGL RectangleShape for the body of the
                Node.
            output_ports: A list of Node objects.
            pos: A tuple with x an y coordinate position for the object.
            previous_connections: A list of nodes.
            select: A reference to an object being selected.
    """
    def __init__(self, canvas, x, y, id, refresh=True):
        """ Initializes the Node class.
            
            Args:
                canvas: A reference to a OGL ShapeCanvas.
                x: A float denoting the x position of the object.
                y: A float denoting the y position of the object.
                id: An integer denoting the ID of the object.
                refresh: A boolean indicating whether or not to refresh the
                    canvas.
        """
        ogl.CompositeShape.__init__(self)
        self.id = id
        self.node_selected = False
        self.SetCanvas(canvas)
        self.main_window = canvas.parent.GetParent()
        self.pos = (0, 0)
        self.select = None
        self.previous_connections = []
        self.additional_attributes = {}
        
        self.node_shape = ogl.RectangleShape(80, 20)
        self.node_shape.SetCornerRadius(-0.2)
        self.node_shape.SetDraggable(False, True)
        self.node_shape.SetShadowMode(ogl.SHADOW_RIGHT)
        # If we don't do this the shape will take all left-clicks for itself
        self.node_shape.SetSensitivityFilter(0)
        self.label = ogl.RectangleShape(100, 23)
        self.label.SetCornerRadius(-0.2)
        self.label.SetDraggable(False, True)
        self.input_ports = None
        self.output_ports = None
        self.setupNode()
        self.AddChild(self.node_shape)
        self.AddChild(self.label)
        self.AddConstraint(ogl.Constraint(ogl.CONSTRAINT_ABOVE, self.node_shape, [self.label]))
        
        if self.input_ports:
            self.input_ports.SetDraggable(False, True)
            self.AddChild(self.input_ports)
            if self.input_ports.GetWidth() > 20:
                self.node_shape.SetWidth(self.node_shape.GetWidth() + 20)
            self.AddConstraint(ogl.Constraint(ogl.CONSTRAINT_ALIGNED_LEFT, self.node_shape, [self.input_ports]))
            if self.node_shape.GetHeight() < self.input_ports.GetHeight():
                self.node_shape.SetHeight(self.input_ports.GetHeight() + 3)
        if self.output_ports:
            self.output_ports.SetDraggable(False, True)
            self.AddChild(self.output_ports)
            if self.output_ports.GetWidth() > 20:
                self.node_shape.SetWidth(self.node_shape.GetWidth() + 20)
            self.AddConstraint(ogl.Constraint(ogl.CONSTRAINT_ALIGNED_RIGHT, self.node_shape, [self.output_ports]))
            if self.node_shape.GetHeight() < self.output_ports.GetHeight():
                self.node_shape.SetHeight(self.output_ports.GetHeight() + 3)
        self.Recompute()
        
        dc = wx.ClientDC(canvas)
        canvas.PrepareDC(dc)
        self.Move(dc, x, y)
        self.SetX(x)
        self.SetY(y)
        canvas.diagram.AddShape(self)
        self.Show(True)
        canvas.shapes.append(self)
        canvas.id_counter += 1
        canvas.resizeWindow(x, y)
        if refresh:
             canvas.Refresh(False)
    
    def __repr__(self):
        return "%s: %s" % (type(self), self.label.GetRegions()[0].GetFormattedText()[0].GetText())
    
    def __str__(self):
        return self.__repr__()
    
    def dumps(self):
        """ Creates an XML Element and passes it's information on to it.
            
            Is used when saving an XML file.
        """
        pos = {"X": str(self.GetX()), "Y": str(self.GetY()), "ID": str(self.id)}
        node_xml = et.Element(self.__class__.__name__, pos)
        if self.output_ports:
            input_xml = et.Element("ConnectedTo")
            node_xml.append(input_xml)
            for i in range(len(self.output_ports)):
                con = self.output_ports[i].connection
                if con is not None:
                    connection_dic = {
                        "ID": str(con.node.id),
                        "TOPORT": str(con.node.input_ports.end_list.index(con)),
                        "FROMPORT": str(i),
                        "DATATYPE": str(self.output_ports[i].data_type)
                    }
                    con_xml = et.Element("Con", connection_dic)
                    input_xml.append(con_xml)
        return node_xml
    
    def makeConnections(self):
        for con in self.previous_connections:
            out_node_port = self.output_ports[int(con["FROMPORT"])]
            out_node_port.data_type = con["DATATYPE"]
            in_node = None
            for shape in self.GetCanvas().shapes:
                if shape.id == int(con["ID"]):
                    in_node = shape
            if not in_node:
                continue
            in_node_port = in_node.input_ports[int(con["TOPORT"])]
            out_node_port.connectNodes(in_node_port)
    
    def loads(self):
        """Takes information from parsed XML file and stores it as own data."""
        pass
    
    def setupNode(self):
        """Set the label, color, and size of the node."""
        self.node_shape.SetBrush(wx.CYAN_BRUSH)
        self.label.AddText("A Node!!!!")
        canvas = self.GetCanvas()
        labels = ["F", "F"]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        labels = ["F"]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.output_ports.SetDraggable(False, True)
    
    def getInputDevice(self, check_connect=True, do_remove=False):
        if self in global_input_nodes:
            if self.device is not None and check_connect:
                if not self.device.isConnected():
                    if ("WL" in self.device.device_type and not self.device.wireless_com):
                        if self.device.switchToWirelessMode():
                            serial_hex = self.device.serial_number_hex
                            print "Lost connection to wired sensor, reverting to wireless"
                            print "Switched "+ serial_hex + " to wireless"
                            if not self.device.isConnected():
                                if do_remove:
                                    self.device = None
                        else:
                            if do_remove:
                                self.device = None
                    else:
                        if do_remove:
                            self.device = None
            return self.device
        
        if self.input_ports is None:
            return None
        if len(self.input_ports) > 1:
            return None
        if len(self.input_ports) and self.input_ports[0].connection:
            return self.input_ports[0].connection.node.getInputDevice(check_connect, do_remove)
        return None
    
    def getInputDeviceNode(self):
        if self.input_ports[0].connection:
            node_type = type(self.input_ports[0].connection.node)
            if node_type is TSSNode:
                return self.input_ports[0].connection.node
        
        if self.input_ports is None:
            return None
        if len(self.input_ports) > 1:
            return None
        if len(self.input_ports) and self.input_ports[0].connection:
            return self.input_ports[0].connection.node.getInputDeviceNode()
        return None
    
    def setUpdateData(self):
        # Check for good input
        for port in self.input_ports:
            if port.data is None:
                return False
            elif port.connection is None:
                # Set all outgoing Node's data to None and return
                for out_port in self.output_ports:
                    if out_port.connection is not None:
                        out_port.connection.data = None
                return False
        # Calculate
        out_tuple = self.performCalculation()
        
        # Set outgoing datas
        for i in range(len(self.output_ports)):
            if self.output_ports[i].connection is not None:
                self.output_ports[i].connection.data = out_tuple[i]
        return True
    
    def setDataTypes(self):
        pass
    
    def performOperation(self):
        self.setDataTypes()
        clear_stale = self.setUpdateData()
        
        if len(self.output_ports) == 1:
            port = self.output_ports[0]
            if port.connection is not None:
                port.connection.node.performOperation()
        else:
            prev_nodes = []
            for port in self.output_ports:
                if (port.connection is not None and
                        port.connection.node not in prev_nodes):
                    port.connection.node.performOperation()
                    prev_nodes.append(port.connection.node)
        if clear_stale:
            for port in self.input_ports:
                port.data = None
    
    def performCalculation(self):
        return [["Fail"]]
    
    def whatDidIHit(self, x, y):
        """ Function used to determined if the object has been selected by the
            mouse.
            
            Args:
                x: The mouse's x position.
                y: The mouse's y position.
            
            Returns:
                A reference to the object that was selected.
        """
        self.select = None
        for shape in self.GetChildren():
            hit = shape.HitTest(x, y)
            if hit:
                if type(shape) is NodeConnections:
                    obj = shape.whatDidIHit(x, y)
                    if obj is not None:
                        self.select = obj
                else:
                    pass
        return self.select
    
    def loopDetection(self, other_object):
        """ Detects if a loop is going to occur when connecting Node objects.
            
            Args:
                other_object: Another Node instance.
            
            Returns:
                A boolean indicating whether or not a loop was detected.
        """
        if self.input_ports:
            for c in self.input_ports.end_list:
                if c.connection:
                    if c.connection.node is other_object:
                        ################LOOP DETECTED################
                        return True
                    if c.connection.node.loopDetection(other_object):
                        return True
        return False
    
    def onContextMenu(self, event):
        canvas = self.GetCanvas()
        if not hasattr(self, "popup_id1"):
            self.popup_id1 = wx.NewId()
            self.popup_id2 = wx.NewId()
            self.popup_id3 = wx.NewId()
            
            canvas.Bind(wx.EVT_MENU, self.stopTimeForPopUp, id=self.popup_id1)
            canvas.Bind(wx.EVT_MENU, self.onPopupDelNode, id=self.popup_id2)
            canvas.Bind(wx.EVT_MENU, self.onPopupDisconnectNodes,
                id=self.popup_id3)
        # Make a menu
        menu = wx.Menu()
        # Add some other items
        menu.Append(self.popup_id1, "Properties")
        menu.Append(self.popup_id2, "Delete Node")
        if self.whatDidIHit(self.pos[0], self.pos[1]) and self.select.connection is not None:
            menu.Append(self.popup_id3, "Disconnect")
        canvas.PopupMenu(menu)
        menu.Destroy()
    
    def stopTimeForPopUp(self, event):
        if self.main_window is not None:
            main_timer_interval = self.main_window.update_timer.GetInterval()
            self.main_window.update_timer.Stop()
        if global_config_win.IsShown():
            global_config_win.onClose(None)
        side_timer_interval = global_side_panel.update_timer.GetInterval()
        global_side_panel.update_timer.Stop()
        self.onPopupProperties(event)
        if self.main_window is not None:
            self.main_window.update_timer.Start(main_timer_interval)
        global_side_panel.update_timer.Start(side_timer_interval)
    
    def onPopupProperties(self, event):
        dlg = PropertiesDialogDefault(self, -1, "Properties", size=(350, 200), style=wx.DEFAULT_DIALOG_STYLE)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()  # This does not return until the dialog is closed
        if val == wx.ID_OK:
            pass
        dlg.Destroy()
    
    def onPopupDelNode(self, event):
        self.Remove()
    
    def onPopupDisconnectNodes(self, event):
        self.select.disconnectNodes()
        self.GetCanvas().Refresh(False)
    
    ## OGL Functions
    def OnLeftClick(self, x, y, keys=0, attachment=0):
        self.node_selected = self.whatDidIHit(x, y)
        if self.node_selected:
            self.GetCanvas().Refresh(False)
        ogl.CompositeShape.OnLeftClick(self, x, y, keys, attachment)
    
    def OnBeginDragLeft(self, x, y, keys=0, attachment=0):
        shape = self.GetShape()
        self.node_selected = shape.whatDidIHit(x ,y)
        if self.node_selected:
            canvas = shape.GetCanvas()
            canvas.Refresh(False)
            return
        ogl.CompositeShape.OnBeginDragLeft(self, x, y, keys, attachment)
    
    def OnDragLeft(self, draw, x, y, keys=0, attachment=0):
        if self.node_selected:
            dc = wx.ClientDC(self.GetCanvas())
            self.GetCanvas().PrepareDC(dc)
            dc.SetLogicalFunction(ogl.OGLRBLF)
            points = ((self.node_selected.node_shape.GetX(), self.node_selected.node_shape.GetY()), (x, y))
            dc.DrawLines(points)
            
            return
        ogl.CompositeShape.OnDragLeft(self, draw, x, y, keys, attachment)
    
    def OnEndDragLeft(self, x, y, keys=0, attachment=0):
        node_list = self.GetCanvas().shapes
        new_end = None
        for node in node_list:
            an_end = node.whatDidIHit(x, y)
            if an_end is not None:
                new_end = an_end
        if self.node_selected:
            canvas = self.GetCanvas()
            if new_end and self.node_selected.isConnectionValid(new_end):
                self.node_selected.connectNodes(new_end)
                self.node_selected.initalUpdateNodes()
            canvas.Refresh(False)
            return
        if x < 50:
            x = 50
        if y < 50:
            y = 50
        
        self.GetCanvas().resizeWindow(x, y)
        ogl.CompositeShape.OnEndDragLeft(self, x, y, keys, attachment)
    
    def Remove(self):
        canvas = self.GetCanvas()
        if hasattr(self, "popup_id1"):
            canvas.Unbind(wx.EVT_MENU, handler=self.stopTimeForPopUp, id=self.popup_id1)
            canvas.Unbind(wx.EVT_MENU, handler=self.onPopupDelNode, id=self.popup_id2)
            canvas.Unbind(wx.EVT_MENU, handler=self.onPopupDisconnectNodes, id=self.popup_id3)
        canvas.shapes.remove(self)
        canvas.diagram.RemoveShape(self)
        self.Detach()
        self.Delete()
        canvas.Refresh(False)
    
    def OnRightClick(self, x, y, keys=0, attachment=0):
        self.pos = (x, y)
        self.onContextMenu(None)
    
    def Delete(self):
        while len(self.GetChildren()):
            child = self.GetChildren()[-1]
            self.RemoveChild(child)
            child.Delete()
        ogl.RectangleShape.Delete(self)
        self._constraints = []
        self._divisions = []


### Connection Utility Classes ###
class NodeConnections(ogl.CompositeShape):
    
    """ A container for the input/output connections for a given Node object.
        
        Attributes:
            end_list = A list of Connection objects.
            node_shape: An instance of OGL RectangleShape.
            parent: A reference to a Node object.
    """
    def __init__(self, canvas, node_list, parent, connection_type):
        """ Initializes the NodeConnections class.
            
            Args:
                canvas: A reference to a OGL ShapeCanvas.
                node_list: A list of names object is connected to.
                parent: A reference to a Node object.
                connection_type: An integer indicating if input/output.
        """
        ogl.CompositeShape.__init__(self)
        self.SetCanvas(canvas)
        self.parent = parent
        self.node_shape = ogl.RectangleShape(1, 1)
        self.node_shape.SetDraggable(False, True)
        self.node_shape.SetSensitivityFilter(0)
        self.AddChild(self.node_shape)
        self.end_list = []
        
        for node_name in node_list:
            new_node = None
            if type(node_name) is str:
                new_node = Connection(canvas, connection_type, node_name, self)
            else:
                new_node = Connection(canvas, connection_type, node_name[0], self, node_name[1])
            self.end_list.append(new_node)
            new_node.SetDraggable(False, True)
            self.AddChild(new_node)
        
        constraint = ogl.Constraint(ogl.CONSTRAINT_CENTRED_VERTICALLY, self.node_shape, self.end_list)
        self.AddConstraint(constraint)
        self.Recompute()
    
    def __getitem__(self, key):
        return self.end_list[key]
    
    def __iter__(self):
        return self.end_list.__iter__()
    
    def __len__(self):
        return len(self.end_list)
    
    def index(self, obj):
        return self.end_list.index(obj)
    
    def whatDidIHit(self, x, y):
        """ Function used to determined if the object has been selected by the
            mouse.
            
            Args:
                x: The mouse's x position.
                y: The mouse's y position.
            
            Returns:
                A reference to the object that was selected or None
        """
        hits = []
        for shape in self.GetChildren():
            hit = shape.HitTest(x, y)
            if hit:
                hits.append(shape)
        if len(hits) > 0:
            return hits[-1].whatDidIHit(x, y)
        return None
    
    ## OGL Functions
    def OnRightClick(self, x, y, keys=0, attachment=0):
        self.node.OnRightClick(x, y, keys, attachment)
    
    def Delete(self):
        while len(self.GetChildren()):
            child = self.GetChildren()[-1]
            self.RemoveChild(child)
            child.Delete()
        ogl.RectangleShape.Delete(self)
        self._constraints = []
        self._divisions = []


class Connection(ogl.CompositeShape):
    
    """ A single connection between two nodes.
        
        A connection manages whether the attempted link between two nodes is
        valid or not. A connection will also continue the chain of execution for
        the linked nodes if the link is valid.
        
        Attributes:
            connection: A reference to another Node object.
            connection_type: An integer indicating if input/output.
            data: A reference to one of the math_lib.py classes or None.
            data_type: A string indicating the type of connection.
            description: A string describing the connection.
            description_label: An instance of a OGL TextShape.
            label: An instance of a OGL TextShape.
            node: A reference to a Node object.
            node_shape: An instance of a OGL CircleShape.
            parent: A reference to a NodeConnections object.
    """
    def __init__(self, canvas, connection_type, data_type, parent, description=""):
        """ Initializes the Connection class.
            
            Args:
                canvas: A reference to a OGL ShapeCanvas.
                connection_type: An integer indicating if input/output.
                data_type: A string indicating the type of connection.
                parent: A reference to a NodeConnections object.
                description: A string describing the connection (default is "")
        """
        ogl.CompositeShape.__init__(self)
        self.SetCanvas(canvas)
        self.parent = parent
        self.node = parent.parent
        self.description = description
        self.connection_type = connection_type
        self.connection = None
        self.data_type = data_type
        self.data = None
        self.timestamp = -1
        self.SetDraggable(False, True)
        
        self.node_shape = ogl.CircleShape(20)
        self.node_shape.SetDraggable(False, True)
        self.node_shape._draggable = False
        # If we don't do this the shape will take all left-clicks for itself
        self.node_shape.SetSensitivityFilter(0)
        self.node_shape.SetBrush(wx.GREEN_BRUSH)
        self.label = ogl.TextShape(18, 24)
        self.label.SetFont(wx.Font(9, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD))
        self.label.SetDraggable(False, True)
        self.label.AddText(data_type)
        self.label.SetSensitivityFilter(0)
        
        size = 0
        if description:
            size = len(self.description) * 9 + 5
        self.description_label = ogl.TextShape(size, 24)
        self.description_label.SetSensitivityFilter(0)
        self.description_label.SetFont(wx.Font(9, wx.FONTFAMILY_MODERN, wx.NORMAL, wx.FONTWEIGHT_BOLD))
        self.description_label.SetDraggable(False, True)
        self.description_label.AddText(self.description)
        self.AddConstraint(ogl.Constraint(ogl.CONSTRAINT_CENTRED_BOTH, self.node_shape, [self.label]))
        
        self.AddChild(self.node_shape)
        self.AddChild(self.label)
        self.AddChild(self.description_label)
        if connection_type == CONNECTION_INPUT:
            self.AddConstraint(ogl.Constraint(ogl.CONSTRAINT_RIGHT_OF, self.node_shape, [self.description_label]))
        else:
            self.AddConstraint(ogl.Constraint(ogl.CONSTRAINT_LEFT_OF, self.node_shape, [self.description_label]))
    
    def updateText(self):
        self.label.ClearText()
        self.label.AddText(self.data_type)
    
    def isConnectionValid(self, other_connection):
        # Checks thats an output goes to an input and an input goes to an out
        if self.connection_type == other_connection.connection_type:
            return False
        
        # Checks if connects are on same node
        if self.node == other_connection.node:
            return False
        
        if self.connection is not None or other_connection.connection is not None:
            return False
        
        if self.data_type != other_connection.data_type and not (self.data_type in WILD_TYPES or other_connection.data_type in WILD_TYPES):
            return False
        
        if (self.data_type in WILD_TYPES and self.connection_type is CONNECTION_OUTPUT) or (other_connection.data_type in WILD_TYPES and other_connection.connection_type is CONNECTION_OUTPUT):
            return False
        elif (self.data_type == '#' or other_connection.data_type == '#') and not ((self.data_type == '#' and other_connection.data_type in ORIENT_TYPES) or (other_connection.data_type == '#' and self.data_type in ORIENT_TYPES)):
            return False
        
        if self.connection_type is CONNECTION_OUTPUT:
            if self.node.loopDetection(other_connection.node):
                return False
        else:
            if other_connection.node.loopDetection(self.node):
                return False
        return True
    
    def connectNodes(self, other_connection):
        self.connection = other_connection
        self.node_shape.SetBrush(wx.RED_BRUSH)
        other_connection.connection = self
        other_connection.node_shape.SetBrush(wx.RED_BRUSH)
        line = ogl.LineShape()
        line.SetCanvas(self)
        line.SetPen(wx.Pen(wx.RED, 1))
        line.SetBrush(wx.BLACK_BRUSH)
        line.AddArrow(ogl.ARROW_ARROW, 1, 15)
        line.MakeControlPoints()
        line.MakeLineControlPoints(2)
        line.Initialise()
        
        if self.connection_type == CONNECTION_OUTPUT:
            self.node_shape.AddLine(line, other_connection.node_shape)
        else:
            other_connection.node_shape.AddLine(line, self.node_shape)
        
        self.GetCanvas().diagram.AddShape(line)
        line.Show(True)
    
    def initalUpdateNodes(self):
        if self.connection_type == CONNECTION_OUTPUT:
            self.node.performOperation()
        else:
            self.connection.node.performOperation()
    
    def disconnectNodes(self):
        if self.connection is not None:
            self.node_shape.GetLines()[-1].Delete()
            self.connection.node_shape.SetBrush(wx.GREEN_BRUSH)
            
            if self.connection.connection_type == CONNECTION_INPUT:
                self.connection.data = None
                self.connection.timestamp = None
                self.connection.node.performOperation()
            else:
                self.connection.connection.data = None
                self.connection.connection.timestamp = None
            
            tmp_con = self.connection.connection.node
            self.connection.connection = None
            tmp_con2 = self.connection.node
            self.connection = None
            tmp_con2.setDataTypes()
            
            if tmp_con.GetCanvas():
                tmp_con.setDataTypes()
        self.node_shape.SetBrush(wx.GREEN_BRUSH)
        if self.connection_type == CONNECTION_INPUT:
            self.data = None
            self.timestamp = -1
    
    def whatDidIHit(self, x, y):
        """ Function used to determined if the object has been selected by the
            mouse.
            
            Args:
                x: The mouse's x position.
                y: The mouse's y position.
            
            Returns:
                A reference to self or None
        """
        if self.node_shape.HitTest(x, y):
            return self
        return None
    
    ## OGL Functions
    def Delete(self):
        while len(self.GetChildren()):
            child = self.GetChildren()[-1]
            self.RemoveChild(child)
            child.Delete()
        while len(self.node_shape.GetLines()):
            self.disconnectNodes()
        ogl.CompositeShape.Delete(self)
        self._constraints = []
        self._divisions = []
    
    # Should never be called but are OGL dependent
    def OnBeginDragLeft(self, x, y, keys=0, attachment=0):
        self.node.OnBeginDragLeft(x, y, keys, attachment)
    
    def OnDragLeft(self, draw, x, y, keys=0, attachment=0):
        self.node.OnDragLeft(draw, x, y, keys, attachment)
    
    def OnEndDragLeft(self, x, y, keys=0, attachment=0):
        self.node.OnEndDragLeft(x, y, keys, attachment)
    
    def OnRightClick(self, x, y, keys=0, attachment=0):
        self.node.OnRightClick(x, y, keys, attachment)


### Child Classes ###
class TSSNode(Node):
    
    """A Node object that is used for TSSensor objects."""
    global global_input_nodes
    def setupNode(self):
        self.label.AddText("TSS Input Node")
        self.node_shape.SetWidth(120)
        self.node_shape.SetBrush(wx.Brush((255, 211, 155), wx.SOLID))
        canvas = self.GetCanvas()
        labels = [("Q", "None")]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.output_ports.end_list[0].data = None
        self.output_ports.end_list[0].timestamp = -1
        self.device = None
        self.ts_axis = None
        self.orient_dir = Matrix4()
        self.orient_axis = 8
        global_input_nodes.append(self)
        self.output_ports.end_list[0].description_label.SetWidth(120)
        self.output_ports.end_list[0].description_label.SetHeight(30)
    
    def dumps(self):
        node_xml = Node.dumps(self)
        if self.device is not None:
            quat = self.device.getTareAsQuaternion()
            serial = self.device.serial_number
            serial_hex = self.device.serial_number_hex
            dev_type = self.device.device_type
            if quat is None:
                if "WL" in dev_type and not self.device.wireless_com:
                    print "Lost wired connection reverting to wireless"
                    if self.device.switchToWirelessMode():
                        print "Switched " + serial_hex + " to wireless"
                        quat = self.device.getTareAsQuaternion()
            if "WL" in dev_type and self.device.wireless_com:
                connection_dic = {"SERIAL": serial_hex}
            else:
                connection_dic = {"COMPORT": self.device.port_name, "SERIAL": serial_hex}
            con_xml = et.Element("TSS_Sensor", connection_dic)
            node_xml.append(con_xml)
            
            mat = self.orient_dir.asRowArray()
            connection_dic = {
                "R0C0": str(mat[0]),
                "R0C1": str(mat[1]),
                "R0C2": str(mat[2]),
                "R0C3": str(mat[3]),
                "R1C0": str(mat[4]),
                "R1C1": str(mat[5]),
                "R1C2": str(mat[6]),
                "R1C3": str(mat[7]),
                "R2C0": str(mat[8]),
                "R2C1": str(mat[9]),
                "R2C2": str(mat[10]),
                "R2C3": str(mat[11]),
                "R3C0": str(mat[12]),
                "R3C1": str(mat[13]),
                "R3C2": str(mat[14]),
                "R3C3": str(mat[15]),
                "AXISORIENT": str(self.orient_axis)
            }
            con_xml = et.Element("OrientPlacementData", connection_dic)
            node_xml.append(con_xml)
            
            if quat is not None:
                connection_dic = {
                    "X": str(quat[0]),
                    "Y": str(quat[1]),
                    "Z": str(quat[2]),
                    "W": str(quat[3])
                }
                con_xml = et.Element("TareData", connection_dic)
                node_xml.append(con_xml)
        
        return node_xml
    
    def loads(self):
        if "TSS_Sensor" in self.additional_attributes:
            serial_hex = self.additional_attributes["TSS_Sensor"]["SERIAL"]
            tare_quat = None
            try:
                orient_data = self.additional_attributes["OrientPlacementData"]
                self.orient_dir = Matrix4([
                    float(orient_data["R0C0"]),
                    float(orient_data["R0C1"]),
                    float(orient_data["R0C2"]),
                    float(orient_data["R0C3"]),
                    float(orient_data["R1C0"]),
                    float(orient_data["R1C1"]),
                    float(orient_data["R1C2"]),
                    float(orient_data["R1C3"]),
                    float(orient_data["R2C0"]),
                    float(orient_data["R2C1"]),
                    float(orient_data["R2C2"]),
                    float(orient_data["R2C3"]),
                    float(orient_data["R3C0"]),
                    float(orient_data["R3C1"]),
                    float(orient_data["R3C2"]),
                    float(orient_data["R3C3"])
                ])
                self.orient_axis = int(orient_data["AXISORIENT"])
            except:
                print "Sensor", serial_hex,
                print "has corrupt or missing OrientPlacementData"
            try:
                calibrate_data = self.additional_attributes["CalibrateData"]
                calibrate_quat = Quaternion([
                    float(calibrate_data["X"]),
                    float(calibrate_data["Y"]),
                    float(calibrate_data["Z"]),
                    float(calibrate_data["W"])
                ])
            except:
                print "Sensor", serial_hex,
                print "has corrupt or missing CalibrateData"
            try:
                tare_data = self.additional_attributes["TareData"]
                tare_quat = [
                    float(tare_data["X"]),
                    float(tare_data["Y"]),
                    float(tare_data["Z"]),
                    float(tare_data["W"])
                ]
            except:
                print "Sensor", serial_hex,
                print "has corrupt or missing TareData"
            
            serial = int(serial_hex, 16)
            if serial in global_sensor_list:
                self.device = global_sensor_list[serial]
            
            if self.device:
                if tare_quat is not None:
                    tare_quat_norm = Quaternion(tare_quat).normalizeCopy()
                    quat_len = tare_quat_norm.length()
                    if quat_len > 1.0001 or quat_len < 0.99998:
                        pass
                    self.device.tareWithQuaternion(tare_quat_norm.asArray())
                times = 0
                quat_data = None
                while times < 3:
                    if quat_data is None:
                        quat_data = self.device.getTaredOrientationAsQuaternion()
                    if self.ts_axis is None:
                        self.ts_axis = self.device.getAxisDirections()
                    
                    if quat_data is not None and self.ts_axis is not None:
                        quat = Quaternion(quat_data)
                        for f in sc.AXIS_DIR_MAP[self.orient_axis][self.ts_axis]:
                            f(quat)
                        self.output_ports.end_list[0].data = quat
                        times = 3
                    times += 1
                if quat_data is None:
                    print "####Quat get fail", self.device.serial_number_hex
                if self.ts_axis is None:
                    print "####Axis get fail", self.device.serial_number_hex
                self.output_ports.end_list[0].description_label.ClearText()
                sens_name = self.device.device_type + "-" + self.device.serial_number_hex
                self.output_ports.end_list[0].description_label.AddText(sens_name)
                self.GetCanvas().Refresh(False)
    
    def setUpdateData(self, data_map=None):
        if self.output_ports[0].connection is not None:
            if self.device is not None:
                serial = self.device.serial_number
                timestamp = None
                quat = None
                if data_map is None:
                    quat_data = None
                    try:
                        timestamp, quat_data = global_poll_map[serial]
                    except KeyError:
                        if self.device in global_sensor_filter:
                            hw_id = '{0:08X}'.format(serial)
                            print "Opps I got a key error on", hw_id
                            self.device = None
                            connection_node = self.output_ports.end_list[0]
                            connection_node.description_label.ClearText()
                            connection_node.description_label.AddText("None")
                            self.GetCanvas().Refresh(False)
                    except:
                        # There is no data
                        pass
                    if quat_data is not None:
                        quat = Quaternion(quat_data)
                    
                else:
                    try:
                        timestamp, quat = data_map[serial].pop(0)
                    except:
                        pass
                
                if quat is not None:
                    for f in sc.AXIS_DIR_MAP[self.orient_axis][self.ts_axis]:
                        f(quat)
                    self.output_ports.end_list[0].data = quat
                    self.output_ports.end_list[0].timestamp = timestamp
                else:
                    self.output_ports[0].data = None
                    self.output_ports.end_list[0].data = None
                    self.output_ports.end_list[0].timestamp = -1
            
            ## NEED TO CHECK IF CODE IS CORRECT ##
            connection_node = self.output_ports[0].connection
            node_connection = connection_node.node
            if type(node_connection) is CloneNode:
                for ports in node_connection.output_ports:
                    if ports.connection is None:
                        continue
                    ports.connection.data = self.output_ports[0].data
                    ports.connection.timestamp = self.output_ports[0].timestamp
            else:
                connection_node.data = self.output_ports[0].data
                connection_node.timestamp = self.output_ports[0].timestamp
    
    def performOperation(self, data_map=None):
        self.setUpdateData(data_map)
        if self.output_ports[0].connection is not None:
            self.output_ports[0].connection.node.performOperation()
    
    def onSensorConfigureApply(self):
        self.orient_axis = global_config_win.orient_panel.orient_axis
        self.orient_dir = global_config_win.orient_panel.orient_dir.copy()
    
    def calibrateInputNode(self):
        success = True
        got_data = False
        times = 0
        gravity = None
        tared_data = None
        hex_num = self.device.serial_number_hex
        while not got_data:
            if gravity is None:
                gravity = [0] * 3
                count = 0
                for i in range(5):
                    accel_vec = self.device.getCorrectedAccelerometerVector()
                    if accel_vec is not None:
                        gravity[0] -= accel_vec[0]
                        gravity[1] -= accel_vec[1]
                        gravity[2] -= accel_vec[2]
                        count += 1
                if count < 3:
                    gravity = None
                else:
                    gravity[0] /= count
                    gravity[1] /= count
                    gravity[2] /= count
            times += 1
            if gravity is not None:
                got_data = True
                gravity_vec = Vector3(gravity)
                gravity_vec.normalize()
                true_gravity = Vector3()
                
                # Compensate the true gravity vector for different axis
                # directions and orientation of sensor
                mesh_axis_dir_list = sc.ts_api.parseAxisDirections(self.orient_axis)
                sens_axis_dir_list = sc.ts_api.parseAxisDirections(self.ts_axis)
                
                mesh_axis = mesh_axis_dir_list[0]
                y_mesh = mesh_axis_dir_list[2]
                sens_axis, x_sens, y_sens, z_sens = sens_axis_dir_list
                y_idx_mesh = mesh_axis.find("Y")
                
                if sens_axis[y_idx_mesh] == "X":
                    true_gravity.x = -1.0
                    if y_mesh != x_sens:
                        true_gravity.x *= -1.0
                if sens_axis[y_idx_mesh] == "Y":
                    true_gravity.y = -1.0
                    if y_mesh != y_sens:
                        true_gravity.y *= -1.0
                if sens_axis[y_idx_mesh] == "Z":
                    true_gravity.z = -1.0
                    if y_mesh != z_sens:
                        true_gravity.z *= -1.0
                
                # Calculate what direction is up and the sensor's rotation
                # offset from there
                val = gravity_vec.dot(true_gravity)
                val = max(min(val, 1.0), -1.0)
                ang = math.acos(val)
                axis = gravity_vec.cross(true_gravity)
                axis.normalize()
                axis_list = axis.asArray() + [ang]
                offset = -(AxisAngle(axis_list).toQuaternion())
                # Apply the offset to the sensor and tare
                offset_data = offset.asArray()
                times = 0
                while(times < 3 and not self.device.offsetWithQuaternion(offset_data)):
                    times += 1
                if times >= 3:
                    message = "Failed to send offset data to sensor (%s)" % (hex_num)
                    caption = "Data Sent Failed"
                    wx.MessageBox(message, caption, wx.OK | wx.ICON_ERROR)
                    success = False
                    break
                else:
                    times = 0
                    while(times < 3 and not self.device.tareWithCurrentOrientation()):
                        times += 1
                    if times >= 3:
                        message = "Failed to tare sensor (%s)" % (hex_num)
                        caption = "Tare Failed"
                        wx.MessageBox(message, caption, wx.OK | wx.ICON_ERROR)
                        success = False
                        break
            elif times >= 3:
                got_data = True
                message = "Failed to receive data from sensor (%s)" % (hex_num)
                caption = "Data Received Failed"
                wx.MessageBox(message, caption, wx.OK | wx.ICON_ERROR)
                success = False
                break
        return success
    
    def onPopupProperties(self, event):
        if not global_config_win.IsShown():
            if global_poll_bool:
                stopStream()
        
        dlg = TSSPropertiesDialog(self, -1, "Properties")
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        if val == wx.ID_OK:
            try:
                if self.device is not None:
                    self.ts_axis = self.device.getAxisDirections()
                    quat_data = self.device.getTaredOrientationAsQuaternion()
                    sens_name = self.device.device_type + "-" + self.device.serial_number_hex
                    if quat_data is not None:
                        quat = Quaternion(quat_data)
                        for f in sc.AXIS_DIR_MAP[self.orient_axis][self.ts_axis]:
                            f(quat)
                        self.output_ports.end_list[0].data = quat
                    self.output_ports.end_list[0].description_label.ClearText()
                    self.output_ports.end_list[0].description_label.AddText(sens_name)
                else:
                    self.output_ports.end_list[0].data = None
                    self.output_ports.end_list[0].timestamp = -1
                    self.output_ports.end_list[0].description_label.ClearText()
                    self.output_ports.end_list[0].description_label.AddText("None")
            except:
                wx.MessageBox("Bad data given: try again", "Bad Input", wx.ICON_ERROR)
            self.GetCanvas().Refresh(False)
        dlg.Destroy()
        
        if not global_config_win.IsShown():
            if global_poll_bool:
                startStream()
        else:
            pollLastSteamData()
        self.performOperation()
    
    ## OGL Functions
    def Delete(self):
        global_input_nodes.remove(self)
        Node.Delete(self)
        global_side_panel.updatePanel()


class TSSPropertiesDialog(PropertiesDialogDefault):
    
    """ A PropertiesDialogDefault object.
        
        Attributes:
            msg: A reference to a wx.TextCtrl object that is used if the node's
                device is not connected.
            node: A reference to a TSSNode object.
            sensor_choice_box: A reference to a wx.Choice object that holds a
                name of a TSSensor object using its device type and serial
                number hex string.
    """
    global global_sensor_list, global_dongle_list
    def __init__(self, parent, id, title, size=wx.DefaultSize, pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):
        """ Initializes the TSSPropertiesDialog class.
            
            Args:
                parent: A reference to a VirtualSensorNode object.
                id: An integer denoting an ID for the window.
                title: A string denoting the title of the window.
                size: A tuple that stores a width and height for the window.
                pos: A tuple with x an y coordinate position for the window.
                style: An integer denoting the style of the window.
        """
        PropertiesDialogDefault.__init__(self, parent, id, title, size, pos, style)
    
    def addProperties(self, sizer, parent):
        self.node = parent
        self.sensor_choice_box = wx.Choice(self, -1, size=(125, -1))
        self.sensor_choice_box.Bind(wx.EVT_CHOICE, self.onChoice)
        sens_list = []
        for id in global_sensor_list:
            add_to_list = True
            dev_type = global_sensor_list[id].device_type
            id_hex = global_sensor_list[id].serial_number_hex
            for node in global_input_nodes:
                if node.device is not None:
                    if node.device.serial_number == id:
                        if node is not parent:
                            add_to_list = False
                            break
            if add_to_list:
                sens_list.append(dev_type + "-" + id_hex)
        
        sens_list.sort()
        self.sensor_choice_box.SetItems(["None"] + sens_list)
        self.sensor_choice_box.SetSelection(0)
        
        tmp_sens_name = "None"
        if parent.device is not None:
            id = parent.device.serial_number
            id_hex = parent.device.serial_number_hex
            if id in global_sensor_list:
                tmp_sens_name = parent.device.device_type + "-" + id_hex
                self.sensor_choice_box.SetStringSelection(tmp_sens_name)
            else:
                parent.device = None
                parent.output_ports.end_list[0].description_label.ClearText()
                parent.output_ports.end_list[0].data = None
                parent.output_ports.end_list[0].description_label.AddText("None")
                parent.GetCanvas().Refresh()
        
        sizer.AddSpacer((0, 15))
        self.msg = wx.StaticText(self, wx.NewId(), "", (3, 3), (207, -1), wx.ALIGN_CENTRE)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer((5, 0))
        label = wx.StaticText(self, -1, "TSDevice:")
        box.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)
        box.AddSpacer((5, 0))
        box.Add(self.sensor_choice_box, 0)
        box.AddSpacer((5, 0))
        sizer.AddSpacer((0, 5))
        sizer.Add(box, 0, wx.ALIGN_CENTER)
        
        config_btn = wx.Button(self, wx.NewId(), 'Configure', size=(100, -1))
        config_btn.Bind(wx.EVT_BUTTON, self.onConfigure)
        sizer.AddSpacer((0, 10))
        sizer.Add(config_btn, 0, wx.ALIGN_CENTRE | wx.ALL)
        if parent.device is None:
            config_btn.Disable()
        
        btn_box = wx.BoxSizer(wx.HORIZONTAL)
        
        reconnect_btn = wx.Button(self, wx.NewId(), 'Reconnect', size=(100, -1))
        reconnect_btn.Bind(wx.EVT_BUTTON, self.onReconnect)
        reconnect_btn.Disable()
        
        find_btn = wx.Button(self, wx.NewId(), 'Find Devices', size=(100, -1))
        find_btn.Bind(wx.EVT_BUTTON, self.onFind)
        
        btn_box.AddSpacer((5, 0))
        btn_box.Add(reconnect_btn, 0, wx.ALIGN_CENTRE | wx.ALL)
        btn_box.AddSpacer((5, 0))
        btn_box.Add(find_btn, 0, wx.ALIGN_CENTRE | wx.ALL)
        btn_box.AddSpacer((5, 0))
        
        sizer.AddSpacer((0, 10))
        sizer.Add(btn_box, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
    
    def onReconnect(self, event):
        if self.node.device is not None:
            if self.node.device.reconnect():
                self.FindWindowByLabel("Reconnect").Disable()
                self.msg.SetLabel("")
                self.msg.SetSize((207, -1))
                self.FindWindowByLabel("Configure").Enable()
    
    def onFind(self, event):
        sc.global_updated_sensors = True
        for id in global_sensor_list:
            sensor = global_sensor_list[id]
            if not sensor.isConnected():
                if "WL" in sensor.device_type and not sensor.wireless_com:
                    if sensor.switchToWirelessMode() and sensor.isConnected():
                        continue
                string = sensor.device_type + '-' + sensor.serial_number_hex
                name_idx = self.sensor_choice_box.FindString(string)
                if name_idx != -1:
                    self.sensor_choice_box.Delete(name_idx)
                if self.node.device == sensor:
                    self.node.device = None
                sensor.close()
                del global_sensor_list[id]
        
        for id in global_dongle_list.keys():
            dongle = global_dongle_list[id]
            if not dongle.isConnected():
                dongle.close()
                del global_dongle_list[id]
        
        progress_bar = sc.ProgressSensorsAndDongles()
        progress_bar.searchSensorsAndDongles()
        
        if len(global_dongle_list) > 0:
            count = 0
            progress_bar.setValue(count)
            progress_bar.SetTitle("Checking TSDongles' Logical ID Table...")
            progress_bar.setRange(len(global_dongle_list) * 15)
            for dongle in global_dongle_list.values():
                for i in range(15):
                    count += 1
                    wl_id = dongle.getSerialNumberAtLogicalID(i)
                    wl_id_hex = '{0:08X}'.format(wl_id)
                    if wl_id != 0:
                        if wl_id not in global_sensor_list:
                            wireless = dongle.setSensorToDongle(i, wl_id)
                            if wireless is None:
                                print "Failed to find", wl_id_hex
                                continue
                            
                            if not wireless.switchToWiredMode():
                                wireless.switchToWirelessMode()
                            if not wireless.isConnected():
                                print "Failed to add", wl_id_hex
                            else:
                                print "Created TSWLSensor Wireless Serial:",
                                print wl_id_hex, "Firmware Date:",
                                print wireless.getFirmwareVersionString()
                    progress_bar.setValue(count)
        progress_bar.destroy()
        
        if sc.global_check_unknown:
            dlg = sc.UnknownPortDialog()
            dlg.CenterOnScreen()
            dlg.ShowModal()
            dlg.Destroy()
        
        sens_list = []
        for id in global_sensor_list:
            add_to_list = True
            dev_type = global_sensor_list[id].device_type
            id_hex = global_sensor_list[id].serial_number_hex
            for n in global_input_nodes:
                if n.device is not None:
                    if n.device.serial_number == id:
                        if n is not self.node:
                            add_to_list = False
                            break
            if add_to_list:
                sens_list.append(dev_type + "-" + id_hex)
        
        sens_list.sort()
        self.sensor_choice_box.SetItems(["None"] + sens_list)
        if self.node.device is not None:
            string = self.node.device.device_type + '-' + self.node.device.serial_number_hex
            self.sensor_choice_box.SetStringSelection(string)
        else:
            self.sensor_choice_box.SetSelection(0)
        
        global_config_win.updateTree()
        
        command = wx.CommandEvent(wx.wxEVT_COMMAND_CHOICE_SELECTED)
        command.SetString(self.sensor_choice_box.GetStringSelection())
        self.sensor_choice_box.Command(command)
    
    def onConfigure(self, event):
        device_name = self.sensor_choice_box.GetStringSelection()
        dev_type, serial_hex = device_name.rsplit('-', 1)
        item = global_config_win.findTreeItem(device_name, global_config_win.sensor_root)
        if item is not None:
            global_config_win.device_tree.SelectItem(item)
        else:
            if "WL" in dev_type:
                item = global_config_win.findTreeItem(device_name, global_config_win.dongle_root)
                if item is not None:
                    global_config_win.device_tree.SelectItem(item)
        global_config_win.counter = 0
        
        global_config_win.notebook.AddPage(global_config_win.orient_panel, "Orientation Placement")
        global_config_win.orient_panel.initSettings(self.node.orient_dir, self.node.onSensorConfigureApply)
        global_config_win.device_tree.Disable()
        
        global_config_win.update_timer.Start()
        global_config_win.Show()
        global_config_win.SetFocus()
        if not global_config_win.IsActive():
            global_config_win.Restore()
            global_config_win.Raise()
    
    def onChoice(self, event):
        device_name = event.GetString()
        config_btn = self.FindWindowByLabel("Configure")
        reconnect_btn = self.FindWindowByLabel("Reconnect")
        config_btn.Disable()
        reconnect_btn.Disable()
        self.msg.SetLabel("")
        self.msg.SetSize((207, -1))
        if device_name != "None":
            dev_type, serial_hex = device_name.rsplit('-', 1)
            serial = int(serial_hex, 16)
            if serial in global_sensor_list:
                self.node.device = global_sensor_list[serial]
            if not self.node.device.isConnected():
                self.msg.SetLabel("Device " + device_name + " is not connected")
                self.msg.SetSize((207, -1))
                reconnect_btn.Enable()
            else:
                config_btn.Enable()
        else:
            self.node.device = None


class VirtualSensorNode(Node):
    
    """A Node object that is used for outputing data to the user to use."""
    global global_output_nodes
    def setupNode(self):
        self.node_shape.SetBrush(wx.Brush((40, 145, 250), wx.SOLID))
        canvas = self.GetCanvas()
        labels = ["#"]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        self.name = nameCheck("Virt Sens")
        self.label.AddText(self.name)
        global_output_nodes.append(self)
        global_side_panel.updatePanel()
    
    def dumps(self):
        node_xml = Node.dumps(self)
        connection_dic = {"NAME": self.name}
        con_xml = et.Element("NodeName", connection_dic)
        node_xml.append(con_xml)
        return node_xml
    
    def loads(self):
        name = self.additional_attributes["NodeName"]["NAME"]
        self.label.ClearText()
        self.label.AddText(name)
        self.name = name
    
    def setDataTypes(self):
        if self.input_ports[0].connection:
            self.input_ports[0].data_type = self.input_ports[0].connection.data_type
        else:
            self.input_ports[0].data_type = "#"
        if not self.GetCanvas().parent.IsShown():
            return
        self.input_ports[0].updateText()
    
    def getSensorOrientDir(self):
        input_ports = self.input_ports
        while len(input_ports) and input_ports[0].connection:
            if len(input_ports) > 1:
                return None
            if type(input_ports[0].connection.node) is TSSNode:
                return input_ports[0].connection.node.orient_dir.copy()
            input_ports = input_ports[0].connection.node.input_ports
    
    def setSensorOrientDir(self, orient):
        input_ports = self.input_ports
        while len(input_ports) and input_ports[0].connection:
            if len(input_ports) > 1:
                return
            if type(input_ports[0].connection.node) is TSSNode:
                input_ports[0].connection.node.orient_axis = sc.convertMatrix4ToAxisDir(orient)
                input_ports[0].connection.node.orient_dir = orient.copy()
                return
            input_ports = input_ports[0].connection.node.input_ports
    
    def performOperation(self):
        self.setDataTypes()
    
    def onPopupProperties(self, event):
        dlg = VirtualSensorPropertiesDialog(self, -1, "Properties", size=(350, 200), style=wx.DEFAULT_DIALOG_STYLE)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        if val == wx.ID_OK:
            if self.name != dlg.node_name.GetValue():
                self.label.ClearText()
                tmp_name = nameCheck(dlg.node_name.GetValue())
                dlg.node_name.SetValue(tmp_name)
                self.name = dlg.node_name.GetValue()
                self.label.AddText(dlg.node_name.GetValue())
                self.GetCanvas().Refresh(True)
        dlg.Destroy()
        global_side_panel.updatePanel()
    
    ## OGL Functions
    def Delete(self):
        global_output_nodes.remove(self)
        Node.Delete(self)
        global_side_panel.updatePanel()


class VirtualSensorPropertiesDialog(PropertiesDialogDefault):
    
    """ A PropertiesDialogDefault object.
        
        Attributes:
            label: An instance of wx.StaticText used for output to screen.
            node: A reference to a VirtualSensorNode object.
            node_name: An instance of wx.TextCtrl with the name of the node.
    """
    def __init__(self, parent, id, title, size=wx.DefaultSize,
                 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):
        """ Initializes the VirtualSensorPropertiesDialog class.
            
            Args:
                parent: A reference to a VirtualSensorNode object.
                id: An integer denoting an ID for the window.
                title: A string denoting the title of the window.
                size: A tuple that stores a width and height for the window.
                pos: A tuple with x an y coordinate position for the window.
                style: An integer denoting the style of the window.
        """
        PropertiesDialogDefault.__init__(self, parent, id, title, size, pos, style)
    
    def addProperties(self, sizer, parent):
        self.node = parent
        type_str = ""
        if parent.input_ports[0].data_type == "F":
            type_str = "Float: "
        elif parent.input_ports[0].data_type == "V":
            type_str = "Vector 3: "
        elif parent.input_ports[0].data_type == "A":
            type_str = "Axis Angle: "
        elif parent.input_ports[0].data_type == "Q":
            type_str = "Quaternion: "
        elif parent.input_ports[0].data_type == "E":
            type_str = "Euler: "
        elif parent.input_ports[0].data_type == "M":
            type_str = "Matrix 3: "
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Name:")
        self.node_name = wx.TextCtrl(self, -1, parent.name)
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        box.Add(self.node_name, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        label = wx.StaticText(self, -1, "Current Output:")
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.label = wx.StaticText(self, -1,
            type_str + str(parent.input_ports.end_list[0].data))
        box.Add(self.label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        button = wx.Button(self, wx.NewId(), 'Refresh Value', (50, 50),
            (90, 28))
        button.Bind(wx.EVT_BUTTON, self.onButtonClick)
        sizer.Add(button, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
    
    def onButtonClick(self, event):
        """ Updates the label of the object.
            
            Args:
                event: A wxPython event.
        """
        if self.node.input_ports[0].connection is not None:
            self.node.input_ports[0].connection.node.setUpdateData()
        self.node.setDataTypes()
        type_str = ""
        if self.node.input_ports[0].data_type == "F":
            type_str = "Float: "
        elif self.node.input_ports[0].data_type == "V":
            type_str = "Vector 3: "
        elif self.node.input_ports[0].data_type == "A":
            type_str = "Axis Angle: "
        elif self.node.input_ports[0].data_type == "Q":
            type_str = "Quaternion: "
        elif self.node.input_ports[0].data_type == "E":
            type_str = "Euler: "
        elif self.node.input_ports[0].data_type == "M":
            type_str = "Matrix 3: "
        
        self.label.SetLabel(type_str + str(self.node.input_ports.end_list[0].data))


class OutputNode(Node):
    
    """A Node object that is used for outputing data to the user."""
    def setupNode(self):
        global global_output_nodes
        self.label.AddText("Output Node")
        self.node_shape.SetBrush(wx.GREEN_BRUSH)
        canvas = self.GetCanvas()
        labels = ["*"]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        self.name = "Output Node"
        global_output_nodes.append(self)
        global_side_panel.updatePanel()
    
    def dumps(self):
        node_xml = Node.dumps(self)
        connection_dic = {"NAME": self.name}
        con_xml = et.Element("NodeName", connection_dic)
        node_xml.append(con_xml)
        return node_xml
    
    def loads(self):
        name = self.additional_attributes["NodeName"]["NAME"]
        self.label.ClearText()
        self.label.AddText(name)
        self.name = name
    
    def setDataTypes(self):
        if self.input_ports[0].connection:
            self.input_ports[0].data_type = \
                self.input_ports[0].connection.data_type
        else:
            self.input_ports[0].data_type = "*"
        
        if not self.GetCanvas().parent.IsShown():
            return
        
        self.input_ports[0].updateText()
    
    def performOperation(self):
        self.setDataTypes()
    
    def onPopupProperties(self, event):
        dlg = OutputPropertiesDialog(self, -1, "Properties", size=(350, 200), style=wx.DEFAULT_DIALOG_STYLE)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        self.label.ClearText()
        self.label.AddText(dlg.node_name.GetValue())
        self.name = dlg.node_name.GetValue()
        self.GetCanvas().Refresh(False)
        dlg.Destroy()
        global_side_panel.updatePanel()
    
    ## OGL Functions
    def Delete(self):
        global global_output_nodes
        global_output_nodes.remove(self)
        Node.Delete(self)
        global_side_panel.updatePanel()


class OutputPropertiesDialog(PropertiesDialogDefault):
    
    """ A PropertiesDialogDefault object.
        
        Attributes:
            label: An instance of wx.StaticText used for output to screen.
            node: A reference to a OutputNode object.
            node_name: An instance of wx.TextCtrl with the name of the node.
    """
    def __init__(self, parent, id, title, size=wx.DefaultSize, pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):
        """ Initializes the OutputPropertiesDialog class.
            
            Args:
                parent: A reference to a OutputNode object.
                id: An integer denoting an ID for the window.
                title: A string denoting the title of the window.
                size: A tuple that stores a width and height for the window.
                pos: A tuple with x an y coordinate position for the window.
                style: An integer denoting the style of the window.
        """
        PropertiesDialogDefault.__init__(self, parent, id, title, size, pos, style)
    
    def addProperties(self, sizer, parent):
        self.node = parent
        type_str = ""
        if parent.input_ports[0].data_type == "F":
            type_str = "Float: "
        elif parent.input_ports[0].data_type == "V":
            type_str = "Vector 3: "
        elif parent.input_ports[0].data_type == "A":
            type_str = "Axis Angle: "
        elif parent.input_ports[0].data_type == "Q":
            type_str = "Quaternion: "
        elif parent.input_ports[0].data_type == "E":
            type_str = "Euler: "
        elif parent.input_ports[0].data_type == "M":
            type_str = "Matrix 3: "
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Name:")
        self.node_name = wx.TextCtrl(self, -1, parent.name)
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        box.Add(self.node_name, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        label = wx.StaticText(self, -1, "Current Output:")
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.label = wx.StaticText(
            self, -1, type_str + str(parent.input_ports.end_list[0].data))
        box.Add(self.label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        button = wx.Button(self, wx.NewId(), 'Refresh Value', (50, 50),
            (90, 28))
        button.Bind(wx.EVT_BUTTON, self.onButtonClick)
        sizer.Add(button, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
    
    def onButtonClick(self, event):
        """ Updates the label of the object.
            
            Args:
                event: A wxPython event.
        """
        if self.node.input_ports[0].connection is not None:
            self.node.input_ports[0].connection.node.setUpdateData()
        self.node.setDataTypes()
        type_str = ""
        if self.node.input_ports[0].data_type == "F":
            type_str = "Float: "
        elif self.node.input_ports[0].data_type == "V":
            type_str = "Vector 3: "
        elif self.node.input_ports[0].data_type == "A":
            type_str = "Axis Angle: "
        elif self.node.input_ports[0].data_type == "Q":
            type_str = "Quaternion: "
        elif self.node.input_ports[0].data_type == "E":
            type_str = "Euler: "
        elif self.node.input_ports[0].data_type == "M":
            type_str = "Matrix 3: "
        
        self.label.SetLabel(type_str + str(self.node.input_ports.end_list[0].data))


class StaticQuaternionNode(Node):
    
    """A Node object that is used for creating a quaternion node."""
    def setupNode(self):
        global global_static_nodes
        global_static_nodes.append(self)
        self.label.AddText("Quaternion Node")
        self.label.SetFont(
            wx.Font(8, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL))
        self.node_shape.SetBrush(wx.GREY_BRUSH)
        canvas = self.GetCanvas()
        labels = ["Q"]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.output_ports.end_list[0].data = Quaternion()
        self.output_ports.end_list[0].data.normalize()
    
    def dumps(self):
        node_xml = Node.dumps(self)
        tmp_data = self.output_ports.end_list[0].data.asArray()
        connection_dic = {
            "X": str(tmp_data[0]),
            "Y": str(tmp_data[1]),
            "Z": str(tmp_data[2]),
            "W": str(tmp_data[3])
        }
        con_xml = et.Element("QuatData", connection_dic)
        node_xml.append(con_xml)
        return node_xml
    
    def loads(self):
        data = self.additional_attributes["QuatData"]
        quat = [
            float(data["X"]),
            float(data["Y"]),
            float(data["Z"]),
            float(data["W"])
        ]
        
        self.output_ports.end_list[0].data = Quaternion(quat)
        self.output_ports.end_list[0].data.normalize()
    
    def setUpdateData(self):
        if self.output_ports[0].connection is not None:
            self.output_ports[0].connection.data = self.output_ports[0].data
    
    def performOperation(self):
        self.setUpdateData()
        if self.output_ports[0].connection is not None:
            self.output_ports[0].connection.node.performOperation()
    
    def onPopupProperties(self, event):
        dlg = StaticQuaternionPropertiesDialog(self, -1, "Properties", size=(350, 200), style=wx.DEFAULT_DIALOG_STYLE)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        
        if val == wx.ID_OK:
            try:
                new_quat = Quaternion([
                    dlg.x_text.GetValue(),
                    dlg.y_text.GetValue(),
                    dlg.z_text.GetValue(),
                    dlg.w_text.GetValue()
                ])
                self.output_ports.end_list[0].data = new_quat
                self.output_ports.end_list[0].data.normalize()
            except:
                wx.MessageBox("Bad data given: try again", "Bad Input", wx.ICON_ERROR)
            self.performOperation()
        
        dlg.Destroy()
    
    ## OGL Functions
    def Delete(self):
        global global_static_nodes
        global_static_nodes.remove(self)
        Node.Delete(self)


class StaticQuaternionPropertiesDialog(PropertiesDialogDefault):
    
    """ A PropertiesDialogDefault object.
        
        Attributes:
            w_text: A wx.FloatSpin instance used for denoting the w-value in a
                quaternion.
            x_text: A wx.FloatSpin instance used for denoting the x-value in a
                quaternion.
            y_text: A wx.FloatSpin instance used for denoting the y-value in a
                quaternion.
            z_text: A wx.FloatSpin instance used for denoting the z-value in a
                quaternion.
    """
    def addProperties(self, sizer, parent):
        label = wx.StaticText(self, -1, "Set Quaternion")
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        quat = parent.output_ports.end_list[0].data.asArray()
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        
        label = wx.StaticText(self, -1, "X:")
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.x_text = float_spin.FloatSpin(self, -1, size=(75, -1), value=quat[0], increment=0.1, digits=4)
        box.Add(self.x_text, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        label = wx.StaticText(self, -1, "Y:")
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.y_text = float_spin.FloatSpin(self, -1, size=(75, -1), value=quat[1], increment=0.1, digits=4)
        box.Add(self.y_text, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        label = wx.StaticText(self, -1, "Z:")
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.z_text = float_spin.FloatSpin(self, -1, size=(75, -1), value=quat[2], increment=0.1, digits=4)
        box.Add(self.z_text, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        label = wx.StaticText(self, -1, "W:")
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.w_text = float_spin.FloatSpin(self, -1, size=(75, -1), value=quat[3], increment=0.1, digits=4)
        box.Add(self.w_text, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)


class StaticFloatNode(Node):
    
    """A Node object that is used for creating a float node."""
    def setupNode(self):
        global global_static_nodes
        global_static_nodes.append(self)
        self.label.AddText("Float Node")
        self.node_shape.SetBrush(wx.Brush((255, 218, 185), wx.SOLID))
        canvas = self.GetCanvas()
        labels = ["F"]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.output_ports.end_list[0].data = 1.0
    
    def dumps(self):
        node_xml = Node.dumps(self)
        connection_dic = {"F": str(self.output_ports.end_list[0].data)}
        con_xml = et.Element("FloatData", connection_dic)
        node_xml.append(con_xml)
        return node_xml
    
    def loads(self):
        data = self.additional_attributes["FloatData"]
        self.output_ports.end_list[0].data = float(data["F"])
    
    def setUpdateData(self):
        if self.output_ports[0].connection is not None:
            self.output_ports[0].connection.data = self.output_ports[0].data
    
    def performOperation(self):
        self.setUpdateData()
        if self.output_ports[0].connection is not None:
            self.output_ports[0].connection.node.performOperation()
    
    def onPopupProperties(self, event):
        dlg = StaticFloatDialog(self, -1, "Properties", size=(350, 200), style=wx.DEFAULT_DIALOG_STYLE)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        
        if val == wx.ID_OK:
            try:
                new_float = dlg.float_val.GetValue()
                self.output_ports.end_list[0].data = new_float
            except:
                wx.MessageBox("Bad data given: try again", "Bad Input", wx.ICON_ERROR)
            self.performOperation()
        
        dlg.Destroy()
    
    ## OGL Functions
    def Delete(self):
        global global_static_nodes
        global_static_nodes.remove(self)
        Node.Delete(self)


class StaticFloatDialog(PropertiesDialogDefault):
    
    """ A PropertiesDialogDefault object.
        
        Attributes:
            float_val: A wx.FloatSpin instance used for denoting the float
                value.
    """
    def addProperties(self, sizer, parent):
        label = wx.StaticText(self, -1, "Set Float")
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        tmp_float = parent.output_ports.end_list[0].data
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.float_val = float_spin.FloatSpin(self, -1, (50, 50), size=(10, -1), value=tmp_float, increment=0.1, digits=4)
        box.Add(self.float_val, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)


class StaticVectorNode(Node):
    
    """A Node object that is used for creating a vector node."""
    def setupNode(self):
        global global_static_nodes
        global_static_nodes.append(self)
        self.label.AddText("Vector 3 Node")
        self.node_shape.SetBrush(wx.Brush((127, 255, 212), wx.SOLID))
        canvas = self.GetCanvas()
        labels = ["V"]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.output_ports.end_list[0].data = Vector3()
    
    def dumps(self):
        node_xml = Node.dumps(self)
        tmp_vec = self.output_ports.end_list[0].data.asArray()
        connection_dic = {
            "X": str(tmp_vec[0]),
            "Y": str(tmp_vec[1]),
            "Z": str(tmp_vec[2])
        }
        con_xml = et.Element("VecData", connection_dic)
        node_xml.append(con_xml)
        return node_xml
    
    def loads(self):
        data = self.additional_attributes["VecData"]
        vec = Vector3([float(data["X"]), float(data["Y"]), float(data["Z"])])
        self.output_ports.end_list[0].data = vec
    
    def setUpdateData(self):
        if self.output_ports[0].connection is not None:
            self.output_ports[0].connection.data = self.output_ports[0].data
    
    def performOperation(self):
        self.setUpdateData()
        if self.output_ports[0].connection is not None:
            self.output_ports[0].connection.node.performOperation()
    
    def onPopupProperties(self, event):
        dlg = StaticVectorDialog(self, -1, "Properties", size=(350, 200), style=wx.DEFAULT_DIALOG_STYLE)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        
        if val == wx.ID_OK:
            try:
                new_vec = Vector3([
                    dlg.x_text.GetValue(),
                    dlg.y_text.GetValue(),
                    dlg.z_text.GetValue()
                ])
                self.output_ports.end_list[0].data = new_vec
            except:
                wx.MessageBox("Bad data given: try again", "Bad Input", wx.ICON_ERROR)
            self.performOperation()
        
        dlg.Destroy()
    
    ## OGL Functions
    def Delete(self):
        global global_static_nodes
        global_static_nodes.remove(self)
        Node.Delete(self)


class StaticVectorDialog(PropertiesDialogDefault):
    
    """ A PropertiesDialogDefault object.
        
        Attributes:
            x_text: A wx.FloatSpin instance used for denoting the x-value in a
                vector.
            y_text: A wx.FloatSpin instance used for denoting the y-value in a
                vector.
            z_text: A wx.FloatSpin instance used for denoting the z-value in a
                vector.
    """
    def addProperties(self, sizer, parent):
        label = wx.StaticText(self, -1, "Set Vector")
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        vec = parent.output_ports.end_list[0].data.asArray()
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "X:")
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.x_text = float_spin.FloatSpin(self, -1, size=(75, -1), value=vec[0], increment=0.1, digits=4)
        box.Add(self.x_text, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        label = wx.StaticText(self, -1, "Y:")
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.y_text = float_spin.FloatSpin(self, -1, size=(75, -1), value=vec[1], increment=0.1, digits=4)
        box.Add(self.y_text, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        label = wx.StaticText(self, -1, "Z:")
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.z_text = float_spin.FloatSpin(self, -1, size=(75, -1), value=vec[2], increment=0.1, digits=4)
        box.Add(self.z_text, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)


class StaticEulerNode(Node):
    
    """A Node object that is used for creating a euler node."""
    def setupNode(self):
        global global_static_nodes
        global_static_nodes.append(self)
        self.label.AddText("Euler Node")
        self.node_shape.SetBrush(wx.Brush((50, 205, 50), wx.SOLID))
        canvas = self.GetCanvas()
        labels = ["E"]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.output_ports.end_list[0].data = Euler()
    
    def dumps(self):
        node_xml = Node.dumps(self)
        data = self.output_ports.end_list[0].data.asDegreeArray()
        connection_dic = {
            "X": str(data[0]),
            "Y": str(data[1]),
            "Z": str(data[2])
        }
        con_xml = et.Element("EulerData", connection_dic)
        node_xml.append(con_xml)
        return node_xml
    
    def loads(self):
        data = self.additional_attributes["EulerData"]
        euler = Euler([float(data["X"]), float(data["Y"]), float(data["Z"])], True)
        self.output_ports.end_list[0].data = euler
    
    def setUpdateData(self):
        if self.output_ports[0].connection is not None:
            self.output_ports[0].connection.data = self.output_ports[0].data
    
    def performOperation(self):
        self.setUpdateData()
        if self.output_ports[0].connection is not None:
            self.output_ports[0].connection.node.performOperation()
    
    def onPopupProperties(self, event):
        dlg = StaticEulerPropertiesDialog(self, -1, "Properties", size=(350, 200), style=wx.DEFAULT_DIALOG_STYLE)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        
        if val == wx.ID_OK:
            try:
                new_euler = Euler([dlg.x_text.GetValue(), dlg.y_text.GetValue(), dlg.z_text.GetValue()], True)
                self.output_ports.end_list[0].data = new_euler
            except:
                wx.MessageBox("Bad data given: try again", "Bad Input", wx.ICON_ERROR)
            self.performOperation()
        
        dlg.Destroy()
    
    ## OGL Functions
    def Delete(self):
        global global_static_nodes
        global_static_nodes.remove(self)
        Node.Delete(self)


class StaticEulerPropertiesDialog(PropertiesDialogDefault):
    
    """ A PropertiesDialogDefault object.
        
        Attributes:
            x_text: A wx.FloatSpin instance used for denoting the x-axis value
                in an euler.
            y_text: A wx.FloatSpin instance used for denoting the y-axis value
                in an euler.
            z_text: A wx.FloatSpin instance used for denoting the z-axis value
                in an euler.
    """
    def addProperties(self, sizer, parent):
        label = wx.StaticText(self, -1, "Set Euler Angles\n(Angles in Degrees)")
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        tmp_euler = parent.output_ports.end_list[0].data.asDegreeArray()
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        
        label = wx.StaticText(self, -1, "X:")
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.x_text = float_spin.FloatSpin(self, -1, size=(75, -1), value=tmp_euler[0], increment=0.1, digits=4)
        box.Add(self.x_text, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        label = wx.StaticText(self, -1, "Y:")
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.y_text = float_spin.FloatSpin(self, -1, size=(75, -1), value=tmp_euler[1], increment=0.1, digits=4)
        box.Add(self.y_text, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        label = wx.StaticText(self, -1, "Z:")
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.z_text = float_spin.FloatSpin(self, -1, size=(75, -1), value=tmp_euler[2], increment=0.1, digits=4)
        box.Add(self.z_text, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)


class StaticAxisAngleNode(Node):
    
    """A Node object that is used for creating a axis angle node."""
    def setupNode(self):
        global global_static_nodes
        global_static_nodes.append(self)
        self.label.AddText("Axis Angle Node")
        self.label.SetFont(wx.Font(8, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL))
        self.node_shape.SetBrush(wx.Brush((0, 255, 127), wx.SOLID))
        canvas = self.GetCanvas()
        labels = ["A"]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.output_ports.end_list[0].data = AxisAngle()
    
    def dumps(self):
        node_xml = Node.dumps(self)
        data = self.output_ports.end_list[0].data.asDegreeArray()
        connection_dic = {
            "X": str(data[0]),
            "Y": str(data[1]),
            "Z": str(data[2]),
            "ANGLE": str(data[3])
        }
        con_xml = et.Element("AAData", connection_dic)
        node_xml.append(con_xml)
        return node_xml
    
    def loads(self):
        data = self.additional_attributes["AAData"]
        tmp_axis_ang = AxisAngle([float(data["X"]), float(data["Y"]), float(data["Z"]), float(data["ANGLE"])], True)
        self.output_ports.end_list[0].data = tmp_axis_ang
    
    def setUpdateData(self):
        if self.output_ports[0].connection is not None:
            self.output_ports[0].connection.data = self.output_ports[0].data
    
    def performOperation(self):
        self.setUpdateData()
        if self.output_ports[0].connection is not None:
            self.output_ports[0].connection.node.performOperation()
    
    def onPopupProperties(self, event):
        dlg = StaticAxisAnglePropertiesDialog(self, -1, "Properties", size=(350, 200), style=wx.DEFAULT_DIALOG_STYLE)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        
        if val == wx.ID_OK:
            try:
                new_axis_ang = AxisAngle([dlg.x_text.GetValue(), dlg.y_text.GetValue(), dlg.z_text.GetValue(), dlg.ang_text.GetValue()], True)
                self.output_ports.end_list[0].data = new_axis_ang
                self.output_ports.end_list[0].data.normalize()
            except:
                wx.MessageBox("Bad data given: try again", "Bad Input", wx.ICON_ERROR)
            self.performOperation()
        
        dlg.Destroy()
    
    ## OGL Functions
    def Delete(self):
        global global_static_nodes
        global_static_nodes.remove(self)
        Node.Delete(self)


class StaticAxisAnglePropertiesDialog(PropertiesDialogDefault):
    
    """ A PropertiesDialogDefault object.
        
        Attributes:
            ang_text: A wx.FloatSpin instance used for denoting the angle-value
                in an axis angle.
            x_text: A wx.FloatSpin instance used for denoting the x-value in an
                axis angle.
            y_text: A wx.FloatSpin instance used for denoting the y-value in an
                axis angle.
            z_text: A wx.FloatSpin instance used for denoting the z-value in an
                axis angle.
    """
    def addProperties(self, sizer, parent):
        label = wx.StaticText(self, -1, "Set Axis Angle Values\n(Angles in Degrees)")
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        tmp_axis_ang = parent.output_ports.end_list[0].data.asDegreeArray()
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        
        label = wx.StaticText(self, -1, "X:")
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        self.x_text = float_spin.FloatSpin(self, -1, size=(75, -1), value=tmp_axis_ang[0], increment=0.1, digits=4)
        box.Add(self.x_text, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        label = wx.StaticText(self, -1, "Y:")
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.y_text = float_spin.FloatSpin(self, -1, size=(75, -1), value=tmp_axis_ang[1], increment=0.1, digits=4)
        box.Add(self.y_text, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        label = wx.StaticText(self, -1, "Z:")
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.z_text = float_spin.FloatSpin(self, -1, size=(75, -1), value=tmp_axis_ang[2], increment=0.1, digits=4)
        box.Add(self.z_text, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        label = wx.StaticText(self, -1, "Angle:")
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.ang_text = float_spin.FloatSpin(self, -1, size=(75, -1), value=tmp_axis_ang[3], increment=0.1, digits=4)
        box.Add(self.ang_text, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)


class StaticMatrixNode(Node):
    
    """A Node object that is used for creating a matrix node."""
    def setupNode(self):
        global global_static_nodes
        global_static_nodes.append(self)
        self.label.AddText("Matrix Node")
        self.node_shape.SetBrush(wx.Brush((124, 252, 0), wx.SOLID))
        canvas = self.GetCanvas()
        labels = ["M"]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.output_ports.end_list[0].data = Matrix3()
    
    def dumps(self):
        node_xml = Node.dumps(self)
        mat = self.output_ports.end_list[0].data.asRowArray()
        connection_dic = {
            "R0C0": str(mat[0]),
            "R0C1": str(mat[1]),
            "R0C2": str(mat[2]),
            "R1C0": str(mat[3]),
            "R1C1": str(mat[4]),
            "R1C2": str(mat[5]),
            "R2C0": str(mat[6]),
            "R2C1": str(mat[7]),
            "R2C2": str(mat[8])
        }
        con_xml = et.Element("MatData", connection_dic)
        node_xml.append(con_xml)
        return node_xml
    
    def loads(self):
        data = self.additional_attributes["MatData"]
        mat = Matrix3([
            float(data["R0C0"]),
            float(data["R0C1"]),
            float(data["R0C2"]),
            float(data["R1C0"]),
            float(data["R1C1"]),
            float(data["R1C2"]),
            float(data["R2C0"]),
            float(data["R2C1"]),
            float(data["R2C2"])
        ])
        mat.orthonormalize()
        self.output_ports.end_list[0].data = mat
    
    def setUpdateData(self):
        if self.output_ports[0].connection is not None:
            self.output_ports[0].connection.data = self.output_ports[0].data
    
    def performOperation(self):
        self.setUpdateData()
        if self.output_ports[0].connection is not None:
            self.output_ports[0].connection.node.performOperation()
    
    def onPopupProperties(self, event):
        dlg = StaticMatrixPropertiesDialog(self, -1, "Properties", size=(350, 200), style=wx.DEFAULT_DIALOG_STYLE)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        
        if val == wx.ID_OK:
            try:
                new_mat = Matrix3([
                    dlg.text00.GetValue(),
                    dlg.text01.GetValue(),
                    dlg.text02.GetValue(),
                    dlg.text10.GetValue(),
                    dlg.text11.GetValue(),
                    dlg.text12.GetValue(),
                    dlg.text20.GetValue(),
                    dlg.text21.GetValue(),
                    dlg.text22.GetValue()
                ])
                new_mat.orthonormalize()
                self.output_ports.end_list[0].data = new_mat
            except:
                wx.MessageBox("Bad data given: try again", "Bad Input", wx.ICON_ERROR)
            self.performOperation()
        
        dlg.Destroy()
    
    ## OGL Functions
    def Delete(self):
        global global_static_nodes
        global_static_nodes.remove(self)
        Node.Delete(self)


class StaticMatrixPropertiesDialog(PropertiesDialogDefault):
    
    """ A PropertiesDialogDefault object.
        
        Attributes:
            text00: A wx.FloatSpin instance used for denoting a value in a
                matrix.
            text01: A wx.FloatSpin instance used for denoting a value in a
                matrix.
            text02: A wx.FloatSpin instance used for denoting a value in a
                matrix.
            text10: A wx.FloatSpin instance used for denoting a value in a
                matrix.
            text11: A wx.FloatSpin instance used for denoting a value in a
                matrix.
            text12: A wx.FloatSpin instance used for denoting a value in a
                matrix.
            text20: A wx.FloatSpin instance used for denoting a value in a
                matrix.
            text21: A wx.FloatSpin instance used for denoting a value in a
                matrix.
            text22: A wx.FloatSpin instance used for denoting a value in a
                matrix.
    """
    def addProperties(self, sizer, parent):
        label = wx.StaticText(self, -1, "Set Matrix Values")
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        tmp_mat = parent.output_ports.end_list[0].data.asRowArray()
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.text00 = float_spin.FloatSpin(self, -1, size=(75, -1), value=tmp_mat[0], increment=0.1, digits=4)
        box.Add(self.text00, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.text01 = float_spin.FloatSpin(self, -1, size=(75, -1), value=tmp_mat[1], increment=0.1, digits=4)
        box.Add(self.text01, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.text02 = float_spin.FloatSpin(self, -1, size=(75, -1), value=tmp_mat[2], increment=0.1, digits=4)
        box.Add(self.text02, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        box2 = wx.BoxSizer(wx.HORIZONTAL)
        self.text10 = float_spin.FloatSpin(self, -1, size=(75, -1), value=tmp_mat[3], increment=0.1, digits=4)
        box2.Add(self.text10, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.text11 = float_spin.FloatSpin(self, -1, size=(75, -1), value=tmp_mat[4], increment=0.1, digits=4)
        box2.Add(self.text11, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.text12 = float_spin.FloatSpin(self, -1, size=(75, -1), value=tmp_mat[5], increment=0.1, digits=4)
        box2.Add(self.text12, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        box3 = wx.BoxSizer(wx.HORIZONTAL)
        self.text20 = float_spin.FloatSpin(self, -1, size=(75, -1), value=tmp_mat[6], increment=0.1, digits=4)
        box3.Add(self.text20, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.text21 = float_spin.FloatSpin(self, -1, size=(75, -1), value=tmp_mat[7], increment=0.1, digits=4)
        box3.Add(self.text21, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.text22 = float_spin.FloatSpin(self, -1, size=(75, -1), value=tmp_mat[8], increment=0.1, digits=4)
        box3.Add(self.text22, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        sizer.Add(box2, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        sizer.Add(box3, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)


class ConstraintNode(Node):
    
    """A Node object that is used for creating a constraint node."""
    def setupNode(self):
        self.label.AddText("Constraint Node")
        self.node_shape.SetBrush(wx.Brush("ORANGE RED", wx.SOLID))
        canvas = self.GetCanvas()
        labels = ["F"]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.min = 0.0
        self.max = 180.0
    
    def dumps(self):
        node_xml = Node.dumps(self)
        connection_dic ={"MIN": str(self.min), "MAX": str(self.max)}
        con_xml = et.Element("ConstraintData", connection_dic)
        node_xml.append(con_xml)
        return node_xml
    
    def loads(self):
        self.min = float(self.additional_attributes["ConstraintData"]["MIN"])
        self.max = float(self.additional_attributes["ConstraintData"]["MAX"])
    
    def performCalculation(self):
        in_data = self.input_ports[0].data
        return [max(self.min, min(self.max, in_data))]
    
    def onPopupProperties(self, event):
        dlg = ConstraintPropertiesDialog(self, -1, "Properties", size=(350, 200), style=wx.DEFAULT_DIALOG_STYLE)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        
        if val == wx.ID_OK:
            try:
                tmp_min = dlg.min_text.GetValue()
                tmp_max = dlg.max_text.GetValue()
                if tmp_min < tmp_max:
                    self.min = tmp_min
                    self.max = tmp_max
                else:
                    raise Exception()
            except:
                wx.MessageBox("Bad data given: try again", "Bad Input", wx.ICON_ERROR)
            self.performOperation()
        
        dlg.Destroy()


class ConstraintPropertiesDialog(PropertiesDialogDefault):
    
    """ A PropertiesDialogDefault object.
        
        Attributes:
            max_text: A wx.FloatSpin instance used for denoting the maximum
                value.
            min_text: A wx.FloatSpin instance used for denoting the minimum
                value.
    """
    def addProperties(self, sizer, parent):
        label = wx.StaticText(self, -1, "Set Constraint")
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        tmp_max = parent.max
        tmp_min = parent.min
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Min:")
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.min_text = float_spin.FloatSpin(self, -1, (50, 50), size=(75, -1), value=tmp_min, increment=0.1, digits=4)
        box.Add(self.min_text, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        label = wx.StaticText(self, -1, "Max:")
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        self.max_text = float_spin.FloatSpin(self, -1, (50, 50), size=(75, -1), value=tmp_max, increment=0.1, digits=4)
        box.Add(self.max_text, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)


class InvertNode(Node):
    
    """A Node object that is used for creating a invert node."""
    def setupNode(self):
        self.label.AddText("Invert")
        self.node_shape.SetBrush(wx.Brush("FOREST GREEN", wx.SOLID))
        canvas = self.GetCanvas()
        labels = ["*"]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
    
    def setDataTypes(self):
        if self.input_ports[0].connection:
            self.output_ports[0].data_type = self.input_ports[0].connection.data_type
        else:
            self.output_ports[0].data_type = "*"
            self.output_ports[0].disconnectNodes()
        self.output_ports[0].updateText()
    
    def performCalculation(self):
        return [-self.input_ports[0].data]


class MirrorNode(Node):
    
    """A Node object that is used for creating a mirror node."""
    def setupNode(self):
        self.node_shape.SetBrush(wx.Brush((123, 55, 56), wx.SOLID))
        canvas = self.GetCanvas()
        labels = ["#"]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        labels = ["Q"]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.orient_list = ["X", "Y", "Z"]
        self.cur_axis = 1
        self.label.AddText("Mirror " + self.orient_list[self.cur_axis])
    
    def dumps(self):
        node_xml = Node.dumps(self)
        connection_dic = {"AXIS": self.orient_list[self.cur_axis]}
        con_xml = et.Element("SetAxis", connection_dic)
        node_xml.append(con_xml)
        return node_xml
    
    def loads(self):
        self.cur_axis = self.orient_list.index(self.additional_attributes["SetAxis"]["AXIS"])
        self.label.ClearText()
        self.label.AddText("Mirror " + self.orient_list[self.cur_axis])
    
    def performCalculation(self):
        in_data = self.input_ports[0].data
        if not type(in_data)  is Quaternion:
            in_data= in_data.toQuaternion()
        x, y, z, w = in_data.asArray()
        if self.cur_axis == 0:
            out_data = Quaternion((x, y, -z, -w))
        elif self.cur_axis == 1:
            out_data = Quaternion((-x, y, z, -w))
        elif self.cur_axis == 2:
            out_data = Quaternion((x, -y, z, -w))
        return [out_data]
    
    def onPopupProperties(self, event):
        dlg = MirrorNodePropertiesDialog(self, -1, "Properties", size=(350, 200), style=wx.DEFAULT_DIALOG_STYLE)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        
        if val == wx.ID_OK:
            index = dlg.choice.GetCurrentSelection()
            self.cur_axis = index
            self.label.ClearText()
            self.label.AddText("Mirror " + self.orient_list[self.cur_axis])
        
        dlg.Destroy()


class MirrorNodePropertiesDialog(PropertiesDialogDefault):
    
    """ A PropertiesDialogDefault object.
        
        Attributes:
            choice: A wx.Choice instance that has a list of axes.
    """
    def addProperties(self, sizer, parent):
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Mirror to:", (15, 50), (75, -1))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.choice = wx.Choice(self, -1, (100, 50), choices=parent.orient_list)
        self.choice.SetSelection(parent.cur_axis)
        box.Add(self.choice, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)


class ConvertXNode(Node):
    
    """A Node object that is used for creating a convert node."""
    def setupNode(self):
        self.label.SetFont(wx.Font(7, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL))
        self.node_shape.SetBrush(wx.Brush("MEDIUM SLATE BLUE", wx.SOLID))
        canvas = self.GetCanvas()
        labels = ["#"]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        labels = ["Q"]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.orient_list = ["Quaternion", "Euler", "AxisAngle", "Matrix"]
        self.cur_conversion = 0
        self.label.AddText("Convert2" + self.orient_list[ self.cur_conversion])
    
    def dumps(self):
        node_xml = Node.dumps(self)
        connection_dic = {"TYPE": self.orient_list[self.cur_conversion]}
        con_xml = et.Element("CurrentConversion", connection_dic)
        node_xml.append(con_xml)
        return node_xml
    
    def loads(self):
        self.setConversion(self.additional_attributes["CurrentConversion"]["TYPE"])
    
    def performCalculation(self):
        in_data = self.input_ports[0].data
        if self.cur_conversion == 0 and not type(in_data) is Quaternion:
            return [in_data.toQuaternion()]
        elif self.cur_conversion == 1 and not type(in_data) is Euler:
            return [in_data.toEuler()]
        elif self.cur_conversion == 2 and not type(in_data) is AxisAngle:
            return [in_data.toAxisAngle()]
        elif self.cur_conversion == 3 and not type(in_data) is Matrix3:
            return [in_data.toMatrix3()]
        else:
            return [in_data]
    
    def onPopupProperties(self, event):
        dlg = ConvertXPropertiesDialog(self, -1, "Properties", size=(350, 200), style=wx.DEFAULT_DIALOG_STYLE)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        
        if val == wx.ID_OK:
            index = dlg.choice.GetCurrentSelection()
            self.setConversion(self.orient_list[index])
        
        dlg.Destroy()
    
    def setConversion(self, string):
        index = self.orient_list.index(string)
        self.cur_conversion = index
        self.label.ClearText()
        self.label.AddText("Convert2" + self.orient_list[index])
        self.cur_conversion = index
        self.output_ports.end_list[0].data_type = self.orient_list[index][0]
        self.output_ports.end_list[0].disconnectNodes()
        self.output_ports.end_list[0].updateText()
        self.GetCanvas().Refresh(False)


class ConvertXPropertiesDialog(PropertiesDialogDefault):
    
    """ A PropertiesDialogDefault object.
        
        Attributes:
            choice: A wx.Choice instance that has a list of possible
                conversions.
    """
    def addProperties(self, sizer, parent):
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Convert to:", (15, 50), (75, -1))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.choice = wx.Choice(self, -1, (100, 50), choices=parent.orient_list)
        self.choice.SetSelection(parent.cur_conversion)
        box.Add(self.choice, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)


class CloneNode(Node):
    
    """A Node object that is used for creating a clone node."""
    def setupNode(self):
        self.label.AddText("CloneNode")
        self.node_shape.SetBrush(wx.Brush("GOLD", wx.SOLID))
        canvas = self.GetCanvas()
        labels = ["*"]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        labels = ["*", "*"]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
    
    def setDataTypes(self):
        if self.input_ports[0].connection:
            data_type = self.input_ports[0].connection.data_type
            for port in self.output_ports.end_list:
                port.data_type = data_type
        else:
            for port in self.output_ports.end_list:
                port.data_type = "*"
                port.disconnectNodes()
        if not self.GetCanvas().parent.IsShown():
            return
        for port in self.output_ports.end_list:
            port.updateText()
    
    def dumps(self):
        node_xml = Node.dumps(self)
        clone_dic = {"TYPE": str(len(self.output_ports.end_list))}
        con_xml = et.Element("OutputCount", clone_dic)
        node_xml.append(con_xml)
        return node_xml
    
    def loads(self):
        if "OutputCount" in self.additional_attributes:
            count = int(self.additional_attributes["OutputCount"]["TYPE"])
            for port in self.output_ports.end_list:
                port.disconnectNodes()
            self.RemoveChild(self.output_ports)
            self.output_ports.Delete()
            
            labels = ["*"] * count
            self.output_ports = NodeConnections(self.GetCanvas(), labels, self, CONNECTION_OUTPUT)
            self.Show(False)
            x_tmp = self.GetX()
            y_tmp = self.GetY()
            dc = wx.ClientDC(self.GetCanvas())
            self.Move(dc, 0, -10)
            self.SetX(0)
            self.SetY(-10)
            self.output_ports.SetDraggable(False, True)
            self.AddChild(self.output_ports)
            self.AddConstraint(ogl.Constraint(ogl.CONSTRAINT_ALIGNED_RIGHT, self.node_shape, [self.output_ports]))
            if self.node_shape.GetHeight() != self.output_ports.GetHeight() + 3:
                self.node_shape.SetHeight(self.output_ports.GetHeight() + 3)
            self.Recompute()
            self.output_ports.Show(True)
            for port in self.output_ports.end_list:
                port.updateText()
            self.Move(dc, x_tmp, y_tmp)
            self.SetX(x_tmp)
            self.SetY(y_tmp)
            self.Show(True)
            self.GetCanvas().Refresh(False)
    
    def performCalculation(self):
        return [self.input_ports[0].data] * len(self.output_ports.end_list)
    
    def onPopupProperties(self, event):
        dlg = ClonePropertiesDialog(self, -1, "Properties", size=(350, 200), style=wx.DEFAULT_DIALOG_STYLE)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        
        if val == wx.ID_OK:
            for port in self.output_ports.end_list:
                port.disconnectNodes()
            self.RemoveChild(self.output_ports)
            self.output_ports.Delete()
            count = dlg.output_number.GetValue()
            if self.input_ports[0].connection:
                data_type = self.input_ports[0].connection.data_type
            else:
                data_type = "*"
            labels = [data_type] * count
            self.output_ports = NodeConnections(self.GetCanvas(), labels, self, CONNECTION_OUTPUT)
            self.Show(False)
            x_tmp = self.GetX()
            y_tmp = self.GetY()
            dc = wx.ClientDC(self.GetCanvas())
            self.Move(dc, 0, -10)
            self.SetX(0)
            self.SetY(-10)
            self.output_ports.SetDraggable(False, True)
            self.AddChild(self.output_ports)
            self.AddConstraint(ogl.Constraint(ogl.CONSTRAINT_ALIGNED_RIGHT, self.node_shape, [self.output_ports]))
            if self.node_shape.GetHeight() != self.output_ports.GetHeight() + 3:
                self.node_shape.SetHeight(self.output_ports.GetHeight() + 3)
            self.Recompute()
            self.output_ports.Show(True)
            for port in self.output_ports.end_list:
                port.updateText()
            self.Move(dc, x_tmp, y_tmp)
            self.SetX(x_tmp)
            self.SetY(y_tmp)
            self.Show(True)
            self.GetCanvas().Refresh(False)
        
        dlg.Destroy()


class ClonePropertiesDialog(PropertiesDialogDefault):
    
    """ A PropertiesDialogDefault object.
        
        Attributes:
            output_number: A wx.SpinCtrl instance that denotes the number of
                clones.
    """
    def addProperties(self, sizer, parent):
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Output count:", (15, 50), (75, -1))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.output_number = wx.SpinCtrl(self, -1, "", (100, 50))
        self.output_number.SetRange(2, 100)
        self.output_number.SetValue(len(parent.output_ports))
        box.Add(self.output_number, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)


class ComposeXNode(Node):
    
    """A Node object that is used for creating a compose node."""
    def setupNode(self):
        self.label.SetFont(wx.Font(7 ,wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL))
        self.node_shape.SetBrush(wx.Brush((210, 105, 30), wx.SOLID))
        canvas = self.GetCanvas()
        labels = [("F", ":X"), ("F", ":Y"), ("F", ":Z"), ("F", ":W")]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        labels = ["Q"]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.structure_list = ["Quaternion", "Euler", "AxisAngle", "Matrix", "Vector"]
        self.cur_composition = 0
        self.label.AddText("Compose " + self.structure_list[self.cur_composition])
    
    def dumps(self):
        node_xml = Node.dumps(self)
        connection_dic = {"TYPE": self.structure_list[self.cur_composition]}
        con_xml = et.Element("CurrentComposition", connection_dic)
        node_xml.append(con_xml)
        return node_xml
    
    def loads(self):
        self.setType(self.additional_attributes["CurrentComposition"]["TYPE"])
    
    def performCalculation(self):
        in_data = []
        for float_data in self.input_ports:
            in_data.append(float_data.data)
        if in_data:
            if self.cur_composition == 0:
                data = Quaternion(in_data)
                data.normalize()
                return [data]
            elif self.cur_composition == 1:
                data = Euler(in_data, True)
                return [data]
            elif self.cur_composition == 2:
                data = AxisAngle(in_data, True)
                data.normalize()
                return [data]
            elif self.cur_composition == 3:
                data = Matrix3(in_data)
                data.orthonormalize()
                return [data]
            elif self.cur_composition == 4:
                data = Vector3(in_data)
                return [data]
            else:
                raise Exception("Oh my.....the ComposeXNode has failed :(")
    
    def onPopupProperties(self, event):
        dlg = ComposeXPropertiesDialog(self, -1, "Properties", size=(350, 200), style=wx.DEFAULT_DIALOG_STYLE)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        
        if val == wx.ID_OK:
            index = dlg.choice.GetCurrentSelection()
            self.setType(self.structure_list[index])
        
        dlg.Destroy()
    
    def setType(self,string):
        canvas = self.GetCanvas()
        index = self.structure_list.index(string)
        self.cur_composition = index
        self.label.ClearText()
        self.label.AddText("Compose " + self.structure_list[index])
        self.cur_composition = index
        self.output_ports.end_list[0].data_type = self.structure_list[index][0]
        self.output_ports.end_list[0].disconnectNodes()
        self.output_ports.end_list[0].updateText()
        for port in self.input_ports.end_list:
            port.disconnectNodes()
        self.RemoveChild(self.input_ports)
        self.input_ports.Delete()
        if string == "Quaternion":
            labels = [("F", ":X"), ("F", ":Y"), ("F", ":Z"), ("F", ":W")]
        elif string == "AxisAngle":
            labels = [("F", ":X"), ("F", ":Y"), ("F", ":Z"), ("F", ":Angle")]
        elif string == "Euler":
            labels = [("F", ":X DEG"), ("F", ":Y DEG"), ("F", ":Z DEG")]
        elif string == "Vector":
            labels = [("F", ":X"), ("F", ":Y"), ("F", ":Z")]
        elif string == "Matrix":
            labels = [
                ("F", ":R0C0"), ("F", ":R0C1"), ("F", ":R0C2"),
                ("F", ":R1C0"), ("F", ":R1C1"), ("F", ":R1C2"),
                ("F", ":R2C0"), ("F", ":R2C1"), ("F", ":R2C2")
            ]
        else:
            raise Exception("We have failed to change the type for the compose node! The passed in string was: ", string)
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        
        self.Show(False)
        x_tmp = self.GetX()
        y_tmp = self.GetY()
        dc = wx.ClientDC(self.GetCanvas())
        self.Move(dc, 0, -10)
        self.SetX(0)
        self.SetY(-10)
        self.input_ports.SetDraggable(False, True)
        self.AddChild(self.input_ports)
        self.AddConstraint(ogl.Constraint(ogl.CONSTRAINT_ALIGNED_LEFT, self.node_shape, [self.input_ports]))
        if self.node_shape.GetHeight() != self.input_ports.GetHeight() + 3:
            self.node_shape.SetHeight(self.input_ports.GetHeight() + 3)
        self.Recompute()
        self.input_ports.Show(True)
        for port in self.input_ports.end_list:
            port.updateText()
        self.Move(dc, x_tmp, y_tmp)
        self.SetX(x_tmp)
        self.SetY(y_tmp)
        self.Show(True)
        self.GetCanvas().Refresh(False)


class ComposeXPropertiesDialog(PropertiesDialogDefault):
    
    """ A PropertiesDialogDefault object.
        
        Attributes:
            choice: A wx.Choice instance that has a list of possible
                orientations to compose.
    """
    def addProperties(self, sizer, parent):
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Compose:", (15, 50), (75, -1))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.choice = wx.Choice(self, -1, (100, 50), choices=parent.structure_list)
        self.choice.SetSelection(parent.cur_composition)
        box.Add(self.choice, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)


class DecomposeXNode(Node):
    
    """A Node object that is used for creating a decompose node."""
    def setupNode(self):
        self.label.SetFont(wx.Font(7, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL))
        self.node_shape.SetBrush(wx.Brush((210, 105, 30), wx.SOLID))
        canvas = self.GetCanvas()
        labels = ["Q"]
        self.input_ports = NodeConnections(canvas, labels, self,
            CONNECTION_INPUT)
        labels = [("F", "X:"), ("F", "Y:"), ("F", "Z:"), ("F", "W:")]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.structure_list = [
            "Quaternion",
            "Euler[Degrees]",
            "Euler[Radians]",
            "AxisAngle[Degrees]",
            "AxisAngle[Radians]",
            "Matrix",
            "Vector"
        ]
        self.cur_composition = 0
        self.label.AddText("Decompose " + self.structure_list[self.cur_composition])
        self.label.SetHeight(32)
    
    def dumps(self):
        node_xml = Node.dumps(self)
        connection_dic = {"TYPE": self.structure_list[self.cur_composition]}
        con_xml = et.Element("CurrentComposition", connection_dic)
        node_xml.append(con_xml)
        return node_xml
    
    def loads(self):
        self.setType(self.additional_attributes["CurrentComposition"]["TYPE"])
    
    def performCalculation(self):
        in_data = self.input_ports[0].data
        if self.cur_composition == 0:       # "Quaternion"
            return in_data.asArray()
        elif self.cur_composition == 1:     # "Euler[Degrees]"
            return in_data.asDegreeArray()
        elif self.cur_composition == 2:     # "Euler[Radians]"
            return in_data.asRadianArray()
        elif self.cur_composition == 3:     # "AxisAngle[Degrees]"
            return in_data.asDegreeArray()
        elif self.cur_composition == 4:     # "AxisAngle[Radians]"
            return in_data.asRadianArray()
        elif self.cur_composition == 5:     # "Matrix"
            return in_data.asRowArray()
        elif self.cur_composition == 6:     # "Vector"
            return in_data.asArray()
        else:
            raise Exception("Oh my.....the DecomposeXNode has failed :(")
    
    def onPopupProperties(self, event):
        dlg = DecomposeXPropertiesDialog(self, -1, "Properties", size=(350, 200), style=wx.DEFAULT_DIALOG_STYLE)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        
        if val == wx.ID_OK:
            index = dlg.choice.GetCurrentSelection()
            self.setType(self.structure_list[index])
        
        dlg.Destroy()
    
    def setType(self, string):
        canvas = self.GetCanvas()
        index = self.structure_list.index(string)
        self.label.ClearText()
        self.label.AddText("Decompose " + self.structure_list[index])
        self.cur_composition = index
        self.input_ports.end_list[0].data_type = self.structure_list[index][0]
        self.input_ports.end_list[0].disconnectNodes()
        self.input_ports.end_list[0].updateText()
        
        for port in self.output_ports.end_list:
            port.disconnectNodes()
        self.RemoveChild(self.output_ports)
        self.output_ports.Delete()
        if string == "Quaternion":
            labels = [("F", "X:"), ("F", "Y:"), ("F", "Z:"), ("F", "W:")]
        elif string == "AxisAngle[Degrees]" or  string == "AxisAngle[Radians]":
            labels = [("F", "X:"), ("F", "Y:"), ("F", "Z:"), ("F", "Angle:")]
        elif string == "Euler[Degrees]":
            labels = [("F", "DEG X:"), ("F", "DEG Y:"), ("F", "DEG Z:")]
        elif string == "Euler[Radians]":
            labels = [("F", "RAD X:"), ("F", "RAD Y:"), ("F", "RAD Z:")]
        elif string == "Vector":
            labels = [("F", "X:"), ("F", "Y:"), ("F", "Z:")]
        elif string == "Matrix":
            labels = [
                ("F", "R0C0:"), ("F", "R0C1:"), ("F", "R0C2:"),
                ("F", "R1C0:"), ("F", "R1C1:"), ("F", "R1C2:"),
                ("F", "R2C0:"), ("F", "R2C1:"), ("F", "R2C2:")
            ]
        else:
            raise Exception("We have failed to change the type for the decompose node! The passed in string was: ", string)
        
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.Show(False)
        x_tmp = self.GetX()
        y_tmp = self.GetY()
        dc = wx.ClientDC(self.GetCanvas())
        self.Move(dc, 0, -10)
        self.SetX(0)
        self.SetY(-10)
        self.output_ports.SetDraggable(False, True)
        self.AddChild(self.output_ports)
        self.AddConstraint(ogl.Constraint(ogl.CONSTRAINT_ALIGNED_RIGHT, self.node_shape, [self.output_ports]))
        if self.node_shape.GetHeight() != self.output_ports.GetHeight() + 3:
            self.node_shape.SetHeight(self.output_ports.GetHeight() + 3)
        self.Recompute()
        self.output_ports.Show(True)
        for port in self.output_ports.end_list:
            port.updateText()
        self.Move(dc, x_tmp, y_tmp)
        self.SetX(x_tmp)
        self.SetY(y_tmp)
        self.Show(True)
        self.GetCanvas().Refresh(False)
        self.output_ports.SetDraggable(False, True)


class DecomposeXPropertiesDialog(PropertiesDialogDefault):
    
    """ A PropertiesDialogDefault object.
        
        Attributes:
            choice: A wx.Choice instance that has a list of possible
                orientations to decompose.
    """
    def addProperties(self, sizer, parent):
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Decompose:", (15, 50), (75, -1))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.choice = wx.Choice(self, -1, (100, 50), choices=parent.structure_list)
        self.choice.SetSelection(parent.cur_composition)
        box.Add(self.choice, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)


class Degree2RadianNode(Node):
    
    """A Node object that is used for creating a degree to radian node."""
    def setupNode(self):
        self.label.AddText("Degree2RadianNode")
        self.label.SetFont(wx.Font(7, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL))
        self.node_shape.SetBrush(wx.Brush((132, 112, 255), wx.SOLID))
        canvas = self.GetCanvas()
        labels = [("F", ":Deg")]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        labels = [("F", "Rad:")]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
    
    def performCalculation(self):
        in_data = self.input_ports[0].data
        return [math.radians(in_data)]


class Radian2DegreeNode(Node):
    
    """A Node object that is used for creating a radian to degree node."""
    def setupNode(self):
        self.label.AddText("Radian2DegreeNode")
        self.label.SetFont(wx.Font(7, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL))
        self.node_shape.SetBrush(wx.Brush((132, 112, 255), wx.SOLID))
        canvas = self.GetCanvas()
        labels = [("F", ":Rad")]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        labels = [("F", "Deg:")]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
    
    def performCalculation(self):
        in_data = self.input_ports[0].data
        return [math.degrees(in_data)]


class ScaleNode(Node):
    
    """A Node object that is used for creating a scale node."""
    def setupNode(self):
        self.node_shape.SetBrush(wx.Brush("ORANGE RED", wx.SOLID))
        canvas = self.GetCanvas()
        labels = ["F", "F"]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        labels = ["F"]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.structure_list = ["Float", "Vector"]
        self.cur_structure = 0
        self.label.AddText("Scale " + self.structure_list[self.cur_structure])
    
    def dumps(self):
        node_xml = Node.dumps(self)
        connection_dic = {"TYPE": self.structure_list[self.cur_structure]}
        con_xml = et.Element("CurrentStructure", connection_dic)
        node_xml.append(con_xml)
        return node_xml
    
    def loads(self):
        self.setType(self.additional_attributes["CurrentStructure"]["TYPE"])
    
    def performCalculation(self):
        scale_data = self.input_ports[0].data
        in_data = self.input_ports[1].data
        return [in_data * scale_data]
    
    def onPopupProperties(self, event):
        dlg = ScalePropertiesDialog(self, -1, "Properties", size=(350, 200), style=wx.DEFAULT_DIALOG_STYLE)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        
        if val == wx.ID_OK:
            index = dlg.choice.GetCurrentSelection()
            self.setType(self.structure_list[index])
            self.performOperation()
            self.GetCanvas().Refresh(False)
        
        dlg.Destroy()
    
    def setType(self, type_str):
        self.label.ClearText()
        self.cur_structure = self.structure_list.index(type_str)
        self.label.AddText("Scale " + type_str)
        old_data_type = self.input_ports.end_list[0].data_type
        if type_str == "Float":
            self.input_ports.end_list[0].data_type = "F"
            self.output_ports.end_list[0].data_type = "F"
        elif type_str == "Vector":
            self.input_ports.end_list[0].data_type = "V"
            self.output_ports.end_list[0].data_type = "V"
        if old_data_type != self.input_ports.end_list[0].data_type:
            self.input_ports.end_list[0].disconnectNodes()
            self.output_ports.end_list[0].disconnectNodes()
        self.input_ports.end_list[0].updateText()
        self.output_ports.end_list[0].updateText()


class ScalePropertiesDialog(PropertiesDialogDefault):
    
    """ A PropertiesDialogDefault object.
        
        Attributes:
            choice: A wx.Choice instance that has a list of possible objects to
                scale.
    """
    def addProperties(self, sizer, parent):
        box = wx.BoxSizer(wx.HORIZONTAL)
        label =wx.StaticText(self, -1, "Scale Type:", (15, 50), (75, -1))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.choice = wx.Choice(self, -1, (100, 50), choices=parent.structure_list)
        self.choice.SetSelection(parent.cur_structure)
        box.Add(self.choice, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)


class RotationalOffsetNode(Node):
    
    """A Node object that is used for creating a rotational offset node."""
    def setupNode(self):
        self.node_shape.SetBrush(wx.Brush((255, 248, 220), wx.SOLID))
        canvas=self.GetCanvas()
        labels = [("#", ":Indp"), ("#", ":Dep")]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        labels = ["#"]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.structure_list = ["Orientation", "Vector"]
        self.cur_structure = 0
        self.label.SetFont(wx.Font(7, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL))
        self.label.AddText("RotOffset")
        self.label.AddText("[" + self.structure_list[self.cur_structure] + "]")
        self.label.SetHeight(32)
    
    def dumps(self):
        node_xml = Node.dumps(self)
        dic = {"cur_structure":str(self.cur_structure)}
        con_xml = et.Element("RotationalOffset", dic)
        node_xml.append(con_xml)
        return node_xml
    
    def loads(self):
        if "RotationalOffset" in self.additional_attributes:
            data = self.additional_attributes["RotationalOffset"]
            self.cur_structure = int(data["cur_structure"])
            self.label.ClearText()
            self.label.AddText("RotOffset")
            self.label.AddText("[" + self.structure_list[self.cur_structure] + "]")
            if self.cur_structure == 0:
                self.input_ports.end_list[1].data_type = "#"
                self.output_ports.end_list[0].data_type = "#"
            if self.cur_structure == 1:
                self.input_ports.end_list[1].data_type = "V"
                self.output_ports.end_list[0].data_type = "V"
            self.input_ports[0].updateText()
            self.input_ports[1].updateText()
            self.output_ports[0].updateText()
    
    def performCalculation(self):
        offset = self.input_ports[0].data
        in_data = self.input_ports[1].data
        offset_type = type(offset)
        if self.cur_structure == 0:
            if offset_type is Euler:
                offset = offset.toMatrix3('xyz')
            elif offset_type is Quaternion or offset_type is AxisAngle:
                offset = offset.toMatrix3()
            in_data_type = type(in_data)
            if in_data_type is Euler:
                in_data = in_data.toMatrix3('xyz')
                return [(offset * in_data).toEuler('xyz')]
            elif in_data_type is Quaternion:
                in_data = in_data.toMatrix3()
                return [(offset * in_data).toQuaternion()]
            elif in_data_type is AxisAngle:
                in_data = in_data.toMatrix3()
                return [(offset * in_data).toAxisAngle()]
            elif offset_type is Matrix3 or offset_type is Vector3:
                return [offset * in_data]
        if self.cur_structure == 1:
            if offset_type is Euler:
                offset = offset.toMatrix3('xyz')
                return [offset * in_data]
            elif offset_type is Quaternion:
                offset = offset.toMatrix3()
                return [offset * in_data]
            elif offset_type is AxisAngle:
                offset= offset.toMatrix3()
                return [offset * in_data]
            elif offset_type is Matrix3 or offset_type is Vector3:
                return [offset * in_data]
        return [self.cur_structure]
    
    def setDataTypes(self):
        if self.input_ports[0].connection:
            d_type = self.input_ports[0].connection.data_type
            self.input_ports[0].data_type = d_type
        else:
            self.input_ports[0].data_type = "#"
        
        if self.input_ports[1].connection and self.cur_structure == 0:
            d_type = self.input_ports[1].connection.data_type
            self.input_ports[1].data_type = d_type
            self.output_ports[0].data_type = d_type
        elif self.cur_structure == 0:
            self.input_ports[1].data_type = "#"
            self.output_ports[0].data_type = "#"
            self.output_ports[0].disconnectNodes()
        
        self.input_ports[0].updateText()
        self.input_ports[1].updateText()
        self.output_ports[0].updateText()
    
    def onPopupProperties(self, event):
        dlg = RotationalOffsetPropertiesDialog(self, -1, "Properties", size=(350, 200), style=wx.DEFAULT_DIALOG_STYLE)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        
        if val == wx.ID_OK:
            index = dlg.choice.GetCurrentSelection()
            prev_structure=self.cur_structure
            self.cur_structure = index
            self.label.ClearText()
            self.label.AddText("RotOffset")
            self.label.AddText("[" + self.structure_list[self.cur_structure] + "]")
            if prev_structure != self.cur_structure:
                if self.cur_structure == 0:
                    self.input_ports.end_list[1].data_type = "#"
                    self.output_ports.end_list[0].data_type = "#"
                    self.output_ports.end_list[0].disconnectNodes()
                    self.input_ports.end_list[1].disconnectNodes()
                if self.cur_structure == 1:
                    self.input_ports.end_list[1].data_type = "V"
                    self.output_ports.end_list[0].data_type = "V"
                    self.output_ports.end_list[0].disconnectNodes()
                    self.input_ports.end_list[1].disconnectNodes()
                
                self.input_ports.end_list[0].updateText()
                self.input_ports.end_list[1].updateText()
                self.output_ports.end_list[0].updateText()
            
            self.performOperation()
            self.GetCanvas().Refresh(False)
        
        dlg.Destroy()


class RotationalOffsetPropertiesDialog(PropertiesDialogDefault):
    
    """ A PropertiesDialogDefault object.
        
        Attributes:
            choice: A wx.Choice instance that has a list of possible matrices to
                calculate the rotational offset.
    """
    def addProperties(self, sizer, parent):
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Matrix Type:", (15, 50), (75, -1))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.choice = wx.Choice(self, -1, (100, 50), choices=parent.structure_list)
        self.choice.SetSelection(parent.cur_structure)
        box.Add(self.choice, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)


class DifferanceAngleQuatNode(Node):
    
    """ A Node object that is used for creating a difference angle quaternion
        node.
    """
    def setupNode(self):
        self.node_shape.SetBrush(wx.Brush("SEA GREEN", wx.SOLID))
        canvas = self.GetCanvas()
        labels = ["Q", "Q"]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        labels = [("F", "Rad")]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.label.SetFont(wx.Font(7, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL))
        self.label.AddText("Differance AngleQuat")
    
    def performCalculation(self):
        quat1 = self.input_ports[0].data
        quat2 = self.input_ports[1].data
        quat1.normalize()
        quat2.normalize()
        tmp_dot = quat1.dot(quat2)
        tmp_dot = max(min(tmp_dot, 1.0), -1.0)
        angle = math.acos(tmp_dot) * 2.0
        if angle > math.pi:
            angle = math.pi - (angle - math.pi)
        return [angle]


class DifferanceOrientNode(Node):
    
    """A Node object that is used for creating a difference angle node."""
    def setupNode(self):
        self.node_shape.SetBrush(wx.Brush("SEA GREEN", wx.SOLID))
        canvas = self.GetCanvas()
        labels = ["#", "#"]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        labels = [("Q","Quat:")]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.label.SetFont(wx.Font(7, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL))
        self.label.AddText("Differance Orient")
    
    def performCalculation(self):
        mat1 = self.input_ports[0].data
        mat2 = self.input_ports[1].data
        if not type(mat1) is Matrix3:
            mat1 = mat1.toMatrix3()
        if not type(mat2) is Matrix3:
            mat2 = mat2.toMatrix3()
        
        mat3 = -mat1 * mat2
        
        return [mat3.toQuaternion()]


class DotProductNode(Node):
    
    """ A Node object that is used for calculating the dot product between two
        vectors.
    """
    def setupNode(self):
        self.node_shape.SetBrush(wx.Brush("SEA GREEN", wx.SOLID))
        canvas = self.GetCanvas()
        labels = [("V", ":Left"), ("V", ":Right")]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        labels = [("F","Prod:")]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.label.SetFont(wx.Font(7, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL))
        self.label.AddText("Dot Product")
    
    def performCalculation(self):
        vec1 = self.input_ports[0].data
        vec2 = self.input_ports[1].data
        
        prod = vec1.dot(vec2)
        
        return [prod]


class CrossProductNode(Node):
    
    """ A Node object that is used for calculating the cross product between two
        vectors.
    """
    def setupNode(self):
        self.node_shape.SetBrush(wx.Brush("SEA GREEN", wx.SOLID))
        canvas = self.GetCanvas()
        labels = [("V", ":Left"), ("V", ":Right")]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        labels = [("V","Prod:")]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.label.SetFont(wx.Font(7, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL))
        self.label.AddText("Cross Product")
    
    def performCalculation(self):
        vec1 = self.input_ports[0].data
        vec2 = self.input_ports[1].data
        
        prod = vec1.cross(vec2)
        
        return [prod]


class AngleBetweenNode(Node):
    
    """ A Node object that is used for calculating the angle between two
        vectors.
    """
    def setupNode(self):
        self.node_shape.SetBrush(wx.Brush("SEA GREEN", wx.SOLID))
        canvas = self.GetCanvas()
        labels = [("V", ":Left"), ("V", ":Right")]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        labels = [("F","Angle:")]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.label.SetFont(wx.Font(7, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL))
        self.label.AddText("Angle Between")
    
    def performCalculation(self):
        vec1 = self.input_ports[0].data.normalizeCopy()
        vec2 = self.input_ports[1].data.normalizeCopy()
        
        dot_prod = vec1.dot(vec2)
        angle = math.degrees(math.acos(dot_prod))
        
        return [angle]


class NormalizeVectorNode(Node):
    
    """ A Node object that is used for calculating the normalized form of the
        input vector.
    """
    def setupNode(self):
        self.node_shape.SetBrush(wx.Brush("SEA GREEN", wx.SOLID))
        canvas = self.GetCanvas()
        labels = ["V"]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        labels = ["V"]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.label.SetFont(wx.Font(7, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL))
        self.label.AddText("Normalize")
    
    def performCalculation(self):
        vec1 = self.input_ports[0].data
        
        return [vec1.normalizeCopy()]


class MultiplyRotationNode(Node):
    
    """ A Node object that is used for multiplying two rotation structures
        together.
    """
    def setupNode(self):
        self.node_shape.SetBrush(wx.Brush("SEA GREEN", wx.SOLID))
        canvas = self.GetCanvas()
        labels = [("#", ":Left"), ("#", ":Right")]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        labels = [("#", "Prod:")]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.structure_list = ["Quaternion", "Matrix", "Axis Angle", "Euler"]
        self.cur_structure = 0
        self.label.SetFont(wx.Font(7, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL))
        self.label.AddText("Multiply Rotation")
        self.label.AddText("[" + self.structure_list[self.cur_structure] + "]")
        self.label.SetHeight(32)
    
    def performCalculation(self):
        rot1 = self.input_ports[0].data
        rot2 = self.input_ports[1].data
        
        rot1_type = type(rot1)
        if rot1_type is Euler:
            rot1 = rot1.toMatrix3('xyz')
        elif rot1_type is Quaternion or rot1_type is AxisAngle:
            rot1 = rot1.toMatrix3()
        
        rot2_type = type(rot2)
        if rot2_type is Euler:
            rot2 = rot2.toMatrix3('xyz')
        elif rot2_type is Quaternion or rot2_type is AxisAngle:
            rot2 = rot2.toMatrix3()
        
        prod = rot1 * rot2
        cur_mode = self.structure_list[self.cur_structure]
        if cur_mode == "Quaternion":
            prod = prod.toQuaternion()
        elif cur_mode == "Axis Angle":
            prod = prod.toAxisAngle()
        elif cur_mode == "Euler":
            prod = prod.toEuler()
        
        return [prod]
    
    def setDataTypes(self):
        if self.input_ports[0].connection:
            d_type = self.input_ports[0].connection.data_type
            self.input_ports[0].data_type = d_type
        else:
            self.input_ports[0].data_type = "#"
        
        if self.input_ports[1].connection:
            d_type = self.input_ports[1].connection.data_type
            self.input_ports[1].data_type = d_type
        else:
            self.input_ports[1].data_type = "#"
        
        if self.cur_structure == 0:
            self.output_ports[0].data_type = "Q"
        elif self.cur_structure == 1:
            self.output_ports[0].data_type = "M"
        elif self.cur_structure == 2:
            self.output_ports[0].data_type = "A"
        elif self.cur_structure == 3:
            self.output_ports[0].data_type = "E"
        
        self.input_ports[0].updateText()
        self.input_ports[1].updateText()
        self.output_ports[0].updateText()
    
    def onPopupProperties(self, event):
        dlg = MultiplyRotationPropertiesDialog(self, -1, "Properties", size=(350, 200), style=wx.DEFAULT_DIALOG_STYLE)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        
        if val == wx.ID_OK:
            index = dlg.choice.GetCurrentSelection()
            prev_structure=self.cur_structure
            self.cur_structure = index
            self.label.ClearText()
            self.label.AddText("Multiply Rotation")
            self.label.AddText("[" + self.structure_list[self.cur_structure] + "]")
            if prev_structure != self.cur_structure:
                self.input_ports.end_list[1].data_type = "#"
                self.output_ports.end_list[0].data_type = "#"
                self.output_ports.end_list[0].disconnectNodes()
                self.input_ports.end_list[1].disconnectNodes()
                
                self.input_ports.end_list[0].updateText()
                self.input_ports.end_list[1].updateText()
                self.output_ports.end_list[0].updateText()
            
            self.performOperation()
            self.GetCanvas().Refresh(False)
        
        dlg.Destroy()


class MultiplyRotationPropertiesDialog(PropertiesDialogDefault):
    
    """ A PropertiesDialogDefault object.
        
        Attributes:
            choice: A wx.Choice instance that has a list of possible matrices to
                calculate the rotational offset.
    """
    def addProperties(self, sizer, parent):
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Rotation Type:", (15, 50), (75, -1))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.choice = wx.Choice(self, -1, (100, 50), choices=parent.structure_list)
        self.choice.SetSelection(parent.cur_structure)
        box.Add(self.choice, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)


class SumVectorNode(Node):
    
    """ A Node object that is used for calculating the normalized form of the
        input vector.
    """
    def setupNode(self):
        self.node_shape.SetBrush(wx.Brush("SEA GREEN", wx.SOLID))
        canvas = self.GetCanvas()
        labels = ["V", "V"]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        labels = ["V"]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.label.SetFont(wx.Font(7, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL))
        self.label.AddText("Sum Vectors")
    
    def performCalculation(self):
        vec1 = self.input_ports[0].data
        vec2 = self.input_ports[1].data
        
        sum_vec = vec1 + vec2
        
        return [sum_vec]


class InterpolationNode(Node):
    
    """ A Node object that is used for interpolating between two quaternion
        structures.
    """
    def setupNode(self):
        self.node_shape.SetBrush(wx.Brush((99, 184, 255), wx.SOLID))
        canvas = self.GetCanvas()
        labels = ["Q", "Q"]
        self.input_ports = NodeConnections(canvas, labels, self, CONNECTION_INPUT)
        labels = ["Q"]
        self.output_ports = NodeConnections(canvas, labels, self, CONNECTION_OUTPUT)
        self.label.AddText("Interpolation")
        self.percentage = 0.0
    
    def dumps(self):
        node_xml = Node.dumps(self)
        connection_dic = {"F": str(self.percentage)}
        con_xml = et.Element("PercentageData", connection_dic)
        node_xml.append(con_xml)
        return node_xml
    
    def loads(self):
        data = self.additional_attributes["PercentageData"]
        self.percentage = float(data["F"])
    
    def performCalculation(self):
        quat1 = self.input_ports[0].data
        quat2 = self.input_ports[1].data
        
        prod = quat1.slerp(quat2, self.percentage)
        
        return [prod]
    
    def onPopupProperties(self, event):
        dlg = InterpolationPropertiesDialog(self, -1, "Properties", size=(350, 200), style=wx.DEFAULT_DIALOG_STYLE)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        
        if val == wx.ID_OK:
            self.percentage = dlg.percentage.GetValue()
            self.performOperation()
            self.GetCanvas().Refresh(False)
        
        dlg.Destroy()


class InterpolationPropertiesDialog(PropertiesDialogDefault):
    
    """ A PropertiesDialogDefault object.
        
        Attributes:
            choice: A wx.FloatSpin instance that denotes the percentage of
                interpolation.
    """
    def addProperties(self, sizer, parent):
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Percentage:", (15, 50), (75, -1))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.percentage = float_spin.FloatSpin(self, -1, size=(75, -1), value=parent.percentage, min_val=0.0, max_val=1.0, increment=0.1, digits=4)
        box.Add(self.percentage, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)


### Helper Functions ###
def pollLastSteamData():
    global global_poll_map
    if len(global_sensor_filter) == 0:
        for id in global_sensor_list:
            global_poll_map[id] = global_sensor_list[id].stream_last_data
    else:
        for sensor in global_sensor_filter:
            global_poll_map[sensor.serial_number] = sensor.stream_last_data


def refreshOutputs(event=None):
    """ Updates a list of Node objects that output to the screen.
        
        Args:
            event: A wxPython event (default is None).
    """
    global global_manual_refresh
    global_manual_refresh = True
    pollLastSteamData()
    for node in global_input_nodes:
        node.performOperation()
    for node in global_static_nodes:
        node.performOperation()
    global_manual_refresh = False
    global_side_panel.updatePanel()


def refreshOutputsRec():
    """ Updates a list of Node objects that output to the screen.
        
        Used for when the Mocap Studio is recording data.
    """
    pollLastSteamData()
    for node in global_input_nodes:
        node.performOperation()
    for node in global_static_nodes:
        node.performOperation()


def tareAll(event=None):
    """ Tares all the 3-Space Sensors that are currently being for output data.
        
        Args:
            event: A wxPython event (default is None).
    """
    did_tare = True
    is_stream = False
    cancelled = False
    all_yei = global_sensor_list.values()
    if len(all_yei) == 0:
        return False
    
    if global_poll_bool:
        is_stream = True
        stopStream()
    else:
        side_timer_interval = global_side_panel.update_timer.GetInterval()
        global_side_panel.update_timer.Stop()
    message = "Warning!!!\n\tAbout to tare all sensors."
    caption = "Taring all sensors"
    if wx.MessageBox(message, caption, wx.OK | wx.CANCEL) == wx.OK:
        for yei_prod in all_yei:
            tries = 0
            while(tries < 3 and not yei_prod.tareWithCurrentOrientation()):
                tries += 1
                print "Tare failed tries:", tries
            if tries > 3:
                did_tare = False
    else:
        cancelled = True
        did_tare = False
    
    if is_stream:
        startStream(global_stream_wait, global_sensor_filter)
    else:
        global_side_panel.update_timer.Start(side_timer_interval)
        global_side_panel.updatePanel()
    
    if event is not None and not did_tare and not cancelled:
        message = "Tare failed, check sensors and try again"
        caption = "Taring failed"
        wx.MessageBox(message, caption, wx.OK)
    return did_tare


def setStreamingProperties(interval, duration, delay, offset, func_list, callback):
    global global_sensor_filter
    sensor_filter = global_sensor_filter[:]
    failed_list = []
    time_dict = ts_api.global_broadcaster.setStreamingTiming(interval, duration, delay, offset, sensor_filter, callback)
    for sensor in time_dict:
        if not time_dict[sensor]:
            failed_list.append(sensor)
    while len(failed_list) > 0:
        for i in range(len(global_sensor_filter) - 1, -1, -1):
            if global_sensor_filter[i] in failed_list:
                del global_sensor_filter[i]
        message = (
            "Failed to Set Streaming Timing, possible reasons:\n"
            "\tA wired sensor(s) is not plugged in\n"
            "\tA wireless sensor(s) is not turned on\n"
            "\tA wireless sensor(s) is out of range\n"
            "\tA dongle is not plugged in\n"
        )
        caption = "Streaming Timing Failure"
        wx.MessageBox(message, caption, wx.OK | wx.ICON_ERROR)
        failed_name_list = [sens.device_type + '-' + sens.serial_number_hex for sens in failed_list]
        dlg = wx.MultiChoiceDialog(None, "Pick sensors to retry.", "Failed Streaming Timing List", failed_name_list)
        dlg.SetSelections(range(len(failed_name_list)))
        
        if(dlg.ShowModal() == wx.ID_OK):
            sensor_filter = [failed_list[i] for i in dlg.GetSelections()]
            global_sensor_filter += sensor_filter[:]
            
            failed_list = []
            time_dict = ts_api.global_broadcaster.setStreamingTiming(interval, duration, delay, offset, sensor_filter, callback)
            for sensor in time_dict:
                if not time_dict[sensor]:
                    failed_list.append(sensor)
        else:
            failed_list = []
        dlg.Destroy()
    
    sensor_filter = global_sensor_filter[:]
    
    failed_list = []
    slot_dict = ts_api.global_broadcaster.setStreamingSlots(*func_list, filter=sensor_filter, callback_func=callback)
    for sensor in slot_dict:
        if not slot_dict[sensor]:
            failed_list.append(sensor)
    while len(failed_list) > 0:
        for i in range(len(global_sensor_filter) - 1, -1, -1):
            if global_sensor_filter[i] in failed_list:
                del global_sensor_filter[i]
        message = (
            "Failed to Set Streaming Slots, possible reasons:\n"
            "\tA wired sensor(s) is not plugged in\n"
            "\tA wireless sensor(s) is not turned on\n"
            "\tA wireless sensor(s) is out of range\n"
            "\tA dongle is not plugged in\n"
        )
        caption = "Streaming Slots Failure"
        wx.MessageBox(message, caption, wx.OK | wx.ICON_ERROR)
        failed_name_list = [sens.device_type + '-' + sens.serial_number_hex for sens in failed_list]
        dlg = wx.MultiChoiceDialog(None, "Pick sensors to retry.", "Failed Streaming Slots List", failed_name_list)
        dlg.SetSelections(range(len(failed_name_list)))
        
        if(dlg.ShowModal() == wx.ID_OK):
            sensor_filter = [failed_list[i] for i in dlg.GetSelections()]
            global_sensor_filter += sensor_filter[:]
            
            failed_list = []
            slot_dict = ts_api.global_broadcaster.setStreamingSlots(*func_list, filter=sensor_filter, callback_func=callback)
            for sensor in slot_dict:
                if not slot_dict[sensor]:
                    failed_list.append(sensor)
        else:
            failed_list = []
        dlg.Destroy()


def startStream(interval=None, sensor_filter=None, callback=None):
    """ Starts the streaming of data.
        
        Args:
            interval: An integer denoting wait time in milliseconds
                (default is None).
            sensor_filter: A list of 3-Space Sensors' serial numbers that will
                be used to start streaming. If None, all 3-Space Sensors
                connected to the host computer are used. (default is None).
            callback: A function reference to be used when starting a streaming
                session.
    """
    global global_stream_wait, global_sensor_filter
    if interval is not None:
        global_stream_wait = interval
    else:
        global_stream_wait = 15
    print 'starting stream'
    
    # Do 3-Space Sensors
    if sensor_filter is not None:
        global_sensor_filter = sensor_filter[:]
    else:
        global_sensor_filter = global_sensor_list.values()
    
    setStreamingProperties(global_stream_wait, 0xffffffff, 1000000, 0, ['getTaredOrientationAsQuaternion'], callback)
    
    stream_dict = ts_api.global_broadcaster.startStreaming(filter=global_sensor_filter, callback_func=callback)
    failed_list = []
    for sensor in stream_dict:
        if not stream_dict[sensor]:
            failed_list.append(sensor)
    while len(failed_list) > 0:
        for i in range(len(global_sensor_filter) - 1, -1, -1):
            if global_sensor_filter[i] in failed_list:
                del global_sensor_filter[i]
        message = (
            "Streaming Failed to Start, possible reasons:\n"
            "\tWait is set too low use higher value\n"
            "\tThere is too much wireless contention\n"
            "\tA wireless sensor(s) is out of range\n"
        )
        caption = "Streaming Start Failure"
        wx.MessageBox(message, caption, wx.OK | wx.ICON_ERROR)
        failed_name_list = [sens.device_type + '-' + sens.serial_number_hex for sens in failed_list]
        dlg = wx.MultiChoiceDialog(None, "Pick sensors to retry.", "Failed Streaming Sensor List", failed_name_list)
        dlg.SetSelections(range(len(failed_name_list)))
        
        if(dlg.ShowModal() == wx.ID_OK):
            sensor_filter = [failed_list[i] for i in dlg.GetSelections()]
            global_sensor_filter += sensor_filter[:]
            
            failed_list = []
            stream_dict = ts_api.global_broadcaster.startStreaming(filter=sensor_filter, callback_func=callback)
            for sensor in stream_dict:
                if not stream_dict[sensor]:
                    failed_list.append(sensor)
        else:
            failed_list = []
        dlg.Destroy()
    
    # Start updating
    if len(global_sensor_filter) > 0:
        print 'started stream'
        print 'polling'
        pollLastSteamData()
        if global_side_panel.parent.GetParent() is not None:
            print 'starting timer'
            if global_timer_interval:
                global_side_panel.update_timer.Start(global_timer_interval)
            else:
                global_side_panel.update_timer.Start()
        global_side_panel.status.SetLabel("ON")
        pollToggle()
        return True
    return False


def stopStream():
    """Stops the streaming of data."""
    global global_timer_interval, global_sensor_filter
    print 'stopping stream'
    
    # Do 3-Space Sensors
    stop_dict = ts_api.global_broadcaster.stopStreaming(global_sensor_filter)
    failed_list = []
    for sensor in stop_dict:
        if not stop_dict[sensor]:
            failed_list.append(sensor)
    if len(failed_list) > 0:
        if global_side_panel.parent.GetParent() is not None:
            global_timer_interval = global_side_panel.update_timer.GetInterval()
            global_side_panel.update_timer.Stop()
    while len(failed_list) > 0:
        for i in range(len(global_sensor_filter) - 1, -1, -1):
            if global_sensor_filter[i] not in failed_list:
                del global_sensor_filter[i]
        message = (
            "Streaming Failed to Stop, possible reasons:\n"
            "\tThere is too much wireless contention\n"
            "\tA wireless sensor(s) is out of range\n"
        )
        caption = "Streaming Stop Failure"
        wx.MessageBox(message, caption, wx.OK | wx.ICON_ERROR)
        
        message = "Try stopping Streaming again?"
        caption = "Stop Streaming"
        val = wx.MessageBox(message, caption, wx.OK | wx.CANCEL)
        if val == wx.OK:
            stop_dict = ts_api.global_broadcaster.stopStreaming(global_sensor_filter)
            failed_list = []
            for sensor in stop_dict:
                if not stop_dict[sensor]:
                    failed_list.append(sensor)
        else:
            if global_side_panel.parent.GetParent() is not None:
                global_side_panel.update_timer.Start(global_timer_interval)
            return False
    
    print 'stopped stream'
    global_side_panel.status.SetLabel("OFF")
    pollToggle()
    return True


def startRec():
    print 'start recording'
    # Do 3-Space Sensors
    ts_api.global_broadcaster.startRecordingData(global_sensor_filter)


def stopRec():
    print 'stop recording'
    # Do 3-Space Sensors
    ts_api.global_broadcaster.stopRecordingData(global_sensor_filter)


def pollRefreshOutputs(event=None):
    """ Updates a list of Node objects that output to the screen.
        
        Args:
            event: A wxPython event (default is None).
    """
    if global_poll_bool:
        refreshOutputs()
    else:
        if global_side_panel.parent.GetParent() is None:
            refreshOutputs()


def pollToggle(event=None):
    """ Toggles the wx.CheckBox created in the node_graph.py SidePanel for
        polling data.
        
        Args:
            event: A wxPython event (default is None).
    """
    global global_poll_bool
    global_poll_bool = not global_poll_bool


def nameCheck(name, num=0):
    """ A function that checks if a name is already being used.
        
        Appends a number to the name if already exisits.
        Args:
            name: A string denoting a name of some VirtualSensorNode.
            num: An integer denoting the number of instances of that name
                (default is 0)
    """
    for output in global_output_nodes:
        if type(output) is VirtualSensorNode:
            if num == 0 and name == output.name:
                num += 1
                return nameCheck(name, num)
            if name + '-' + str(num) == output.name:
                num += 1
                return nameCheck(name, num)
    if num == 0:
        return name
    return name + '-' + str(num)


def initBaseScript():
    """Initializes the creation of Dongle objects and Sensor objects."""
    if "-noukn" in sys.argv:
        sc.global_check_unknown = False
    
    dlg = sc.ProgressSensorsAndDongles()
    
    # Do 3-Space Sensors
    dlg.searchSensorsAndDongles()
    if len(global_dongle_list) > 0:
        count = 0
        dlg.setValue(count)
        dlg.SetTitle("Checking TSDongles' Logical ID Table...")
        dlg.setRange(len(global_dongle_list) * 15)
        for dongle in global_dongle_list.values():
            for i in range(15):
                count += 1
                wl_id = dongle.getSerialNumberAtLogicalID(i)
                wl_id_hex = '{0:08X}'.format(wl_id)
                if wl_id != 0:
                    wireless = dongle.setSensorToDongle(i, wl_id)
                    if wireless is None:
                        print "Failed to find", wl_id_hex
                        continue
                    
                    if not wireless.switchToWiredMode():
                        wireless.switchToWirelessMode()
                    if not wireless.isConnected():
                        print "Failed to add", wl_id_hex
                    else:
                        print "Created TSWLSensor Wireless Serial:",
                        print wl_id_hex, "Firmware Date:",
                        print wireless.getFirmwareVersionString()
                dlg.setValue(count)
    
    pollLastSteamData()
    dlg.Destroy()
    
    if sc.global_check_unknown and len(sc.global_unknown_list) > 0:
        dlg = sc.UnknownPortDialog()
        dlg.CenterOnScreen()
        dlg.ShowModal()
        dlg.Destroy()


if __name__ == "__main__":
    # from multiprocessing import freeze_support
    # freeze_support()
    ## Main Code
    # Create an "Application" (initializes the WX system)
    app = wx.PySimpleApp()
    
    # Check for 3 Space Sensors and Dongles
    initBaseScript()
    import node_graph as ng
    # Create a frame for use in our application
    frame = ng.MainWindow()
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



