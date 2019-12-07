#!/usr/bin/env python2.7

"""Finds and configures Three Space Sensors and Dongles for the Mocap Studio."""


import os
import sys
_dir_path = os.getcwd()
_idx = _dir_path.rfind("\\")

import wx
import wx.lib.agw.floatspin as float_spin
import wx.lib.colourselect as colour_sel
from wx import glcanvas
import threading
import time
import struct

import gl_scene_graph as gl_sg
from math_lib import *
sys.path.insert(0, os.path.join(_dir_path[:_idx], "3SpaceAPI\\stable"))
import threespace_api as ts_api


## Static Globals ##
SENS_CONF_SIZE = (702, 565)
AXIS_DIR_MAP = {}


### Globals ###
global_sensor_list = ts_api.global_sensorlist
global_dongle_list = ts_api.global_donglist
global_unknown_list = {}
global_draw_lock = threading.Lock()
global_check_unknown = True
global_updated_sensors = False


### Classes ###
### wxGLCanvas ###
class SensorCanvas(glcanvas.GLCanvas):
    
    """ A wxPython GLCanvas that creates the OpenGL world for OpenGL objects to
        be drawn.
        
        Attributes:
            __init: A boolean that indicates whether or not it has been
                initialized.
            axis_dir_data: A list that denotes the Axis Directions of a 3-Space
                Sensor device.
            is_orient: A boolean that indicates wheter or not the user is
                orientating the SensorMeshNode for placement calibratation.
            mask: A flag denoting what is to be masked when drawing.
            root_node: A reference to a GlBackground object.
            sensor_node: A reference to a SensorMeshNode object.
            transform_node: A reference to a TransformMatrixNode object.
            x_sensor_node: A reference to a SensorAxisNode object.
            y_sensor_node: A reference to a SensorAxisNode object.
            z_sensor_node: A reference to a SensorAxisNode object.
    """
    global global_draw_lock
    def __init__(self, parent, canvas_size):
        """ Initializes the SensorCanvas class.
            
            Args:
                parent: A reference to another wxPython class.
                canvas_size: A tuple that stores a width and height.
        """
        glcanvas.GLCanvas.__init__(self, parent, -1, size=canvas_size)
        self.__init = False
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.onEraseBackground)
        self.Bind(wx.EVT_PAINT, self.onPaint)
        
        self.mask = gl_sg.DRAW_ALL
        self.root_node = gl_sg.GlBackground()
        self.transform_node = self.root_node.appendChild(
            gl_sg.TransformMatrixNode([
                1, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, 1, 0,
                0, 0, -125, 1
            ])
        )
        self.sensor_node = self.transform_node.appendChild(gl_sg.SensorMeshNode("whole_wireless_case_model_low_poly.obj"))
        self.x_sensor_node = self.sensor_node.appendChild(gl_sg.SensorAxisNode(gl_sg.DRAW_ARROW_X))
        self.y_sensor_node = self.sensor_node.appendChild(gl_sg.SensorAxisNode(gl_sg.DRAW_ARROW_Y))
        self.z_sensor_node = self.sensor_node.appendChild(gl_sg.SensorAxisNode(gl_sg.DRAW_ARROW_Z))
        self.axis_dir_data = None
        self.is_orient = False
    
    def onEraseBackground(self, event):
        """ Does nothing, but help to avoid flashing on MSW.
            
            Args:
                event: A wxPython event.
        """
        pass
    
    def onPaint(self, event):
        """ Renders the scene to the screen.
            
            Args:
                event: A wxPython event.
        """
        global_draw_lock.acquire()
        dc = wx.PaintDC(self)
        self.SetCurrent()
        if not self.__init:
            self.initGL()
            self.__init = True
        self.onDraw()
        global_draw_lock.release()
    
    def initGL(self):
        """Initializes the OpenGL world."""
        gl_sg.glMatrixMode(gl_sg.GL_PROJECTION)
        gl_sg.glMaterial(gl_sg.GL_FRONT, gl_sg.GL_AMBIENT, [0.2, 0.2, 0.2, 1])
        gl_sg.glMaterial(gl_sg.GL_FRONT, gl_sg.GL_DIFFUSE, [1, 1, 1, 1])
        gl_sg.glMaterial(gl_sg.GL_FRONT, gl_sg.GL_SPECULAR, [1, 1, 1, 1])
        gl_sg.glMaterial(gl_sg.GL_FRONT, gl_sg.GL_SHININESS, 10)
        gl_sg.glLight(gl_sg.GL_LIGHT0, gl_sg.GL_AMBIENT, [1, 1, 1, 1])
        gl_sg.glLight(gl_sg.GL_LIGHT0, gl_sg.GL_DIFFUSE, [1, 1, 1, 1])
        gl_sg.glLight(gl_sg.GL_LIGHT0, gl_sg.GL_SPECULAR, [1, 1, 1, 1])
        gl_sg.glLight(gl_sg.GL_LIGHT0, gl_sg.GL_POSITION, [1, 1, 1, 0])
        gl_sg.glLightModelfv(gl_sg.GL_LIGHT_MODEL_AMBIENT, [0.2, 0.2, 0.2, 1])
        gl_sg.glEnable(gl_sg.GL_NORMALIZE)
        gl_sg.glEnable(gl_sg.GL_LIGHTING)
        gl_sg.glEnable(gl_sg.GL_LIGHT0)
        gl_sg.glDepthFunc(gl_sg.GL_LESS)
        gl_sg.glEnable(gl_sg.GL_DEPTH_TEST)
        gl_sg.glLoadIdentity()
        width, height = self.GetClientSize()
        gl_sg.gluPerspective(45.0, (width * 1.0) / height, 0.1, 300.0)
        gl_sg.glClear(gl_sg.GL_COLOR_BUFFER_BIT | gl_sg.GL_DEPTH_BUFFER_BIT)
        gl_sg.glMatrixMode(gl_sg.GL_MODELVIEW)
        
        # Initialize glut
        gl_sg.glutInit(sys.argv)
        
        if gl_sg.global_gl_version_list is None:
            # Check for the version
            gl_sg.getGLVersion()
    
    def setSensor(self, sensor=None, mode=False, orient=None):
        """ Sets a reference to a 3-Space Sensor device so that the GLCanvas can
            show the sensor mesh rotating.
            
            Args:
                sensor: A reference to a TSSensor object. (default is None)
                mode: A boolean that indicates a mode for the GLCanvas.
                    (default is False)
                orient: A 4x4 Matrix orientation to be used as the initial
                    orientation. (default is None)
        """
        self.sensor_node.ts_sensor = sensor
        self.sensor_node.interactive_mode = mode
        if orient is not None:
            self.sensor_node.orient = orient
        else:
            self.sensor_node.orient = Matrix4().asColArray()
        if sensor is None:
            self.axis_dir_data = None
        else:
            self.axis_dir_data = sensor.getAxisDirections()
    
    def onDraw(self):
        """Draws the scene in the OpenGL world."""
        # Clear color and depth buffers
        gl_sg.glClear(gl_sg.GL_COLOR_BUFFER_BIT | gl_sg.GL_DEPTH_BUFFER_BIT)
        
        # Draw Our SceneGraph
        self.root_node.draw(self.mask)
        
        # Update our sensor mesh
        if self.sensor_node.ts_sensor is not None and not self.is_orient:
            # Get quaternion orientation data from sensor
            tared_orient = self.sensor_node.ts_sensor.getTaredOrientationAsQuaternion()
            if tared_orient is None or self.axis_dir_data is None:
                # No orientation!
                pass
            else:
                # Read axis directions and manipulate the quaternion data to
                # have the sensor mesh match the 3-Space Sensor device's
                # orientation after being tared pointing towards the screen.
                tared_orient = list(tared_orient)
                
                for f in AXIS_DIR_MAP[8][self.axis_dir_data]:
                    f(tared_orient)
                
                # Update orientation based on sensor data
                tmp_orient = (Quaternion(tared_orient).toMatrix4()).asColArray()
                self.sensor_node.sensor_orient = tmp_orient
        elif self.is_orient:
            pass
        else:
            gl_sg.glDisable(gl_sg.GL_DEPTH_TEST)
            gl_sg.glDisable(gl_sg.GL_LIGHTING)
            gl_sg.glEnable(gl_sg.GL_BLEND)
            gl_sg.glBlendFunc(gl_sg.GL_SRC_ALPHA, gl_sg.GL_ONE_MINUS_SRC_ALPHA)
            gl_sg.glMatrixMode(gl_sg.GL_PROJECTION)
            gl_sg.glPushMatrix()
            gl_sg.glLoadIdentity()
            gl_sg.glTranslated(0.0, 0.0, -1.0)
            gl_sg.glBegin(gl_sg.GL_QUADS)
            gl_sg.glColor4f(0.4, 0.4, 0.4, 0.6)
            gl_sg.glVertex2f(-1.0, 1.0)
            gl_sg.glVertex2f(-1.0, -1.0)
            gl_sg.glVertex2f(1.0, -1.0)
            gl_sg.glVertex2f(1.0, 1.0)
            gl_sg.glEnd()
            gl_sg.glPopMatrix()
            gl_sg.glMatrixMode(gl_sg.GL_MODELVIEW)
            gl_sg.glDisable(gl_sg.GL_BLEND)
            gl_sg.glEnable(gl_sg.GL_LIGHTING)
            gl_sg.glEnable(gl_sg.GL_DEPTH_TEST)
        
        # Push into visible buffer
        self.SwapBuffers()


### wxPanel ###
class InfoAxisPanel(wx.Panel):
    
    """ A wxPython Panel object.
        
        Attributes:
            apply_button: A wx.Button instance used to apply the updated
                settings to the selected sensor.
            axis_sel: A wx.Choice instance that indicates axis directions of the
                selected sensor.
            channel: A wx.Choice instance that denotes the wireless channel
                of the selected sensor, if available.
            commit_button: A wx.Button instance used to apply and commit the
                updated settings to the selected sensor.
            is_axis_update: A boolean that denotes if the axis directions on the
                selected sensor needs updated.
            is_chan_update: A boolean that denotes if the wireless channel on
                the selected sensor needs updated.
            is_pan_update: A boolean that denotes if the wireless pan id on the
                selected sensor needs updated.
            pan_id: A wx.SpinCtrl instance that denotes the wireless pan id of
                the selected sensor, if available.
            percent_text: A wx.StaticText instance that denotes the percentage
                of battery life left for the selected sensor, if available.
            serial_text: A wx.StaticText instance that denotes the serial number
                of the selected sensor.
            status_text: A wx.StaticText instance that denotes the battery's
                status of the selected sensor, if available.
            version_text: A wx.StaticText instance that denotes the version of
                the selected sensor.
            x_neg_check: A wx.CheckBox instance that indicates if an axis
                direction of the selected sensor is negated.
            y_neg_check: A wx.CheckBox instance that indicates if an axis
                direction of the selected sensor is negated.
            z_neg_check: A wx.CheckBox instance that indicates if an axis
                direction of the selected sensor is negated.
    """
    def __init__(self, parent):
        """ Initializes the InfoAxisPanel class.
            
            Args:
                parent: A reference to another wxPython object.
        """
        wx.Panel.__init__(self, parent)
        
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        w, h = parent.GetSize()
        
        ## Sensor Information ##
        info_box = wx.StaticBox(self, -1, "Sensor Information")
        font = info_box.GetFont()
        font.SetPointSize(15)
        info_box.SetFont(font)
        info_box_sizer = wx.StaticBoxSizer(info_box, wx.VERTICAL)
        info_box_sizer.SetMinSize((w - 20, -1))
        
        info_grid = wx.GridSizer(2, 2, 10, 50) # rows, cols, vGap, hGap
        font = wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        
        # Sensor Serial & Version
        serial_grid = wx.BoxSizer(wx.HORIZONTAL)
        self.serial_text = wx.StaticText(self, -1, "N/A    ")
        tmp_text = wx.StaticText(self, -1, "Serial Number:")
        tmp_text.SetFont(font)
        serial_grid.Add(tmp_text, 0)
        serial_grid.Add((5, 0))
        serial_grid.Add(self.serial_text, 0)
        
        version_grid = wx.BoxSizer(wx.HORIZONTAL)
        self.version_text = wx.StaticText(self, -1, "N/A    ")
        tmp_text = wx.StaticText(self, -1, "Version:")
        tmp_text.SetFont(font)
        version_grid.Add(tmp_text, 0)
        version_grid.AddSpacer((5, 0))
        version_grid.Add(self.version_text, 0)
        
        # Sensor Battery
        percent_grid = wx.BoxSizer(wx.HORIZONTAL)
        self.percent_text = wx.StaticText(self, -1, "N/A    ")
        tmp_text = wx.StaticText(self, -1, "Battery Charge:")
        tmp_text.SetFont(font)
        percent_grid.Add(tmp_text, 0)
        percent_grid.AddSpacer((5, 0))
        percent_grid.Add(self.percent_text, 0)
        
        status_grid = wx.BoxSizer(wx.HORIZONTAL)
        self.status_text = wx.StaticText(self, -1, "N/A    ")
        tmp_text = wx.StaticText(self, -1, "Battery Status:")
        tmp_text.SetFont(font)
        status_grid.Add(tmp_text, 0)
        status_grid.AddSpacer((5, 0))
        status_grid.Add(self.status_text, 0)
        
        # Sensor Wireless Settings
        pan_grid = wx.BoxSizer(wx.HORIZONTAL)
        self.pan_id = wx.SpinCtrl(self, wx.NewId(), "N/A", size=(60, -1), style=wx.SP_WRAP | wx.SP_ARROW_KEYS, min=1, max=65534, initial=1)
        self.pan_id.Disable()
        tmp_text = wx.StaticText(self, -1, "Pan ID:")
        tmp_text.SetFont(font)
        pan_grid.Add(tmp_text, 0, wx.ALIGN_CENTER_VERTICAL)
        pan_grid.AddSpacer((5, 0))
        pan_grid.Add(self.pan_id, 0)
        
        channel_grid = wx.BoxSizer(wx.HORIZONTAL)
        channels = ["%d"] * 16
        for i in range(16):
            channels[i] = channels[i] % (i + 11)
        channels.insert(0, "N/A")
        self.channel = wx.Choice(self, wx.NewId(), size=(60, -1), choices=channels)
        self.channel.SetSelection(0)
        self.channel.Disable()
        tmp_text = wx.StaticText(self, -1, "Channel:")
        tmp_text.SetFont(font)
        channel_grid.Add(tmp_text, 0, wx.ALIGN_CENTER_VERTICAL)
        channel_grid.AddSpacer((5, 0))
        channel_grid.Add(self.channel, 0)
        
        info_grid.Add(serial_grid, 0)
        info_grid.Add(version_grid, 0)
        info_grid.Add(percent_grid, 0)
        info_grid.Add(status_grid, 0)
        info_grid.Add(pan_grid, 0)
        info_grid.Add(channel_grid, 0)
        
        info_box_sizer.Add(info_grid, 0, wx.ALIGN_CENTER)
        
        
        ## Axis Section ##
        # Initial axis directions' order and handedness
        self.axis_dir_seeds = [[0,1,2,0], [0,2,1,1], [1,0,2,1], [2,0,1,0], [1,2,0,0], [2,1,0,1]]
        
        self.axis_names = [["Right", "Left"], ["Up", "Down"], ["Forward", "Back"]]
        
        axis_box = wx.StaticBox(self, -1, "Axis Direction")
        font = axis_box.GetFont()
        font.SetPointSize(15)
        axis_box.SetFont(font)
        axis_box_sizer = wx.StaticBoxSizer(axis_box, wx.VERTICAL)
        axis_box_sizer.SetMinSize((w - 20, -1))
        
        self.axis_sel = wx.Choice(self, wx.NewId(), size=(260, -1))
        
        axis_grid = wx.GridSizer(1, 3, 0, 10) # rows, cols, vGap, hGap
        self.x_neg_check = wx.CheckBox(self, wx.NewId(), "Negate X")
        self.y_neg_check = wx.CheckBox(self, wx.NewId(), "Negate Y")
        self.z_neg_check = wx.CheckBox(self, wx.NewId(), "Negate Z")
        
        axis_grid.AddMany([
            (self.x_neg_check, 0, wx.ALIGN_CENTER_HORIZONTAL),
            (self.y_neg_check, 0, wx.ALIGN_CENTER_HORIZONTAL),
            (self.z_neg_check, 0, wx.ALIGN_CENTER_HORIZONTAL)
        ])
        
        axis_box_sizer.Add(self.axis_sel, 0, wx.ALIGN_CENTER)
        axis_box_sizer.Add((0, 20))
        axis_box_sizer.Add(axis_grid, 0, wx.ALIGN_CENTER)
        
        self.refreshAxisDirChoices(init=True)
        
        ## Buttons ##
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.apply_button = wx.Button(self, wx.ID_APPLY, size=(150, -1))
        self.commit_button = wx.Button(self, wx.ID_APPLY, "Apply && &Commit", size=(150, -1))
        self.apply_button.Disable()
        self.commit_button.Disable()
        
        button_sizer.Add(self.apply_button, 0)
        button_sizer.AddSpacer((20, 0))
        button_sizer.Add(self.commit_button, 0)
        
        
        ## Booleans ##
        self.is_axis_update = False
        self.is_chan_update = False
        self.is_pan_update = False
        
        
        ## Box Sizer ##
        box_sizer.AddStretchSpacer()
        box_sizer.Add(info_box_sizer, 0, wx.ALIGN_CENTER, 10)
        box_sizer.AddSpacer((0, 35))
        box_sizer.Add(axis_box_sizer, 0, wx.ALIGN_CENTER, 10)
        box_sizer.AddStretchSpacer()
        box_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER)
        
        self.SetSizer(box_sizer)
        self.Disable()
    
    def initSettings(self, sensor=None):
        """ Initializes the InfoAxisPanel attributes with data from a passed in
            3-Space Sensor device.
            
            Args:
                sensor: A reference to a TSSensor object. (default is None)
        """
        if sensor is None:
            self.serial_text.SetLabel("N/A    ")
            self.version_text.SetLabel("N/A    ")
            self.percent_text.SetLabel("N/A    ")
            self.status_text.SetLabel("N/A    ")
            self.pan_id.SetValueString("N/A")
            chan_idx = self.channel.FindString("N/A")
            if chan_idx == -1:
                self.channel.Insert("N/A", 0)
            self.channel.SetSelection(0)
            self.axis_sel.SetSelection(0)
            self.x_neg_check.SetValue(False)
            self.y_neg_check.SetValue(False)
            self.z_neg_check.SetValue(False)
            
            self.is_axis_update = False
            self.is_chan_update = False
            self.is_pan_update = False
            
            self.Disable()
            return False
        else:
            if not sensor.isConnected():
                self.serial_text.SetLabel("N/A    ")
                self.version_text.SetLabel("N/A    ")
                self.percent_text.SetLabel("N/A    ")
                self.status_text.SetLabel("N/A    ")
                self.pan_id.SetValueString("N/A")
                chan_idx = self.channel.FindString("N/A")
                if chan_idx == -1:
                    self.channel.Insert("N/A", 0)
                self.channel.SetSelection(0)
                self.axis_sel.SetSelection(0)
                self.x_neg_check.SetValue(False)
                self.y_neg_check.SetValue(False)
                self.z_neg_check.SetValue(False)
                
                self.is_axis_update = False
                self.is_chan_update = False
                self.is_pan_update = False
                
                self.Disable()
                return False
            axis_data = sensor.getAxisDirections()
            if axis_data is not None:
                self.axis_sel.SetSelection(axis_data & 7)
                
                self.x_neg_check.SetValue(axis_data & 32)
                self.y_neg_check.SetValue(axis_data & 16)
                self.z_neg_check.SetValue(axis_data & 8)
            else:
                self.axis_sel.SetSelection(0)
                self.x_neg_check.SetValue(False)
                self.y_neg_check.SetValue(False)
                self.z_neg_check.SetValue(False)
                
                self.is_axis_update = False
                self.is_chan_update = False
                self.is_pan_update = False
                
                return False
            self.refreshAxisDirChoices()
            
            self.serial_text.SetLabel(sensor.serial_number_hex)
            try:
                self.version_text.SetLabel(sensor.getFirmwareVersionString())
            except:
                self.version_text.SetLabel("N/A    ")
            
            try:
                self.percent_text.SetLabel("%d %%" %
                    sensor.getBatteryPercentRemaining())
            except:
                self.percent_text.SetLabel("N/A    ")
            
            try:
                bat_stat = sensor.getBatteryStatus()
                if bat_stat == 1:
                    text = "Charged"
                elif bat_stat == 2:
                    text = "Charging"
                else:
                    text = "Draining"
                self.status_text.SetLabel(text)
            except:
                self.status_text.SetLabel("N/A    ")
            
            self.Enable()
            self.pan_id.Disable()
            self.channel.Disable()
            
            if "WL" in sensor.device_type:
                try:
                    self.pan_id.SetValue(sensor.getWirelessPanID())
                except:
                    # We know the sensor is there, it just failed on a wireless
                    # communication
                    self.pan_id.SetValue(sensor.dongle.getWirelessPanID())
                chan_idx = self.channel.FindString("N/A")
                if chan_idx != -1:
                    self.channel.Delete(chan_idx)
                try:
                    self.channel.SetSelection(sensor.getWirelessChannel() - 11)
                except:
                    # We know the sensor is there, it just failed on a wireless
                    # communication
                    self.channel.SetSelection(sensor.dongle.getWirelessChannel() - 11)
                if not sensor.wireless_com:
                    self.pan_id.Enable()
                    self.channel.Enable()
            else:
                self.pan_id.SetValueString("N/A")
                chan_idx = self.channel.FindString("N/A")
                if chan_idx == -1:
                    self.channel.Insert("N/A", 0)
                self.channel.SetSelection(0)
        
        self.apply_button.Disable()
        self.commit_button.Disable()
        
        return True
    
    def onSpinCtrl(self, event):
        self.is_pan_update = True
        self.apply_button.Enable()
        self.commit_button.Enable()
    
    def onChoice(self, event):
        if event.GetId() == self.channel.GetId():
            self.is_chan_update = True
        else:
            self.is_axis_update = True
            self.refreshAxisDirChoices()
        self.apply_button.Enable()
        self.commit_button.Enable()
    
    def refreshAxisDirChoices(self, init=False):
        choices = []
        axes = ["X","Y","Z"]
        handedness_vals = ["Left-handed", "Right-handed"]
        axis_vals = [self.x_neg_check.GetValue(), self.y_neg_check.GetValue(), self.z_neg_check.GetValue()]
        for seed in self.axis_dir_seeds:
            text = "("
            handedness = seed[3]
            for axis in range(3):
                text += axes[axis] + ": "
                text += self.axis_names[seed[axis]][axis_vals[axis]]
                if axis != 2:
                    text += ", "
                handedness += axis_vals[axis]
            text += ") ("
            text += handedness_vals[handedness % 2] + ")"
            choices.append(text)
        
        if init:
            selection = 0
        else:
            selection = self.axis_sel.GetSelection()
        self.axis_sel.SetItems(choices)
        self.axis_sel.SetSelection(selection)
    
    def onCheck(self, event):
        self.is_axis_update = True
        self.refreshAxisDirChoices()
        self.apply_button.Enable()
        self.commit_button.Enable()
    
    def returnAxisValues(self):
        axis_dir = self.axis_sel.GetSelection()
        
        if self.x_neg_check.GetValue():
            axis_dir |= 32
        if self.y_neg_check.GetValue():
            axis_dir |= 16
        if self.z_neg_check.GetValue():
            axis_dir |= 8
        
        return axis_dir
    
    def setSettings(self, sensor):
        if self.is_axis_update:
            self.is_axis_update = False
            if not sensor.setAxisDirections(self.returnAxisValues()):
                self.is_axis_update = True
        if self.is_chan_update:
            self.is_chan_update = False
            if not sensor.setWirelessChannel(self.channel.GetSelection() + 11):
                self.is_chan_update = True
        if self.is_pan_update:
            self.is_pan_update = False
            if not sensor.setWirelessPanID(self.pan_id.GetValue()):
                self.is_pan_update = True
        
        if not self.is_axis_update and not self.is_chan_update and not self.is_pan_update:
            self.apply_button.Disable()
            self.commit_button.Disable()
    
    def setBinds(self, win):
        """ Sets the binds for the InfoAxisPanel class and its attributes.
            
            Args:
                win: A reference to the main window, a wxPython object.
        """
        # SpinCtrl Binds
        self.pan_id.Bind(wx.EVT_SPINCTRL, self.onSpinCtrl)
        
        # Choice Binds
        self.channel.Bind(wx.EVT_CHOICE, self.onChoice)
        self.axis_sel.Bind(wx.wx.EVT_CHOICE, self.onChoice)
        
        # Check Box Binds
        self.x_neg_check.Bind(wx.EVT_CHECKBOX, self.onCheck)
        self.y_neg_check.Bind(wx.EVT_CHECKBOX, self.onCheck)
        self.z_neg_check.Bind(wx.EVT_CHECKBOX, self.onCheck)
        
        # Button Binds
        self.apply_button.Bind(wx.EVT_BUTTON, win.onApplyButton)
        self.commit_button.Bind(wx.EVT_BUTTON, win.onApplyCommitSettings)


### wxPanel ###
class TarePanel(wx.Panel):
    
    """ A wxPython Panel object.
        
        Attributes:
            commit_button: A wx.Button instance that tares the selected sensor
                according towat method was chosen and commits the settings.
            gyro_button: A wx.Button instance that calibrates the gyros of the
                selected sensor.
            tare_button: A wx.Button instance that tares the selected sensor
                according to what method was chosen.
            tare_choice_box: A wx.Choice instance that has a list of TSSensors
                and TSWSensors objects.
            tare_cur_orient_sel: A wx.RadioButton instance that indicates what
                method of taring to use.
            tare_mat_sel: A wx.RadioButton instance that indicates what method
                of taring to use.
            tare_mat_00: A wx.FloatSpin instance used for denoting a value in a
                matrix.
            tare_mat_01: A wx.FloatSpin instance used for denoting a value in a
                matrix.
            tare_mat_02: A wx.FloatSpin instance used for denoting a value in a
                matrix.
            tare_mat_10: A wx.FloatSpin instance used for denoting a value in a
                matrix.
            tare_mat_11: A wx.FloatSpin instance used for denoting a value in a
                matrix.
            tare_mat_12: A wx.FloatSpin instance used for denoting a value in a
                matrix.
            tare_mat_20: A wx.FloatSpin instance used for denoting a value in a
                matrix.
            tare_mat_21: A wx.FloatSpin instance used for denoting a value in a
                matrix.
            tare_mat_22: A wx.FloatSpin instance used for denoting a value in a
                matrix.
            tare_quat_sel: A wx.RadioButton instance that indicates what method
                of taring to use.
            tare_sensor_sel: A wx.RadioButton instance that indicates what
                method of taring to use.
            w_tare_quat: A wx.FloatSpin instance used for denoting the w-value
                in a quaternion.
            x_tare_quat: A wx.FloatSpin instance used for denoting the x-value
                in a quaternion.
            y_tare_quat: A wx.FloatSpin instance used for denoting the y-value
                in a quaternion.
            z_tare_quat: A wx.FloatSpin instance used for denoting the z-value
                in a quaternion.
    """
    def __init__(self, parent):
        """ Initializes the TarePanel class.
            
            Args:
                parent: A reference to another wxPython object.
        """
        wx.Panel.__init__(self, parent)
        
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        w, h = parent.GetSize()
        
        ## Taring Section ##
        # Tare Box
        tare_box = wx.StaticBox(self, -1, "Tare")
        font = tare_box.GetFont()
        font.SetPointSize(15)
        tare_box.SetFont(font)
        tare_box_sizer = wx.StaticBoxSizer(tare_box, wx.HORIZONTAL)
        tare_box_sizer.SetMinSize((w - 20, -1))
        
        # Current Orientation
        self.tare_cur_orient_sel = wx.RadioButton(self, wx.NewId(), "With Current Orientation ", style=wx.RB_GROUP)
        
        # Quaternion
        quat_grid = wx.BoxSizer(wx.VERTICAL)
        self.tare_quat_sel = wx.RadioButton(self, wx.NewId(), "With Quaternion ")
        
        quat_vals_grid = wx.BoxSizer(wx.HORIZONTAL)
        self.x_tare_quat = float_spin.FloatSpin(self, wx.NewId(), size=(60, -1), increment=0.1, digits=2)
        self.y_tare_quat = float_spin.FloatSpin(self, wx.NewId(), size=(60, -1), increment=0.1, digits=2)
        self.z_tare_quat = float_spin.FloatSpin(self, wx.NewId(), size=(60, -1), increment=0.1, digits=2)
        self.w_tare_quat = float_spin.FloatSpin(self, wx.NewId(), size=(60, -1), value=1.0, increment=0.1, digits=2)
        
        quat_vals_grid.AddSpacer((15, 0))
        quat_vals_grid.Add(wx.StaticText(self, -1, "X"), 0,
            wx.ALIGN_CENTER_VERTICAL)
        quat_vals_grid.AddSpacer((5, 0))
        quat_vals_grid.Add(self.x_tare_quat, 0, wx.ALIGN_CENTER_VERTICAL)
        quat_vals_grid.AddSpacer((10, 0))
        quat_vals_grid.Add(wx.StaticText(self, -1, "Y"), 0, wx.ALIGN_CENTER_VERTICAL)
        quat_vals_grid.AddSpacer((5, 0))
        quat_vals_grid.Add(self.y_tare_quat, 0, wx.ALIGN_CENTER_VERTICAL)
        quat_vals_grid.AddSpacer((10, 0))
        quat_vals_grid.Add(wx.StaticText(self, -1, "Z"), 0, wx.ALIGN_CENTER_VERTICAL)
        quat_vals_grid.AddSpacer((5, 0))
        quat_vals_grid.Add(self.z_tare_quat, 0, wx.ALIGN_CENTER_VERTICAL)
        quat_vals_grid.AddSpacer((10, 0))
        quat_vals_grid.Add(wx.StaticText(self, -1, "W"), 0, wx.ALIGN_CENTER_VERTICAL)
        quat_vals_grid.AddSpacer((5, 0))
        quat_vals_grid.Add(self.w_tare_quat, 0, wx.ALIGN_CENTER_VERTICAL)
        
        quat_grid.Add(self.tare_quat_sel, 0)
        quat_grid.AddSpacer((0, 5))
        quat_grid.Add(quat_vals_grid, 0)
        
        # Rotation Matrix
        mat_grid = wx.BoxSizer(wx.VERTICAL)
        self.tare_mat_sel = wx.RadioButton(self, wx.NewId(), "With Rotation Matrix ")
        
        mat_inner_grid = wx.BoxSizer(wx.HORIZONTAL)
        mat_vals_grid = wx.GridSizer(3, 3, 5, 5)
        self.tare_mat_00 = float_spin.FloatSpin(self, wx.NewId(), size=(60, -1), value=1.0, increment=0.1, digits=2)
        self.tare_mat_01 = float_spin.FloatSpin(self, wx.NewId(), size=(60, -1), increment=0.1, digits=2)
        self.tare_mat_02 = float_spin.FloatSpin(self, wx.NewId(), size=(60, -1), increment=0.1, digits=2)
        
        self.tare_mat_10 = float_spin.FloatSpin(self, wx.NewId(), size=(60, -1), increment=0.1, digits=2)
        self.tare_mat_11 = float_spin.FloatSpin(self, wx.NewId(), size=(60, -1), value=1.0, increment=0.1, digits=2)
        self.tare_mat_12 = float_spin.FloatSpin(self, wx.NewId(), size=(60, -1), increment=0.1, digits=2)
        
        self.tare_mat_20 = float_spin.FloatSpin(self, wx.NewId(), size=(60, -1), increment=0.1, digits=2)
        self.tare_mat_21 = float_spin.FloatSpin(self, wx.NewId(), size=(60, -1), increment=0.1, digits=2)
        self.tare_mat_22 = float_spin.FloatSpin(self, wx.NewId(), size=(60, -1), value=1.0, increment=0.1, digits=2)
        
        mat_vals_grid.AddMany([
            (self.tare_mat_00, 0, wx.ALIGN_CENTER),
            (self.tare_mat_01, 0, wx.ALIGN_CENTER),
            (self.tare_mat_02, 0, wx.ALIGN_CENTER),
            (self.tare_mat_10, 0, wx.ALIGN_CENTER),
            (self.tare_mat_11, 0, wx.ALIGN_CENTER),
            (self.tare_mat_12, 0, wx.ALIGN_CENTER),
            (self.tare_mat_20, 0, wx.ALIGN_CENTER),
            (self.tare_mat_21, 0, wx.ALIGN_CENTER),
            (self.tare_mat_22, 0, wx.ALIGN_CENTER)
        ])
        
        mat_inner_grid.AddSpacer((15, 0))
        mat_inner_grid.Add(mat_vals_grid, 0)
        
        mat_grid.Add(self.tare_mat_sel, 0)
        mat_grid.AddSpacer((0, 5))
        mat_grid.Add(mat_inner_grid, 0)
        
        # Another Bone's tare orientation
        sensor_grid = wx.BoxSizer(wx.VERTICAL)
        sensor_choice_grid = wx.BoxSizer(wx.HORIZONTAL)
        self.tare_sensor_sel = wx.RadioButton(self, wx.NewId(), "With Sensor ")
        self.tare_choice_box = wx.Choice(self, wx.NewId(), size=(150, 16))
        
        sensor_choice_grid.AddSpacer((15, 0))
        sensor_choice_grid.Add(self.tare_choice_box, 0)
        
        sensor_grid.Add(self.tare_sensor_sel, 0)
        sensor_grid.AddSpacer((0, 5))
        sensor_grid.Add(sensor_choice_grid, 0)
        
        option_sizer = wx.BoxSizer(wx.VERTICAL)
        
        option_sizer.Add(self.tare_cur_orient_sel, 0, wx.EXPAND | wx.ALL)
        option_sizer.AddSpacer((0, 10))
        option_sizer.Add(quat_grid, 0, wx.EXPAND | wx.ALL)
        option_sizer.AddSpacer((0, 10))
        option_sizer.Add(mat_grid, 0, wx.EXPAND | wx.ALL)
        option_sizer.AddSpacer((0, 10))
        option_sizer.Add(sensor_grid, 0, wx.EXPAND | wx.ALL)
        option_sizer.AddSpacer((0, 5))
        
        tare_box_sizer.AddSpacer((50, 0))
        tare_box_sizer.Add(option_sizer, 0, wx.EXPAND | wx.ALL)
        
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.tare_button = wx.Button(self, wx.NewId(), "&Tare", size=(150, -1))
        self.commit_button = wx.Button(self, wx.ID_APPLY, "Tare && &Commit", size=(150, -1))
        
        self.gyro_button = wx.Button(self, wx.NewId(), "Calibrate &Gyros", size=(150, -1))
        
        btn_sizer.Add(self.tare_button, 0)
        btn_sizer.AddSpacer((25, 0))
        btn_sizer.Add(self.commit_button, 0)
        
        ## Box Sizer ##
        box_sizer.AddStretchSpacer()
        box_sizer.Add(tare_box_sizer, 0, wx.ALIGN_CENTER)
        box_sizer.AddStretchSpacer()
        box_sizer.Add(self.gyro_button, 0, wx.ALIGN_CENTER)
        box_sizer.AddSpacer((0, 10))
        box_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER)
        
        self.SetSizer(box_sizer)
        self.Disable()
    
    def initSettings(self, sensor_str=None):
        """ Initializes the TarePanel's choice box and removes the string that
            is passed in.
            
            Args:
                sensor_str: A string that denotes a name of a sensor to be
                    removed from the choice box.
        """
        if sensor_str is None:
            self.Disable()
        else:
            tmp_list = global_sensor_list.values()
            name_list = []
            for tmp in tmp_list:
                name_list.append(tmp.device_type + '-' + tmp.serial_number_hex)
            name_list.sort()
            self.tare_choice_box.SetItems(name_list)
            name_idx = self.tare_choice_box.FindString(sensor_str)
            if name_idx != -1:
                self.tare_choice_box.Delete(name_idx)
            
            self.Enable()
    
    def returnValues(self):
        """ Returns an orientation for the sensor to use as its indentity
            orientation.
            
            Returns:
                A list that contains orientation data for either a quaternion or
                a 3x3 matrix in row major.
        """
        tare_type = 0
        tare_data = None
        # Figure out which radio button is selected
        if self.tare_quat_sel.GetValue():
            x_val = self.x_tare_quat.GetValue()
            y_val = self.y_tare_quat.GetValue()
            z_val = self.z_tare_quat.GetValue()
            w_val = self.w_tare_quat.GetValue()
            tmp_quat = Quaternion([x_val, y_val, z_val, w_val])
            tmp_quat.normalize()
            
            tare_type = 1
            tare_data = tmp_quat.asArray()
            x_val, y_val, z_val, w_val = tare_data
            
            self.x_tare_quat.SetValue(x_val)
            self.y_tare_quat.SetValue(y_val)
            self.z_tare_quat.SetValue(z_val)
            self.w_tare_quat.SetValue(w_val)
        
        elif self.tare_mat_sel.GetValue():
            mat_vals = []
            mat_vals.append(self.tare_mat_00.GetValue())
            mat_vals.append(self.tare_mat_01.GetValue())
            mat_vals.append(self.tare_mat_02.GetValue())
            mat_vals.append(self.tare_mat_10.GetValue())
            mat_vals.append(self.tare_mat_11.GetValue())
            mat_vals.append(self.tare_mat_12.GetValue())
            mat_vals.append(self.tare_mat_20.GetValue())
            mat_vals.append(self.tare_mat_21.GetValue())
            mat_vals.append(self.tare_mat_22.GetValue())
            tmp_mat = Matrix3(mat_vals)
            tmp_mat.orthonormalize()
            
            tare_type = 2
            tare_data = tmp_mat.asRowArray()
            m00, m01, m02, m10, m11, m12, m20, m21, m22 = tare_data
            
            self.tare_mat_00.SetValue(m00)
            self.tare_mat_01.SetValue(m01)
            self.tare_mat_02.SetValue(m02)
            self.tare_mat_10.SetValue(m10)
            self.tare_mat_11.SetValue(m11)
            self.tare_mat_12.SetValue(m12)
            self.tare_mat_20.SetValue(m20)
            self.tare_mat_21.SetValue(m21)
            self.tare_mat_22.SetValue(m22)
        
        elif self.tare_sensor_sel.GetValue():
            tare_type = 3
            tare_data = self.tare_choice_box.GetStringSelection()
        
        return tare_type, tare_data
    
    def setBinds(self, win):
        """ Sets the binds for the InfoAxisPanel class and its attributes.
            
            Args:
                win: A reference to the main window, a wxPython object.
        """
        # Button Binds
        self.tare_button.Bind(wx.EVT_BUTTON, win.onTareButton)
        self.commit_button.Bind(wx.EVT_BUTTON, win.onTareButton)
        self.gyro_button.Bind(wx.EVT_BUTTON, win.onGyroButton)


### wxPanel ###
class LEDCompPanel(wx.Panel):
    
    """ A wxPython Panel object.
        
        Attributes:
            accel_check: A wx.CheckBox instance that denotes whether or not the
                accelerometer is enabled on the selected sensor.
            accel_max: A wx.FloatSpin instance that denotes the max trust value.
            accel_min: A wx.FloatSpin instance that denotes the min trust value.
            apply_button: A wx.Button instance used to apply the updated
                settings to the selected sensor.
            avg_percent: A wx.FloatSpin instance that denotes the running
                average percent of the selected sensor's data.
            commit_button: A wx.Button instance used to apply and commit the
                updated settings to the selected sensor.
            compass_check: A wx.CheckBox instance that denotes whether or not
                the compass is enabled on the selected sensor.
            compass_max: A wx.FloatSpin instance that denotes the max trust
                value.
            compass_min: A wx.FloatSpin instance that denotes the min trust
                value.
            is_accel_trust_update: A boolean that denotes if the accelerometer's
                trust values on the selected sensor needs updated.
            is_accel_update: A boolean that denotes if the accelerometer enabled
                state on the selected sensor needs updated.
            is_avg_update: A boolean that denotes if the running average percent
                of the selected sensor needs updated.
            is_compass_trust_update: A boolean that denotes if the compass's
                trust values on the selected sensor needs updated.
            is_compass_update: A boolean that denotes if the compass enabled
                state on the selected sensor needs updated.
            is_gyro_update: A boolean that denotes if the gyroscope enabled
                state on the selected sensor needs updated.
            is_led_color_update: A boolean that denotes if the LED color of the
                selected sensor needs updated.
            is_led_mode_update: A boolean that denotes if the LED mode on the
                selected sensor needs updated.
            is_sample_update: A boolean that denotes if the sample rate on the
                selected sensor needs updated.
            is_update_update: A boolean that denotes if the desired update rate
                on the selected sensor needs updated.
            led_color: A wx.ColourSelect instance that is use for the color of
                the LED on the selected sensor.
            led_normal: A wx.RadioButton instance that represents what LED mode
                the selected sensor is in.
            led_static: A wx.RadioButton instance that represents what LED mode
                the selected sensor is in.
            gyro_check: A wx.CheckBox instance that denotes whether or not the
                gyroscope is enabled on the selected sensor.
            sample_rate: A wx.SpinCtrl instance that denotes the oversampling
                rate of the selected sensor.
            update_rate: A wx.SpinCtrl instance that denotes the desired update
                rate for the selected sensor in microseconds.
    """
    def __init__(self, parent):
        """ Initializes the LEDCompPanel class.
            
            Args:
                parent: A reference to another wxPython object.
        """
        wx.Panel.__init__(self, parent)
        
        inner_box = wx.BoxSizer(wx.VERTICAL)
        outer_box = wx.BoxSizer(wx.VERTICAL)
        w, h = parent.GetSize()
        
        ## LED Settings ##
        led_box = wx.StaticBox(self, -1, "LED Settings")
        font = led_box.GetFont()
        font.SetPointSize(15)
        led_box.SetFont(font)
        led_box_sizer = wx.StaticBoxSizer(led_box, wx.HORIZONTAL)
        led_box_sizer.SetMinSize((w - 20, -1))
        
        # LED Color
        color_grid = wx.BoxSizer(wx.HORIZONTAL)
        self.led_color = colour_sel.ColourSelect(self, wx.NewId())
        
        color_grid.Add(wx.StaticText(self, -1, "LED Color:"), 0, wx.ALIGN_CENTER_VERTICAL)
        color_grid.Add((10, 0))
        color_grid.Add(self.led_color, 0)
        
        # LED Mode
        mode_grid = wx.BoxSizer(wx.HORIZONTAL)
        self.led_normal = wx.RadioButton(self, wx.NewId(), "Normal", style=wx.RB_GROUP)
        self.led_static = wx.RadioButton(self, wx.NewId(), "Static")
        
        mode_grid.Add(wx.StaticText(self, -1, "LED Mode:", name="led_mode"), 0, wx.ALIGN_CENTER_VERTICAL)
        mode_grid.AddSpacer((10, 0))
        mode_grid.Add(self.led_normal, 0)
        mode_grid.AddSpacer((5, 0))
        mode_grid.Add(self.led_static, 0)
        
        led_option_sizer = wx.BoxSizer(wx.VERTICAL)
        led_option_sizer.Add(color_grid, 0, wx.EXPAND | wx.ALL)
        led_option_sizer.AddSpacer((0, 10))
        led_option_sizer.Add(mode_grid, 0, wx.EXPAND | wx.ALL)
        
        led_box_sizer.AddSpacer((125, 0))
        led_box_sizer.Add(led_option_sizer, 0)
        
        ## Sensor Components ##
        comp_box = wx.StaticBox(self, -1, "Sensor Components")
        font = comp_box.GetFont()
        font.SetPointSize(15)
        comp_box.SetFont(font)
        comp_box_sizer = wx.StaticBoxSizer(comp_box, wx.HORIZONTAL)
        comp_box_sizer.SetMinSize((w - 20, -1))
        
        comp_inner_box1 = wx.BoxSizer(wx.HORIZONTAL)
        # Accelerometer
        self.accel_check = wx.CheckBox(self, wx.NewId(), "  Accelerometer")
        
        # Compass
        self.compass_check = wx.CheckBox(self, wx.NewId(), "  Compass")
        
        # Gyroscope
        self.gyro_check = wx.CheckBox(self, wx.NewId(), "  Gyroscope")
        
        comp_inner_box1.AddSpacer((40, 0))
        comp_inner_box1.Add(self.accel_check, 0)
        comp_inner_box1.AddSpacer((10, 0))
        comp_inner_box1.Add(self.compass_check, 0)
        comp_inner_box1.AddSpacer((10, 0))
        comp_inner_box1.Add(self.gyro_check, 0)
        
        comp_inner_box2 = wx.BoxSizer(wx.VERTICAL)
        comp_inner_box2a = wx.BoxSizer(wx.HORIZONTAL)
        
        # Accelerometer Trust Values
        self.accel_min = float_spin.FloatSpin(self, wx.NewId(), size=(90, -1), value=0.01, min_val=0.0, max_val=1.0, increment=0.001, digits=5)
        self.accel_max = float_spin.FloatSpin(self, wx.NewId(), size=(90, -1), value=0.16666, min_val=0.0, max_val=1.0, increment=0.001, digits=5)
        
        comp_inner_box2a.Add(wx.StaticText(self, -1, "Accelerometer Trust Values:", name="accel_trust"), 0, wx.ALIGN_CENTER_VERTICAL)
        comp_inner_box2a.AddSpacer((10, 0))
        comp_inner_box2a.Add(self.accel_min, 0, wx.ALIGN_CENTER_VERTICAL)
        comp_inner_box2a.AddSpacer((3, 0))
        comp_inner_box2a.Add(wx.StaticText(self, -1, "to", name="accel_to"), 0, wx.ALIGN_CENTER_VERTICAL)
        comp_inner_box2a.AddSpacer((3, 0))
        comp_inner_box2a.Add(self.accel_max, 0, wx.ALIGN_CENTER_VERTICAL)
        
        comp_inner_box2.Add(comp_inner_box2a, 0)
        
        comp_inner_box3 = wx.BoxSizer(wx.VERTICAL)
        comp_inner_box3a = wx.BoxSizer(wx.HORIZONTAL)
        
        # Compass Trust Values
        self.compass_min = float_spin.FloatSpin(self, wx.NewId(), size=(90, -1), value=0.01, min_val=0.0, max_val=1.0, increment=0.001, digits=5)
        self.compass_max = float_spin.FloatSpin(self, wx.NewId(), size=(90, -1), value=0.16666, min_val=0.0, max_val=1.0, increment=0.001, digits=5)
        
        comp_inner_box3a.AddSpacer((26, 0))
        comp_inner_box3a.Add(wx.StaticText(self, -1, "Compass Trust Values:", name="compass_trust"), 0, wx.ALIGN_CENTER_VERTICAL)
        comp_inner_box3a.AddSpacer((10, 0))
        comp_inner_box3a.Add(self.compass_min, 0, wx.ALIGN_CENTER_VERTICAL)
        comp_inner_box3a.AddSpacer((3, 0))
        comp_inner_box3a.Add(wx.StaticText(self, -1, "to", name="compass_to"), 0, wx.ALIGN_CENTER_VERTICAL)
        comp_inner_box3a.AddSpacer((3, 0))
        comp_inner_box3a.Add(self.compass_max, 0, wx.ALIGN_CENTER_VERTICAL)
        
        comp_inner_box3.Add(comp_inner_box3a, 0)
        
        comp_inner_box4 = wx.BoxSizer(wx.VERTICAL)
        comp_inner_box4a = wx.BoxSizer(wx.HORIZONTAL)
        # Desired Update Rate
        self.update_rate = wx.SpinCtrl(self, wx.NewId(), '', size=(60, -1), style=wx.SP_WRAP | wx.SP_ARROW_KEYS, max=10000)
        
        comp_inner_box4a.AddSpacer((31, 0))
        comp_inner_box4a.Add(wx.StaticText(self, -1, "Desired Update Rate:"), 0, wx.ALIGN_CENTER_VERTICAL)
        comp_inner_box4a.AddSpacer((10, 0))
        comp_inner_box4a.Add(self.update_rate, 0)
        
        comp_inner_box4.Add(comp_inner_box4a, 0)
        
        comp_inner_box5 = wx.BoxSizer(wx.VERTICAL)
        comp_inner_box5a = wx.BoxSizer(wx.HORIZONTAL)
        # Oversampling Rate (Samples per Frame)
        self.sample_rate = wx.SpinCtrl(self, wx.NewId(), '', size=(45, -1), style=wx.SP_WRAP | wx.SP_ARROW_KEYS, min=1, max=10, initial=1)
        
        comp_inner_box5a.AddSpacer((40, 0))
        comp_inner_box5a.Add(wx.StaticText(self, -1, "Samples per Frame:"), 0, wx.ALIGN_CENTER_VERTICAL)
        comp_inner_box5a.AddSpacer((10, 0))
        comp_inner_box5a.Add(self.sample_rate, 0)
        
        comp_inner_box5.Add(comp_inner_box5a, 0)
        
        comp_inner_box6 = wx.BoxSizer(wx.VERTICAL)
        comp_inner_box6a = wx.BoxSizer(wx.HORIZONTAL)
        # Running Average Percent
        self.avg_percent = float_spin.FloatSpin(self, wx.NewId(), size=(60, -1), min_val=0.0, max_val=97.0, digits=2)
        
        comp_inner_box6a.AddSpacer((34, 0))
        comp_inner_box6a.Add(wx.StaticText(self, -1, "Running Average %:"), 0, wx.ALIGN_CENTER_VERTICAL)
        comp_inner_box6a.AddSpacer((10, 0))
        comp_inner_box6a.Add(self.avg_percent, 0)
        
        comp_inner_box6.Add(comp_inner_box6a, 0)
        
        ## Components Sizer ##
        comp_option_sizer = wx.BoxSizer(wx.VERTICAL)
        comp_option_sizer.Add(comp_inner_box1, 0)
        comp_option_sizer.AddSpacer((0, 10))
        comp_option_sizer.Add(comp_inner_box2, 0)
        comp_option_sizer.AddSpacer((0, 10))
        comp_option_sizer.Add(comp_inner_box3, 0)
        comp_option_sizer.AddSpacer((0, 10))
        comp_option_sizer.Add(comp_inner_box4, 0)
        comp_option_sizer.AddSpacer((0, 10))
        comp_option_sizer.Add(comp_inner_box5, 0)
        comp_option_sizer.AddSpacer((0, 10))
        comp_option_sizer.Add(comp_inner_box6, 0)
        
        # comp_box_sizer.AddSpacer((55, 0))
        comp_box_sizer.AddStretchSpacer()
        comp_box_sizer.Add(comp_option_sizer, 0)
        comp_box_sizer.AddStretchSpacer()
        
        ## Booleans ##
        self.is_accel_trust_update = False
        self.is_accel_update = False
        self.is_avg_update = False
        self.is_compass_trust_update = False
        self.is_compass_update = False
        self.is_gyro_update = False
        self.is_led_color_update = False
        self.is_led_mode_update = False
        self.is_sample_update = False
        self.is_update_update = False
        
        ## Buttons ##
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.apply_button = wx.Button(self, wx.ID_APPLY, size=(150, -1))
        self.commit_button = wx.Button(self, wx.ID_APPLY, "Apply && &Commit", size=(150, -1))
        self.apply_button.Disable()
        self.commit_button.Disable()
        
        button_sizer.Add(self.apply_button, 0)
        button_sizer.AddSpacer((20, 0))
        button_sizer.Add(self.commit_button, 0)
        
        ## Inner Box Sizer ##
        inner_box.Add(led_box_sizer, 0, wx.ALIGN_CENTER)
        inner_box.AddSpacer((0, 10))
        inner_box.Add(comp_box_sizer, 0)
        
        ## Outer Box Sizer ##
        outer_box.AddStretchSpacer()
        outer_box.Add(inner_box, 0, wx.ALIGN_CENTER)
        outer_box.AddStretchSpacer()
        outer_box.Add(button_sizer, 0, wx.ALIGN_CENTER)
        
        self.SetSizer(outer_box)
        self.Disable()
    
    def disableLEDMode(self):
        self.FindWindowByName("led_mode").Disable()
        self.led_static.Disable()
        self.led_normal.Disable()
    
    def enableLEDMode(self):
        self.FindWindowByName("led_mode").Enable()
        self.led_static.Enable()
        self.led_normal.Enable()
    
    def initSettings(self, sensor=None):
        """ Initializes the LEDCompPanel attributes with data from a passed in
            3-Space Sensor device.
            
            Args:
                sensor: A reference to a TSSensor object. (default is None)
        """
        if sensor is None:
            # LED Settings
            self.led_color.SetColour([0, 0, 0])
            self.led_static.SetValue(False)
            
            # Accelerometer Settings
            self.accel_min.SetToDefaultValue()
            self.accel_max.SetToDefaultValue()
            
            # Compass Settings
            self.compass_min.SetToDefaultValue()
            self.compass_max.SetToDefaultValue()
            
            # Other Settings
            self.update_rate.SetValue(0)
            self.sample_rate.SetValue(1)
            self.avg_percent.SetToDefaultValue()
            
            self.is_accel_trust_update = False
            self.is_accel_update = False
            self.is_avg_update = False
            self.is_compass_trust_update = False
            self.is_compass_update = False
            self.is_gyro_update = False
            self.is_led_color_update = False
            self.is_led_mode_update = False
            self.is_sample_update = False
            self.is_update_update = False
            
            self.Disable()
        else:
            # Accelerometer Settings
            try:
                self.accel_check.SetValue(sensor.getAccelerometerEnabledState())
            except:
                self.accel_check.SetValue(False)
            
            data = sensor.getAccelerometerTrustValues()
            if data is not None:
                self.accel_min.SetValue(data[0])
                self.accel_max.SetValue(data[1])
            else:
                self.accel_min.SetToDefaultValue()
                self.accel_max.SetToDefaultValue()
            
            # Compass Settings
            try:
                self.compass_check.SetValue(sensor.getCompassEnabledState())
            except:
                self.compass_check.SetValue(False)
            
            data = sensor.getCompassTrustValues()
            if data is not None:
                self.compass_min.SetValue(data[0])
                self.compass_max.SetValue(data[1])
            else:
                self.compass_min.SetToDefaultValue()
                self.compass_max.SetToDefaultValue()
            
            # Gyroscope Settings
            try:
                self.gyro_check.SetValue(sensor.getGyroscopeEnabledState())
            except:
                self.gyro_check.SetValue(False)
            
            # Other Settings
            try:
                self.update_rate.SetValue(sensor.getDesiredUpdateRate())
            except:
                self.update_rate.SetValue(0)
            
            try:
                self.sample_rate.SetValue(sensor.getOversampleRate())
            except:
                self.sample_rate.SetValue(1)
            
            try:
                self.avg_percent.SetValue(sensor.getRunningAveragePercent())
            except:
                self.avg_percent.SetToDefaultValue()
            
            # Call events
            self.onCheck(self.accel_check)
            self.onCheck(self.compass_check)
            
            self.Enable()
            
            # LED Settings
            try:
                self.led_color.SetColour([i * 255.0 for i in sensor.getLEDColor()])
            except:
                self.led_color.SetColour([0, 0, 0])
            
            try:
                mode = sensor.getLEDMode()
                if mode is not None:
                    self.enableLEDMode()
                    if mode:
                        self.led_static.SetValue(True)
                    else:
                        self.led_normal.SetValue(True)
                else:
                    self.disableLEDMode()
            except:
                self.disableLEDMode()
        
        self.apply_button.Disable()
        self.commit_button.Disable()
    
    def onCheck(self, event):
        evt_id = event.GetId()
        is_enable = event.IsChecked()
        if evt_id == self.accel_check.GetId():
            self.is_accel_update = True
            if is_enable:
                self.FindWindowByName("accel_trust").Enable()
                self.accel_min.Enable()
                self.FindWindowByName("accel_to").Enable()
                self.accel_max.Enable()
            else:
                self.FindWindowByName("accel_trust").Disable()
                self.accel_min.Disable()
                self.FindWindowByName("accel_to").Disable()
                self.accel_max.Disable()
        
        elif evt_id == self.compass_check.GetId():
            self.is_compass_update = True
            if is_enable:
                self.FindWindowByName("compass_trust").Enable()
                self.compass_min.Enable()
                self.FindWindowByName("compass_to").Enable()
                self.compass_max.Enable()
            else:
                self.FindWindowByName("compass_trust").Disable()
                self.compass_min.Disable()
                self.FindWindowByName("compass_to").Disable()
                self.compass_max.Disable()
        
        else:
            self.is_gyro_update = True
        
        self.apply_button.Enable()
        self.commit_button.Enable()
    
    def onRadio(self, event):
        self.is_led_mode_update = True
        
        self.apply_button.Enable()
        self.commit_button.Enable()
    
    def onSpinCtrl(self, event):
        evt_id = event.GetId()
        
        if evt_id == self.accel_max.GetId() or evt_id == self.accel_min.GetId():
            self.is_accel_trust_update = True
        elif evt_id == self.compass_max.GetId() or evt_id == self.compass_min.GetId():
            self.is_compass_trust_update = True
        elif evt_id == self.avg_percent.GetId():
            self.is_avg_update = True
        elif evt_id == self.sample_rate.GetId():
            self.is_sample_update = True
        else:
            self.is_update_update = True
        
        self.apply_button.Enable()
        self.commit_button.Enable()
    
    def onColourSelect(self, event):
        self.is_led_color_update = True
        self.apply_button.Enable()
        self.commit_button.Enable()
    
    def setSettings(self, sensor):
        # LED Settings
        if self.is_led_color_update:
            self.is_led_color_update = False
            if not sensor.setLEDColor([i / 255.0 for i in self.led_color.GetColour()]):
                self.is_led_color_update = True
        if self.is_led_mode_update:
            self.is_led_mode_update = False
            if not sensor.setLEDMode(self.led_static.GetValue()):
                self.is_led_mode_update = True
        
        # Accelerometer Settings
        if self.is_accel_update:
            self.is_accel_update = False
            if not sensor.setAccelerometerEnabled(self.accel_check.GetValue()):
                self.is_accel_update = True
        if self.is_accel_trust_update:
            self.is_accel_trust_update = False
            min_val = self.accel_min.GetValue()
            max_val = self.accel_max.GetValue()
            if not sensor.setConfidenceAccelerometerTrustValues(min_val, max_val):
                self.is_accel_trust_update = True
        
        # Compass Settings
        if self.is_compass_update:
            self.is_compass_update = False
            if not sensor.setCompassEnabled(self.compass_check.GetValue()):
                self.is_compass_update = True
        if self.is_compass_trust_update:
            self.is_compass_trust_update = False
            min_val = self.compass_min.GetValue()
            max_val = self.compass_max.GetValue()
            if not sensor.setConfidenceCompassTrustValues(min_val, max_val):
                self.is_compass_trust_update = True
        
        # Gyroscope Settings
        if self.is_gyro_update:
            self.is_gyro_update = False
            if not sensor.setGyroscopeEnabled(self.gyro_check.GetValue()):
                self.is_gyro_update = True
        
        # Other Settings
        if self.is_update_update:
            self.is_update_update = False
            if not sensor.setDesiredUpdateRate(self.update_rate.GetValue()):
                self.is_update_update = True
        if self.is_sample_update:
            self.is_sample_update = False
            if not sensor.setOversampleRate(self.sample_rate.GetValue()):
                self.is_sample_update = True
        if self.is_avg_update:
            self.is_avg_update = False
            if not sensor.setRunningAveragePercent(self.avg_percent.GetValue()):
                self.is_avg_update = True
        
        self.apply_button.Disable()
        self.commit_button.Disable()
    
    def setBinds(self, win):
        """ Sets the binds for the LEDCompPanel class and its attributes.
            
            Args:
                win: A reference to the main window, a wxPython object.
        """
        # Colour Select Binds
        self.led_color.Bind(colour_sel.EVT_COLOURSELECT, self.onColourSelect)
        
        # Radio Button Binds
        self.led_static.Bind(wx.EVT_RADIOBUTTON, self.onRadio)
        self.led_normal.Bind(wx.EVT_RADIOBUTTON, self.onRadio)
        
        # Check Box Binds
        self.accel_check.Bind(wx.EVT_CHECKBOX, self.onCheck)
        self.compass_check.Bind(wx.EVT_CHECKBOX, self.onCheck)
        self.gyro_check.Bind(wx.EVT_CHECKBOX, self.onCheck)
        
        # SpinCtrl Binds
        self.accel_max.Bind(wx.EVT_SPINCTRL, self.onSpinCtrl)
        self.accel_min.Bind(wx.EVT_SPINCTRL, self.onSpinCtrl)
        self.compass_max.Bind(wx.EVT_SPINCTRL, self.onSpinCtrl)
        self.compass_min.Bind(wx.EVT_SPINCTRL, self.onSpinCtrl)
        self.avg_percent.Bind(wx.EVT_SPINCTRL, self.onSpinCtrl)
        self.sample_rate.Bind(wx.EVT_SPINCTRL, self.onSpinCtrl)
        self.update_rate.Bind(wx.EVT_SPINCTRL, self.onSpinCtrl)
        
        # Button Binds
        self.apply_button.Bind(wx.EVT_BUTTON, win.onApplyButton)
        self.commit_button.Bind(wx.EVT_BUTTON, win.onApplyCommitSettings)


### wxPanel ###
class OrientPanel(wx.Panel):
    
    """ A wxPython Panel object.
        
        Attributes:
            apply_button: A wx.Button instance that applies the orientation
                placement for the sensor.
            apply_func: A function that applies the orientation placement for
                the sensor.
            orient_axis: An integer denoting the axis direction to manipulate
                the sensor's quaternion to.
            orient_dir: A Matrix4 instance denoting the orientation direction of
                the sensor.
            sensor_canvas: A SensorCanvas instance.
            x_rot: A wx.FloatSpin instance used to denote the x-value in an
                Euler.
            y_rot: A wx.FloatSpin instance used to denote the y-value in an
                Euler.
            z_rot: A wx.FloatSpin instance used to denote the z-value in an
                Euler.
    """
    def __init__(self, parent, sensor_canvas):
        """ Initializes the OrientPanel class.
            
            Args:
                parent: A reference to another wxPython object.
        """
        wx.Panel.__init__(self, parent)
        
        self.orient_axis = 8
        self.orient_dir = Matrix4()
        self.apply_func = None
        self.sensor_canvas = sensor_canvas
        
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        w, h = parent.GetSize()
        
        ## Orientation Section ##
        # Orientation Box
        orient_box = wx.StaticBox(self, -1, "Orientation Placement")
        font = orient_box.GetFont()
        font.SetPointSize(15)
        orient_box.SetFont(font)
        orient_box_sizer = wx.StaticBoxSizer(orient_box, wx.HORIZONTAL)
        orient_box_sizer.SetMinSize((w - 20, -1))
        
        # Euler Angles
        euler_grid = wx.BoxSizer(wx.VERTICAL)
        euler_vals_grid = wx.BoxSizer(wx.HORIZONTAL)
        self.x_rot= float_spin.FloatSpin(self, wx.NewId(), size=(60, -1), increment=0.1, digits=2)
        self.y_rot= float_spin.FloatSpin(self, wx.NewId(), size=(60, -1), increment=0.1, digits=2)
        self.z_rot= float_spin.FloatSpin(self, wx.NewId(), size=(60, -1), increment=0.1, digits=2)
        
        euler_vals_grid.Add(wx.StaticText(self, -1, "X"), 0, wx.ALIGN_CENTER_VERTICAL)
        euler_vals_grid.AddSpacer((5, 0))
        euler_vals_grid.Add(self.x_rot, 0, wx.ALIGN_CENTER_VERTICAL)
        euler_vals_grid.AddSpacer((10, 0))
        euler_vals_grid.Add(wx.StaticText(self, -1, "Y"), 0, wx.ALIGN_CENTER_VERTICAL)
        euler_vals_grid.AddSpacer((5, 0))
        euler_vals_grid.Add(self.y_rot, 0, wx.ALIGN_CENTER_VERTICAL)
        euler_vals_grid.AddSpacer((10, 0))
        euler_vals_grid.Add(wx.StaticText(self, -1, "Z"), 0, wx.ALIGN_CENTER_VERTICAL)
        euler_vals_grid.AddSpacer((5, 0))
        euler_vals_grid.Add(self.z_rot, 0, wx.ALIGN_CENTER_VERTICAL)
        
        euler_grid.Add(euler_vals_grid, 0)
        
        orient_box_sizer.AddSpacer((50, 0))
        orient_box_sizer.Add(euler_grid, 0, wx.EXPAND | wx.ALL)
        
        self.apply_button = wx.Button(self, wx.ID_APPLY, size=(150, -1))
        
        ## Box Sizer ##
        box_sizer.AddStretchSpacer()
        box_sizer.Add(orient_box_sizer, 0, wx.ALIGN_CENTER)
        box_sizer.AddStretchSpacer()
        box_sizer.Add(self.apply_button, 0, wx.ALIGN_CENTER)
        
        self.SetSizer(box_sizer)
        self.Disable()
    
    def initSettings(self, sensor_dir=None, func=None):
        """ Initializes the OrientPanel's attributes for the sensor.
            
            Args:
                sensor_dir: A matrix that denotes the orientation placement of a
                    sensor.
        """
        if sensor_dir is None:
            self.Disable()
        else:
            self.orient_axis = convertMatrix4ToAxisDir(sensor_dir)
            self.orient_dir = sensor_dir.copy()
            self.apply_func = func
            x_val, y_val, z_val = sensor_dir.toEuler().asDegreeArray()
            self.x_rot.SetValue(x_val)
            self.y_rot.SetValue(y_val)
            self.z_rot.SetValue(z_val)
            
            self.Enable()
            self.apply_button.Disable()
    
    def onSpinCtrl(self, event):
        tmp_mat = Euler([self.x_rot.GetValue(), self.y_rot.GetValue(), self.z_rot.GetValue()], is_degrees=True).toMatrix4()
        self.orient_axis = convertMatrix4ToAxisDir(tmp_mat)
        self.orient_dir = tmp_mat
        self.sensor_canvas.sensor_node.sensor_orient = tmp_mat.asColArray()
        if event is not None:
            self.apply_button.Enable()
    
    def onButton(self, event):
        self.apply_func()
        self.apply_button.Disable()
    
    def setBinds(self):
        """Sets the binds for the OrientPanel class and its attributes."""
        # SpinCtrl Binds
        self.x_rot.Bind(wx.EVT_SPINCTRL, self.onSpinCtrl)
        self.y_rot.Bind(wx.EVT_SPINCTRL, self.onSpinCtrl)
        self.z_rot.Bind(wx.EVT_SPINCTRL, self.onSpinCtrl)
        
        # Button Binds
        self.apply_button.Bind(wx.EVT_BUTTON, self.onButton)


### wxPanel ###
class DonglePanel(wx.Panel):
    
    """ A wxPython Panel object.
        
        Attributes:
            apply_button: A wx.Button instance used to apply the updated
                settings to the selected dongle.
            channel: A wx.Choice instance used to denote the wireless channel
                for the selected dongle.
            channel_table: A list of wx.Gauge instances used to denote the noise
                level of the wireless channels for the selected dongle.
            commit_button: A wx.Button instance used to apply and commit the
                updated settings to the selected dongle.
            is_chan_update: A boolean that denotes if the wireless channel on
                the selected dongle needs updated.
            is_led_color_update: A boolean that denotes if the LED color of the
                selected dongle needs updated.
            is_led_mode_update: A boolean that denotes if the LED mode on the
                selected dongle needs updated.
            is_pan_update: A boolean that denotes if the wireless pan id on the
                selected dongle needs updated.
            is_text_update: A boolean that denotes if the wireless table serial
                number(s) have been changed.
            led_color: A wx.ColourSelect instance that is use for the color of
                the LED on the selected dongle.
            led_normal: A wx.RadioButton instance that represents what LED mode
                the selected dongle is in.
            led_static: A wx.RadioButton instance that represents what LED mode
                the selected dongle is in.
            pan_id: A wx.SpinCtrl instance used to denote the wireless pan ID
                for the selected dongle.
            serial_text: A wx.StaticText instance used to denote the serial
                number for the selected dongle.
            valid_commands: A list of valid event key commands that can be
                performed on the wireless_table.
            valid_entry: A string of valid characters that can be used in the
                wireless_table.
            version_text: A wx.StaticText instance that denotes the version of
                the selected dongle.
            wireless_table: A list of wx.TextCtrl instances used to denote the
                serial numbers of wireless sensors that are paired with the
                selected dongle.
    """
    def __init__(self, parent):
        """ Initializes the DonglePanel class.
            
            Args:
                parent: A reference to another wxPython object.
        """
        wx.Panel.__init__(self, parent)
        
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.valid_entry = "0123456789ABCDEFabcdef"
        self.valid_commands = [8, 9, 13, 127, 314, 315, 316, 317]
        
        w, h = parent.GetSize()
        
        ## Sensor Information ##
        info_box = wx.StaticBox(self, -1, "Sensor Information")
        font = info_box.GetFont()
        font.SetPointSize(15)
        info_box.SetFont(font)
        info_box_sizer = wx.StaticBoxSizer(info_box, wx.HORIZONTAL)
        info_box_sizer.SetMinSize((w - 20, -1))
        
        font = wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        
        # Sensor Serial & Version
        serial_grid = wx.BoxSizer(wx.HORIZONTAL)
        self.serial_text = wx.StaticText(self, -1, "N/A    ")
        tmp_text = wx.StaticText(self, -1, "Serial Number:")
        tmp_text.SetFont(font)
        serial_grid.Add(tmp_text, 0)
        serial_grid.Add((5, 0))
        serial_grid.Add(self.serial_text, 0)
        
        version_grid = wx.BoxSizer(wx.HORIZONTAL)
        self.version_text = wx.StaticText(self, -1, "N/A    ")
        tmp_text = wx.StaticText(self, -1, "Version:")
        tmp_text.SetFont(font)
        version_grid.Add(tmp_text, 0)
        version_grid.AddSpacer((5, 0))
        version_grid.Add(self.version_text, 0)
        
        info_box_sizer.AddSpacer((50, 0))
        info_box_sizer.Add(serial_grid, 0)
        info_box_sizer.AddSpacer((50, 0))
        info_box_sizer.Add(version_grid, 0)
        
        ## LED Settings ##
        led_box = wx.StaticBox(self, -1, "LED Settings")
        font = led_box.GetFont()
        font.SetPointSize(15)
        led_box.SetFont(font)
        led_box_sizer = wx.StaticBoxSizer(led_box, wx.HORIZONTAL)
        led_box_sizer.SetMinSize((w - 20, -1))
        
        # LED Color
        color_grid = wx.BoxSizer(wx.HORIZONTAL)
        self.led_color = colour_sel.ColourSelect(self, wx.NewId())
        
        color_grid.Add(wx.StaticText(self, -1, "LED Color:"), 0, wx.ALIGN_CENTER_VERTICAL)
        color_grid.Add((10, 0))
        color_grid.Add(self.led_color, 0)
        
        # LED Mode
        mode_grid = wx.BoxSizer(wx.HORIZONTAL)
        self.led_normal = wx.RadioButton(self, wx.NewId(), "Normal", style=wx.RB_GROUP)
        self.led_static = wx.RadioButton(self, wx.NewId(), "Static")
        
        mode_grid.Add(wx.StaticText(self, -1, "LED Mode:", name="led_mode"), 0, wx.ALIGN_CENTER_VERTICAL)
        mode_grid.AddSpacer((10, 0))
        mode_grid.Add(self.led_normal, 0)
        mode_grid.AddSpacer((5, 0))
        mode_grid.Add(self.led_static, 0)
        
        led_option_sizer = wx.BoxSizer(wx.VERTICAL)
        led_option_sizer.Add(color_grid, 0, wx.EXPAND | wx.ALL)
        led_option_sizer.AddSpacer((0, 10))
        led_option_sizer.Add(mode_grid, 0, wx.EXPAND | wx.ALL)
        
        led_box_sizer.AddSpacer((125, 0))
        led_box_sizer.Add(led_option_sizer, 0)
        
        ## Wireless Settings ##
        wireless_box = wx.StaticBox(self, -1, "Wireless Settings")
        font = wireless_box.GetFont()
        font.SetPointSize(15)
        wireless_box.SetFont(font)
        wireless_box_sizer = wx.StaticBoxSizer(wireless_box, wx.VERTICAL)
        wireless_box_sizer.SetMinSize((w - 20, -1))
        
        # Pan ID, Channel, Channel Noise
        pan_chan_box = wx.BoxSizer(wx.HORIZONTAL)
        # Pan ID
        self.pan_id = wx.SpinCtrl(self, wx.NewId(), '', size=(60, -1), style=wx.SP_WRAP | wx.SP_ARROW_KEYS, min=1, max=65534, initial=1)
        
        # Channel
        channels = ["%d"] * 16
        for i in range(16):
            channels[i] = channels[i] % (i + 11)
        self.channel = wx.Choice(self, wx.NewId(), size=(60, -1), choices=channels)
        
        
        pan_chan_box.Add(wx.StaticText(self, -1, "Pan ID:"), 0, wx.ALIGN_CENTER_VERTICAL)
        pan_chan_box.AddSpacer((5, 0))
        pan_chan_box.Add(self.pan_id, 0)
        pan_chan_box.AddSpacer((10, 0))
        pan_chan_box.Add(wx.StaticText(self, -1, "Channel:"), 0, wx.ALIGN_CENTER_VERTICAL)
        pan_chan_box.AddSpacer((5, 0))
        pan_chan_box.Add(self.channel, 0)
        
        table_box = wx.BoxSizer(wx.HORIZONTAL)
        
        # Channel Noise
        channel_noise_box = wx.StaticBox(self, -1, "Channel Quality")
        channel_noise_box_sizer = wx.StaticBoxSizer(channel_noise_box, wx.VERTICAL)
        channel_grid1 = wx.BoxSizer(wx.HORIZONTAL)
        channel_grid2 = wx.BoxSizer(wx.HORIZONTAL)
        channel_grid3 = wx.BoxSizer(wx.HORIZONTAL)
        channel_grid4 = wx.BoxSizer(wx.HORIZONTAL)
        channel_grid5 = wx.BoxSizer(wx.HORIZONTAL)
        channel_grid6 = wx.BoxSizer(wx.HORIZONTAL)
        channel_grid7 = wx.BoxSizer(wx.HORIZONTAL)
        channel_grid8 = wx.BoxSizer(wx.HORIZONTAL)
        self.channel_table = []
        for i in range(16):
            self.channel_table.append(wx.Gauge(self, wx.NewId(), 10, size=(10, 18), style=wx.GA_VERTICAL))
            self.channel_table[i].SetValue(10)
            self.channel_table[i].SetForegroundColour((0, 255, 0))
            
            # Channels 11 & 19
            if i == 0 or i == 8:
                j = i + 11
                channel_grid1.Add(wx.StaticText(self, -1, "%d" % j), 0, wx.ALIGN_CENTER_VERTICAL)
                channel_grid1.AddSpacer((5, 0))
                channel_grid1.Add(self.channel_table[i], 0)
                if j < 19:
                    channel_grid1.InsertSpacer(0, (5, 0))
                    channel_grid1.AddSpacer((15, 0))
                else:
                    channel_grid1.AddSpacer((10, 0))
            # Channels 12 & 20
            elif i == 1 or i == 9:
                j = i + 11
                channel_grid2.Add(wx.StaticText(self, -1, "%d" % j), 0, wx.ALIGN_CENTER_VERTICAL)
                channel_grid2.AddSpacer((5, 0))
                channel_grid2.Add(self.channel_table[i], 0)
                if j < 19:
                    channel_grid2.InsertSpacer(0, (5, 0))
                    channel_grid2.AddSpacer((15, 0))
                else:
                    channel_grid2.AddSpacer((10, 0))
            # Channels 13 & 21
            elif i == 2 or i == 10:
                j = i + 11
                channel_grid3.Add(wx.StaticText(self, -1, "%d" % j), 0, wx.ALIGN_CENTER_VERTICAL)
                channel_grid3.AddSpacer((5, 0))
                channel_grid3.Add(self.channel_table[i], 0)
                if j < 19:
                    channel_grid3.InsertSpacer(0, (5, 0))
                    channel_grid3.AddSpacer((15, 0))
                else:
                    channel_grid3.AddSpacer((10, 0))
            # Channels 14 & 22
            elif i == 3 or i == 11:
                j = i + 11
                channel_grid4.Add(wx.StaticText(self, -1, "%d" % j), 0, wx.ALIGN_CENTER_VERTICAL)
                channel_grid4.AddSpacer((5, 0))
                channel_grid4.Add(self.channel_table[i], 0)
                if j < 19:
                    channel_grid4.InsertSpacer(0, (5, 0))
                    channel_grid4.AddSpacer((15, 0))
                else:
                    channel_grid4.AddSpacer((10, 0))
            # Channels 15 & 23
            elif i == 4 or i == 12:
                j = i + 11
                channel_grid5.Add(wx.StaticText(self, -1, "%d" % j), 0, wx.ALIGN_CENTER_VERTICAL)
                channel_grid5.AddSpacer((5, 0))
                channel_grid5.Add(self.channel_table[i], 0)
                if j < 19:
                    channel_grid5.InsertSpacer(0, (5, 0))
                    channel_grid5.AddSpacer((15, 0))
                else:
                    channel_grid5.AddSpacer((10, 0))
            # Channels 16 & 24
            elif i == 5 or i == 13:
                j = i + 11
                channel_grid6.Add(wx.StaticText(self, -1, "%d" % j), 0, wx.ALIGN_CENTER_VERTICAL)
                channel_grid6.AddSpacer((5, 0))
                channel_grid6.Add(self.channel_table[i], 0)
                if j < 19:
                    channel_grid6.InsertSpacer(0, (5, 0))
                    channel_grid6.AddSpacer((15, 0))
                else:
                    channel_grid6.AddSpacer((10, 0))
            # Channels 17 & 25
            elif i == 6 or i == 14:
                j = i + 11
                channel_grid7.Add(wx.StaticText(self, -1, "%d" % j), 0, wx.ALIGN_CENTER_VERTICAL)
                channel_grid7.AddSpacer((5, 0))
                channel_grid7.Add(self.channel_table[i], 0)
                if j < 19:
                    channel_grid7.InsertSpacer(0, (5, 0))
                    channel_grid7.AddSpacer((15, 0))
                else:
                    channel_grid7.AddSpacer((10, 0))
            # Channels 18 & 26
            elif i == 7 or i == 15:
                j = i + 11
                channel_grid8.Add(wx.StaticText(self, -1, "%d" % j), 0, wx.ALIGN_CENTER_VERTICAL)
                channel_grid8.AddSpacer((5, 0))
                channel_grid8.Add(self.channel_table[i], 0)
                if j < 19:
                    channel_grid8.InsertSpacer(0, (5, 0))
                    channel_grid8.AddSpacer((15, 0))
                else:
                    channel_grid8.AddSpacer((10, 0))
        
        channel_noise_box_sizer.Add(channel_grid1, 0)
        channel_noise_box_sizer.AddSpacer((0, 5))
        channel_noise_box_sizer.Add(channel_grid2, 0)
        channel_noise_box_sizer.AddSpacer((0, 5))
        channel_noise_box_sizer.Add(channel_grid3, 0)
        channel_noise_box_sizer.AddSpacer((0, 5))
        channel_noise_box_sizer.Add(channel_grid4, 0)
        channel_noise_box_sizer.AddSpacer((0, 5))
        channel_noise_box_sizer.Add(channel_grid5, 0)
        channel_noise_box_sizer.AddSpacer((0, 5))
        channel_noise_box_sizer.Add(channel_grid6, 0)
        channel_noise_box_sizer.AddSpacer((0, 5))
        channel_noise_box_sizer.Add(channel_grid7, 0)
        channel_noise_box_sizer.AddSpacer((0, 5))
        channel_noise_box_sizer.Add(channel_grid8, 0)
        
        # Wireless Table
        wireless_table_box = wx.StaticBox(self, -1, "Wireless Table")
        wireless_table_box_sizer = wx.StaticBoxSizer(wireless_table_box, wx.VERTICAL)
        wireless_grid1 = wx.BoxSizer(wx.HORIZONTAL)
        wireless_grid2 = wx.BoxSizer(wx.HORIZONTAL)
        wireless_grid3 = wx.BoxSizer(wx.HORIZONTAL)
        wireless_grid4 = wx.BoxSizer(wx.HORIZONTAL)
        wireless_grid5 = wx.BoxSizer(wx.HORIZONTAL)
        wireless_grid6 = wx.BoxSizer(wx.HORIZONTAL)
        wireless_grid7 = wx.BoxSizer(wx.HORIZONTAL)
        wireless_grid8 = wx.BoxSizer(wx.HORIZONTAL)
        self.wireless_table = []
        for i in range(15):
            self.wireless_table.append(wx.TextCtrl(self, wx.NewId(), "00000000", size=(100, 18), style=wx.TE_PROCESS_ENTER))
            self.wireless_table[-1].SetMaxLength(8)
            
            # Table 0 & 8
            if i == 0 or i == 8:
                wireless_grid1.Add(wx.StaticText(self, -1, "%d." % i), 0, wx.ALIGN_CENTER_VERTICAL)
                wireless_grid1.AddSpacer((5, 0))
                wireless_grid1.Add(self.wireless_table[i], 0)
                if i < 8:
                    wireless_grid1.AddSpacer((15, 0))
            # Table 1 & 9
            elif i == 1 or i == 9:
                wireless_grid2.Add(wx.StaticText(self, -1, "%d." % i), 0, wx.ALIGN_CENTER_VERTICAL)
                wireless_grid2.AddSpacer((5, 0))
                wireless_grid2.Add(self.wireless_table[i], 0)
                if i < 8:
                    wireless_grid2.AddSpacer((15, 0))
            # Table 2 & 10
            elif i == 2 or i == 10:
                wireless_grid3.Add(wx.StaticText(self, -1, "%d." % i), 0, wx.ALIGN_CENTER_VERTICAL)
                wireless_grid3.AddSpacer((5, 0))
                wireless_grid3.Add(self.wireless_table[i], 0)
                if i < 8:
                    wireless_grid3.AddSpacer((10, 0))
            # Table 3 & 11
            elif i == 3 or i == 11:
                wireless_grid4.Add(wx.StaticText(self, -1, "%d." % i), 0, wx.ALIGN_CENTER_VERTICAL)
                wireless_grid4.AddSpacer((5, 0))
                wireless_grid4.Add(self.wireless_table[i], 0)
                if i < 8:
                    wireless_grid4.AddSpacer((10, 0))
            # Table 4 & 12
            elif i == 4 or i == 12:
                wireless_grid5.Add(wx.StaticText(self, -1, "%d." % i), 0, wx.ALIGN_CENTER_VERTICAL)
                wireless_grid5.AddSpacer((5, 0))
                wireless_grid5.Add(self.wireless_table[i], 0)
                if i < 8:
                    wireless_grid5.AddSpacer((10, 0))
            # Table 5 & 13
            elif i == 5 or i == 13:
                wireless_grid6.Add(wx.StaticText(self, -1, "%d." % i), 0, wx.ALIGN_CENTER_VERTICAL)
                wireless_grid6.AddSpacer((5, 0))
                wireless_grid6.Add(self.wireless_table[i], 0)
                if i < 8:
                    wireless_grid6.AddSpacer((10, 0))
            # Table 6 & 14
            elif i == 6 or i == 14:
                wireless_grid7.Add(wx.StaticText(self, -1, "%d." % i), 0, wx.ALIGN_CENTER_VERTICAL)
                wireless_grid7.AddSpacer((5, 0))
                wireless_grid7.Add(self.wireless_table[i], 0)
                if i < 8:
                    wireless_grid7.AddSpacer((10, 0))
            # Table 7
            else:
                wireless_grid8.Add(wx.StaticText(self, -1, "7."), 0, wx.ALIGN_CENTER_VERTICAL)
                wireless_grid8.AddSpacer((5, 0))
                wireless_grid8.Add(self.wireless_table[i], 0)
        
        wireless_table_box_sizer.Add(wireless_grid1, 0)
        wireless_table_box_sizer.AddSpacer((0, 5))
        wireless_table_box_sizer.Add(wireless_grid2, 0)
        wireless_table_box_sizer.AddSpacer((0, 5))
        wireless_table_box_sizer.Add(wireless_grid3, 0)
        wireless_table_box_sizer.AddSpacer((0, 5))
        wireless_table_box_sizer.Add(wireless_grid4, 0)
        wireless_table_box_sizer.AddSpacer((0, 5))
        wireless_table_box_sizer.Add(wireless_grid5, 0)
        wireless_table_box_sizer.AddSpacer((0, 5))
        wireless_table_box_sizer.Add(wireless_grid6, 0)
        wireless_table_box_sizer.AddSpacer((0, 5))
        wireless_table_box_sizer.Add(wireless_grid7, 0)
        wireless_table_box_sizer.AddSpacer((0, 5))
        wireless_table_box_sizer.Add(wireless_grid8, 0)
        
        table_box.AddSpacer((5, 0))
        table_box.Add(wireless_table_box_sizer, 0)
        table_box.AddSpacer((10, 0))
        table_box.Add(channel_noise_box_sizer, 0)
        table_box.AddSpacer((5, 0))
        
        wireless_box_sizer.Add(pan_chan_box, 0, wx.ALIGN_CENTER)
        wireless_box_sizer.AddSpacer((0, 5))
        wireless_box_sizer.Add(table_box, 0, wx.ALIGN_CENTER)
        
        ## Booleans ##
        self.is_chan_update = False
        self.is_led_color_update = False
        self.is_led_mode_update = False
        self.is_pan_update = False
        self.is_text_update = False
        
        ## Buttons ##
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.apply_button = wx.Button(self, wx.ID_APPLY, size=(150, -1))
        self.commit_button = wx.Button(self, wx.ID_APPLY, "Apply && &Commit", size=(150, -1))
        self.apply_button.Disable()
        self.commit_button.Disable()
        
        button_sizer.Add(self.apply_button, 0)
        button_sizer.AddSpacer((20, 0))
        button_sizer.Add(self.commit_button, 0)
        
        ## Box Sizer ##
        box_sizer.AddStretchSpacer()
        box_sizer.Add(info_box_sizer, 0, wx.ALIGN_CENTER)
        box_sizer.AddSpacer((0, 10))
        box_sizer.Add(led_box_sizer, 0, wx.ALIGN_CENTER)
        box_sizer.AddSpacer((0, 10))
        box_sizer.Add(wireless_box_sizer, 0, wx.ALIGN_CENTER)
        box_sizer.AddStretchSpacer()
        box_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER)
        
        self.SetSizer(box_sizer)
        self.Disable()
    
    def initSettings(self, dongle=None):
        """ Initializes the DonglePanel attributes with data from a passed in
            3-Space Sensor Dongle device.
            
            Args:
                dongle: A reference to a TSDongle object. (default is None)
        """
        if dongle is None:
            # Information Settings
            self.serial_text.SetLabel("N/A    ")
            self.version_text.SetLabel("N/A    ")
            
            # LED Settings
            self.led_color.SetColour([0, 0, 0])
            self.led_static.SetValue(False)
            
            # Pan ID and Channel Settings
            self.pan_id.SetValueString("N/A")
            chan_idx = self.channel.FindString("N/A")
            if chan_idx == -1:
                self.channel.Insert("N/A", 0)
            self.channel.SetSelection(0)
            
            # Channel Noise Settings
            self.updateChannelNoise(dongle)
            
            # Wireless Table Settings
            for i in range(15):
                self.wireless_table[i].SetValue("0" * 8)
            
            self.is_chan_update = False
            self.is_led_color_update = False
            self.is_led_mode_update = False
            self.is_pan_update = False
            self.is_text_update = False
            
            self.Disable()
            return False
        else:
            if not dongle.isConnected():
                self.is_chan_update = False
                self.is_led_color_update = False
                self.is_led_mode_update = False
                self.is_pan_update = False
                self.is_text_update = False
                
                self.Disable()
                return False
            # Information Settings
            self.serial_text.SetLabel(dongle.serial_number_hex)
            self.version_text.SetLabel(dongle.getFirmwareVersionString())
            
            # LED Settings
            color = [i * 255.0 for i in dongle.getLEDColor()]
            self.led_color.SetColour(color)
            mode = dongle.getLEDMode()
            if mode:
                self.led_static.SetValue(True)
            else:
                self.led_normal.SetValue(True)
            
            # Pan ID Settings
            self.pan_id.SetValue(dongle.getWirelessPanID())
            
            # Channel Settings
            chan_idx = self.channel.FindString("N/A")
            if chan_idx != -1:
                self.channel.Delete(chan_idx)
            self.channel.SetStringSelection(str(dongle.getWirelessChannel()))
            
            # Channel Noise Settings
            self.updateChannelNoise(dongle)
            
            # Wireless Table Settings
            for i in range(15):
                hw_id_hex = '{0:08X}'.format(dongle.wireless_table[i])
                self.wireless_table[i].SetValue(hw_id_hex)
            
            self.Enable()
        
        self.apply_button.Disable()
        self.commit_button.Disable()
        
        return True
    
    def onSpinCtrl(self, event):
        self.is_pan_update = True
        self.apply_button.Enable()
        self.commit_button.Enable()
    
    def onChoice(self, event):
        self.is_chan_update = True
        self.apply_button.Enable()
        self.commit_button.Enable()
    
    def onRadio(self, event):
        self.is_led_mode_update = True
        self.apply_button.Enable()
        self.commit_button.Enable()
    
    def onColourSelect(self, event):
        self.is_led_color_update = True
        self.apply_button.Enable()
        self.commit_button.Enable()
    
    def updateChannelNoise(self, dongle):
        if dongle is not None:
            channel_noise = dongle.getWirelessChannelNoiseLevels()
            if channel_noise is not None:
                for i in range(16):
                    val = ((255 - channel_noise[i]) / 25.5) + 1
                    if val < 2:
                        val = 2
                    self.channel_table[i].SetValue(val)
                    if val < 3.5:
                        self.channel_table[i].SetForegroundColour((255, 0, 0))
                    elif val < 6.5:
                        self.channel_table[i].SetForegroundColour((255, 255, 0))
                    else:
                        self.channel_table[i].SetForegroundColour((0, 255, 0))
            else:
                for i in range(16):
                    self.channel_table[i].SetValue(10)
        else:
            for i in range(16):
                self.channel_table[i].SetValue(10)
    
    def setSettings(self, dongle):
        # LED Settings
        if self.is_led_color_update:
            self.is_led_color_update = False
            color = self.led_color.GetColour()
            color = [i / 255.0 for i in color]
            dongle.setLEDColor(color)
        if self.is_led_mode_update:
            self.is_led_mode_update = False
            dongle.setLEDMode(self.led_static.GetValue())
        
        # Pan ID Settings
        if self.is_pan_update:
            self.is_pan_update = False
            dongle.setWirelessPanID(self.pan_id.GetValue())
        
        # Channel Settings
        if self.is_chan_update:
            self.is_chan_update = False
            dongle.setWirelessChannel(int(self.channel.GetStringSelection()))
        
        # Wireless Table Settings
        if self.is_text_update:
            for i in range(15):
                hw_id_hex = self.wireless_table[i].GetValue()
                hw_id = int(hw_id_hex, 16)
                if hw_id != 0:
                    if hw_id in global_sensor_list:
                        if global_sensor_list[hw_id].dongle == dongle:
                            continue
                    wl_sens = dongle.setSensorToDongle(i, hw_id)
                    if wl_sens is None:
                        print "Failed to find", hw_id_hex
                        continue
                    
                    if not wl_sens.switchToWiredMode():
                        wl_sens.switchToWirelessMode()
                    if wl_sens.isConnected():
                        print "Created TSWLSensor Wireless Serial:",
                        print hw_id_hex, "Firmware Date:",
                        print wl_sens.getFirmwareVersionString()
                    else:
                        print "Failed to add", hw_id_hex
                else:
                    wl_sens = dongle[i]
                    if wl_sens is not None:
                        if wl_sens.serial_number in global_sensor_list:
                            if not wl_sens.switchToWiredMode():
                                del global_sensor_list[wl_sens.serial_number]
                    dongle.setSensorToDongle(i, hw_id)
        
        self.apply_button.Disable()
        self.commit_button.Disable()
    
    def setBinds(self, win):
        """ Sets the binds for the DonglePanel class and its attributes.
            
            Args:
                win: A reference to the main window, a wxPython object.
        """
        # Colour Select Binds
        self.led_color.Bind(colour_sel.EVT_COLOURSELECT, self.onColourSelect)
        
        # Radio Button Binds
        self.led_static.Bind(wx.EVT_RADIOBUTTON, self.onRadio)
        self.led_normal.Bind(wx.EVT_RADIOBUTTON, self.onRadio)
        
        # SpinCtrl Binds
        self.pan_id.Bind(wx.EVT_SPINCTRL, self.onSpinCtrl)
        
        # Choice Binds
        self.channel.Bind(wx.EVT_CHOICE, self.onChoice)
        
        # TextCtrl Binds
        for i in range(15):
            self.wireless_table[i].Bind(wx.EVT_CHAR, win.onTextEntry)
            self.wireless_table[i].Bind(wx.EVT_TEXT_ENTER, win.onTextEntry)
            self.wireless_table[i].Bind(wx.EVT_KILL_FOCUS, win.onTextEntry)
        
        # Button Binds
        self.apply_button.Bind(wx.EVT_BUTTON, win.onApplyButton)
        self.commit_button.Bind(wx.EVT_BUTTON, win.onApplyCommitSettings)


### wxFrame ###
class SensorConfigurationWindow(wx.Frame):
    
    """ A wxPython Frame that creates the window for Sensor Configuration.
        
        Attributes:
            add_popup: A wx.Menu() used as a Popup for adding wireless devices
                to the dongle devices in the device tree.
            counter: An integer denoting how many milliseconds have passed.
            device_tree: A wx.TreeCtrl instance that holds the names of known
                3-Space Sensor devices. (name: 'device_type-serial_number_hex')
            dng_img: An image used for the DNG type devices of the device_tree.
            done_button: A wx.Button instance that closes the window.
            dongle_panel: A DonglePanel instance.
            dongle_popup: A wx.Menu() used as a Popup for dongle devices in the
                device tree.
            dongle_root: A wx.TreeItemId that is the root for dongle devices and
                wireless sensor devices communicating to the dongle devices.
            fail_img: An image used for unconnected devices of the device_tree.
            find_button: A wx.Button instance used to find more sensors.
            img_list: = A wx.ImageList instance that holds a list of images the
                device_tree uses.
            info_axis_panel: An InfoAxisPanel instance.
            led_comp_panel: A LEDCompPanel instance.
            mesh_init: A 4x4 Matrix orientation to be used as the initial
                    orientation for the sensor mesh.
            notebook: A wx.Notebook instance that holds pages for changing
                settings for the selected sensor and dongle.
            orient_panel: An OrientPanel instance.
            redraw: A boolean that denotes a redraw needs to take place.
            root_img: An image used for the roots of the device_tree.
            paired_img: An image used for paired wireless devices of the
                device_tree that cannot communicate wirelessly at the moment.
            selected_dongle: A reference to an instance of a TSDongle object.
            selected_sensor: A reference to an instance of a TSSensor object.
            sensor_canvas: A SensorCanvas instance.
            sensor_popup: A wx.Menu() used as a Popup for sensor devices in the
                device tree.
            sensor_root: A wx.TreeItemId that is the root for sensor devices
                connected via USB
            tare_panel: A TarePanel instance.
            update_timer: A wx.Timer instance that is used to update the Frame.
            usb_img: An image used for the USB type devices of the device_tree.
            wl_img: An image used for the wireless type devices of the
                device_tree.
    """
    global global_sensor_list, global_dongle_list
    def __init__(self, parent, size=wx.DefaultSize, title="Sensor Configuration Window"):
        """ Initializes the SensorConfigurationWindow class.
            
            Args:
                parent: A reference to another wxPython object.
                size: A tuple that stores a width and height for the Dialog.
                    (default is wx.DefaultSize)
                title: A string that denotes the title of the Dialog window.
                    (default is "Sensor Configuration Dialog")
        """
        wx.Frame.__init__(self, parent, -1, title, size=size, style=wx.DEFAULT_FRAME_STYLE)
        
        self.SetMinSize(SENS_CONF_SIZE)
        self.SetBackgroundColour((212, 208, 200))
        
        if parent is not None:
            self.SetIcon(parent.GetIcon())
        else:
            self.SetIcon(wx.Icon(os.path.join(_dir_path, "media\\3Space_Icon.ico"), wx.BITMAP_TYPE_ICO))
        
        w, h = self.GetSize()
        
        inner_box1 = wx.BoxSizer(wx.VERTICAL)
        inner_box2 = wx.BoxSizer(wx.HORIZONTAL)
        outer_box = wx.BoxSizer(wx.VERTICAL)
        
        # Timer for updating the glcanvas
        self.update_timer = wx.Timer(self)
        
        self.redraw = False
        
        # A counter for how many seconds have passed
        self.counter = 0
        
        ## Sensor Section ##
        self.selected_sensor = None
        self.selected_dongle = None
        
        self.sensor_canvas = SensorCanvas(self, (200, 200))
        self.mesh_init = [
            0.707107, 0.3536, -0.6124, 0,
            0, 0.866, 0.5, 0,
            0.707107, -0.3536, 0.6124, 0,
            0, 0, 0, 1
        ]
        self.sensor_canvas.setSensor(orient=self.mesh_init)
        
        sensor_box = wx.StaticBox(self, -1)
        sensor_box_sizer = wx.StaticBoxSizer(sensor_box, wx.VERTICAL)
        
        self.find_button = wx.Button(self, wx.ID_REFRESH, "Find Devices", size=(100, -1))
        
        self.device_tree = wx.TreeCtrl(self, wx.NewId(), size=(w - 482, h - 322), style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT)
        
        self.img_list = wx.ImageList(16, 16)
        self.root_img = self.img_list.Add(wx.Bitmap(os.path.join(_dir_path, "media\\3-Space_Logo.jpg")))
        self.usb_img = self.img_list.Add(wx.Bitmap(os.path.join(_dir_path, "media\\USB.jpg")))
        self.dng_img = self.img_list.Add(wx.Bitmap(os.path.join(_dir_path, "media\\Dongle.jpg")))
        self.wl_img = self.img_list.Add(wx.Bitmap(os.path.join(_dir_path, "media\\Wireless.jpg")))
        #self.fail_img = self.img_list.Add(wx.Bitmap(os.path.join(_dir_path, "media\\Error.png")))
        #self.paired_img = self.img_list.Add(wx.Bitmap(os.path.join(_dir_path, "media\\Paired.png")))
        
        self.device_tree.AssignImageList(self.img_list)
        
        root = self.device_tree.AddRoot("3-Space Sensor Devices")
        
        self.sensor_root = self.device_tree.AppendItem(root, "Wired Sensors", self.root_img)
        
        self.dongle_root = self.device_tree.AppendItem(root, "Dongles & Paired Sensors", self.root_img)
        
        
        sensor_box_sizer.AddSpacer((0, 5))
        sensor_box_sizer.Add(self.find_button, 0, wx.ALIGN_CENTER)
        sensor_box_sizer.AddSpacer((0, 5))
        sensor_box_sizer.Add(self.device_tree, 1, wx.EXPAND)
        
        ## Inner Box 1 ##
        inner_box1.Add(self.sensor_canvas, 0, wx.ALIGN_CENTER)
        inner_box1.AddSpacer((0, 10))
        inner_box1.Add(sensor_box_sizer, 1, wx.EXPAND)
        
        
        ## Notebook Section ##
        self.notebook = wx.Notebook(self, size=(450, h - 65))
        #self.info_axis_panel = InfoAxisPanel(self.notebook)
        self.tare_panel = TarePanel(self.notebook)
        self.led_comp_panel = LEDCompPanel(self.notebook)
        self.orient_panel = OrientPanel(self.notebook, self.sensor_canvas)
        self.dongle_panel = DonglePanel(self.notebook)
        #self.notebook.AddPage(self.info_axis_panel, "Info && Axis Directions")
        self.notebook.AddPage(self.tare_panel, "Tare")
        self.notebook.AddPage(self.led_comp_panel, "LED && Components")
        self.notebook.AddPage(self.orient_panel, "Orientation Placement")
        self.notebook.AddPage(self.dongle_panel, "Dongle Settings")
        #self.notebook.RemovePage(4)
        self.notebook.RemovePage(3)
        
        
        ## Inner Box 2 ##
        inner_box2.AddSpacer((5, 0))
        inner_box2.Add(inner_box1, 1, wx.EXPAND)
        inner_box2.AddSpacer((5, 0))
        inner_box2.Add(self.notebook, 0, wx.EXPAND)
        inner_box2.AddSpacer((5, 0))
        
        
        ## Button Box ##
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.done_button = wx.Button(self, wx.ID_OK, "Done")
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(self.done_button, 0)
        btn_sizer.AddSpacer((5, 0))
        
        ## Outer Box ##
        outer_box.AddSpacer((0, 5))
        outer_box.Add(inner_box2, 1, wx.EXPAND)
        outer_box.AddSpacer((0, 10))
        outer_box.Add(btn_sizer, 0, wx.EXPAND)
        
        
        ## Frame Layout ##
        self.SetAutoLayout(True)
        self.SetSizer(outer_box)
        self.Layout()
        
        
        ## Popup Menus ##
        # Dongle
        self.dongle_popup = wx.Menu()
        menu_item = self.dongle_popup.Append(wx.NewId(), "Auto Pair")
        self.Bind(wx.EVT_MENU, self.onAutoPair, menu_item)
        menu_item = self.dongle_popup.Append(wx.NewId(), "Clear")
        self.Bind(wx.EVT_MENU, self.onClear, menu_item)
        
        # Sensor
        self.sensor_popup = wx.Menu()
        
        # New
        self.add_popup = wx.Menu()
        
        
        ## Binds ##
        # Self Binds
        self.Bind(wx.EVT_TIMER, self.timeUpdate, self.update_timer)
        self.Bind(wx.EVT_SIZE, self.onWinSize)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        
        # Notebook Binds
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onSensorPageChanged)
        
        # Button Binds
        self.find_button.Bind(wx.EVT_BUTTON, self.onFindDevices)
        self.done_button.Bind(wx.EVT_BUTTON, self.onClose)
        
        # Tree Binds
        self.device_tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.onDeviceChoice)
        self.device_tree.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.onRightClick)
        
        # Panel Binds
        #self.info_axis_panel.setBinds(self)
        self.tare_panel.setBinds(self)
        self.led_comp_panel.setBinds(self)
        self.orient_panel.setBinds()
        self.dongle_panel.setBinds(self)
        
        self.updateTree()
    
    def findTreeItem(self, name, root):
        child = self.device_tree.GetLastChild(root)
        while child.IsOk():
            child_name = self.device_tree.GetItemText(child).split(': ')[-1]
            if child_name == name:
                return child
            if self.device_tree.ItemHasChildren(child):
                item = self.findTreeItem(name, child)
                if item is not None:
                    return item
            child = self.device_tree.GetPrevSibling(child)
        return None
    
    def updateTree(self, root=None):
        """ Updates the device tree.
            
            Args:
                root: A reference to a root that needs to update. If None, the
                    whole tree will update. (default is None)
        """
        if root is None:
            self.device_tree.DeleteChildren(self.sensor_root)
            self.device_tree.DeleteChildren(self.dongle_root)
            
            for sensor in global_sensor_list:
                dev_type = global_sensor_list[sensor].device_type
                if "WL" in dev_type and global_sensor_list[sensor].wireless_com:
                    continue
                sens = self.device_tree.AppendItem(self.sensor_root, dev_type + '-' + '{0:08X}'.format(sensor))
                if "USB" in dev_type:
                    self.device_tree.SetItemImage(sens, self.usb_img)
                else:
                    self.device_tree.SetItemImage(sens, self.wl_img)
            
            for dongle in global_dongle_list:
                dong = self.device_tree.AppendItem(self.dongle_root, "DNG-" + '{0:08X}'.format(dongle), self.dng_img)
                wl_table = global_dongle_list[dongle].wireless_table[:]
                for i in range(15):
                    i_str = str(i)
                    if i < 10:
                        i_str = '  ' + i_str
                    if wl_table[i] != 0:
                        id = wl_table[i]
                        id_hex = '{0:08X}'.format(id)
                        if id in global_sensor_list:
                            dev_type = global_sensor_list[id].device_type
                            if global_sensor_list[id].wireless_com:
                                self.device_tree.AppendItem(dong, i_str + ": " + dev_type + "-" + id_hex, self.wl_img)
                            else:
                                if global_sensor_list[id].dongle == dongle:
                                    self.device_tree.AppendItem(dong, i_str + ": " + dev_type + "-" + id_hex, self.paired_img)
                                else:
                                    self.device_tree.AppendItem(dong, i_str + ": " + dev_type + "-" + id_hex, self.fail_img)
                        else:
                            self.device_tree.AppendItem(dong, i_str + ": WL-" + id_hex, self.fail_img)
                    else:
                        self.device_tree.AppendItem(dong, i_str + ": None")
            
            self.device_tree.SortChildren(self.sensor_root)
            self.device_tree.SortChildren(self.dongle_root)
        else:
            tmp_dng = ""
            if self.selected_dongle is not None:
                tmp_dng = self.selected_dongle.serial_number
            self.device_tree.DeleteChildren(root)
            
            if root == self.sensor_root:
                for sensor in global_sensor_list:
                    dev_type = global_sensor_list[sensor].device_type
                    if "WL" in dev_type and global_sensor_list[sensor].wireless_com:
                        continue
                    sens = self.device_tree.AppendItem(root, dev_type + '-' + '{0:08X}'.format(sensor))
                    if "USB" in dev_type:
                        self.device_tree.SetItemImage(sens, self.usb_img)
                    else:
                        self.device_tree.SetItemImage(sens, self.wl_img)
            else:
                for dongle in global_dongle_list:
                    dong = self.device_tree.AppendItem(root, "DNG-" + '{0:08X}'.format(dongle), self.dng_img)
                    wl_table = global_dongle_list[dongle].wireless_table[:]
                    for i in range(15):
                        i_str = str(i)
                        if i < 10:
                            i_str = '  ' + i_str
                        if wl_table[i] != 0:
                            id = wl_table[i]
                            id_hex = '{0:08X}'.format(id)
                            if id in global_sensor_list:
                                dev_type = global_sensor_list[id].device_type
                                if global_sensor_list[id].wireless_com:
                                    self.device_tree.AppendItem(dong, i_str + ": " + dev_type + "-" + id_hex, self.wl_img)
                                else:
                                    if global_sensor_list[id].dongle == dongle:
                                        self.device_tree.AppendItem(dong, i_str + ": " + dev_type + "-" + id_hex, self.paired_img)
                                    else:
                                        self.device_tree.AppendItem(dong, i_str + ": " + dev_type + "-" + id_hex, self.fail_img)
                            else:
                                self.device_tree.AppendItem(dong, i_str + ": WL-" + id_hex, self.fail_img)
                        else:
                            self.device_tree.AppendItem(dong, i_str + ": None")
                    
                    if dongle == tmp_dng:
                        self.device_tree.SelectItem(dong)
            
            self.device_tree.SortChildren(root)
    
    def onSensorPageChanged(self, event):
        new = event.GetSelection()
        page_text = event.GetEventObject().GetPageText(new)
        if new == 3:
            if page_text != "Dongle Settings":
                self.sensor_canvas.is_orient = True
                self.orient_panel.onSpinCtrl(None)
            else:
                self.sensor_canvas.is_orient = False
        else:
            self.sensor_canvas.is_orient = False
        event.Skip()
    
    def onUpdateAxes(self, event):
        """ Updates the axis meshes to match accordingly to the axis directions
            of the selected sensor.
            
            Args:
                event: A wxPython event.
        """
        axis_dir = self.info_axis_panel.returnAxisValues()
        axis_order, x_neg, y_neg, z_neg = ts_api.parseAxisDirections(axis_dir)
        
        x_dir = Matrix3()
        y_dir = Matrix3()
        z_dir = Matrix3()
        
        # Check what axis directions are set and act accordingly
        if axis_order == 'XYZ':
            if x_neg:
                x_dir = Matrix3(MATRIX3_180_Y)
            if y_neg:
                y_dir = Matrix3(MATRIX3_180_X)
            if z_neg:
                z_dir = Matrix3(MATRIX3_180_X)
        
        elif axis_order == 'XZY':
            y_dir = Matrix3(MATRIX3_NEG_90_X)
            z_dir = Matrix3(MATRIX3_90_X)
            
            if x_neg:
                x_dir = Matrix3(MATRIX3_180_Y)
            if y_neg:
                y_dir = Matrix3(MATRIX3_180_X) * y_dir
            if z_neg:
                z_dir = Matrix3(MATRIX3_180_X) * z_dir
        
        elif axis_order == 'YXZ':
            x_dir = Matrix3(MATRIX3_90_Z)
            y_dir = Matrix3(MATRIX3_NEG_90_Z)
            
            if x_neg:
                x_dir = Matrix3(MATRIX3_180_X) * x_dir
            if y_neg:
                y_dir = Matrix3(MATRIX3_180_Y) * y_dir
            if z_neg:
                z_dir = Matrix3(MATRIX3_180_X)
        
        elif axis_order == 'YZX':
            x_dir = Matrix3(MATRIX3_90_Y)
            y_dir = Matrix3(MATRIX3_NEG_90_Z)
            z_dir = Matrix3(MATRIX3_90_X)
            
            if x_neg:
                x_dir = Matrix3(MATRIX3_180_X) * x_dir
            if y_neg:
                y_dir = Matrix3(MATRIX3_180_Y) * y_dir
            if z_neg:
                z_dir = Matrix3(MATRIX3_180_X) * z_dir
        
        elif axis_order == 'ZXY':
            x_dir = Matrix3(MATRIX3_90_Z)
            y_dir = Matrix3(MATRIX3_NEG_90_X)
            z_dir = Matrix3(MATRIX3_NEG_90_Y)
            
            if x_neg:
                x_dir = Matrix3(MATRIX3_180_X) * x_dir
            if y_neg:
                y_dir = Matrix3(MATRIX3_180_X) * y_dir
            if z_neg:
                z_dir = Matrix3(MATRIX3_180_Y) * z_dir
        
        else:
            x_dir = Matrix3(MATRIX3_90_Y)
            z_dir = Matrix3(MATRIX3_NEG_90_Y)
            
            if x_neg:
                x_dir = Matrix3(MATRIX3_180_X) * x_dir
            if y_neg:
                y_dir = Matrix3(MATRIX3_180_X)
            if z_neg:
                z_dir = Matrix3(MATRIX3_180_Y) * z_dir
        
        # Update meshes
        self.sensor_canvas.x_sensor_node.orient = x_dir.toMatrix4().asColArray()
        self.sensor_canvas.y_sensor_node.orient = y_dir.toMatrix4().asColArray()
        self.sensor_canvas.z_sensor_node.orient = z_dir.toMatrix4().asColArray()
    
    def onRightClick(self, event):
        item = event.GetItem()
        self.device_tree.SelectItem(item)
        sens_list = self.device_tree.GetItemText(self.sensor_root)
        dong_list = self.device_tree.GetItemText(self.dongle_root)
        if item.IsOk():
            item_name = self.device_tree.GetItemText(item)
            if item_name != sens_list and item_name != dong_list:
                mouse_pos = event.GetPoint()
                tree_pos = self.device_tree.GetPosition()
                pos = (mouse_pos[0] + tree_pos[0], mouse_pos[1] + tree_pos[1])
                item_name = item_name.split(': ')[-1]
                if item_name == "None":
                    id_list = global_sensor_list.keys()
                    id_list.sort()
                    for id in id_list:
                        sens = global_sensor_list[id]
                        if "WL" in sens.device_type:
                            tmp_name = sens.device_type + "-" + sens.serial_number_hex
                            if sens.wireless_com:
                                continue
                            if self.findTreeItem(tmp_name, self.dongle_root):
                                continue
                            menu_item = self.add_popup.Append(wx.NewId(), tmp_name)
                            self.Bind(wx.EVT_MENU, self.onSelect, menu_item)
                    self.PopupMenu(self.add_popup, pos)
                    menu_list = self.add_popup.GetMenuItems()
                    for i in range(len(menu_list) - 1, -1, -1):
                        self.add_popup.RemoveItem(menu_list[i]).Destroy()
                else:
                    sensor_type, id_hex = item_name.rsplit('-', 1)
                    id = int(id_hex, 16)
                    reconnect_item = None
                    disconnect_item = None
                    if sensor_type == "DNG":
                        if self.device_tree.GetItemImage(item) == self.fail_img:
                            reconnect_item = self.dongle_popup.Insert(0, wx.NewId(), "Reconnect")
                            self.Bind(wx.EVT_MENU, self.onReconnect, reconnect_item)
                        else:
                            disconnect_item = self.dongle_popup.Insert(2, wx.NewId(), "Disconnect")
                            self.Bind(wx.EVT_MENU, self.onDisconnect, disconnect_item)
                        self.PopupMenu(self.dongle_popup, pos)
                        if reconnect_item is not None:
                            self.dongle_popup.RemoveItem(reconnect_item)
                        if disconnect_item is not None:
                            self.dongle_popup.RemoveItem(disconnect_item)
                    elif "WL" in sensor_type and id in global_sensor_list and global_sensor_list[id].wireless_com:
                        menu_item = self.sensor_popup.Append(wx.NewId(), "Remove Sensor")
                        self.Bind(wx.EVT_MENU, self.onRemove, menu_item)
                        list_popup = wx.Menu()
                        self.sensor_popup.AppendMenu(wx.NewId(), "Change Sensor", list_popup)
                        for sens in global_sensor_list.values():
                            if "WL" in sens.device_type:
                                tmp_name = sens.device_type + "-" + sens.serial_number_hex
                                if sens.wireless_com:
                                    continue
                                menu_item = list_popup.Append(wx.NewId(), tmp_name)
                                self.Bind(wx.EVT_MENU, self.onSelect, menu_item)
                        if self.device_tree.GetItemImage(item) == self.fail_img:
                            reconnect_item = self.sensor_popup.Insert(0, wx.NewId(), "Reconnect")
                            self.Bind(wx.EVT_MENU, self.onReconnect, reconnect_item)
                        self.PopupMenu(self.sensor_popup, pos)
                        if reconnect_item is not None:
                            self.sensor_popup.RemoveItem(reconnect_item)
                        menu_list = list_popup.GetMenuItems()
                        for i in range(len(menu_list) - 1, -1, -1):
                            list_popup.RemoveItem(menu_list[i]).Destroy()
                        menu_list = self.sensor_popup.GetMenuItems()
                        for i in range(len(menu_list) - 1, -1, -1):
                            self.sensor_popup.RemoveItem(menu_list[i]).Destroy()
                    else:
                        if self.device_tree.GetItemImage(item) == self.fail_img:
                            reconnect_item = self.sensor_popup.Insert(0, wx.NewId(), "Reconnect")
                            self.Bind(wx.EVT_MENU, self.onReconnect, reconnect_item)
                        else:
                            disconnect_item = self.sensor_popup.Insert(0, wx.NewId(), "Disconnect")
                            self.Bind(wx.EVT_MENU, self.onDisconnect, disconnect_item)
                        self.PopupMenu(self.sensor_popup, pos)
                        if reconnect_item is not None:
                            self.sensor_popup.RemoveItem(reconnect_item)
                        if disconnect_item is not None:
                            self.sensor_popup.RemoveItem(disconnect_item)
    
    def onWinSize(self, event):
        self.redraw = True
        event.Skip()
    
    def timeUpdate(self, event):
        """ Updates the SensorCanvas object.
            
            Args:
                event: A wxPython event.
        """
        if self.redraw:
            w, h = self.GetSize()
            self.device_tree.SetSize((w - 482, h - 322))
            self.notebook.SetSize((450, h - 65))
            self.redraw = False
        
        # Refresh the glcanvas
        self.sensor_canvas.Refresh()
        if self.selected_sensor is not None:
            self.counter += 1
            if self.counter >= 50:
                self.counter = 0
                try:
                    bat_per = self.selected_sensor.getBatteryPercentRemaining()
                    if bat_per is not None:
                        self.info_axis_panel.percent_text.SetLabel("%d %%" % bat_per)
                    else:
                        self.info_axis_panel.percent_text.SetLabel("N/A    ")
                    bat_stat = self.selected_sensor.getBatteryStatus()
                    if bat_stat is not None:
                        if bat_stat == 1:
                            text = "Charged"
                        elif bat_stat == 2:
                            text = "Charging"
                        else:
                            text = "Draining"
                        self.info_axis_panel.status_text.SetLabel(text)
                    else:
                        self.info_axis_panel.status_text.SetLabel("N/A    ")
                except:
                    pass
        elif self.selected_dongle is not None:
            self.counter += 1
            if self.counter >= 50:
                self.counter = 0
                self.dongle_panel.updateChannelNoise(self.selected_dongle)
    
    def onClose(self, event):
        """ Closes the SensorConfigurationWindow but not destroying it.
            
            Args:
                event: A wxPython event.
        """
        if self.notebook.GetPageCount() == 4:
            self.notebook.SetSelection(0)
            self.notebook.RemovePage(3)
            self.device_tree.Enable()
        
        self.Show(False)  # Close the frame.
        self.update_timer.Stop()
        if self.selected_sensor is not None or self.selected_dongle is not None:
            self.device_tree.Unselect()
        self.selected_sensor = None
        self.selected_dongle = None
        self.sensor_canvas.setSensor(orient=self.mesh_init)
        if event is not None:
            if self.GetParent() is None:
                self.onAppClose(event)
            else:
                self.GetParent().onConfigureClose()
    
    def onAppClose(self, event):
        """ Closes the SensorConfigurationWindow and destroys it.
            
            Args:
                event: A wxPython event.
        """
        self.Unbind(wx.EVT_TIMER)
        for tss in global_sensor_list.values():
            tss.close()
        for dong in global_dongle_list.values():
            dong.close()
        self.device_tree.Unselect()
        self.Destroy()
    
    def onAutoPair(self, event):
        """ Automatically pairs TSWLSensors with TSDongles and commits the
            settings.
            
            Args:
                event: A wxPython event.
        """
        global global_updated_sensors
        
        root = self.device_tree.GetSelection()
        child, cookie = self.device_tree.GetFirstChild(root)
        sens_list = global_sensor_list.keys()
        for i in range(len(sens_list) - 1, -1, -1):
            sens = sens_list[i]
            if "WL" not in global_sensor_list[sens].device_type:
                del sens_list[i]
            elif sens in self.selected_dongle.wireless_table:
                del sens_list[i]
        sens_list.sort()
        pan_id = self.selected_dongle.getWirelessPanID()
        chan = self.selected_dongle.getWirelessChannel()
        while child.IsOk() and len(sens_list) > 0:
            idx, child_name = self.device_tree.GetItemText(child).split(': ')
            if child_name == "None":
                id = sens_list.pop(0)
                hex_id = '{0:08X}'.format(id)
                global_sensor_list[id].setWirelessPanID(pan_id)
                global_sensor_list[id].setWirelessChannel(chan)
                wireless = self.selected_dongle.setSensorToDongle(int(idx), id)
                if wireless is None:
                    print "Failed to add", hex_id, "None"
                    continue
                
                if not wireless.switchToWiredMode():
                    wireless.switchToWirelessMode()
                if not wireless.isConnected():
                    print "Failed to add", hex_id, "Connect"
                    continue
                else:
                    wireless.commitWirelessSettings()
                    print "Created TSWLSensor Wireless Serial:",
                    print hex_id, "Firmware Date:",
                    print wireless.getFirmwareVersionString()
                self.device_tree.SetItemText(child, idx + ": " + wireless.device_type + "-" + hex_id)
                self.device_tree.SetItemImage(child, self.paired_img)
            child = self.device_tree.GetNextSibling(child)
        self.selected_dongle.commitWirelessSettings()
        self.dongle_panel.initSettings(self.selected_dongle)
        
        global_updated_sensors = True
    
    def onClear(self, event):
        """ Automatically clears the TSDongles knowledge of any TSWLSensors and
            commits the settings.
            
            Args:
                event: A wxPython event.
        """
        global global_updated_sensors
        
        root = self.device_tree.GetSelection()
        child = self.device_tree.GetLastChild(root)
        while child.IsOk():
            idx, child_name = self.device_tree.GetItemText(child).split(': ')
            if child_name != "None":
                self.device_tree.SetItemText(child, idx + ": None")
                self.device_tree.SetItemImage(child, -1)
                sensor_type, id_hex = child_name.rsplit('-', 1)
                id = int(id_hex, 16)
                if id in global_sensor_list:
                    wl_sens = global_sensor_list[id]
                    if self.selected_dongle == wl_sens.dongle:
                        if not wl_sens.switchToWiredMode():
                            # global_sensor_list[id].close()
                            del global_sensor_list[id]
                self.selected_dongle.setSensorToDongle(int(idx), 0)
            child = self.device_tree.GetPrevSibling(child)
        self.selected_dongle.commitWirelessSettings()
        self.dongle_panel.initSettings(self.selected_dongle)
        
        global_updated_sensors = True
    
    def onSelect(self, event):
        """ Pairs a selected TSWLSensor with a TSDongle and commits the
            settings.
            
            Args:
                event: A wxPython event.
        """
        global global_updated_sensors
        
        # Get item and parent
        item = self.device_tree.GetSelection()
        idx, item_name = self.device_tree.GetItemText(item).split(': ')
        item_par = self.device_tree.GetItemParent(item)
        par_id = int(self.device_tree.GetItemText(item_par).rsplit('-', 1)[-1], 16)
        
        # Add to dongle and update tree
        dongle = global_dongle_list[par_id]
        pan_id = dongle.getWirelessPanID()
        chan = dongle.getWirelessChannel()
        id_hex = event.GetEventObject().GetLabel(event.GetId()).rsplit('-', 1)[-1]
        id = int(id_hex, 16)
        global_sensor_list[id].setWirelessPanID(pan_id)
        global_sensor_list[id].setWirelessChannel(chan)
        wireless = dongle.setSensorToDongle(int(idx), id)
        if item_name != "None":
            item_id = int(item_name.rsplit('-', 1)[-1], 16)
            if item_id in global_sensor_list:
                if not global_sensor_list[item_id].switchToWiredMode():
                    del global_sensor_list[item_id]
        self.device_tree.SetItemText(item, idx + ": " + wireless.device_type + "-" + id_hex)
        if wireless is None:
            print "Failed to add", id_hex
            self.device_tree.SetItemImage(item, self.fail_img)
        else:
            if not wireless.switchToWiredMode():
                wireless.switchToWirelessMode()
            if not wireless.isConnected():
                print "Failed to add", id_hex
                self.device_tree.SetItemImage(item, self.fail_img)
            else:
                wireless.commitWirelessSettings()
                print "Created TSWLSensor Wireless Serial:",
                print id_hex, "Firmware Date:",
                print wireless.getFirmwareVersionString()
                self.device_tree.SetItemImage(item, self.paired_img)
        dongle.commitWirelessSettings()
        
        self.device_tree.SelectItem(item)
        
        global_updated_sensors = True
    
    def onRemove(self, event):
        """ Removes a selected TSWLSensor from a TSDongle and commits the
            settings.
            
            Args:
                event: A wxPython event.
        """
        global global_updated_sensors
        
        # Get item and parent
        item = self.device_tree.GetSelection()
        idx, item_name = self.device_tree.GetItemText(item).split(': ')
        item_id = int(item_name.rsplit('-', 1)[-1], 16)
        item_par = self.device_tree.GetItemParent(item)
        par_id = int(self.device_tree.GetItemText(item_par).rsplit('-', 1)[-1], 16)
        
        # Reset item
        self.device_tree.SetItemText(item, idx + ": None")
        self.device_tree.SetItemImage(item, -1)
        self.device_tree.SelectItem(item)
        
        # Remove from dongle and wireless list
        dongle = global_dongle_list[par_id]
        if item_id in global_sensor_list:
            if dongle == global_sensor_list[item_id].dongle:
                if not global_sensor_list[item_id].switchToWiredMode():
                    global_sensor_list[item_id].close()
                    del global_sensor_list[item_id]
        dongle.setSensorToDongle(int(idx), 0)
        dongle.commitWirelessSettings()
        
        global_updated_sensors = True
    
    def onReconnect(self, event):
        """ Tries to do a reconnect on the selected device.
            
            Args:
                event: A wxPython event.
        """
        # Get item
        item = self.device_tree.GetSelection()
        item_name = self.device_tree.GetItemText(item).split(': ')[-1]
        item_type, item_id_hex = item_name.rsplit('-', 1)
        item_id = int(item_id_hex, 16)
        
        # Reconnect device
        if item_type == "DNG":
            global_dongle_list[item_id].reconnect()
        else:
            if "WL" in item_type:
                if not global_sensor_list[item_id].wireless_com:
                    global_sensor_list[item_id].reconnect()
            else:
                global_sensor_list[item_id].reconnect()
        self.device_tree.SelectItem(item)
    
    def onDisconnect(self, event):
        """ Disconnect the selected device.
            
            Args:
                event: A wxPython event.
        """
        # Get item
        item = self.device_tree.GetSelection()
        item_name = self.device_tree.GetItemText(item).split(': ')[-1]
        item_type, item_id_hex = item_name.rsplit('-', 1)
        item_id = int(item_id_hex, 16)
        
        # Reconnect device
        if item_type == "DNG":
            global_dongle_list[item_id].close()
        else:
            if "WL" in item_type:
                if not global_sensor_list[item_id].wireless_com:
                    global_sensor_list[item_id].close()
            else:
                global_sensor_list[item_id].close()
        
        self.device_tree.SelectItem(item)
    
    def onDeviceChoice(self, event):
        """ Updates the SensorConfigurationWindow based on what was chosen from
            the device_tree.
            
            Args:
                event: A wxPython event.
        """
        global global_updated_sensors
        
        idx = None
        tmp_name = "None"
        sens_list = self.device_tree.GetItemText(self.sensor_root)
        dong_list = self.device_tree.GetItemText(self.dongle_root)
        item = event.GetItem()
        if item.IsOk():
            tmp_name = self.device_tree.GetItemText(item).split(': ')[-1]
        
        if tmp_name not in [sens_list, dong_list, "None"]:
            sensor_type, id_hex = tmp_name.rsplit('-', 1)
            id = int(id_hex, 16)
            if sensor_type == "DNG":
                if self.notebook.GetPageCount() > 1:
                    self.notebook.AddPage(self.dongle_panel, "Dongle Settings")
                    self.notebook.SetSelection(3)
                    self.notebook.RemovePage(2)
                    self.notebook.RemovePage(1)
                    self.notebook.RemovePage(0)
                self.sensor_canvas.setSensor(orient=self.mesh_init)
                self.selected_sensor = None
                self.selected_dongle = global_dongle_list[id]
                is_ok = self.dongle_panel.initSettings(self.selected_dongle)
                if not is_ok:
                    self.selected_dongle.close()
                    self.selected_dongle = None
                    self.device_tree.SetItemImage(item, self.fail_img)
                    child = self.device_tree.GetLastChild(item)
                    while child.IsOk():
                        child_name = self.device_tree.GetItemText(child)
                        child_name = child_name.split(': ')[-1]
                        if child_name != "None":
                            self.device_tree.SetItemImage(child, self.fail_img)
                        child = self.device_tree.GetPrevSibling(child)
                else:
                    self.device_tree.SetItemImage(item, self.dng_img)
                    child = self.device_tree.GetLastChild(item)
                    while child.IsOk():
                        child_name = self.device_tree.GetItemText(child)
                        child_name = child_name.split(': ')[-1]
                        if child_name != "None":
                            id = int(child_name.rsplit('-', 1)[-1], 16)
                            if id in global_sensor_list:
                                sens = global_sensor_list[id]
                                if sens.isConnected():
                                    if sens.wireless_com:
                                        self.device_tree.SetItemImage(child, self.wl_img)
                                    else:
                                        if sens.dongle == self.selected_dongle:
                                            self.device_tree.SetItemImage(child, self.paired_img)
                                        else:
                                            self.device_tree.SetItemImage(child, self.fail_img)
                        child = self.device_tree.GetPrevSibling(child)
            else:
                if self.notebook.GetPageCount() == 1:
                    self.notebook.AddPage(self.info_axis_panel, "Info && Axis Directions")
                    self.notebook.AddPage(self.tare_panel, "Tare")
                    self.notebook.AddPage(self.led_comp_panel, "LED && Components")
                    self.notebook.SetSelection(1)
                    self.notebook.RemovePage(0)
                self.selected_dongle = None
                self.dongle_panel.initSettings()
                is_ok = False
                if id in global_sensor_list:
                    self.selected_sensor = global_sensor_list[id]
                    is_ok = self.info_axis_panel.initSettings(self.selected_sensor)
                    if "WL" in sensor_type:
                        if not is_ok:
                            if self.selected_sensor.wireless_com:
                                self.selected_sensor = None
                                self.device_tree.SetItemImage(item, self.fail_img)
                                self.sensor_canvas.setSensor(orient=self.mesh_init)
                                self.tare_panel.initSettings()
                                self.led_comp_panel.initSettings()
                                self.onUpdateAxes(event)
                                return
                            elif self.selected_sensor.switchToWirelessMode():
                                self.selected_sensor.close()
                                self.device_tree.SetItemImage(item, self.fail_img)
                                item = self.findTreeItem(tmp_name, self.dongle_root)
                                self.device_tree.SelectItem(item)
                                return
                            else:
                                self.selected_sensor.close()
                                self.selected_sensor = None
                                self.device_tree.SetItemImage(item, self.fail_img)
                                self.sensor_canvas.setSensor(orient=self.mesh_init)
                                self.tare_panel.initSettings()
                                self.led_comp_panel.initSettings()
                                self.onUpdateAxes(event)
                                return
                        else:
                            item_par = self.device_tree.GetItemParent(item)
                            if self.selected_sensor.wireless_com and item_par == self.sensor_root:
                                if self.selected_sensor.switchToWirelessMode():
                                    self.selected_sensor.close()
                                    self.device_tree.SetItemImage(item, self.fail_img)
                                    item = self.findTreeItem(tmp_name, self.dongle_root)
                                    self.device_tree.SelectItem(item)
                                    return
                                else:
                                    self.selected_sensor.close()
                                    self.selected_sensor = None
                                    self.device_tree.SetItemImage(item, self.fail_img)
                                    self.sensor_canvas.setSensor(orient=self.mesh_init)
                                    self.tare_panel.initSettings()
                                    self.led_comp_panel.initSettings()
                                    self.onUpdateAxes(event)
                                    return
                            elif not self.selected_sensor.wireless_com and item_par != self.sensor_root:
                                if self.selected_sensor.switchToWiredMode():
                                    par = self.device_tree.GetItemText(item_par)
                                    par_name = par.split(': ')[-1]
                                    par_id = int(par_name.rsplit('-', 1)[1], 16)
                                    dongle = global_dongle_list[par_id]
                                    if self.selected_sensor.dongle == dongle:
                                        self.device_tree.SetItemImage(item, self.paired_img)
                                    else:
                                        self.device_tree.SetItemImage(item, self.fail_img)
                                    item = self.findTreeItem(tmp_name, self.sensor_root)
                                    print item
                                    self.device_tree.SelectItem(item)
                                    return
                                else:
                                    self.selected_sensor = None
                                    self.device_tree.SetItemImage(item, self.fail_img)
                                    self.sensor_canvas.setSensor(orient=self.mesh_init)
                                    self.tare_panel.initSettings()
                                    self.led_comp_panel.initSettings()
                                    self.onUpdateAxes(event)
                                    return
                    
                    elif not is_ok:
                        self.selected_sensor.close()
                        self.selected_sensor = None
                        self.device_tree.SetItemImage(item, self.fail_img)
                        self.sensor_canvas.setSensor(orient=self.mesh_init)
                        self.tare_panel.initSettings()
                        self.led_comp_panel.initSettings()
                        self.onUpdateAxes(event)
                        return
                elif "WL" in sensor_type:
                    idx = self.device_tree.GetItemText(item).split(': ')[0]
                    item_par = self.device_tree.GetItemParent(item)
                    par_name = self.device_tree.GetItemText(item_par)
                    par_id = int(par_name.rsplit('-', 1)[-1], 16)
                    dongle = global_dongle_list[par_id]
                    wireless = dongle.setSensorToDongle(int(idx), id)
                    
                    if wireless is None:
                        print "Failed to find", id_hex
                        self.selected_sensor = None
                        self.info_axis_panel.initSettings()
                        self.device_tree.SetItemImage(item, self.fail_img)
                        self.sensor_canvas.setSensor(orient=self.mesh_init)
                        self.tare_panel.initSettings()
                        self.led_comp_panel.initSettings()
                        self.onUpdateAxes(event)
                        return
                    else:
                        if not wireless.switchToWiredMode():
                            wireless.switchToWirelessMode()
                        is_ok = self.info_axis_panel.initSettings(wireless)
                        if is_ok:
                            print "Created TSWLSensor Wireless Serial:",
                            print id_hex, "Firmware Date:",
                            print wireless.getFirmwareVersionString()
                            self.selected_sensor = wireless
                            self.device_tree.SetItemImage(item, self.wl_img)
                            
                            global_updated_sensors = True
                        else:
                            print "Failed to add", id_hex
                            self.selected_sensor = None
                            self.info_axis_panel.initSettings()
                            self.device_tree.SetItemImage(item, self.fail_img)
                            self.sensor_canvas.setSensor(orient=self.mesh_init)
                            self.tare_panel.initSettings()
                            self.led_comp_panel.initSettings()
                            self.onUpdateAxes(event)
                            return
                else:
                    self.selected_sensor = None
                    self.info_axis_panel.initSettings()
                    self.device_tree.SetItemImage(item, self.fail_img)
                    self.sensor_canvas.setSensor(orient=self.mesh_init)
                    self.tare_panel.initSettings()
                    self.led_comp_panel.initSettings()
                    self.onUpdateAxes(event)
                    return
                
                self.sensor_canvas.setSensor(self.selected_sensor, True)
                self.tare_panel.initSettings(tmp_name)
                self.led_comp_panel.initSettings(self.selected_sensor)
                if sensor_type == "USB":
                    self.device_tree.SetItemImage(item, self.usb_img)
                else:
                    self.device_tree.SetItemImage(item, self.wl_img)
        
        else:
            self.selected_sensor = None
            self.selected_dongle = None
            self.led_comp_panel.initSettings()
            self.sensor_canvas.setSensor(orient=self.mesh_init)
            self.tare_panel.initSettings()
            self.info_axis_panel.initSettings()
            self.dongle_panel.initSettings()
        
        self.onUpdateAxes(event)
    
    def onTextEntry(self, event):
        """ Checks the text entry of the dongle_panel's wx.TextCtrls if they are
            a valid entry.
            
            Args:
                event: A wxPython event.
        """
        evt_type = event.GetEventType()
        text_ctrl = event.GetEventObject()
        if evt_type == wx.wxEVT_KILL_FOCUS:
            new_id = text_ctrl.GetValue().upper()
            if len(new_id) == 0:
                idx = self.dongle_panel.wireless_table.index(text_ctrl)
                hw_id_hex = '{0:08X}'.format(self.selected_dongle.wireless_table[idx])
                text_ctrl.SetValue(hw_id_hex)
            else:
                new_id = '{0:>08}'.format(new_id)
                text_ctrl.SetValue(new_id)
        elif evt_type == wx.wxEVT_COMMAND_TEXT_ENTER:
            new_id = text_ctrl.GetValue().upper()
            if len(new_id) == 0:
                idx = self.dongle_panel.wireless_table.index(text_ctrl)
                hw_id_hex = '{0:08X}'.format(self.selected_dongle.wireless_table[idx])
                text_ctrl.SetValue(hw_id_hex)
            else:
                new_id = '{0:>08}'.format(new_id)
                text_ctrl.SetValue(new_id)
        elif evt_type == wx.wxEVT_CHAR:
            evt_key = event.GetKeyCode()
            if evt_key in self.dongle_panel.valid_commands:
                if evt_key == 8 or evt_key == 127:
                    self.dongle_panel.is_text_update = True
                    self.dongle_panel.apply_button.Enable()
                    self.dongle_panel.commit_button.Enable()
                event.Skip()
            elif evt_key < 256:
                if chr(evt_key) in self.dongle_panel.valid_entry:
                    self.dongle_panel.is_text_update = True
                    self.dongle_panel.apply_button.Enable()
                    self.dongle_panel.commit_button.Enable()
                    event.Skip()
    
    def onGyroButton(self, event):
        """ Calibrates the gyros of the selected sensor.
            
            Args:
                event: A wxPython event.
        """
        if self.selected_sensor:
            self.selected_sensor.beginGyroscopeAutoCalibration()
            time.sleep(2)
    
    def onTareButton(self, event):
        """ Tares the selected sensor according to what was selected.
            
            Args:
                event: A wxPython event.
        """
        # Check for a valid selected sensor
        if self.selected_sensor:
            # Retrieve the tare data
            tare_type, data = self.tare_panel.returnValues()
            
            if tare_type == 0:
                # Tare with current orient
                self.selected_sensor.tareWithCurrentOrientation()
            
            elif tare_type == 1:
                # Tare with a provided quaternion (LHS rotation)
                # Identity points North
                self.selected_sensor.tareWithQuaternion(data)
            
            elif tare_type == 2:
                # Tare with provided Rotation Matrix (LHS rotation)
                # Works for the wireless sensors only currently
                # Identity points North
                self.selected_sensor.tareWithRotationMatrix(data)
            
            elif tare_type == 3:
                # Tare with the selected sensor
                if data != "":
                    sensor_type, id_hex = data.split("-")
                    id = int(id_hex, 16)
                    if id in global_sensor_list:
                        tmp_sensor = global_sensor_list[id]
                        if tmp_sensor.isConnected():
                            self.selected_sensor.tareWithQuaternion(tmp_sensor.getTareOrientationAsQuaternion())
                else:
                    return
            
            if event.GetEventObject().GetLabel()[0] == "T":
                self.selected_sensor.commitSettings()
    
    def onApplyButton(self, event):
        """ Applies the settings to the selected sensor or dongle.
            
            Args:
                event: A wxPython event.
        """
        if self.selected_sensor:
            notebook_idx = self.notebook.GetSelection()
            if notebook_idx == 0:
                self.info_axis_panel.setSettings(self.selected_sensor)
                self.sensor_canvas.axis_dir_data = self.info_axis_panel.returnAxisValues()
                self.onUpdateAxes(event)
            elif notebook_idx == 2:
                self.led_comp_panel.setSettings(self.selected_sensor)
        elif self.selected_dongle:
            self.dongle_panel.setSettings(self.selected_dongle)
            if self.dongle_panel.is_text_update:
                self.dongle_panel.is_text_update = False
                self.updateTree(self.dongle_root)
    
    def onApplyCommitSettings(self, event):
        """ Applies and Commits the settings to the selected sensor or dongle.
            
            Args:
                event: A wxPython event.
        """
        if self.selected_sensor:
            notebook_idx = self.notebook.GetSelection()
            if notebook_idx == 0:
                self.info_axis_panel.setSettings(self.selected_sensor)
                self.sensor_canvas.axis_dir_data = self.info_axis_panel.returnAxisValues()
                self.onUpdateAxes(event)
                if "WL" in self.selected_sensor.device_type:
                    self.selected_sensor.commitWirelessSettings()
            elif notebook_idx == 2:
                self.led_comp_panel.setSettings(self.selected_sensor)
            self.selected_sensor.commitSettings()
        elif self.selected_dongle:
            self.dongle_panel.setSettings(self.selected_dongle)
            self.selected_dongle.commitWirelessSettings()
            self.selected_dongle.commitSettings()
            if self.dongle_panel.is_text_update:
                self.dongle_panel.is_text_update = False
                self.updateTree(self.dongle_root)
    
    def onFindDevices(self, event):
        """ Finds new sensor and dongle devices and deletes the ones that are
            not communicating.
            
            Args:
                event: A wxPython event.
        """
        global global_updated_sensors
        global_updated_sensors = True
        if self.selected_sensor is not None or self.selected_dongle is not None:
            self.device_tree.Unselect()
        self.selected_sensor = None
        self.selected_dongle = None
        
        child = self.device_tree.GetLastChild(self.sensor_root)
        while child.IsOk():
            id = int(self.device_tree.GetItemText(child).rsplit('-', 1)[-1], 16)
            sensor = global_sensor_list[id]
            if not sensor.isConnected():
                sensor.close()
                del global_sensor_list[id]
                self.device_tree.Delete(child)
                child = self.device_tree.GetLastChild(self.sensor_root)
            else:
                child = self.device_tree.GetPrevSibling(child)
        
        child = self.device_tree.GetLastChild(self.dongle_root)
        while child.IsOk():
            id = int(self.device_tree.GetItemText(child).rsplit('-', 1)[-1], 16)
            dongle = global_dongle_list[id]
            if not dongle.isConnected():
                w_child = self.device_tree.GetLastChild(child)
                while w_child.IsOk():
                    text = self.device_tree.GetItemText(w_child).split(': ')[-1]
                    if text == "None":
                        w_child = self.device_tree.GetPrevSibling(w_child)
                        continue
                    wl_id = int(text.rsplit('-', 1)[-1], 16)
                    if wl_id not in global_sensor_list:
                        w_child = self.device_tree.GetPrevSibling(w_child)
                    else:
                        del global_sensor_list[wl_id]
                        w_child = self.device_tree.GetPrevSibling(w_child)
                
                dongle.close()
                del global_dongle_list[id]
                self.device_tree.DeleteChildren(child)
                self.device_tree.Delete(child)
                child = self.device_tree.GetLastChild(self.dongle_root)
            else:
                w_child = self.device_tree.GetLastChild(child)
                while w_child.IsOk():
                    text = self.device_tree.GetItemText(w_child).split(': ')[-1]
                    if text == "None":
                        w_child = self.device_tree.GetPrevSibling(w_child)
                        continue
                    wl_id = int(text.rsplit('-', 1)[-1], 16)
                    if wl_id not in global_sensor_list:
                        self.device_tree.SetItemText(w_child, "None")
                        self.device_tree.SetItemImage(w_child, -1)
                        w_child = self.device_tree.GetPrevSibling(w_child)
                    else:
                        wireless = global_sensor_list[wl_id]
                        if not wireless.isConnected():
                            # wireless.close()
                            del global_sensor_list[wl_id]
                            self.device_tree.SetItemText(w_child, "None")
                            self.device_tree.SetItemImage(w_child, -1)
                        w_child = self.device_tree.GetPrevSibling(w_child)
                child = self.device_tree.GetPrevSibling(child)
        
        progress_bar = ProgressSensorsAndDongles()
        progress_bar.searchSensorsAndDongles()
        
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
                    wireless = dongle.setSensorToDongle(i, wl_id)
                    if wireless is None:
                        print "Failed to find", wl_id_hex
                        continue
                    
                    if not wireless.switchToWiredMode():
                        wireless.switchToWirelessMode()
                    if wireless.isConnected():
                        print "Created TSWLSensor Wireless Serial:",
                        print wl_id_hex, "Firmware Date:",
                        print wireless.getFirmwareVersionString()
                    else:
                        print "Failed to add", wl_id_hex
                progress_bar.setValue(count)
        progress_bar.destroy()
        
        if global_check_unknown and len(global_unknown_list) > 0:
            dlg = UnknownPortDialog()
            dlg.CenterOnScreen()
            time_interval = self.update_timer.GetInterval()
            self.update_timer.Stop()
            dlg.ShowModal()
            self.update_timer.Start(time_interval)
            dlg.Destroy()
        
        self.updateTree()


### wxDialog ###
class UnknownPortDialog(wx.Dialog):
    
    """ A wxPython Dialog that creates the window for checking unknown ports.
        
        Attributes:
            check_list: A wx.CheckListBox instance that is used for denoting
                what COM ports to check if connected to a 3-Space Sensor device.
    """
    global global_unknown_list
    def __init__(self, parent=None, size=(400, 275), title="Unknown Ports Dialog"):
        """ Initializes the UnknownPortDialog class.
            
            Args:
                parent: A reference to another wxPython object.
                size: A tuple that stores a width and height for the Dialog.
                    (default is wx.DefaultSize)
                title: A string that denotes the title of the Dialog window.
                    (default is "Unknown Ports Dialog")
        """
        if parent:
            wx.Dialog.__init__(self, parent, -1, title, size=size)
        else:
            wx.Dialog.__init__(self, parent, -1, title, size=size, style=wx.CAPTION | wx.DIALOG_NO_PARENT | wx.STAY_ON_TOP)
        
        
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        
        ## Text Message ##
        text_box = wx.BoxSizer(wx.VERTICAL)
        font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        
        text1 = (
            "There are serial ports that were found that cannot be\n"
            "identified without polling the port."
        )
        text2 = (
            "Polling a port that is not a 3-Space Sensor might cause\n"
            "erroneous behavior to the device on that port.\n"
            "So make sure you know what you are doing."
        )
        
        text_box1 = wx.StaticText(self, -1, text1)
        text_box2 = wx.StaticText(self, -1, "Warning:")
        text_box2.SetFont(font)
        text_box2a = wx.StaticText(self, -1, text2)
        
        text_box.Add(text_box1)
        text_box.AddSpacer((0, 5))
        text_box.Add(text_box2)
        text_box.AddSpacer((0, 3))
        text_box.Add(text_box2a)
        
        ## Check List ##
        try:
            sort_list = sorted(global_unknown_list.iterkeys(), key=lambda s: int(s.strip('COM')))
        except:
            sort_list = sorted(global_unknown_list.iterkeys())
        
        choice_list = []
        for i in sort_list:
            choice_list.append(i + "        " + global_unknown_list[i][1])
        
        self.check_list = wx.CheckListBox(self, wx.NewId(), size=(250, 50), choices=choice_list)
        
        ## Check Box ##
        ignore_check = wx.CheckBox(self, wx.NewId(), "Always ignore unknown ports", (10, 230))
        ignore_check.SetValue(not global_check_unknown)
        
        ## Button Box ##
        poll_btn = wx.Button(self, wx.ID_OK, "Poll ports")
        poll_btn.Disable()
        ignore_btn = wx.Button(self, wx.ID_CANCEL, "Ignore ports")
        
        ## Box Sizer ##
        box_sizer.Add(text_box, 0, wx.ALIGN_CENTER)
        box_sizer.AddSpacer((0, 15))
        box_sizer.Add(self.check_list, 0, wx.ALIGN_CENTER)
        box_sizer.AddSpacer((0, 15))
        box_sizer.Add(poll_btn, 0, wx.ALIGN_CENTER)
        box_sizer.AddSpacer((0, 10))
        box_sizer.Add(ignore_btn, 0, wx.ALIGN_CENTER)
        
        self.SetSizer(box_sizer)
        
        ## Binds ##
        poll_btn.Bind(wx.EVT_BUTTON, self.onButton)
        ignore_btn.Bind(wx.EVT_BUTTON, self.onButton)
        ignore_check.Bind(wx.EVT_CHECKBOX, self.onCheck)
        self.check_list.Bind(wx.EVT_CHECKLISTBOX, self.onCheck)
    
    def onButton(self, event):
        evt_id = event.GetId()
        if evt_id == wx.ID_OK:
            poll_list = []
            created_sensor_list = []
            for i in self.check_list.GetCheckedStrings():
                poll_list.append(i.split("        ")[0])
            progress_bar = ProgressSensorsAndDongles()
            progress_bar.setRange(len(poll_list))
            count = 0
            progress_bar.setValue(count)
            for i in poll_list:
                count += 1
                progress_bar.SetTitle("Polling " + i)
                sens_info = ts_api.getDeviceInfoFromComPort(i)
                print sens_info
                dev_type = sens_info.dev_type
                
                if dev_type == "USB":
                    try:
                        new_sensor = ts_api.TSUSBSensor(i)
                        id = new_sensor.serial_number_hex
                        del global_unknown_list[i]
                        created_sensor_list.append((i, dev_type + '-' + id))
                        print "Created TSSensor on (", i, ") Serial:", id,
                        print "Firmware Date:",
                        print new_sensor.getFirmwareVersionString()
                    except Exception as error:
                        print error
                elif dev_type == "EM":
                    try:
                        new_sensor = ts_api.TSEMSensor(i)
                        id = new_sensor.serial_number_hex
                        del global_unknown_list[i]
                        created_sensor_list.append((i, dev_type + '-' + id))
                        print "Created TSEMSensor on (", i, ") Serial:", id,
                        print "Firmware Date:",
                        print new_sensor.getFirmwareVersionString()
                    except Exception as error:
                        print error
                else:
                    created_sensor_list.append((i, None))
                progress_bar.setValue(count)
            
            caption = "Connected Ports"
            message = ""
            for i in created_sensor_list:
                if i[1] is None:
                    message += (i[0] + "    Did not create any 3-Space Sensor units\n")
                else:
                    message += (i[0] + "    Created " + i[1] + " 3-Space Sensor\n")
            
            progress_bar.destroy()
            
            wx.MessageBox(message, caption, wx.OK)
        event.Skip()
    
    def onCheck(self, event):
        global global_check_unknown
        evt_type = event.GetEventType()
        if evt_type == wx.EVT_CHECKLISTBOX.typeId:
            if len(self.check_list.GetChecked()) > 0:
                self.FindWindowById(wx.ID_OK).Enable()
            else:
                self.FindWindowById(wx.ID_OK).Disable()
        else:
            global_check_unknown = not global_check_unknown


### wxMiniFrame ###
class ProgressSensorsAndDongles(wx.MiniFrame):
    
    """ A wxPython MiniFrame that creates the window for a progress bar.
        
        Attributes:
            gauge: A wx.Gauge instance that shows the progress being made.
    """
    global global_unknown_list
    def __init__(self, parent=None, title="Progress Bar"):
        """ Initializes the ProgressSensorsAndDongles class.
            
            Args:
                parent: A reference to another wxPython object (default None)
                title: A string denoting the title of the window
                    (default "Progress Bar")
        """
        wx.MiniFrame.__init__(self, parent, -1, title, size=(400, 100), style=wx.STAY_ON_TOP | wx.CAPTION)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.gauge = wx.Gauge(self, wx.NewId(), size=(250, -1))
        self.setValue(1)
        sizer.AddSpacer((0, 20))
        sizer.Add(self.gauge, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND | wx.ALL)
        self.SetSizer(sizer)
        self.CenterOnScreen()
        
        self.Show()
    
    def searchSensorsAndDongles(self):
        """Searches for USB connections to TSSensor and TSDongle objects."""
        self.SetTitle("One Moment, Checking for 3-Space Sensor Units...")
        print "Searching for Sensors and Dongles......"
        # Get our list of COM ports
        sens_port_list = ts_api.getComPorts(filter=ts_api.TSS_FIND_ALL_KNOWN)
        
        self.setRange(len(sens_port_list))
        count = 0
        self.setValue(count)
        
        print "    Found", len(sens_port_list)
        for port in sens_port_list:
            count += 1
            com_port, name, dev_type = port
            if dev_type == "USB":
                try:
                    new_sensor = ts_api.TSUSBSensor(com_port, timestamp_mode=ts_api.TSS_TIMESTAMP_SYSTEM)
                    id = new_sensor.serial_number_hex
                    print "Created TSUSBSensor on (", com_port, ") Serial:", id,
                    print "Firmware Date:",
                    print new_sensor.getFirmwareVersionString()
                except Exception as error:
                    print error
            elif dev_type == "DNG":
                try:
                    new_dongle = ts_api.TSDongle(com_port, timestamp_mode=ts_api.TSS_TIMESTAMP_SYSTEM)
                    id = new_dongle.serial_number_hex
                    print "Created TSDongle on (", com_port, ") Serial:", id,
                    print "Firmware Date:",
                    print new_dongle.getFirmwareVersionString()
                except Exception as error:
                    print error
            elif "WL" in dev_type:
                try:
                    new_sensor = ts_api.TSWLSensor(com_port=com_port, timestamp_mode=ts_api.TSS_TIMESTAMP_SYSTEM)
                    id = new_sensor.serial_number_hex
                    print "Created TSWLSensor on (", com_port, ") Serial:", id,
                    print "Firmware Date:",
                    print new_sensor.getFirmwareVersionString()
                except Exception as error:
                    print error
            elif dev_type == "EM":
                try:
                    new_sensor = ts_api.TSEMSensor(com_port, timestamp_mode=ts_api.TSS_TIMESTAMP_SYSTEM)
                    id = new_sensor.serial_number_hex
                    print "Created TSEMSensor on (", com_port, ") Serial:", id,
                    print "Firmware Date:",
                    print new_sensor.getFirmwareVersionString()
                except Exception as error:
                    print error
            elif dev_type == "DL":
                try:
                    new_sensor = ts_api.TSDLSensor(com_port, timestamp_mode=ts_api.TSS_TIMESTAMP_SYSTEM)
                    id = new_sensor.serial_number_hex
                    print "Created TSDLSensor on (", com_port, ") Serial:", id,
                    print "Firmware Date:",
                    print new_sensor.getFirmwareVersionString()
                except Exception as error:
                    print error
            elif dev_type == "BT":
                try:
                    new_sensor = ts_api.TSBTSensor(com_port, timestamp_mode=ts_api.TSS_TIMESTAMP_SYSTEM)
                    id = new_sensor.serial_number_hex
                    print "Created TSBTSensor on (", com_port, ") Serial:", id,
                    print "Firmware Date:",
                    print new_sensor.getFirmwareVersionString()
                except Exception as error:
                    print error
            self.setValue(count)
        
        if global_check_unknown:
            ukn_port_list = ts_api.getComPorts(filter=ts_api.TSS_FIND_UNKNOWN)
            if len(ukn_port_list) > 0:
                self.SetTitle("Found Unknown Device...")
                for port in ukn_port_list:
                    global_unknown_list[port[0]] = port
    
    def setRange(self, new_range):
        self.gauge.SetRange(new_range)
    
    def setValue(self, val):
        self.gauge.SetValue(val)
    
    def getRange(self):
        return self.gauge.GetRange()
    
    def getValue(self):
        return self.gauge.GetValue()
    
    def destroy(self):
        wx.MiniFrame.Destroy(self)


### Helper Functions ###
def getWirelessRetries():
    return ts_api.getSystemWirelessRetries()


def setWirelessRetries(val):
    ts_api.setSystemWirelessRetries(val)


### Axis Direction Helper Functions ###
def convertMatrix4ToAxisDir(matrix):
    matrix_axis_dir = 0
    
    # Get orientation as array
    tmp_array = matrix.asColArray()
    
    # Get the axes of the orientation
    x_mat_vec = Vector3(tmp_array[:3]).normalizeCopy()
    y_mat_vec = Vector3(tmp_array[4:7]).normalizeCopy()
    z_mat_vec = Vector3(tmp_array[8:11]).normalizeCopy() * -1.0
    
    # Create unit vectors
    x_vec = Vector3(UNIT_X)
    y_vec = Vector3(UNIT_Y)
    z_vec = Vector3(UNIT_Z)
    
    # Find what global (LHS) axis the matrix z axis is closest to
    x_dot_z = abs(z_mat_vec.dot(x_vec))
    y_dot_z = abs(z_mat_vec.dot(y_vec))
    z_dot_z = abs(z_mat_vec.dot(z_vec))
    
    x_sign = 0
    y_sign = 0
    z_sign = 0
    
    if x_dot_z > y_dot_z and x_dot_z > z_dot_z:
        x_sign = (z_mat_vec.dot(x_vec) * (abs(z_mat_vec.dot(x_vec))) ** -1)
        
        # Find what global (LHS) axis the matrix y axis is closest to
        y_dot_y = abs(y_mat_vec.dot(y_vec))
        z_dot_y = abs(y_mat_vec.dot(z_vec))
        
        if y_dot_y > z_dot_y:
            y_sign = (y_mat_vec.dot(y_vec) * (abs(y_mat_vec.dot(y_vec))) ** -1)
            
            # The global (LHS) axis the matrix x axis is closest to
            z_sign = (x_mat_vec.dot(z_vec) * (abs(x_mat_vec.dot(z_vec))) ** -1)
            
            matrix_axis_dir += 5
        
        else:
            z_sign = (y_mat_vec.dot(z_vec) * (abs(y_mat_vec.dot(z_vec))) ** -1)
            
            # The global (LHS) axis the matrix x axis is closest to
            y_sign = (x_mat_vec.dot(y_vec) * (abs(x_mat_vec.dot(y_vec))) ** -1)
            
            matrix_axis_dir += 3
    
    elif y_dot_z > x_dot_z and y_dot_z > z_dot_z:
        y_sign = (z_mat_vec.dot(y_vec) * (abs(z_mat_vec.dot(y_vec))) ** -1)
        
        # Find what global (LHS) axis the matrix y axis is closest to
        x_dot_y = abs(y_mat_vec.dot(x_vec))
        z_dot_y = abs(y_mat_vec.dot(z_vec))
        
        if x_dot_y > z_dot_y:
            x_sign = (y_mat_vec.dot(x_vec) * (abs(y_mat_vec.dot(x_vec))) ** -1)
            
            # The global (LHS) axis the matrix x axis is closest to
            z_sign = (x_mat_vec.dot(z_vec) * (abs(x_mat_vec.dot(z_vec))) ** -1)
            
            matrix_axis_dir += 4
        
        else:
            z_sign = (y_mat_vec.dot(z_vec) * (abs(y_mat_vec.dot(z_vec))) ** -1)
            
            # The global (LHS) axis the matrix x axis is closest to
            x_sign = (x_mat_vec.dot(x_vec) * (abs(x_mat_vec.dot(x_vec))) ** -1)
            
            matrix_axis_dir += 1
    
    else:
        z_sign = (z_mat_vec.dot(z_vec) * (abs(z_mat_vec.dot(z_vec))) ** -1)
        
        # Find what global (LHS) axis the matrix y axis is closest to
        x_dot_y = abs(y_mat_vec.dot(x_vec))
        y_dot_y = abs(y_mat_vec.dot(y_vec))
        
        if x_dot_y > y_dot_y:
            x_sign = (y_mat_vec.dot(x_vec) * (abs(y_mat_vec.dot(x_vec))) ** -1)
            
            # The global (LHS) axis the matrix x axis is closest to
            y_sign = (x_mat_vec.dot(y_vec) * (abs(x_mat_vec.dot(y_vec))) ** -1)
            
            matrix_axis_dir += 2
        
        else:
            y_sign = (y_mat_vec.dot(y_vec) * (abs(y_mat_vec.dot(y_vec))) ** -1)
            
            # The global (LHS) axis the matrix x axis is closest to
            x_sign = (x_mat_vec.dot(x_vec) * (abs(x_mat_vec.dot(x_vec))) ** -1)
    
    if x_sign < 0:
        matrix_axis_dir += 32
    if y_sign < 0:
        matrix_axis_dir += 16
    if z_sign < 0:
        matrix_axis_dir += 8
    
    return matrix_axis_dir


def negateQuaternionX(quat):
    quat[0] *= -1


def negateQuaternionXY(quat):
    quat[0] *= -1
    quat[1] *= -1


def negateQuaternionXYZ(quat):
    quat[0] *= -1
    quat[1] *= -1
    quat[2] *= -1


def negateQuaternionXZ(quat):
    quat[0] *= -1
    quat[2] *= -1


def negateQuaternionY(quat):
    quat[1] *= -1


def negateQuaternionYZ(quat):
    quat[1] *= -1
    quat[2] *= -1


def negateQuaternionZ(quat):
    quat[2] *= -1


def swapQuaternionXZY(quat):
    z_tmp = quat[1]
    quat[1] = quat[2]
    quat[2] = z_tmp


def swapQuaternionYXZ(quat):
    y_tmp = quat[0]
    quat[0] = quat[1]
    quat[1] = y_tmp


def swapQuaternionYZX(quat):
    y_tmp = quat[2]
    z_tmp = quat[0]
    quat[0] = quat[1]
    quat[1] = y_tmp
    quat[2] = z_tmp


def swapQuaternionZXY(quat):
    y_tmp = quat[0]
    z_tmp = quat[1]
    quat[0] = quat[2]
    quat[1] = y_tmp
    quat[2] = z_tmp


def swapQuaternionZYX(quat):
    z_tmp = quat[0]
    quat[0] = quat[2]
    quat[2] = z_tmp


# MAP[Mesh Axis][Sensor Axis](Convert Functions)
# Negations are for the component not the axis.
# For example, -ZYX means axis order ZYX negation on first component (for
# quaternion this is x) and Y-Z-X means axis order YZX negation on second and
# third component (for quaternion this is y and z)
AXIS_DIR_MAP = {
    1:      # XZY
    {
        0: (swapQuaternionXZY, negateQuaternionXYZ),        # XYZ
        1: (),                                              # XZY
        2: (swapQuaternionYZX,),                            # YXZ
        3: (swapQuaternionYXZ, negateQuaternionXYZ),        # YZX
        4: (swapQuaternionZYX, negateQuaternionXYZ),        # ZXY
        5: (swapQuaternionZXY,),                            # ZYX
        8: (swapQuaternionXZY, negateQuaternionY),          # XY-Z
        9: (negateQuaternionXY,),                           # XZ-Y
        10: (swapQuaternionYZX, negateQuaternionXZ),        # YX-Z
        11: (swapQuaternionYXZ, negateQuaternionZ),         # YZ-X
        12: (swapQuaternionZYX, negateQuaternionX),         # ZX-Y
        13: (swapQuaternionZXY, negateQuaternionYZ),        # ZY-X
        16: (swapQuaternionXZY, negateQuaternionZ),         # X-YZ
        17: (negateQuaternionXZ,),                          # X-ZY
        18: (swapQuaternionYZX, negateQuaternionYZ),        # Y-XZ
        19: (swapQuaternionYXZ, negateQuaternionX),         # Y-ZX
        20: (swapQuaternionZYX, negateQuaternionY),         # Z-XY
        21: (swapQuaternionZXY, negateQuaternionXY),        # Z-YX
        24: (swapQuaternionXZY, negateQuaternionX),         # X-Y-Z
        25: (negateQuaternionYZ,),                          # X-Z-Y
        26: (swapQuaternionYZX, negateQuaternionXY),        # Y-X-Z
        27: (swapQuaternionYXZ, negateQuaternionY),         # Y-Z-X
        28: (swapQuaternionZYX, negateQuaternionZ),         # Z-X-Y
        29: (swapQuaternionZXY, negateQuaternionXZ),        # Z-Y-X
        32: (swapQuaternionXZY, negateQuaternionX),         # -XYZ
        33: (negateQuaternionYZ,),                          # -XZY
        34: (swapQuaternionYZX, negateQuaternionXY),        # -YXZ
        35: (swapQuaternionYXZ, negateQuaternionY),         # -YZX
        36: (swapQuaternionZYX, negateQuaternionZ),         # -ZXY
        37: (swapQuaternionZXY, negateQuaternionXZ),        # -ZYX
        40: (swapQuaternionXZY, negateQuaternionZ),         # -XY-Z
        41: (negateQuaternionXZ,),                          # -XZ-Y
        42: (swapQuaternionYZX, negateQuaternionYZ),        # -YX-Z
        43: (swapQuaternionYXZ, negateQuaternionX),         # -YZ-X
        44: (swapQuaternionZYX, negateQuaternionY),         # -ZX-Y
        45: (swapQuaternionZXY, negateQuaternionXY),        # -ZY-X
        48: (swapQuaternionXZY, negateQuaternionY),         # -X-YZ
        49: (negateQuaternionXY,),                          # -X-ZY
        50: (swapQuaternionYZX, negateQuaternionXZ),        # -Y-XZ
        51: (swapQuaternionYXZ, negateQuaternionZ),         # -Y-ZX
        52: (swapQuaternionZYX, negateQuaternionX),         # -Z-XY
        53: (swapQuaternionZXY, negateQuaternionYZ),        # -Z-YX
        56: (swapQuaternionXZY, negateQuaternionXYZ),       # -X-Y-Z
        57: (),                                             # -X-Z-Y
        58: (swapQuaternionYZX,),                           # -Y-X-Z
        59: (swapQuaternionYXZ, negateQuaternionXYZ),       # -Y-Z-X
        60: (swapQuaternionZYX, negateQuaternionXYZ),       # -Z-X-Y
        61: (swapQuaternionZXY,)                            # -Z-Y-X
    },
    2:      # YXZ
    {
        0: (swapQuaternionYXZ, negateQuaternionXYZ),        # XYZ
        1: (swapQuaternionZXY,),                            # XZY
        2: (),                                              # YXZ
        3: (swapQuaternionZYX, negateQuaternionXYZ),        # YZX
        4: (swapQuaternionXZY, negateQuaternionXYZ),        # ZXY
        5: (swapQuaternionYZX,),                            # ZYX
        8: (swapQuaternionYXZ, negateQuaternionZ),          # XY-Z
        9: (swapQuaternionZXY, negateQuaternionYZ),         # XZ-Y
        10: (negateQuaternionXY,),                          # YX-Z
        11: (swapQuaternionZYX, negateQuaternionX),         # YZ-X
        12: (swapQuaternionXZY, negateQuaternionY),         # ZX-Y
        13: (swapQuaternionYZX, negateQuaternionXZ),        # ZY-X
        16: (swapQuaternionYXZ, negateQuaternionX),         # X-YZ
        17: (swapQuaternionZXY, negateQuaternionXY),        # X-ZY
        18: (negateQuaternionXZ,),                          # Y-XZ
        19: (swapQuaternionZYX, negateQuaternionY),         # Y-ZX
        20: (swapQuaternionXZY, negateQuaternionZ),         # Z-XY
        21: (swapQuaternionYZX, negateQuaternionYZ),        # Z-YX
        24: (swapQuaternionYXZ, negateQuaternionY),         # X-Y-Z
        25: (swapQuaternionZXY, negateQuaternionXZ),        # X-Z-Y
        26: (negateQuaternionYZ,),                          # Y-X-Z
        27: (swapQuaternionZYX, negateQuaternionZ),         # Y-Z-X
        28: (swapQuaternionXZY, negateQuaternionX),         # Z-X-Y
        29: (swapQuaternionYZX, negateQuaternionXY),        # Z-Y-X
        32: (swapQuaternionYXZ, negateQuaternionY),         # -XYZ
        33: (swapQuaternionZXY, negateQuaternionXZ),        # -XZY
        34: (negateQuaternionYZ,),                          # -YXZ
        35: (swapQuaternionZYX, negateQuaternionZ),         # -YZX
        36: (swapQuaternionXZY, negateQuaternionX),         # -ZXY
        37: (swapQuaternionYZX, negateQuaternionXY),        # -ZYX
        40: (swapQuaternionYXZ, negateQuaternionX),         # -XY-Z
        41: (swapQuaternionZXY, negateQuaternionXY),        # -XZ-Y
        42: (negateQuaternionXZ,),                          # -YX-Z
        43: (swapQuaternionZYX, negateQuaternionY),         # -YZ-X
        44: (swapQuaternionXZY, negateQuaternionZ),         # -ZX-Y
        45: (swapQuaternionYZX, negateQuaternionYZ),        # -ZY-X
        48: (swapQuaternionYXZ, negateQuaternionZ),         # -X-YZ
        49: (swapQuaternionZXY, negateQuaternionYZ),        # -X-ZY
        50: (negateQuaternionXY,),                          # -Y-XZ
        51: (swapQuaternionZYX, negateQuaternionX),         # -Y-ZX
        52: (swapQuaternionXZY, negateQuaternionY),         # -Z-XY
        53: (swapQuaternionYZX, negateQuaternionXZ),        # -Z-YX
        56: (swapQuaternionYXZ, negateQuaternionXYZ),       # -X-Y-Z
        57: (swapQuaternionZXY,),                           # -X-Z-Y
        58: (),                                             # -Y-X-Z
        59: (swapQuaternionZYX, negateQuaternionXYZ),       # -Y-Z-X
        60: (swapQuaternionXZY, negateQuaternionXYZ),       # -Z-X-Y
        61: (swapQuaternionYZX,)                            # -Z-Y-X
    },
    5:      # ZYX
    {
        0: (swapQuaternionZYX, negateQuaternionXYZ),        # XYZ
        1: (swapQuaternionYZX,),                            # XZY
        2: (swapQuaternionZXY,),                            # YXZ
        3: (swapQuaternionXZY, negateQuaternionXYZ),        # YZX
        4: (swapQuaternionYXZ, negateQuaternionXYZ),        # ZXY
        5: (),                                              # ZYX
        8: (swapQuaternionZYX, negateQuaternionX),          # XY-Z
        9: (swapQuaternionYZX, negateQuaternionXZ),         # XZ-Y
        10: (swapQuaternionZXY, negateQuaternionYZ),        # YX-Z
        11: (swapQuaternionXZY, negateQuaternionY),         # YZ-X
        12: (swapQuaternionYXZ, negateQuaternionZ),         # ZX-Y
        13: (negateQuaternionXY,),                          # ZY-X
        16: (swapQuaternionZYX, negateQuaternionY),         # X-YZ
        17: (swapQuaternionYZX, negateQuaternionYZ),        # X-ZY
        18: (swapQuaternionZXY, negateQuaternionXY),        # Y-XZ
        19: (swapQuaternionXZY, negateQuaternionZ),         # Y-ZX
        20: (swapQuaternionYXZ, negateQuaternionX),         # Z-XY
        21: (negateQuaternionXZ,),                          # Z-YX
        24: (swapQuaternionZYX, negateQuaternionZ),         # X-Y-Z
        25: (swapQuaternionYZX, negateQuaternionXY),        # X-Z-Y
        26: (swapQuaternionZXY, negateQuaternionXZ),        # Y-X-Z
        27: (swapQuaternionXZY, negateQuaternionX),         # Y-Z-X
        28: (swapQuaternionYXZ, negateQuaternionY),         # Z-X-Y
        29: (negateQuaternionYZ,),                          # Z-Y-X
        32: (swapQuaternionZYX, negateQuaternionZ),         # -XYZ
        33: (swapQuaternionYZX, negateQuaternionXY),        # -XZY
        34: (swapQuaternionZXY, negateQuaternionXZ),        # -YXZ
        35: (swapQuaternionXZY, negateQuaternionX),         # -YZX
        36: (swapQuaternionYXZ, negateQuaternionY),         # -ZXY
        37: (negateQuaternionYZ,),                          # -ZYX
        40: (swapQuaternionZYX, negateQuaternionY),         # -XY-Z
        41: (swapQuaternionYZX, negateQuaternionYZ),        # -XZ-Y
        42: (swapQuaternionZXY, negateQuaternionXY),        # -YX-Z
        43: (swapQuaternionXZY, negateQuaternionZ),         # -YZ-X
        44: (swapQuaternionYXZ, negateQuaternionX),         # -ZX-Y
        45: (negateQuaternionXZ,),                          # -ZY-X
        48: (swapQuaternionZYX, negateQuaternionX),         # -X-YZ
        49: (swapQuaternionYZX, negateQuaternionXZ),        # -X-ZY
        50: (swapQuaternionZXY, negateQuaternionYZ),        # -Y-XZ
        51: (swapQuaternionXZY, negateQuaternionY),         # -Y-ZX
        52: (swapQuaternionYXZ, negateQuaternionZ),         # -Z-XY
        53: (negateQuaternionXY,),                          # -Z-YX
        56: (swapQuaternionZYX, negateQuaternionXYZ),       # -X-Y-Z
        57: (swapQuaternionYZX,),                           # -X-Z-Y
        58: (swapQuaternionZXY,),                           # -Y-X-Z
        59: (swapQuaternionXZY, negateQuaternionXYZ),       # -Y-Z-X
        60: (swapQuaternionYXZ, negateQuaternionXYZ),       # -Z-X-Y
        61: ()                                              # -Z-Y-X
    },
    8:      # XY-Z
    {
        0: (negateQuaternionXY,),                           # XYZ
        1: (swapQuaternionXZY, negateQuaternionZ),          # XZY
        2: (swapQuaternionYXZ, negateQuaternionZ),          # YXZ
        3: (swapQuaternionYZX, negateQuaternionXY),         # YZX
        4: (swapQuaternionZXY, negateQuaternionXY),         # ZXY
        5: (swapQuaternionZYX, negateQuaternionZ),          # ZYX
        8: (),                                              # XY-Z
        9: (swapQuaternionXZY, negateQuaternionX),          # XZ-Y
        10: (swapQuaternionYXZ, negateQuaternionXYZ),       # YX-Z
        11: (swapQuaternionYZX, negateQuaternionYZ),        # YZ-X
        12: (swapQuaternionZXY, negateQuaternionXZ),        # ZX-Y
        13: (swapQuaternionZYX, negateQuaternionY),         # ZY-X
        16: (negateQuaternionYZ,),                          # X-YZ
        17: (swapQuaternionXZY, negateQuaternionXYZ),       # X-ZY
        18: (swapQuaternionYXZ, negateQuaternionY),         # Y-XZ
        19: (swapQuaternionYZX, negateQuaternionXZ),        # Y-ZX
        20: (swapQuaternionZXY,),                           # Z-XY
        21: (swapQuaternionZYX, negateQuaternionX),         # Z-YX
        24: (negateQuaternionXZ,),                          # X-Y-Z
        25: (swapQuaternionXZY, negateQuaternionY),         # X-Z-Y
        26: (swapQuaternionYXZ, negateQuaternionX),         # Y-X-Z
        27: (swapQuaternionYZX,),                           # Y-Z-X
        28: (swapQuaternionZXY, negateQuaternionYZ),        # Z-X-Y
        29: (swapQuaternionZYX, negateQuaternionXYZ),       # Z-Y-X
        32: (negateQuaternionXZ,),                          # -XYZ
        33: (swapQuaternionXZY, negateQuaternionY),         # -XZY
        34: (swapQuaternionYXZ, negateQuaternionX),         # -YXZ
        35: (swapQuaternionYZX,),                           # -YZX
        36: (swapQuaternionZXY, negateQuaternionYZ),        # -ZXY
        37: (swapQuaternionZYX, negateQuaternionXYZ),       # -ZYX
        40: (negateQuaternionYZ,),                          # -XY-Z
        41: (swapQuaternionXZY, negateQuaternionXYZ),       # -XZ-Y
        42: (swapQuaternionYXZ, negateQuaternionY),         # -YX-Z
        43: (swapQuaternionYZX, negateQuaternionXZ),        # -YZ-X
        44: (swapQuaternionZXY,),                           # -ZX-Y
        45: (swapQuaternionZYX, negateQuaternionX),         # -ZY-X
        48: (),                                             # -X-YZ
        49: (swapQuaternionXZY, negateQuaternionX),         # -X-ZY
        50: (swapQuaternionYXZ, negateQuaternionXYZ),       # -Y-XZ
        51: (swapQuaternionYZX, negateQuaternionYZ),        # -Y-ZX
        52: (swapQuaternionZXY, negateQuaternionXZ),        # -Z-XY
        53: (swapQuaternionZYX, negateQuaternionY),         # -Z-YX
        56: (negateQuaternionXY,),                          # -X-Y-Z
        57: (swapQuaternionXZY, negateQuaternionZ),         # -X-Z-Y
        58: (swapQuaternionYXZ, negateQuaternionZ),         # -Y-X-Z
        59: (swapQuaternionYZX, negateQuaternionXY),        # -Y-Z-X
        60: (swapQuaternionZXY, negateQuaternionXY),        # -Z-X-Y
        61: (swapQuaternionZYX, negateQuaternionZ)          # -Z-Y-X
    },
    11:     # YZ-X
    {
        0: (swapQuaternionZXY, negateQuaternionXY),         # XYZ
        1: (swapQuaternionYXZ, negateQuaternionZ),          # XZY
        2: (swapQuaternionZYX, negateQuaternionZ),          # YXZ
        3: (negateQuaternionXY,),                           # YZX
        4: (swapQuaternionYZX, negateQuaternionXY),         # ZXY
        5: (swapQuaternionXZY, negateQuaternionZ),          # ZYX
        8: (swapQuaternionZXY, negateQuaternionXZ),         # XY-Z
        9: (swapQuaternionYXZ, negateQuaternionXYZ),        # XZ-Y
        10: (swapQuaternionZYX, negateQuaternionY),         # YX-Z
        11: (),                                             # YZ-X
        12: (swapQuaternionYZX, negateQuaternionYZ),        # ZX-Y
        13: (swapQuaternionXZY, negateQuaternionX),         # ZY-X
        16: (swapQuaternionZXY,),                           # X-YZ
        17: (swapQuaternionYXZ, negateQuaternionY),         # X-ZY
        18: (swapQuaternionZYX, negateQuaternionX),         # Y-XZ
        19: (negateQuaternionYZ,),                          # Y-ZX
        20: (swapQuaternionYZX, negateQuaternionXZ),        # Z-XY
        21: (swapQuaternionXZY, negateQuaternionXYZ),       # Z-YX
        24: (swapQuaternionZXY, negateQuaternionYZ),        # X-Y-Z
        25: (swapQuaternionYXZ, negateQuaternionX),         # X-Z-Y
        26: (swapQuaternionZYX, negateQuaternionXYZ),       # Y-X-Z
        27: (negateQuaternionXZ,),                          # Y-Z-X
        28: (swapQuaternionYZX,),                           # Z-X-Y
        29: (swapQuaternionXZY, negateQuaternionY),         # Z-Y-X
        32: (swapQuaternionZXY, negateQuaternionYZ),        # -XYZ
        33: (swapQuaternionYXZ, negateQuaternionX),         # -XZY
        34: (swapQuaternionZYX, negateQuaternionXYZ),       # -YXZ
        35: (negateQuaternionXZ,),                           # -YZX
        36: (swapQuaternionYZX,),                           # -ZXY
        37: (swapQuaternionXZY, negateQuaternionY),         # -ZYX
        40: (swapQuaternionZXY,),                           # -XY-Z
        41: (swapQuaternionYXZ, negateQuaternionY),         # -XZ-Y
        42: (swapQuaternionZYX, negateQuaternionX),         # -YX-Z
        43: (negateQuaternionYZ,),                          # -YZ-X
        44: (swapQuaternionYZX, negateQuaternionXZ),        # -ZX-Y
        45: (swapQuaternionXZY, negateQuaternionXYZ),       # -ZY-X
        48: (swapQuaternionZXY, negateQuaternionXZ),        # -X-YZ
        49: (swapQuaternionYXZ, negateQuaternionXYZ),       # -X-ZY
        50: (swapQuaternionZYX, negateQuaternionY),         # -Y-XZ
        51: (),                                             # -Y-ZX
        52: (swapQuaternionYZX, negateQuaternionYZ),        # -Z-XY
        53: (swapQuaternionXZY, negateQuaternionX),         # -Z-YX
        56: (swapQuaternionZXY, negateQuaternionXY),        # -X-Y-Z
        57: (swapQuaternionYXZ, negateQuaternionZ),         # -X-Z-Y
        58: (swapQuaternionZYX, negateQuaternionZ),         # -Y-X-Z
        59: (negateQuaternionXY,),                          # -Y-Z-X
        60: (swapQuaternionYZX, negateQuaternionXY),        # -Z-X-Y
        61: (swapQuaternionXZY, negateQuaternionZ),         # -Z-Y-X
    },
    12:     # ZX-Y
    {
        0: (swapQuaternionYZX, negateQuaternionXY),         # XYZ
        1: (swapQuaternionZYX, negateQuaternionZ),          # XZY
        2: (swapQuaternionXZY, negateQuaternionZ),          # YXZ
        3: (swapQuaternionZXY, negateQuaternionXY),         # YZX
        4: (negateQuaternionXY,),                           # ZXY
        5: (swapQuaternionYXZ, negateQuaternionZ),          # ZYX
        8: (swapQuaternionYZX, negateQuaternionYZ),         # XY-Z
        9: (swapQuaternionZYX, negateQuaternionY),          # XZ-Y
        10: (swapQuaternionXZY, negateQuaternionX),         # YX-Z
        11: (swapQuaternionZXY, negateQuaternionXZ),        # YZ-X
        12: (),                                             # ZX-Y
        13: (swapQuaternionYXZ, negateQuaternionXYZ),       # ZY-X
        16: (swapQuaternionYZX, negateQuaternionXZ),        # XY-Z
        17: (swapQuaternionZYX, negateQuaternionX),         # X-ZY
        18: (swapQuaternionXZY, negateQuaternionXYZ),       # Y-XZ
        19: (swapQuaternionZXY,),                           # Y-ZX
        20: (negateQuaternionYZ,),                          # Z-XY
        21: (swapQuaternionYXZ, negateQuaternionY),         # Z-YX
        24: (swapQuaternionYZX,),                           # X-Y-Z
        25: (swapQuaternionZYX, negateQuaternionXYZ),       # X-Z-Y
        26: (swapQuaternionXZY, negateQuaternionY),         # Y-X-Z
        27: (swapQuaternionZXY, negateQuaternionYZ),        # Y-Z-X
        28: (negateQuaternionXZ,),                          # Z-X-Y
        29: (swapQuaternionYXZ, negateQuaternionX),         # Z-Y-X
        32: (swapQuaternionYZX,),                           # -XYZ
        33: (swapQuaternionZYX, negateQuaternionXYZ),       # -XZY
        34: (swapQuaternionXZY, negateQuaternionY),         # -YXZ
        35: (swapQuaternionZXY, negateQuaternionYZ),        # -YZX
        36: (negateQuaternionXZ,),                          # -ZXY
        37: (swapQuaternionYXZ, negateQuaternionX),         # -ZYX
        40: (swapQuaternionYZX, negateQuaternionXZ),        # -XY-Z
        41: (swapQuaternionZYX, negateQuaternionX),         # -XZ-Y
        42: (swapQuaternionXZY, negateQuaternionXYZ),       # -YX-Z
        43: (swapQuaternionZXY,),                           # -YZ-X
        44: (negateQuaternionYZ,),                          # -ZX-Y
        45: (swapQuaternionYXZ, negateQuaternionY),         # -ZY-X
        48: (swapQuaternionYZX, negateQuaternionYZ),        # -X-YZ
        49: (swapQuaternionZYX, negateQuaternionY),         # -X-ZY
        50: (swapQuaternionXZY, negateQuaternionX),         # -Y-XZ
        51: (swapQuaternionZXY, negateQuaternionXZ),        # -Y-ZX
        52: (),                                             # -Z-XY
        53: (swapQuaternionYXZ, negateQuaternionXYZ),       # -Z-YX
        56: (swapQuaternionYZX, negateQuaternionXY),        # -X-Y-Z
        57: (swapQuaternionZYX, negateQuaternionZ),         # -X-Z-Y
        58: (swapQuaternionXZY, negateQuaternionZ),         # -Y-X-Z
        59: (swapQuaternionZXY, negateQuaternionXY),        # -Y-Z-X
        60: (negateQuaternionXY,),                          # -Z-X-Y
        61: (swapQuaternionYXZ, negateQuaternionZ)          # -Z-Y-X
    },
    16:     # X-YZ
    {
        0: (negateQuaternionXZ,),                           # XYZ
        1: (swapQuaternionXZY, negateQuaternionY),          # XZY
        2: (swapQuaternionYXZ, negateQuaternionY),          # YXZ
        3: (swapQuaternionYZX, negateQuaternionXZ),         # YZX
        4: (swapQuaternionZXY, negateQuaternionXZ),         # ZXY
        5: (swapQuaternionZYX, negateQuaternionY),          # ZYX
        8: (negateQuaternionYZ,),                           # XY-Z
        9: (swapQuaternionXZY, negateQuaternionXYZ),        # XZ-Y
        10: (swapQuaternionYXZ, negateQuaternionX),         # YX-Z
        11: (swapQuaternionYZX,),                           # YZ-X
        12: (swapQuaternionZXY, negateQuaternionXY),        # ZX-Y
        13: (swapQuaternionZYX, negateQuaternionZ),         # ZY-X
        16: (),                                             # X-YZ
        17: (swapQuaternionXZY, negateQuaternionX),         # X-ZY
        18: (swapQuaternionYXZ, negateQuaternionZ),         # Y-XZ
        19: (swapQuaternionYZX, negateQuaternionXY),        # Y-ZX
        20: (swapQuaternionZXY, negateQuaternionYZ),        # Z-XY
        21: (swapQuaternionZYX, negateQuaternionXYZ),       # Z-YX
        24: (negateQuaternionXY,),                          # X-Y-Z
        25: (swapQuaternionXZY, negateQuaternionZ),         # X-Z-Y
        26: (swapQuaternionYXZ, negateQuaternionXYZ),       # Y-X-Z
        27: (swapQuaternionYZX, negateQuaternionYZ),        # Y-Z-X
        28: (swapQuaternionZXY,),                           # Z-X-Y
        29: (swapQuaternionZYX, negateQuaternionX),         # Z-Y-X
        32: (negateQuaternionXY,),                          # -XYZ
        33: (swapQuaternionXZY, negateQuaternionZ),         # -XZY
        34: (swapQuaternionYXZ, negateQuaternionXYZ),       # -YXZ
        35: (swapQuaternionYZX, negateQuaternionYZ),        # -YZX
        36: (swapQuaternionZXY,),                           # -ZXY
        37: (swapQuaternionZYX, negateQuaternionX),         # -ZYX
        40: (),                                             # -XY-Z
        41: (swapQuaternionXZY, negateQuaternionX),         # -XZ-Y
        42: (swapQuaternionYXZ, negateQuaternionZ),         # -YX-Z
        43: (swapQuaternionYZX, negateQuaternionXY),        # -YZ-X
        44: (swapQuaternionZXY, negateQuaternionYZ),        # -ZX-Y
        45: (swapQuaternionZYX, negateQuaternionXYZ),       # -ZY-X
        48: (negateQuaternionYZ,),                          # -X-YZ
        49: (swapQuaternionXZY, negateQuaternionXYZ),       # -X-ZY
        50: (swapQuaternionYXZ, negateQuaternionX),         # -Y-XZ
        51: (swapQuaternionYZX,),                           # -Y-ZX
        52: (swapQuaternionZXY, negateQuaternionXY),        # -Z-XY
        53: (swapQuaternionZYX, negateQuaternionZ),         # -Z-YX
        56: (negateQuaternionXZ,),                          # -X-Y-Z
        57: (swapQuaternionXZY, negateQuaternionY),         # -X-Z-Y
        58: (swapQuaternionYXZ, negateQuaternionY),         # -Y-X-Z
        59: (swapQuaternionYZX, negateQuaternionXZ),        # -Y-Z-X
        60: (swapQuaternionZXY, negateQuaternionXZ),        # -Z-X-Y
        61: (swapQuaternionZYX, negateQuaternionY)          # -Z-Y-X
    },
    19:     # Y-ZX
    {
        0: (swapQuaternionZXY, negateQuaternionXZ),         # XYZ
        1: (swapQuaternionYXZ, negateQuaternionY),          # XZY
        2: (swapQuaternionZYX, negateQuaternionY),          # YXZ
        3: (negateQuaternionXZ,),                           # YZX
        4: (swapQuaternionYZX, negateQuaternionXZ),         # ZXY
        5: (swapQuaternionXZY, negateQuaternionY),          # ZYX
        8: (swapQuaternionZXY, negateQuaternionXY),         # XY-Z
        9: (swapQuaternionYXZ, negateQuaternionX),          # XZ-Y
        10: (swapQuaternionZYX, negateQuaternionZ),         # YX-Z
        11: (negateQuaternionYZ,),                          # YZ-X
        12: (swapQuaternionYZX,),                           # ZX-Y
        13: (swapQuaternionXZY, negateQuaternionXYZ),       # ZY-X
        16: (swapQuaternionZXY, negateQuaternionYZ),        # X-YZ
        17: (swapQuaternionYXZ, negateQuaternionZ),         # X-ZY
        18: (swapQuaternionZYX, negateQuaternionXYZ),       # Y-XZ
        19: (),                                             # Y-ZX
        20: (swapQuaternionYZX, negateQuaternionXY),        # Z-XY
        21: (swapQuaternionXZY, negateQuaternionX),         # Z-YX
        24: (swapQuaternionZXY,),                           # X-Y-Z
        25: (swapQuaternionYXZ, negateQuaternionXYZ),       # X-Z-Y
        26: (swapQuaternionZYX, negateQuaternionX),         # Y-X-Z
        27: (negateQuaternionXY,),                          # Y-Z-X
        28: (swapQuaternionYZX, negateQuaternionYZ),        # Z-X-Y
        29: (swapQuaternionXZY, negateQuaternionZ),         # Z-Y-X
        32: (swapQuaternionZXY,),                           # -XYZ
        33: (swapQuaternionYXZ, negateQuaternionXYZ),       # -XZY
        34: (swapQuaternionZYX, negateQuaternionX),         # -YXZ
        35: (negateQuaternionXY,),                          # -YZX
        36: (swapQuaternionYZX, negateQuaternionYZ),        # -ZXY
        37: (swapQuaternionXZY, negateQuaternionZ),         # -ZYX
        40: (swapQuaternionZXY, negateQuaternionYZ),        # -XY-Z
        41: (swapQuaternionYXZ, negateQuaternionZ),         # -XZ-Y
        42: (swapQuaternionZYX, negateQuaternionXYZ),       # -YX-Z
        43: (),                                             # -YZ-X
        44: (swapQuaternionYZX, negateQuaternionXY),        # -ZX-Y
        45: (swapQuaternionXZY, negateQuaternionX),         # -ZY-X
        48: (swapQuaternionZXY, negateQuaternionXY),        # -X-YZ
        49: (swapQuaternionYXZ, negateQuaternionX),         # -X-ZY
        50: (swapQuaternionZYX, negateQuaternionZ),         # -Y-XZ
        51: (negateQuaternionYZ,),                          # -Y-ZX
        52: (swapQuaternionYZX,),                           # -Z-XY
        53: (swapQuaternionXZY, negateQuaternionXYZ),       # -Z-YX
        56: (swapQuaternionZXY, negateQuaternionXZ),        # -X-Y-Z
        57: (swapQuaternionYXZ, negateQuaternionY),         # -X-Z-Y
        58: (swapQuaternionZYX, negateQuaternionY),         # -Y-X-Z
        59: (negateQuaternionXZ,),                          # -Y-Z-X
        60: (swapQuaternionYZX, negateQuaternionXZ),        # -Z-X-Y
        61: (swapQuaternionXZY, negateQuaternionY),         # -Z-Y-X
    },
    20:     # Z-XY
    {
        0: (swapQuaternionYZX, negateQuaternionXZ),         # XYZ
        1: (swapQuaternionZYX, negateQuaternionY),          # XZY
        2: (swapQuaternionXZY, negateQuaternionY),          # YXZ
        3: (swapQuaternionZXY, negateQuaternionXZ),         # YZX
        4: (negateQuaternionXZ,),                           # ZXY
        5: (swapQuaternionYXZ, negateQuaternionY),          # ZYX
        8: (swapQuaternionYZX,),                            # XY-Z
        9: (swapQuaternionZYX, negateQuaternionZ),          # XZ-Y
        10: (swapQuaternionXZY, negateQuaternionXYZ),       # YX-Z
        11: (swapQuaternionZXY, negateQuaternionXY),        # YZ-X
        12: (negateQuaternionYZ,),                          # ZX-Y
        13: (swapQuaternionYXZ, negateQuaternionX),         # ZY-X
        16: (swapQuaternionYZX, negateQuaternionXY),        # XY-Z
        17: (swapQuaternionZYX, negateQuaternionXYZ),       # X-ZY
        18: (swapQuaternionXZY, negateQuaternionX),         # Y-XZ
        19: (swapQuaternionZXY, negateQuaternionYZ),        # Y-ZX
        20: (),                                             # Z-XY
        21: (swapQuaternionYXZ, negateQuaternionZ),         # Z-YX
        24: (swapQuaternionYZX, negateQuaternionYZ),        # X-Y-Z
        25: (swapQuaternionZYX, negateQuaternionX),         # X-Z-Y
        26: (swapQuaternionXZY, negateQuaternionZ),         # Y-X-Z
        27: (swapQuaternionZXY,),                           # Y-Z-X
        28: (negateQuaternionXY,),                          # Z-X-Y
        29: (swapQuaternionYXZ, negateQuaternionXYZ),       # Z-Y-X
        32: (swapQuaternionYZX, negateQuaternionYZ),        # -XYZ
        33: (swapQuaternionZYX, negateQuaternionX),         # -XZY
        34: (swapQuaternionXZY, negateQuaternionZ),         # -YXZ
        35: (swapQuaternionZXY,),                           # -YZX
        36: (negateQuaternionXY,),                          # -ZXY
        37: (swapQuaternionYXZ, negateQuaternionXYZ),       # -ZYX
        40: (swapQuaternionYZX, negateQuaternionXY),        # -XY-Z
        41: (swapQuaternionZYX, negateQuaternionXYZ),       # -XZ-Y
        42: (swapQuaternionXZY, negateQuaternionX),         # -YX-Z
        43: (swapQuaternionZXY, negateQuaternionYZ),        # -YZ-X
        44: (),                                             # -ZX-Y
        45: (swapQuaternionYXZ, negateQuaternionZ),         # -ZY-X
        48: (swapQuaternionYZX,),                           # -X-YZ
        49: (swapQuaternionZYX, negateQuaternionZ),         # -X-ZY
        50: (swapQuaternionXZY, negateQuaternionXYZ),       # -Y-XZ
        51: (swapQuaternionZXY, negateQuaternionXY),        # -Y-ZX
        52: (negateQuaternionYZ,),                          # -Z-XY
        53: (swapQuaternionYXZ, negateQuaternionX),         # -Z-YX
        56: (swapQuaternionYZX, negateQuaternionXZ),        # -X-Y-Z
        57: (swapQuaternionZYX, negateQuaternionY),         # -X-Z-Y
        58: (swapQuaternionXZY, negateQuaternionY),         # -Y-X-Z
        59: (swapQuaternionZXY, negateQuaternionXZ),        # -Y-Z-X
        60: (negateQuaternionXZ,),                          # -Z-X-Y
        61: (swapQuaternionYXZ, negateQuaternionY)          # -Z-Y-X
    },
    25:     # X-Z-Y
    {
        0: (swapQuaternionXZY, negateQuaternionX),          # XYZ
        1: (negateQuaternionYZ,),                           # XZY
        2: (swapQuaternionYZX, negateQuaternionYZ),         # YXZ
        3: (swapQuaternionYXZ, negateQuaternionX),          # YZX
        4: (swapQuaternionZYX, negateQuaternionX),          # ZXY
        5: (swapQuaternionZXY, negateQuaternionYZ),         # ZYX
        8: (swapQuaternionXZY, negateQuaternionZ),          # XY-Z
        9: (negateQuaternionXZ,),                           # XZ-Y
        10: (swapQuaternionYZX, negateQuaternionXY),        # YX-Z
        11: (swapQuaternionYXZ, negateQuaternionY),         # YZ-X
        12: (swapQuaternionZYX, negateQuaternionXYZ),       # ZX-Y
        13: (swapQuaternionZXY,),                           # ZY-X
        16: (swapQuaternionXZY, negateQuaternionY),         # X-YZ
        17: (negateQuaternionXY,),                          # X-ZY
        18: (swapQuaternionYZX,),                           # Y-XZ
        19: (swapQuaternionYXZ, negateQuaternionXYZ),       # Y-ZX
        20: (swapQuaternionZYX, negateQuaternionZ),         # Z-XY
        21: (swapQuaternionZXY, negateQuaternionXZ),        # Z-YX
        24: (swapQuaternionXZY, negateQuaternionXYZ),       # X-Y-Z
        25: (),                                             # X-Z-Y
        26: (swapQuaternionYZX, negateQuaternionXZ),        # Y-X-Z
        27: (swapQuaternionYXZ, negateQuaternionZ),         # Y-Z-X
        28: (swapQuaternionZYX, negateQuaternionY),         # Z-X-Y
        29: (swapQuaternionZXY, negateQuaternionXY),        # Z-Y-X
        32: (swapQuaternionXZY, negateQuaternionXYZ),       # -XYZ
        33: (),                                             # -XZY
        34: (swapQuaternionYZX, negateQuaternionXZ),        # -YXZ
        35: (swapQuaternionYXZ, negateQuaternionZ),         # -YZX
        36: (swapQuaternionZYX, negateQuaternionY),         # -ZXY
        37: (swapQuaternionZXY, negateQuaternionXY),        # -ZYX
        40: (swapQuaternionXZY, negateQuaternionY),         # -XY-Z
        41: (negateQuaternionXY,),                          # -XZ-Y
        42: (swapQuaternionYZX,),                           # -YX-Z
        43: (swapQuaternionYXZ, negateQuaternionXYZ),       # -YZ-X
        44: (swapQuaternionZYX, negateQuaternionZ),         # -ZX-Y
        45: (swapQuaternionZXY, negateQuaternionXZ),        # -ZY-X
        48: (swapQuaternionXZY, negateQuaternionZ),         # -X-YZ
        49: (negateQuaternionXZ,),                          # -X-ZY
        50: (swapQuaternionYZX, negateQuaternionXY),        # -Y-XZ
        51: (swapQuaternionYXZ, negateQuaternionY),         # -Y-ZX
        52: (swapQuaternionZYX, negateQuaternionXYZ),       # -Z-XY
        53: (swapQuaternionZXY,),                           # -Z-YX
        56: (swapQuaternionXZY, negateQuaternionX),         # -X-Y-Z
        57: (negateQuaternionYZ,),                          # -X-Z-Y
        58: (swapQuaternionYZX, negateQuaternionYZ),        # -Y-X-Z
        59: (swapQuaternionYXZ, negateQuaternionX),         # -Y-Z-X
        60: (swapQuaternionZYX, negateQuaternionX),         # -Z-X-Y
        61: (swapQuaternionZXY, negateQuaternionYZ)         # -Z-Y-X
    },
    26:     # Y-X-Z
    {
        0: (swapQuaternionYXZ, negateQuaternionX),          # XYZ
        1: (swapQuaternionZXY, negateQuaternionYZ),         # XZY
        2: (negateQuaternionYZ,),                           # YXZ
        3: (swapQuaternionZYX, negateQuaternionX),          # YZX
        4: (swapQuaternionXZY, negateQuaternionX),          # ZXY
        5: (swapQuaternionYZX, negateQuaternionYZ),         # ZYX
        8: (swapQuaternionYXZ, negateQuaternionY),          # XY-Z
        9: (swapQuaternionZXY,),                            # XZ-Y
        10: (negateQuaternionXZ,),                          # YX-Z
        11: (swapQuaternionZYX, negateQuaternionXYZ),       # YZ-X
        12: (swapQuaternionXZY, negateQuaternionZ),         # ZX-Y
        13: (swapQuaternionYZX, negateQuaternionXY),        # ZY-X
        16: (swapQuaternionYXZ, negateQuaternionXYZ),       # X-YZ
        17: (swapQuaternionZXY, negateQuaternionXZ),        # X-ZY
        18: (negateQuaternionXY,),                          # Y-XZ
        19: (swapQuaternionZYX, negateQuaternionZ),         # Y-ZX
        20: (swapQuaternionXZY, negateQuaternionY),         # Z-XY
        21: (swapQuaternionYZX,),                           # Z-YX
        24: (swapQuaternionYXZ, negateQuaternionZ),         # X-Y-Z
        25: (swapQuaternionZXY, negateQuaternionXY),        # X-Z-Y
        26: (),                                             # Y-X-Z
        27: (swapQuaternionZYX, negateQuaternionY),         # Y-Z-X
        28: (swapQuaternionXZY, negateQuaternionXYZ),       # Z-X-Y
        29: (swapQuaternionYZX, negateQuaternionXZ),        # Z-Y-X
        32: (swapQuaternionYXZ, negateQuaternionZ),         # -XYZ
        33: (swapQuaternionZXY, negateQuaternionXY),        # -XZY
        34: (),                                             # -YXZ
        35: (swapQuaternionZYX, negateQuaternionY),         # -YZX
        36: (swapQuaternionXZY, negateQuaternionXYZ),       # -ZXY
        37: (swapQuaternionYZX, negateQuaternionXZ),        # -ZYX
        40: (swapQuaternionYXZ, negateQuaternionXYZ),       # -XY-Z
        41: (swapQuaternionZXY, negateQuaternionXZ),        # -XZ-Y
        42: (negateQuaternionXY,),                          # -YX-Z
        43: (swapQuaternionZYX, negateQuaternionZ),         # -YZ-X
        44: (swapQuaternionXZY, negateQuaternionY),         # -ZX-Y
        45: (swapQuaternionYZX,),                           # -ZY-X
        48: (swapQuaternionYXZ, negateQuaternionY),         # -X-YZ
        49: (swapQuaternionZXY,),                           # -X-ZY
        50: (negateQuaternionXZ,),                          # -Y-XZ
        51: (swapQuaternionZYX, negateQuaternionXYZ),       # -Y-ZX
        52: (swapQuaternionXZY, negateQuaternionZ),         # -Z-XY
        53: (swapQuaternionYZX, negateQuaternionXY),        # -Z-YX
        56: (swapQuaternionYXZ, negateQuaternionX),         # -X-Y-Z
        57: (swapQuaternionZXY, negateQuaternionYZ),        # -X-Z-Y
        58: (negateQuaternionYZ,),                          # -Y-X-Z
        59: (swapQuaternionZYX, negateQuaternionX),         # -Y-Z-X
        60: (swapQuaternionXZY, negateQuaternionX),         # -Z-X-Y
        61: (swapQuaternionYZX, negateQuaternionYZ),        # -Z-Y-X
    },
    29:     # Z-Y-X
    {
        0: (swapQuaternionZYX, negateQuaternionX),          # XYZ
        1: (swapQuaternionYZX, negateQuaternionYZ),         # XZY
        2: (swapQuaternionZXY, negateQuaternionYZ),         # YXZ
        3: (swapQuaternionXZY, negateQuaternionX),          # YZX
        4: (swapQuaternionYXZ, negateQuaternionX),          # ZXY
        5: (negateQuaternionYZ,),                           # ZYX
        8: (swapQuaternionZYX, negateQuaternionXYZ),        # XY-Z
        9: (swapQuaternionYZX, negateQuaternionXY),         # XZ-Y
        10: (swapQuaternionZXY,),                           # YX-Z
        11: (swapQuaternionXZY, negateQuaternionZ),         # YZ-X
        12: (swapQuaternionYXZ, negateQuaternionY),         # ZX-Y
        13: (negateQuaternionXZ,),                          # ZY-X
        16: (swapQuaternionZYX, negateQuaternionZ),         # X-YZ
        17: (swapQuaternionYZX,),                           # Y-XZ
        18: (swapQuaternionZXY, negateQuaternionXZ),        # Y-XZ
        19: (swapQuaternionXZY, negateQuaternionY),         # Y-ZX
        20: (swapQuaternionYXZ, negateQuaternionXYZ),       # Z-XY
        21: (negateQuaternionXY,),                          # Z-YX
        24: (swapQuaternionZYX, negateQuaternionY),         # X-Y-Z
        25: (swapQuaternionYZX, negateQuaternionXZ),        # X-Z-Y
        26: (swapQuaternionZXY, negateQuaternionXY),        # Y-X-Z
        27: (swapQuaternionXZY, negateQuaternionXYZ),       # Y-Z-X
        28: (swapQuaternionYXZ, negateQuaternionZ),         # Z-X-Y
        29: (),                                             # Z-Y-X
        32: (swapQuaternionZYX, negateQuaternionY),         # -XYZ
        33: (swapQuaternionYZX, negateQuaternionXZ),        # -XZY
        34: (swapQuaternionZXY, negateQuaternionXY),        # -YXZ
        35: (swapQuaternionXZY, negateQuaternionXYZ),       # -YZX
        36: (swapQuaternionYXZ, negateQuaternionZ),         # -ZXY
        37: (),                                             # -ZYX
        40: (swapQuaternionZYX, negateQuaternionZ),         # -XY-Z
        41: (swapQuaternionYZX,),                           # -YX-Z
        42: (swapQuaternionZXY, negateQuaternionXZ),        # -YX-Z
        43: (swapQuaternionXZY, negateQuaternionY),         # -YZ-X
        44: (swapQuaternionYXZ, negateQuaternionXYZ),       # -ZX-Y
        45: (negateQuaternionXY,),                          # -ZY-X
        48: (swapQuaternionZYX, negateQuaternionXYZ),       # -X-YZ
        49: (swapQuaternionYZX, negateQuaternionXY),        # -X-ZY
        50: (swapQuaternionZXY,),                           # -Y-XZ
        51: (swapQuaternionXZY, negateQuaternionZ),         # -Y-ZX
        52: (swapQuaternionYXZ, negateQuaternionY),         # -Z-XY
        53: (negateQuaternionXZ,),                          # -Z-YX
        56: (swapQuaternionZYX, negateQuaternionX),         # -X-Y-Z
        57: (swapQuaternionYZX, negateQuaternionYZ),        # -X-Z-Y
        58: (swapQuaternionZXY, negateQuaternionYZ),        # -Y-X-Z
        59: (swapQuaternionXZY, negateQuaternionX),         # -Y-Z-X
        60: (swapQuaternionYXZ, negateQuaternionX),         # -Z-X-Y
        61: (negateQuaternionYZ,)                           # -Z-Y-X
    },
    32:     # -XYZ
    {
        0: (negateQuaternionYZ,),                           # XYZ
        1: (swapQuaternionXZY, negateQuaternionX),          # XZY
        2: (swapQuaternionYXZ, negateQuaternionX),          # YXZ
        3: (swapQuaternionYZX, negateQuaternionYZ),         # YZX
        4: (swapQuaternionZXY, negateQuaternionYZ),         # ZXY
        5: (swapQuaternionZYX, negateQuaternionX),          # ZYX
        8: (negateQuaternionXZ,),                           # XY-Z
        9: (swapQuaternionXZY, negateQuaternionZ),          # XZ-Y
        10: (swapQuaternionYXZ, negateQuaternionY),         # YX-Z
        11: (swapQuaternionYZX, negateQuaternionXY),        # YZ-X
        12: (swapQuaternionZXY,),                           # ZX-Y
        13: (swapQuaternionZYX, negateQuaternionXYZ),       # ZY-X
        16: (negateQuaternionXY,),                          # X-YZ
        17: (swapQuaternionXZY, negateQuaternionY),         # X-ZY
        18: (swapQuaternionYXZ, negateQuaternionXYZ),       # Y-XZ
        19: (swapQuaternionYZX,),                           # Y-ZX
        20: (swapQuaternionZXY, negateQuaternionXZ),        # Z-XY
        21: (swapQuaternionZYX, negateQuaternionZ),         # Z-YX
        24: (),                                             # X-Y-Z
        25: (swapQuaternionXZY, negateQuaternionXYZ),       # X-Z-Y
        26: (swapQuaternionYXZ, negateQuaternionZ),         # Y-X-Z
        27: (swapQuaternionYZX, negateQuaternionXZ),        # Y-Z-X
        28: (swapQuaternionZXY, negateQuaternionXY),        # Z-X-Y
        29: (swapQuaternionZYX, negateQuaternionY),         # Z-Y-X
        32: (),                                             # -XYZ
        33: (swapQuaternionXZY, negateQuaternionXYZ),       # -XZY
        34: (swapQuaternionYXZ, negateQuaternionZ),         # -YXZ
        35: (swapQuaternionYZX, negateQuaternionXZ),        # -YZX
        36: (swapQuaternionZXY, negateQuaternionXY),        # -ZXY
        37: (swapQuaternionZYX, negateQuaternionY),         # -ZYX
        40: (negateQuaternionXY,),                          # -XY-Z
        41: (swapQuaternionXZY, negateQuaternionY),         # -XZ-Y
        42: (swapQuaternionYXZ, negateQuaternionXYZ),       # -YX-Z
        43: (swapQuaternionYZX,),                           # -YZ-X
        44: (swapQuaternionZXY, negateQuaternionXZ),        # -ZX-Y
        45: (swapQuaternionZYX, negateQuaternionZ),         # -ZY-X
        48: (negateQuaternionXZ,),                          # -X-YZ
        49: (swapQuaternionXZY, negateQuaternionZ),         # -X-ZY
        50: (swapQuaternionYXZ, negateQuaternionY),         # -Y-XZ
        51: (swapQuaternionYZX, negateQuaternionXY),        # -Y-ZX
        52: (swapQuaternionZXY,),                           # -Z-XY
        53: (swapQuaternionZYX, negateQuaternionXYZ),       # -Z-YX
        56: (negateQuaternionYZ,),                          # -X-Y-Z
        57: (swapQuaternionXZY, negateQuaternionX),         # -X-Z-Y
        58: (swapQuaternionYXZ, negateQuaternionX),         # -Y-X-Z
        59: (swapQuaternionYZX, negateQuaternionYZ),        # -Y-Z-X
        60: (swapQuaternionZXY, negateQuaternionYZ),        # -Z-X-Y
        61: (swapQuaternionZYX, negateQuaternionX)          # -Z-Y-X
    },
    35:     # -YZX
    {
        0: (swapQuaternionZXY, negateQuaternionYZ),         # XYZ
        1: (swapQuaternionYXZ, negateQuaternionX),          # XZY
        2: (swapQuaternionZYX, negateQuaternionX),          # YXZ
        3: (negateQuaternionYZ,),                           # YZX
        4: (swapQuaternionYZX, negateQuaternionYZ),         # ZXY
        5: (swapQuaternionXZY, negateQuaternionX),          # ZYX
        8: (swapQuaternionZXY,),                            # XY-Z
        9: (swapQuaternionYXZ, negateQuaternionY),          # XZ-Y
        10: (swapQuaternionZYX, negateQuaternionXYZ),       # YX-Z
        11: (negateQuaternionXZ,),                          # YZ-X
        12: (swapQuaternionYZX, negateQuaternionXY),        # ZX-Y
        13: (swapQuaternionXZY, negateQuaternionZ),         # ZY-X
        16: (swapQuaternionZXY, negateQuaternionXZ),        # X-YZ
        17: (swapQuaternionYXZ, negateQuaternionXYZ),       # X-ZY
        18: (swapQuaternionZYX, negateQuaternionZ),         # Y-XZ
        19: (negateQuaternionXY,),                          # Y-ZX
        20: (swapQuaternionYZX,),                           # Z-XY
        21: (swapQuaternionXZY, negateQuaternionY),         # Z-YX
        24: (swapQuaternionZXY, negateQuaternionXY),        # X-Y-Z
        25: (swapQuaternionYXZ, negateQuaternionZ),         # X-Z-Y
        26: (swapQuaternionZYX, negateQuaternionY),         # Y-X-Z
        27: (),                                             # Y-Z-X
        28: (swapQuaternionYZX, negateQuaternionXZ),        # Z-X-Y
        29: (swapQuaternionXZY, negateQuaternionXYZ),       # Z-Y-X
        32: (swapQuaternionZXY, negateQuaternionXY),        # -XYZ
        33: (swapQuaternionYXZ, negateQuaternionZ),         # -XZY
        34: (swapQuaternionZYX, negateQuaternionY),         # -YXZ
        35: (),                                             # -YZX
        36: (swapQuaternionYZX, negateQuaternionXZ),        # -ZXY
        37: (swapQuaternionXZY, negateQuaternionXYZ),       # -ZYX
        40: (swapQuaternionZXY, negateQuaternionXZ),        # -XY-Z
        41: (swapQuaternionYXZ, negateQuaternionXYZ),       # -XZ-Y
        42: (swapQuaternionZYX, negateQuaternionZ),         # -YX-Z
        43: (negateQuaternionXY,),                          # -YZ-X
        44: (swapQuaternionYZX,),                           # -ZX-Y
        45: (swapQuaternionXZY, negateQuaternionY),         # -ZY-X
        48: (swapQuaternionZXY,),                           # -X-YZ
        49: (swapQuaternionYXZ, negateQuaternionY),         # -X-ZY
        50: (swapQuaternionZYX, negateQuaternionXYZ),       # -Y-XZ
        51: (negateQuaternionXZ,),                          # -Y-ZX
        52: (swapQuaternionYZX, negateQuaternionXY),        # -Z-XY
        53: (swapQuaternionXZY, negateQuaternionZ),         # -Z-YX
        56: (swapQuaternionZXY, negateQuaternionYZ),        # -X-Y-Z
        57: (swapQuaternionYXZ, negateQuaternionX),         # -X-Z-Y
        58: (swapQuaternionZYX, negateQuaternionX),         # -Y-X-Z
        59: (negateQuaternionYZ,),                          # -Y-Z-X
        60: (swapQuaternionYZX, negateQuaternionYZ),        # -Z-X-Y
        61: (swapQuaternionXZY, negateQuaternionX)          # -Z-Y-X
    },
    36:     # -ZXY
    {
        0: (swapQuaternionYZX, negateQuaternionYZ),         # XYZ
        1: (swapQuaternionZYX, negateQuaternionX),          # XZY
        2: (swapQuaternionXZY, negateQuaternionX),          # YXZ
        3: (swapQuaternionZXY, negateQuaternionYZ),         # YZX
        4: (negateQuaternionYZ,),                           # ZXY
        5: (swapQuaternionYXZ, negateQuaternionX),          # ZYX
        8: (swapQuaternionYZX, negateQuaternionXY),         # XY-Z
        9: (swapQuaternionZYX, negateQuaternionXYZ),        # XZ-Y
        10: (swapQuaternionXZY, negateQuaternionZ),         # YX-Z
        11: (swapQuaternionZXY,),                           # YZ-X
        12: (negateQuaternionXZ,),                          # ZX-Y
        13: (swapQuaternionYXZ, negateQuaternionY),         # ZY-X
        16: (swapQuaternionYZX,),                           # X-YX
        17: (swapQuaternionZYX, negateQuaternionZ),         # X-ZY
        18: (swapQuaternionXZY, negateQuaternionY),         # Y-XZ
        19: (swapQuaternionZXY, negateQuaternionXZ),        # Y-ZX
        20: (negateQuaternionXY,),                          # Z-XY
        21: (swapQuaternionYXZ, negateQuaternionXYZ),       # Z-YX
        24: (swapQuaternionYZX, negateQuaternionXZ),        # X-Y-Z
        25: (swapQuaternionZYX, negateQuaternionY),         # X-Z-Y
        26: (swapQuaternionXZY, negateQuaternionXYZ),       # Y-X-Z
        27: (swapQuaternionZXY, negateQuaternionXY),        # Y-Z-X
        28: (),                                             # Z-X-Y
        29: (swapQuaternionYXZ, negateQuaternionZ),         # Z-Y-X
        32: (swapQuaternionYZX, negateQuaternionXZ),        # -XYZ
        33: (swapQuaternionZYX, negateQuaternionY),         # -XZY
        34: (swapQuaternionXZY, negateQuaternionXYZ),       # -YXZ
        35: (swapQuaternionZXY, negateQuaternionXY),        # -YZX
        36: (),                                             # -ZXY
        37: (swapQuaternionYXZ, negateQuaternionZ),         # -ZYX
        40: (swapQuaternionYZX,),                           # -XY-Z
        41: (swapQuaternionZYX, negateQuaternionZ),         # -XZ-Y
        42: (swapQuaternionXZY, negateQuaternionY),         # -YX-Z
        43: (swapQuaternionZXY, negateQuaternionXZ),        # -YZ-X
        44: (negateQuaternionXY,),                          # -ZX-Y
        45: (swapQuaternionYXZ, negateQuaternionXYZ),       # -ZY-X
        48: (swapQuaternionYZX, negateQuaternionXY),        # -X-YZ
        49: (swapQuaternionZYX, negateQuaternionXYZ),       # -X-ZY
        50: (swapQuaternionXZY, negateQuaternionZ),         # -Y-XZ
        51: (swapQuaternionZXY,),                           # -Y-ZX
        52: (negateQuaternionXZ,),                          # -Z-XY
        53: (swapQuaternionYXZ, negateQuaternionY),         # -Z-YX
        56: (swapQuaternionYZX, negateQuaternionYZ),        # -X-Y-Z
        57: (swapQuaternionZYX, negateQuaternionX),         # -X-Z-Y
        58: (swapQuaternionXZY, negateQuaternionX),         # -Y-X-Z
        59: (swapQuaternionZXY, negateQuaternionYZ),        # -Y-Z-X
        60: (negateQuaternionYZ,),                          # -Z-X-Y
        61: (swapQuaternionYXZ, negateQuaternionX)          # -Z-Y-X
    },
    41:     # -XZ-Y
    {
        0: (swapQuaternionXZY, negateQuaternionY),          # XYZ
        1: (negateQuaternionXZ,),                           # XZY
        2: (swapQuaternionYZX, negateQuaternionXZ),         # YXZ
        3: (swapQuaternionYXZ, negateQuaternionY),          # YZX
        4: (swapQuaternionZYX, negateQuaternionY),          # ZXY
        5: (swapQuaternionZXY, negateQuaternionXZ),         # ZYX
        8: (swapQuaternionXZY, negateQuaternionXYZ),        # XY-Z
        9: (negateQuaternionYZ,),                           # XZ-Y
        10: (swapQuaternionYZX,),                           # YX-Z
        11: (swapQuaternionYXZ, negateQuaternionX),         # YZ-X
        12: (swapQuaternionZYX, negateQuaternionZ),         # ZX-Y
        13: (swapQuaternionZXY, negateQuaternionXY),        # ZY-X
        16: (swapQuaternionXZY, negateQuaternionX),         # X-YZ
        17: (),                                             # X-ZY
        18: (swapQuaternionYZX, negateQuaternionXY),        # Y-XZ
        19: (swapQuaternionYXZ, negateQuaternionZ),         # Y-ZX
        20: (swapQuaternionZYX, negateQuaternionXYZ),       # Z-XY
        21: (swapQuaternionZXY, negateQuaternionYZ),        # Z-YX
        24: (swapQuaternionXZY, negateQuaternionZ),         # X-Y-Z
        25: (negateQuaternionXY,),                          # X-Z-Y
        26: (swapQuaternionYZX, negateQuaternionYZ),        # Y-X-Z
        27: (swapQuaternionYXZ, negateQuaternionXYZ),       # Y-Z-X
        28: (swapQuaternionZYX, negateQuaternionX),         # Z-X-Y
        29: (swapQuaternionZXY,),                           # Z-Y-X
        32: (swapQuaternionXZY, negateQuaternionZ),         # -XYZ
        33: (negateQuaternionXY,),                          # -XZY
        34: (swapQuaternionYZX, negateQuaternionYZ),        # -YXZ
        35: (swapQuaternionYXZ, negateQuaternionXYZ),       # -YZX
        36: (swapQuaternionZYX, negateQuaternionX),         # -ZXY
        37: (swapQuaternionZXY,),                           # -ZYX
        40: (swapQuaternionXZY, negateQuaternionX),         # -XY-Z
        41: (),                                             # -XZ-Y
        42: (swapQuaternionYZX, negateQuaternionXY),        # -YX-Z
        43: (swapQuaternionYXZ, negateQuaternionZ),         # -YZ-X
        44: (swapQuaternionZYX, negateQuaternionXYZ),       # -ZX-Y
        45: (swapQuaternionZXY, negateQuaternionYZ),        # -ZY-X
        48: (swapQuaternionXZY, negateQuaternionXYZ),       # -XY-Z
        49: (negateQuaternionYZ,),                          # -XZ-Y
        50: (swapQuaternionYZX,),                           # YX-Z
        51: (swapQuaternionYXZ, negateQuaternionX),         # -Y-ZX
        52: (swapQuaternionZYX, negateQuaternionZ),         # -Z-XY
        53: (swapQuaternionZXY, negateQuaternionXY),        # -Z-YX
        56: (swapQuaternionXZY, negateQuaternionY),         # -X-Y-Z
        57: (negateQuaternionXZ,),                          # -X-Z-Y
        58: (swapQuaternionYZX, negateQuaternionXZ),        # -Y-X-Z
        59: (swapQuaternionYXZ, negateQuaternionY),         # -Y-Z-X
        60: (swapQuaternionZYX, negateQuaternionY),         # -Z-X-Y
        61: (swapQuaternionZXY, negateQuaternionXZ)         # -Z-Y-X
    },
    42:     # -YX-Z
    {
        0: (swapQuaternionYXZ, negateQuaternionY),          # XYZ
        1: (swapQuaternionZXY, negateQuaternionXZ),         # XZY
        2: (negateQuaternionXZ,),                           # YXZ
        3: (swapQuaternionZYX, negateQuaternionY),          # YZX
        4: (swapQuaternionXZY, negateQuaternionY),          # ZXY
        5: (swapQuaternionYZX, negateQuaternionXZ),         # ZYX
        8: (swapQuaternionYXZ, negateQuaternionX),          # XY-Z
        9: (swapQuaternionZXY, negateQuaternionXY),         # XZ-Y
        10: (negateQuaternionYZ,),                          # YX-Z
        11: (swapQuaternionZYX, negateQuaternionZ),         # YZ-X
        12: (swapQuaternionXZY, negateQuaternionXYZ),       # ZX-Y
        13: (swapQuaternionYZX,),                           # ZY-X
        16: (swapQuaternionYXZ, negateQuaternionZ),         # X-YZ
        17: (swapQuaternionZXY, negateQuaternionYZ),        # X-ZY
        18: (),                                             # Y-XZ
        19: (swapQuaternionZYX, negateQuaternionXYZ),       # Y-ZX
        20: (swapQuaternionXZY, negateQuaternionX),         # Z-XY
        21: (swapQuaternionYZX, negateQuaternionXY),        # Z-YX
        24: (swapQuaternionYXZ, negateQuaternionXYZ),       # X-Y-Z
        25: (swapQuaternionZXY,),                           # X-Z-Y
        26: (negateQuaternionXY,),                          # Y-X-Z
        27: (swapQuaternionZYX, negateQuaternionX),         # Y-Z-X
        28: (swapQuaternionXZY, negateQuaternionZ),         # Z-X-Y
        29: (swapQuaternionYZX, negateQuaternionYZ),        # Z-Y-X
        32: (swapQuaternionYXZ, negateQuaternionXYZ),       # -XYZ
        33: (swapQuaternionZXY,),                           # -XZY
        34: (negateQuaternionXY,),                          # -YXZ
        35: (swapQuaternionZYX, negateQuaternionX),         # -YZX
        36: (swapQuaternionXZY, negateQuaternionZ),         # -ZXY
        37: (swapQuaternionYZX, negateQuaternionYZ),        # -ZYX
        40: (swapQuaternionYXZ, negateQuaternionZ),         # -XY-Z
        41: (swapQuaternionZXY, negateQuaternionYZ),        # -XZ-Y
        42: (),                                             # -YX-Z
        43: (swapQuaternionZYX, negateQuaternionXYZ),       # -YZ-X
        44: (swapQuaternionXZY, negateQuaternionX),         # -ZX-Y
        45: (swapQuaternionYZX, negateQuaternionXY),        # -ZY-X
        48: (swapQuaternionYXZ, negateQuaternionX),         # -X-YZ
        49: (swapQuaternionZXY, negateQuaternionXY),        # -X-ZY
        50: (negateQuaternionYZ,),                          # -Y-XZ
        51: (swapQuaternionZYX, negateQuaternionZ),         # -Y-ZX
        52: (swapQuaternionXZY, negateQuaternionXYZ),       # -Z-XY
        53: (swapQuaternionYZX,),                           # -Z-YX
        56: (swapQuaternionYXZ, negateQuaternionY),         # -X-Y-Z
        57: (swapQuaternionZXY, negateQuaternionXZ),        # -X-Z-Y
        58: (negateQuaternionXZ,),                          # -Y-X-Z
        59: (swapQuaternionZYX, negateQuaternionY),         # -Y-Z-X
        60: (swapQuaternionXZY, negateQuaternionY),         # -Z-X-Y
        61: (swapQuaternionYZX, negateQuaternionXZ),        # -Z-Y-X
    },
    45:     # -ZY-X
    {
        0: (swapQuaternionZYX, negateQuaternionY),          # XYZ
        1: (swapQuaternionYZX, negateQuaternionXZ),         # XZY
        2: (swapQuaternionZXY, negateQuaternionXZ),         # YXZ
        3: (swapQuaternionXZY, negateQuaternionY),          # YZX
        4: (swapQuaternionYXZ, negateQuaternionY),          # ZXY
        5: (negateQuaternionXZ,),                           # ZYX
        8: (swapQuaternionZYX, negateQuaternionZ),          # XY-Z
        9: (swapQuaternionYZX,),                            # XZ-Y
        10: (swapQuaternionZXY, negateQuaternionXY),        # YX-Z
        11: (swapQuaternionXZY, negateQuaternionXYZ),       # YZ-X
        12: (swapQuaternionYXZ, negateQuaternionX),         # ZX-Y
        13: (negateQuaternionYZ,),                          # ZY-X
        16: (swapQuaternionZYX, negateQuaternionXYZ),       # X-YZ
        17: (swapQuaternionYZX, negateQuaternionXY),        # X-ZY
        18: (swapQuaternionZXY, negateQuaternionYZ),        # Y-XZ
        19: (swapQuaternionXZY, negateQuaternionX),         # Y-ZX
        20: (swapQuaternionYXZ, negateQuaternionZ),         # Z-XY
        21: (),                                             # Z-YX
        24: (swapQuaternionZYX, negateQuaternionX),         # X-Y-Z
        25: (swapQuaternionYZX, negateQuaternionYZ),        # X-Z-Y
        26: (swapQuaternionZXY,),                           # Y-X-Z
        27: (swapQuaternionXZY, negateQuaternionZ),         # Y-Z-X
        28: (swapQuaternionYXZ, negateQuaternionXYZ),       # Z-X-Y
        29: (negateQuaternionXY,),                          # Z-Y-X
        32: (swapQuaternionZYX, negateQuaternionX),         # -XYZ
        33: (swapQuaternionYZX, negateQuaternionYZ),        # -XZY
        34: (swapQuaternionZXY,),                           # -YXZ
        35: (swapQuaternionXZY, negateQuaternionZ),         # -YZX
        36: (swapQuaternionYXZ, negateQuaternionXYZ),       # -ZXY
        37: (negateQuaternionXY,),                          # -ZYX
        40: (swapQuaternionZYX, negateQuaternionXYZ),       # -XY-Z
        41: (swapQuaternionYZX, negateQuaternionXY),        # -XZ-Y
        42: (swapQuaternionZXY, negateQuaternionYZ),        # -YX-Z
        43: (swapQuaternionXZY, negateQuaternionX),         # -YZ-X
        44: (swapQuaternionYXZ, negateQuaternionZ),         # -ZX-Y
        45: (),                                             # -ZY-X
        48: (swapQuaternionZYX, negateQuaternionZ),         # -X-YZ
        49: (swapQuaternionYZX,),                           # -X-ZY
        50: (swapQuaternionZXY, negateQuaternionXY),        # -Y-XZ
        51: (swapQuaternionXZY, negateQuaternionXYZ),       # -Y-ZX
        52: (swapQuaternionYXZ, negateQuaternionX),         # -Z-XY
        53: (negateQuaternionYZ,),                          # -Z-YX
        56: (swapQuaternionZYX, negateQuaternionY),         # -X-Y-Z
        57: (swapQuaternionYZX, negateQuaternionXZ),        # -X-Z-Y
        58: (swapQuaternionZXY, negateQuaternionXZ),        # -Y-X-Z
        59: (swapQuaternionXZY, negateQuaternionY),         # -Y-Z-X
        60: (swapQuaternionYXZ, negateQuaternionY),         # -Z-X-Y
        61: (negateQuaternionXZ,)                           # -Z-Y-X
    },
    49:     # -X-ZY
    {
        0: (swapQuaternionXZY, negateQuaternionZ),          # XYZ
        1: (negateQuaternionXY,),                           # XZY
        2: (swapQuaternionYZX, negateQuaternionXY),         # YXZ
        3: (swapQuaternionYXZ, negateQuaternionZ),          # YZX
        4: (swapQuaternionZYX, negateQuaternionZ),          # ZXY
        5: (swapQuaternionZXY, negateQuaternionXY),         # ZYX
        8: (swapQuaternionXZY, negateQuaternionX),          # XY-Z
        9: (),                                              # XZ-Y
        10: (swapQuaternionYZX, negateQuaternionYZ),        # YX-Z
        11: (swapQuaternionYXZ, negateQuaternionXYZ),       # YZ-X
        12: (swapQuaternionZYX, negateQuaternionY),         # ZX-Y
        13: (swapQuaternionZXY, negateQuaternionXZ),        # ZY-X
        16: (swapQuaternionXZY, negateQuaternionXYZ),       # X-YZ
        17: (negateQuaternionYZ,),                          # X-ZY
        18: (swapQuaternionYZX, negateQuaternionXZ),        # Y-XZ
        19: (swapQuaternionYXZ, negateQuaternionY),         # Y-ZX
        20: (swapQuaternionZYX, negateQuaternionX),         # Z-XY
        21: (swapQuaternionZXY,),                           # Z-YX
        24: (swapQuaternionXZY, negateQuaternionY),         # X-Y-Z
        25: (negateQuaternionXZ,),                          # X-Z-Y
        26: (swapQuaternionYZX,),                           # Y-X-Z
        27: (swapQuaternionYXZ, negateQuaternionX),         # Y-Z-X
        28: (swapQuaternionZYX, negateQuaternionXYZ),       # Z-X-Y
        29: (swapQuaternionZXY, negateQuaternionYZ),        # Z-Y-X
        32: (swapQuaternionXZY, negateQuaternionY),         # -XYZ
        33: (negateQuaternionXZ,),                          # -XZY
        34: (swapQuaternionYZX,),                           # -YXZ
        35: (swapQuaternionYXZ, negateQuaternionX),         # -YZX
        36: (swapQuaternionZYX, negateQuaternionXYZ),       # -ZXY
        37: (swapQuaternionZXY, negateQuaternionYZ),        # -ZYX
        40: (swapQuaternionXZY, negateQuaternionXYZ),       # -XY-Z
        41: (negateQuaternionYZ,),                          # -XZ-Y
        42: (swapQuaternionYZX, negateQuaternionXZ),        # -YX-Z
        43: (swapQuaternionYXZ, negateQuaternionY),         # -YZ-X
        44: (swapQuaternionZYX, negateQuaternionX),         # -ZX-Y
        45: (swapQuaternionZXY,),                           # -ZY-X
        48: (swapQuaternionXZY, negateQuaternionX),         # -X-YZ
        49: (),                                             # -X-ZY
        50: (swapQuaternionYZX, negateQuaternionYZ),        # -Y-XZ
        51: (swapQuaternionYXZ, negateQuaternionXYZ),       # -Y-ZX
        52: (swapQuaternionZYX, negateQuaternionY),         # -Z-XY
        53: (swapQuaternionZXY, negateQuaternionXZ),        # -Z-YX
        56: (swapQuaternionXZY, negateQuaternionZ),         # -X-Y-Z
        57: (negateQuaternionXY,),                          # -X-Z-Y
        58: (swapQuaternionYZX, negateQuaternionXY),        # -Y-X-Z
        59: (swapQuaternionYXZ, negateQuaternionZ),         # -Y-Z-X
        60: (swapQuaternionZYX, negateQuaternionZ),         # -Z-X-Y
        61: (swapQuaternionZXY, negateQuaternionXY)         # -Z-Y-X
    },
    50:     # -Y-XZ
    {
        0: (swapQuaternionYXZ, negateQuaternionZ),          # XYZ
        1: (swapQuaternionZXY, negateQuaternionXY),         # XZY
        2: (negateQuaternionXY,),                           # YXZ
        3: (swapQuaternionZYX, negateQuaternionZ),          # YZX
        4: (swapQuaternionXZY, negateQuaternionZ),          # ZXY
        5: (swapQuaternionYZX, negateQuaternionXY),         # ZYX
        8: (swapQuaternionYXZ, negateQuaternionXYZ),        # XY-Z
        9: (swapQuaternionZXY, negateQuaternionXZ),         # XZ-Y
        10: (),                                             # YX-Z
        11: (swapQuaternionZYX, negateQuaternionY),         # YZ-X
        12: (swapQuaternionXZY, negateQuaternionX),         # ZX-Y
        13: (swapQuaternionYZX, negateQuaternionYZ),        # ZY-X
        16: (swapQuaternionYXZ, negateQuaternionY),         # X-YZ
        17: (swapQuaternionZXY,),                           # X-ZY
        18: (negateQuaternionYZ,),                          # Y-XZ
        19: (swapQuaternionZYX, negateQuaternionX),         # Y-ZX
        20: (swapQuaternionXZY, negateQuaternionXYZ),       # Z-XY
        21: (swapQuaternionYZX, negateQuaternionXZ),        # Z-YX
        24: (swapQuaternionYXZ, negateQuaternionX),         # X-Y-Z
        25: (swapQuaternionZXY, negateQuaternionYZ),        # X-Z-Y
        26: (negateQuaternionXZ,),                          # Y-X-Z
        27: (swapQuaternionZYX, negateQuaternionXYZ),       # Y-Z-X
        28: (swapQuaternionXZY, negateQuaternionY),         # Z-X-Y
        29: (swapQuaternionYZX,),                           # Z-Y-X
        32: (swapQuaternionYXZ, negateQuaternionX),         # -XYZ
        33: (swapQuaternionZXY, negateQuaternionYZ),        # -XZY
        34: (negateQuaternionXZ,),                          # -YXZ
        35: (swapQuaternionZYX, negateQuaternionXYZ),       # -YZX
        36: (swapQuaternionXZY, negateQuaternionY),         # -ZXY
        37: (swapQuaternionYZX,),                           # -ZYX
        40: (swapQuaternionYXZ, negateQuaternionY),         # -XY-Z
        41: (swapQuaternionZXY,),                           # -XZ-Y
        42: (negateQuaternionYZ,),                          # -YX-Z
        43: (swapQuaternionZYX, negateQuaternionX),         # -YZ-X
        44: (swapQuaternionXZY, negateQuaternionXYZ),       # -ZX-Y
        45: (swapQuaternionYZX, negateQuaternionXZ),        # -ZY-X
        48: (swapQuaternionYXZ, negateQuaternionXYZ),       # -X-YZ
        49: (swapQuaternionZXY, negateQuaternionXZ),        # -X-ZY
        50: (),                                             # -Y-XZ
        51: (swapQuaternionZYX, negateQuaternionY),         # -Y-ZX
        52: (swapQuaternionXZY, negateQuaternionX),         # -Z-XY
        53: (swapQuaternionYZX, negateQuaternionYZ),        # -Z-YX
        56: (swapQuaternionYXZ, negateQuaternionZ),         # -X-Y-Z
        57: (swapQuaternionZXY, negateQuaternionXY),        # -X-Z-Y
        58: (negateQuaternionXY,),                          # -Y-X-Z
        59: (swapQuaternionZYX, negateQuaternionZ),         # -Y-Z-X
        60: (swapQuaternionXZY, negateQuaternionZ),         # -Z-X-Y
        61: (swapQuaternionYZX, negateQuaternionXY),        # -Z-Y-X
    },
    53:     # -Z-YX
    {
        0: (swapQuaternionZYX, negateQuaternionZ),          # XYZ
        1: (swapQuaternionYZX, negateQuaternionXY),         # XZY
        2: (swapQuaternionZXY, negateQuaternionXY),         # YXZ
        3: (swapQuaternionXZY, negateQuaternionZ),          # YZX
        4: (swapQuaternionYXZ, negateQuaternionZ),          # ZXY
        5: (negateQuaternionXY,),                           # ZYX
        8: (swapQuaternionZYX, negateQuaternionY),          # XY-Z
        9: (swapQuaternionYZX, negateQuaternionYZ),         # XZ-Y
        10: (swapQuaternionZXY, negateQuaternionXZ),        # YX-Z
        11: (swapQuaternionXZY, negateQuaternionX),         # YZ-X
        12: (swapQuaternionYXZ, negateQuaternionXYZ),       # ZX-Y
        13: (),                                             # ZY-X
        16: (swapQuaternionZYX, negateQuaternionX),         # X-YZ
        17: (swapQuaternionYZX, negateQuaternionXZ),        # X-ZY
        18: (swapQuaternionZXY,),                           # Y-XZ
        19: (swapQuaternionXZY, negateQuaternionXYZ),       # Y-ZX
        20: (swapQuaternionYXZ, negateQuaternionY),         # Z-XY
        21: (negateQuaternionYZ,),                          # Z-YX
        24: (swapQuaternionZYX, negateQuaternionXYZ),       # X-Y-Z
        25: (swapQuaternionYZX,),                           # X-Z-Y
        26: (swapQuaternionZXY, negateQuaternionYZ),        # Y-X-Z
        27: (swapQuaternionXZY, negateQuaternionY),         # Y-Z-X
        28: (swapQuaternionYXZ, negateQuaternionX),         # Z-X-Y
        29: (negateQuaternionXZ,),                          # Z-Y-X
        32: (swapQuaternionZYX, negateQuaternionXYZ),       # -XYZ
        33: (swapQuaternionYZX,),                           # -XZY
        34: (swapQuaternionZXY, negateQuaternionYZ),        # -YXZ
        35: (swapQuaternionXZY, negateQuaternionY),         # -YZX
        36: (swapQuaternionYXZ, negateQuaternionX),         # -ZXY
        37: (negateQuaternionXZ,),                          # -ZYX
        40: (swapQuaternionZYX, negateQuaternionX),         # -XY-Z
        41: (swapQuaternionYZX, negateQuaternionXZ),        # -XZ-Y
        42: (swapQuaternionZXY,),                           # -YX-Z
        43: (swapQuaternionXZY, negateQuaternionXYZ),       # -YZ-X
        44: (swapQuaternionYXZ, negateQuaternionY),         # -ZX-Y
        45: (negateQuaternionYZ,),                          # -ZY-X
        48: (swapQuaternionZYX, negateQuaternionY),         # -X-YZ
        49: (swapQuaternionYZX, negateQuaternionYZ),        # -X-ZY
        50: (swapQuaternionZXY, negateQuaternionXZ),        # -Y-XZ
        51: (swapQuaternionXZY, negateQuaternionX),         # -Y-ZX
        52: (swapQuaternionYXZ, negateQuaternionXYZ),       # -Z-XY
        53: (),                                             # -Z-YX
        56: (swapQuaternionZYX, negateQuaternionZ),         # -X-Y-Z
        57: (swapQuaternionYZX, negateQuaternionXY),        # -X-Z-Y
        58: (swapQuaternionZXY, negateQuaternionXY),        # -Y-X-Z
        59: (swapQuaternionXZY, negateQuaternionZ),         # -Y-Z-X
        60: (swapQuaternionYXZ, negateQuaternionZ),         # -Z-X-Y
        61: (negateQuaternionXY,)                           # -Z-Y-X
    },
    56:     # -X-Y-Z
    {
        0: (),                                              # XYZ
        1: (swapQuaternionXZY, negateQuaternionXYZ),        # XZY
        2: (swapQuaternionYXZ, negateQuaternionXYZ),        # YXZ
        3: (swapQuaternionYZX,),                            # YZX
        4: (swapQuaternionZXY,),                            # ZXY
        5: (swapQuaternionZYX, negateQuaternionXYZ),        # ZYX
        8: (negateQuaternionXY,),                           # XY-Z
        9: (swapQuaternionXZY, negateQuaternionY),          # XZ-Y
        10: (swapQuaternionYXZ, negateQuaternionZ),         # YX-Z
        11: (swapQuaternionYZX, negateQuaternionXZ),        # YZ-X
        12: (swapQuaternionZXY, negateQuaternionYZ),        # ZX-Y
        13: (swapQuaternionZYX, negateQuaternionX),         # ZY-X
        16: (negateQuaternionXZ,),                          # X-YZ
        17: (swapQuaternionXZY, negateQuaternionZ),         # X-ZY
        18: (swapQuaternionYXZ, negateQuaternionX),         # Y-XZ
        19: (swapQuaternionYZX, negateQuaternionYZ),        # Y-ZX
        20: (swapQuaternionZXY, negateQuaternionXY),        # Z-XY
        21: (swapQuaternionZYX, negateQuaternionY),         # Z-YX
        24: (negateQuaternionYZ,),                          # X-Y-Z
        25: (swapQuaternionXZY, negateQuaternionX),         # X-Z-Y
        26: (swapQuaternionYXZ, negateQuaternionY),         # Y-X-Z
        27: (swapQuaternionYZX, negateQuaternionXY),        # Y-Z-X
        28: (swapQuaternionZXY, negateQuaternionXZ),        # Z-X-Y
        29: (swapQuaternionZYX, negateQuaternionZ),         # Z-Y-X
        32: (negateQuaternionYZ,),                          # -XYZ
        33: (swapQuaternionXZY, negateQuaternionX),         # -XZY
        34: (swapQuaternionYXZ, negateQuaternionY),         # -YXZ
        35: (swapQuaternionYZX, negateQuaternionXY),        # -YZX
        36: (swapQuaternionZXY, negateQuaternionXZ),        # -ZXY
        37: (swapQuaternionZYX, negateQuaternionZ),         # -ZYX
        40: (negateQuaternionXZ,),                          # -XY-Z
        41: (swapQuaternionXZY, negateQuaternionZ),         # -XZ-Y
        42: (swapQuaternionYXZ, negateQuaternionX),         # -YX-Z
        43: (swapQuaternionYZX, negateQuaternionYZ),        # -YZ-X
        44: (swapQuaternionZXY, negateQuaternionXY),        # -ZX-Y
        45: (swapQuaternionZYX, negateQuaternionY),         # -ZY-X
        48: (negateQuaternionXY,),                          # -X-YZ
        49: (swapQuaternionXZY, negateQuaternionY),         # -X-ZY
        50: (swapQuaternionYXZ, negateQuaternionZ),         # -Y-XZ
        51: (swapQuaternionYZX, negateQuaternionXZ),        # -Y-ZX
        52: (swapQuaternionZXY, negateQuaternionYZ),        # -Z-XY
        53: (swapQuaternionZYX, negateQuaternionX),         # -Z-YX
        56: (),                                             # -X-Y-Z
        57: (swapQuaternionXZY, negateQuaternionXYZ),       # -X-Z-Y
        58: (swapQuaternionYXZ, negateQuaternionXYZ),       # -Y-X-Z
        59: (swapQuaternionYZX,),                           # -Y-Z-X
        60: (swapQuaternionZXY,),                           # -Z-X-Y
        61: (swapQuaternionZYX, negateQuaternionXYZ)        # -Z-Y-X
    },
    59:     # -Y-Z-X
    {
        0: (swapQuaternionZXY,),                            # XYZ
        1: (swapQuaternionYXZ, negateQuaternionXYZ),        # XZY
        2: (swapQuaternionZYX, negateQuaternionXYZ),        # YXZ
        3: (),                                              # YZX
        4: (swapQuaternionYZX,),                            # ZXY
        5: (swapQuaternionXZY, negateQuaternionXYZ),        # ZYX
        8: (swapQuaternionZXY, negateQuaternionYZ),         # XY-Z
        9: (swapQuaternionYXZ, negateQuaternionZ),          # XZ-Y
        10: (swapQuaternionZYX, negateQuaternionX),         # YX-Z
        11: (negateQuaternionXY,),                          # YZ-X
        12: (swapQuaternionYZX, negateQuaternionXZ),        # ZX-Y
        13: (swapQuaternionXZY, negateQuaternionY),         # ZY-X
        16: (swapQuaternionZXY, negateQuaternionXY),        # X-YZ
        17: (swapQuaternionYXZ, negateQuaternionX),         # X-ZY
        18: (swapQuaternionZYX, negateQuaternionY),         # Y-XZ
        19: (negateQuaternionXZ,),                          # Y-ZX
        20: (swapQuaternionYZX, negateQuaternionYZ),        # Z-XY
        21: (swapQuaternionXZY, negateQuaternionZ),         # Z-YX
        24: (swapQuaternionZXY, negateQuaternionXZ),        # X-Y-Z
        25: (swapQuaternionYXZ, negateQuaternionY),         # X-Z-Y
        26: (swapQuaternionZYX, negateQuaternionZ),         # Y-X-Z
        27: (negateQuaternionYZ,),                          # Y-Z-X
        28: (swapQuaternionYZX, negateQuaternionXY),        # Z-X-Y
        29: (swapQuaternionXZY, negateQuaternionX),         # Z-Y-X
        32: (swapQuaternionZXY, negateQuaternionXZ),        # -XYZ
        33: (swapQuaternionYXZ, negateQuaternionY),         # -XZY
        34: (swapQuaternionZYX, negateQuaternionZ),         # -YXZ
        35: (negateQuaternionYZ,),                          # -YZX
        36: (swapQuaternionYZX, negateQuaternionXY),        # -ZXY
        37: (swapQuaternionXZY, negateQuaternionX),         # -ZYX
        40: (swapQuaternionZXY, negateQuaternionXY),        # -XY-Z
        41: (swapQuaternionYXZ, negateQuaternionX),         # -XZ-Y
        42: (swapQuaternionZYX, negateQuaternionY),         # -YX-Z
        43: (negateQuaternionXZ,),                          # -YZ-X
        44: (swapQuaternionYZX, negateQuaternionYZ),        # -ZX-Y
        45: (swapQuaternionXZY, negateQuaternionZ),         # -ZY-X
        48: (swapQuaternionZXY, negateQuaternionYZ),        # -X-YZ
        49: (swapQuaternionYXZ, negateQuaternionZ),         # -X-ZY
        50: (swapQuaternionZYX, negateQuaternionX),         # -Y-XZ
        51: (negateQuaternionXY,),                          # -Y-ZX
        52: (swapQuaternionYZX, negateQuaternionXZ),        # -Z-XY
        53: (swapQuaternionXZY, negateQuaternionY),         # -Z-YX
        56: (swapQuaternionZXY,),                           # -X-Y-Z
        57: (swapQuaternionYXZ, negateQuaternionXYZ),       # -X-Z-Y
        58: (swapQuaternionZYX, negateQuaternionXYZ),       # -Y-X-Z
        59: (),                                             # -Y-Z-X
        60: (swapQuaternionYZX,),                           # -Z-X-Y
        61: (swapQuaternionXZY, negateQuaternionXYZ)        # -Z-Y-X
    },
    60:     # -Z-X-Y
    {
        0: (swapQuaternionYZX,),                            # XYZ
        1: (swapQuaternionZYX, negateQuaternionXYZ),        # XZY
        2: (swapQuaternionXZY, negateQuaternionXYZ),        # YXZ
        3: (swapQuaternionZXY,),                            # YZX
        4: (),                                              # ZXY
        5: (swapQuaternionYXZ, negateQuaternionXYZ),        # ZYX
        8: (swapQuaternionYZX, negateQuaternionXZ),         # XY-Z
        9: (swapQuaternionZYX, negateQuaternionX),          # XZ-Y
        10: (swapQuaternionXZY, negateQuaternionY),         # YX-Z
        11: (swapQuaternionZXY, negateQuaternionYZ),        # YZ-X
        12: (negateQuaternionXY,),                          # ZX-Y
        13: (swapQuaternionYXZ, negateQuaternionZ),         # ZY-X
        16: (swapQuaternionYZX, negateQuaternionYZ),        # X-YZ
        17: (swapQuaternionZYX, negateQuaternionY),         # X-ZY
        18: (swapQuaternionXZY, negateQuaternionZ),         # Y-XZ
        19: (swapQuaternionZXY, negateQuaternionXY),        # Y-ZX
        20: (negateQuaternionXZ,),                          # Z-XY
        21: (swapQuaternionYXZ, negateQuaternionX),         # Z-YX
        24: (swapQuaternionYZX, negateQuaternionXY),        # X-Y-Z
        25: (swapQuaternionZYX, negateQuaternionZ),         # X-Z-Y
        26: (swapQuaternionXZY, negateQuaternionX),         # Y-X-Z
        27: (swapQuaternionZXY, negateQuaternionXZ),        # Y-Z-X
        28: (negateQuaternionYZ,),                          # Z-X-Y
        29: (swapQuaternionYXZ, negateQuaternionY),         # Z-Y-X
        32: (swapQuaternionYZX, negateQuaternionXY),        # -XYZ
        33: (swapQuaternionZYX, negateQuaternionZ),         # -XZY
        34: (swapQuaternionXZY, negateQuaternionX),         # -YXZ
        35: (swapQuaternionZXY, negateQuaternionXZ),        # -YZX
        36: (negateQuaternionYZ,),                          # -ZXY
        37: (swapQuaternionYXZ, negateQuaternionY),         # -ZYX
        40: (swapQuaternionYZX, negateQuaternionYZ),        # -XY-Z
        41: (swapQuaternionZYX, negateQuaternionY),         # -XZ-Y
        42: (swapQuaternionXZY, negateQuaternionZ),         # -YX-Z
        43: (swapQuaternionZXY, negateQuaternionXY),        # -YZ-X
        44: (negateQuaternionXZ,),                          # -ZX-Y
        45: (swapQuaternionYXZ, negateQuaternionX),         # -ZY-X
        48: (swapQuaternionYZX, negateQuaternionXZ),        # -X-YZ
        49: (swapQuaternionZYX, negateQuaternionX),         # -X-ZY
        50: (swapQuaternionXZY, negateQuaternionY),         # -Y-XZ
        51: (swapQuaternionZXY, negateQuaternionYZ),        # -Y-ZX
        52: (negateQuaternionXY,),                          # -Z-XY
        53: (swapQuaternionYXZ, negateQuaternionZ),         # -Z-YX
        56: (swapQuaternionYZX,),                           # -X-Y-Z
        57: (swapQuaternionZYX, negateQuaternionXYZ),       # -X-Z-Y
        58: (swapQuaternionXZY, negateQuaternionXYZ),       # -Y-X-Z
        59: (swapQuaternionZXY,),                           # -Y-Z-X
        60: (),                                             # -Z-X-Y
        61: (swapQuaternionYXZ, negateQuaternionXYZ)        # -Z-Y-X
    }
}


if __name__ == "__main__":
    # from multiprocessing import freeze_support
    # freeze_support()
    # Create an "Application" (initializes the WX system)
    app = wx.PySimpleApp()
    
    # Create a frame for use in our application
    frame = SensorConfigurationWindow(None, SENS_CONF_SIZE)
    
    if "-noukn" in sys.argv:
        global_check_unknown = False
    
    if "-find" in sys.argv:
        frame.onFindDevices(None)
    
    frame.Show()
    frame.update_timer.Start()
    
    # Run the application's loop
    app.MainLoop()
    
    # Close serial ports
    for tss in global_sensor_list.values():
        tss.close()
    for dong in global_dongle_list.values():
        dong.close()
    
    # Destroying the objects
    print "Destroying Frame"
    del frame
    print "Destroying App"
    del app
    print "Destroyed!!!"


