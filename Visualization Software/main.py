#!/usr/bin/env python2.7

"""Creates the Mocap Studio."""

__version__ = "2.0.2.5"

__authors__ = [
]

import os
import sys
import time
_dir_path = os.getcwd()
_file_path = os.path.join(_dir_path, "demos")
_user_path = os.path.join(os.environ['USERPROFILE'], "YEI_3-Space_Mocap_Studio_Data_Files")
_log_name = "YEI_3-Space_Mocap_Studio.log"
_config_name = "YEI_3-Space_Mocap_Studio.conf"
try:
    os.mkdir(_user_path)
except:
    pass

## From http://code.activestate.com/recipes/511491-getting-system-information-under-windows/
import system_specs

if __name__ == '__main__':
    # Setup the log file
    if "-nolog" not in sys.argv:
        try:
            log_path = os.path.join(_user_path, _log_name)
            if os.path.isfile(log_path):
                # Rename latest log file
                log_time = time.gmtime(os.path.getmtime(log_path))
                old_log = time.strftime(_log_name[:-4] + "_%Y.%m.%d_%H.%M.%S" + _log_name[-4:], log_time)
                os.rename(log_path, _user_path + "\\" + old_log)
                
                # Check old files and delete if older than 30 days
                cut_off_date = time.time() - 2592000
                for file in os.listdir(_user_path):
                    if file.endswith(".log"):
                        file_path = os.path.join(_user_path, file)
                        if os.path.getmtime(file_path) < cut_off_date:
                            os.remove(file_path)
            
            # Create new log file
            log_file = open(log_path, 'w')
            sys.stdout = log_file
            sys.stderr = log_file
        except:
            print IOError('Failed to create a log file.')
    try:
        sys_specs = system_specs.SystemInformation()
        print "System specs:"
        print "============================================================"
        print "System OS:", sys_specs.os
        print "System CPU:", sys_specs.cpu
        print "System RAM: %dMB total" % sys_specs.totalRam
        print "System RAM: %dMB free" % sys_specs.availableRam
        print "System HD: %dGB free" % sys_specs.hdFree
        print "============================================================"
    except:
        print "Could not get the system's information."

import wx
import wx.lib.agw.floatspin as float_spin
import wx.lib.colourselect as colour_sel
import wx.lib.filebrowsebutton as file_browse
from wx import glcanvas
from wx import wizard
import math
import csv
import threading
# from multiprocessing import freeze_support

import animator_utils as anim_utils
import import_bvh as im_bvh
import export_bvh as ex_bvh
import import_tsh as im_tsh
import export_tsh as ex_tsh

import gl_scene_graph as gl_sg
from math_lib import *
import base_node_graph as base_ng
import node_graph as ng
import sensor_config as sc
import tsh_to_xml


### Static Globals ###
VERSION = "YEI Mocap Studio %s" % (__version__)

FOV = 45.0
NEAR = 1.0
FAR = 2000.0
MAIN_SIZE = (795, 596)
RIGHT_PANEL_SIZE = (350, 20)
BOTTOM_PANEL_SIZE = (795, 35)

SLERP = 37
SQUAD = 38
EXPORT_CENTIMETERS = 41
EXPORT_INCHES = 42
UNIT_CENTIMETERS = 44
UNIT_INCHES = 45
VIEW_NORMAL = 47
VIEW_LINES = 48
VIEW_POINTS = 49

### Globals ###
global_draw_lock = sc.global_draw_lock
global_draw_logo = True
global_export_interp = True
global_interp_method = SLERP
global_export_unit = EXPORT_CENTIMETERS
global_measure_unit = UNIT_CENTIMETERS
global_bone_view = VIEW_NORMAL
global_calibration_timer = False


### Classes ###
### wxGLCanvas ###
class SceneCanvas(glcanvas.GLCanvas):
    
    """ A wxPython GLCanvas that creates the OpenGL world for OpenGL objects to
        be drawn.
        
        Attributes:
            __init: A boolean that indicates whether or not it has been
                initialized.
            axis_node: An instance of GlAxis.
            cam_node: An instance of SNode.
            cam_zoom_node: An instance of TranslateNode. For zooming in/out the
                camera.
            id_mesh_intercept_table: A dictionary of possible objects to be
                selected based on their ID.
            logo_node: An instance of LogoQuadNode.
            mask: A flag denoting what is to be masked when drawing.
            master_id: An integer denoting what ID is currently available.
            pos_ref_node: An instance of TranslateNode. For translating the
                camera.
            root_node: An instance of GlBackground.
            rotate_mesh: An instance of RotationMeshNode.
            size: A tuple that stores a width and height. (width, height)
            translate_mesh: An instance of TranslationMeshNode.
            x: A float denoting the current x-coordinate of the mouse. Used for
                rotation.
            x_last: A float denoting a previous x-coordinate of the mouse. Used
                for rotation.
            x_ref_node: An instance of RotateNode. For rotating the camera
                around the x-axis.
            x_trans: A float denoting the current x-coordinate of the mouse.
                Used for translation.
            x_trans_last: A float denoting a previous x-coordinate of the mouse.
                Used for translation.
            y: A float denoting the current y-coordinate of the mouse. Used for
                rotation.
            y_last: A float denoting a previous y-coordinate of the mouse. Used
                for rotation.
            y_ref_node: An instance of RotateNode. For rotating the camera
                around the y-axis.
            y_trans: A float denoting the current y-coordinate of the mouse.
                Used for translation.
            y_trans_last: A float denoting a previous y-coordinate of the mouse.
                Used for translation.
    """
    def __init__(self, parent):
        """Initializes the SceneCanvas class.
        
        Args:
            parent: A reference to a wxPython object.
        """
        glcanvas.GLCanvas.__init__(self, parent, -1)
        self.__init = False
        
        # Initial mouse positions
        self.x = 0
        self.x_last = 0
        self.y = 0
        self.y_last = 0
        self.x_trans = 0
        self.x_trans_last = 0
        self.y_trans = 0
        self.y_trans_last = 0
        
        self.size = None
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.onEraseBackground)
        self.Bind(wx.EVT_PAINT, self.onPaint)
        
        # GL Scene Graph
        self.mask = gl_sg.DRAW_RENDER
        self.root_node = gl_sg.GlBackground(mask_val=gl_sg.DRAW_ALL)
        self.cam_zoom_node = self.root_node.appendChild(gl_sg.TranslateNode([0.0, 0.0, -80.0], gl_sg.DRAW_ALL))
        self.x_ref_node = self.cam_zoom_node.appendChild(gl_sg.RotateNode(15.0, [1, 0, 0], gl_sg.DRAW_ALL))
        self.y_ref_node = self.x_ref_node.appendChild(gl_sg.RotateNode(0.0, [0, 1, 0], gl_sg.DRAW_ALL))
        self.pos_ref_node = self.y_ref_node.appendChild(gl_sg.TranslateNode([0.0, 0.0, 0.0], gl_sg.DRAW_ALL))
        self.cam_node = self.pos_ref_node.appendChild(gl_sg.SNode(gl_sg.DRAW_ALL))
        self.cam_node.appendChild(gl_sg.GlPlane())
        
        self.axis_node = self.root_node.appendChild(gl_sg.GlAxis())
        
        # Bone GUI interfaces
        self.translate_mesh = self.pos_ref_node.appendChild(gl_sg.TranslationMeshNode())
        self.rotate_mesh = self.pos_ref_node.appendChild(gl_sg.RotationMeshNode())
        self.sensor_mesh = self.pos_ref_node.appendChild(gl_sg.SensorMeshNode("whole_wireless_case_model_low_poly.obj"))
        self.sensor_mesh.scale = [0.05, 0.05, 0.05]
        
        # Texture logo
        self.logo_node = self.root_node.appendChild(gl_sg.LogoQuadNode(global_draw_logo))
        
        # Bone and GUI IDs
        self.master_id = 11
        self.id_mesh_intercept_table = {
            1: 'scale',
            2: 'x_trans',
            3: 'y_trans',
            4: 'z_trans',
            5: 'x_par_trans',
            6: 'y_par_trans',
            7: 'z_par_trans',
            8: 'x_rot',
            9: 'y_rot',
            10: 'z_rot'
        }
    
    def addMesh(self, obj):
        # Register object with table
        self.id_mesh_intercept_table[self.master_id] = obj
        
        if type(obj) is anim_utils.Bone:
            # Make a new bone mesh
            if '-lines' in sys.argv or global_bone_view == VIEW_LINES:
                new_node = self.cam_node.appendChild(gl_sg.BoneMeshNode(self.master_id, obj.length, draw_method=gl_sg.LINES_DRAW))
            elif '-points' in sys.argv or global_bone_view == VIEW_POINTS:
                new_node = self.cam_node.appendChild(gl_sg.BoneMeshNode(self.master_id, obj.length, draw_method=gl_sg.POINTS_DRAW))
            elif '-bones' in sys.argv:
                f_name = None
                if obj.getName() == "Head":
                    f_name = "Head.obj"
                elif obj.getName() == "Neck":
                    f_name = "Neck.obj"
                elif obj.getName() == "Chest":
                    f_name = "Chest.obj"
                if obj.getName() == "LeftUpArm":
                    f_name = "LUpArm.obj"
                elif obj.getName() == "LeftForeArm":
                    f_name = "LForeArm.obj"
                elif obj.getName() == "LeftHand":
                    f_name = "LHand.obj"
                if obj.getName() == "RightUpArm":
                    f_name = "RUpArm.obj"
                elif obj.getName() == "RightForeArm":
                    f_name = "RForeArm.obj"
                elif obj.getName() == "RightHand":
                    f_name = "RHand.obj"
                try:
                    new_node = self.cam_node.appendChild(gl_sg.BoneMeshNode(self.master_id, obj.length, draw_method=gl_sg.MESH_DRAW, file_name=f_name))
                except:
                    new_node = self.cam_node.appendChild(gl_sg.BoneMeshNode(self.master_id, obj.length))
            else:
                new_node = self.cam_node.appendChild(gl_sg.BoneMeshNode(self.master_id, obj.length))
        elif type(obj) is anim_utils.Skeleton:
            # Make a new skeleton mesh
            new_node = self.cam_node.appendChild(gl_sg.SkeletonMeshNode(self.master_id))
        
        # Finish up
        self.master_id += 1
        
        obj.mesh = new_node
    
    def delMesh(self, mesh_node):
        # Unregister object with table
        del self.id_mesh_intercept_table[mesh_node.id]
        
        # Remove mesh_node from scene graph
        for c in range(len(mesh_node.children) - 1, -1, -1):
            del mesh_node.children[c]
        for c in range(len(self.cam_node.children) - 1, -1, -1):
            if type(self.cam_node.children[c]) is gl_sg.BoneMeshNode:
                if self.cam_node.children[c].id == mesh_node.id:
                    del self.cam_node.children[c]
                    break
            if type(self.cam_node.children[c]) is gl_sg.SkeletonMeshNode:
                if self.cam_node.children[c].id == mesh_node.id:
                    del self.cam_node.children[c]
                    break
    
    def drawGL(self, mask_val=None):
        """Draws the scene in the OpenGL world.
        
        Args:
            mask_val: An integer that denotes what can be drawn to the scene.
        """
        # Clear color and depth buffers
        gl_sg.glClear(gl_sg.GL_COLOR_BUFFER_BIT | gl_sg.GL_DEPTH_BUFFER_BIT)
        
        # Draw Our SceneGraph
        if mask_val is not None:
            self.root_node.draw(mask_val)
        else:
            self.root_node.draw(self.mask)
        
        if self.size is None:
            self.size = self.GetClientSize()
        w, h = self.size
        x_scale = 180.0 / w
        y_scale = 180.0 / h
        
        # Compute tranformation for camera rotation
        # Get Delta mouse positions
        x_delta = (self.x - self.x_last) * x_scale
        y_delta = (self.y - self.y_last) * y_scale
        
        # Update Camera Rotation
        self.x_ref_node.angle += y_delta
        self.y_ref_node.angle += x_delta
        self.axis_node.matrix = self.getCameraMat().toMatrix4().asColArray()
        self.x_last, self.y_last = self.x, self.y
        
        # Update Camera Translation
        x_delta = (self.x_trans - self.x_trans_last) * x_scale / 1.5
        y_delta = (self.y_trans - self.y_trans_last) * -y_scale / 1.5
        pan_vec = Vector3([x_delta, y_delta, 0.0])
        cam_rot = self.getCameraMat()
        pan_vec = -cam_rot * pan_vec
        x_pan, y_pan, z_pan = pan_vec.asArray()
        x_pos, y_pos, z_pos = self.pos_ref_node.vector
        self.pos_ref_node.vector = [x_pos + x_pan, y_pos + y_pan, z_pos + z_pan]
        self.x_trans_last, self.y_trans_last = self.x_trans, self.y_trans
        
        # Push into visible buffer
        self.SwapBuffers()
    
    def getCameraLook(self, camera_mat, camera_pos, bone_pos):
        camera_look = (camera_mat * Vector3([0.0, 0.0, -NEAR])).normalizeCopy()
        camera_bone = bone_pos - camera_pos
        dist_cb = camera_bone.length() * camera_look.dot(camera_bone.normalizeCopy())
        return camera_look * dist_cb
    
    def getCameraMat(self):
        euler = Euler([self.x_ref_node.angle, self.y_ref_node.angle, 0.0], True)
        return euler.toMatrix3('yxz')
    
    def getCameraOffset(self, camera_look, camera_pos, bone_pos):
        camera_offset = (bone_pos - camera_pos).normalizeCopy()
        dist_co = camera_look.length() / camera_offset.dot(camera_look.normalizeCopy())
        return -camera_offset * dist_co
    
    def getCameraPos(self, camera_mat):
        cam_zoom = -Vector3(self.cam_zoom_node.vector)
        cam_pos_ref = Vector3(self.pos_ref_node.vector)
        return (camera_mat * cam_zoom) - cam_pos_ref
    
    def getMouseInWorld(self, mouse_pos, bone_pos=Vector3()):
        # Get the camera's matrix and positional data
        cam_mat = -self.getCameraMat()
        cam_pos = self.getCameraPos(cam_mat)
        
        # Calculate the look of the camera to the bone position and a bone plane
        # normal to the camera
        cam_look = self.getCameraLook(cam_mat, cam_pos, bone_pos)
        plane_norm = (-cam_look).normalizeCopy()
        
        # Calculate the camera's position from the bone
        cam_offset = self.getCameraOffset(cam_look, cam_pos, bone_pos)
        
        # Calculate a ray from the camera to the mouse position
        mouse_ray = self.getMouseRay(cam_mat, mouse_pos)
        
        # Calculate distance to plane
        scale = -plane_norm.dot(cam_offset) / plane_norm.dot(mouse_ray)
        
        project_pos = cam_pos + (mouse_ray * scale)
        
        return project_pos
    
    def getMouseRay(self, camera_mat, mouse_pos):
        cur_x, cur_y = mouse_pos
        width, height = self.size
        
        # Calculate the near clip plane
        cam_tan = math.tan(math.radians(FOV / 2.0))
        near_clip_plane = cam_tan * NEAR
        
        # Calculate the canvas ratio
        ratio = (width * 1.0) / height
        
        # Calculate the mouse's position relative to the center of the camera
        cur_x = (cur_x / (width / 2.0)) - 1
        cur_y = 1 - (cur_y / (height / 2.0))
        
        # Calculate the mouse's x and y on the near clip plane
        x_mouse = cur_x * near_clip_plane * ratio
        y_mouse = cur_y * near_clip_plane
        
        # Calculate a ray from the camera to the plane the bone is on
        mouse_ray = (camera_mat * Vector3([x_mouse, y_mouse, -NEAR]))
        
        # Normalize
        mouse_ray.normalize()
        
        return mouse_ray
    
    def initGL(self):
        """Initializes the OpenGL world."""
        gl_sg.glMatrixMode(gl_sg.GL_PROJECTION)
        # Camera projection setup
        gl_sg.glMaterial(gl_sg.GL_FRONT, gl_sg.GL_AMBIENT, [0.2, 0.2, 0.2, 1])
        gl_sg.glMaterial(gl_sg.GL_FRONT, gl_sg.GL_DIFFUSE, [1, 1, 1, 1])
        gl_sg.glMaterial(gl_sg.GL_FRONT, gl_sg.GL_SPECULAR, [1, 1, 1, 1])
        gl_sg.glMaterial(gl_sg.GL_FRONT, gl_sg.GL_SHININESS, 50.0)
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
        aspect = (self.size.width * 1.0) / self.size.height
        gl_sg.gluPerspective(FOV, aspect, NEAR, FAR)
        gl_sg.glClear(gl_sg.GL_COLOR_BUFFER_BIT | gl_sg.GL_DEPTH_BUFFER_BIT)
        gl_sg.glMatrixMode(gl_sg.GL_MODELVIEW)
        
        # Initialize glut
        gl_sg.glutInit(sys.argv)
        
        # Check for the version
        gl_sg.getGLVersion()
        
        # Load textures
        self.logo_node.loadTexture(os.path.join(_dir_path, "media\\YEI_Logo.png"))
    
    def onEraseBackground(self, event=None):
        """Does nothing, but help to avoid flashing on MSW.
        
        Args:
            event: A wxPython event.
        """
        pass
    
    def onSize(self, event=None):
        """ Adjusts the canvas when resizing the window.
            
            Args:
                event: A wxPython event.
        """
        width, height = self.size = self.GetClientSize()
        if self.GetContext() and self.GetParent().IsShown():
            self.logo_node.gl_height = height
            self.logo_node.gl_width = width
            global_draw_lock.acquire()
            self.SetCurrent()
            gl_sg.glViewport(0, 0, width, height)
            gl_sg.glMatrixMode(gl_sg.GL_PROJECTION)
            gl_sg.glLoadIdentity()
            aspect = (width * 1.0) / height
            gl_sg.gluPerspective(FOV, aspect, NEAR, FAR)
            gl_sg.glMatrixMode(gl_sg.GL_MODELVIEW)
            global_draw_lock.release()
        self.Refresh()
    
    def onPaint(self, event=None):
        """Renders the scene to the screen.
        
        Args:
            event: A wxPython event.
        """
        global_draw_lock.acquire()
        dc = wx.PaintDC(self)
        self.SetCurrent()
        if not self.__init:
            self.initGL()
            self.__init = True
        self.drawGL()
        global_draw_lock.release()
    
    def resetMeshSettings(self):
        for k in self.id_mesh_intercept_table.keys():
            if k > 10:
                del self.id_mesh_intercept_table[k]
        self.master_id = 11
        self.cam_node.children = self.cam_node.children[:1]
    
    def selectGL(self, x, y):
        """Finds what OpenGL objects are trying to be selected by the user.
        
        Args:
            x: A float denoting the current x-coordinate of the mouse.
            y: A float denoting the current y-coordinate of the mouse.
        
        Returns:
            A list of objects that have been detected as selected.
        """
        self.SetCurrent()
        trans_gui = False
        rot_gui = False
        if self.mask & gl_sg.DRAW_GUI_TRANS:
            trans_gui = True
        if self.mask & gl_sg.DRAW_GUI_ROT:
            rot_gui = True
        
        hits = []
        done = False
        view = gl_sg.glGetIntegerv(gl_sg.GL_VIEWPORT)
        while len(hits) < 2 and not done:
            buff = None
            gl_sg.glSelectBuffer(64, buff)
            gl_sg.glRenderMode(gl_sg.GL_SELECT)
            gl_sg.glInitNames()
            gl_sg.glPushName(0)
            gl_sg.glMatrixMode(gl_sg.GL_PROJECTION)
            gl_sg.glPushMatrix()
            
            gl_sg.glLoadIdentity()
            gl_sg.gluPickMatrix(x, view[3] - y, 1.0, 1.0, view)
            aspect = (view[2] * 1.0) / view[3]
            gl_sg.gluPerspective(FOV, aspect, NEAR, FAR)
            gl_sg.glMatrixMode(gl_sg.GL_MODELVIEW)
            if trans_gui:
                self.drawGL(gl_sg.DRAW_TRANS_CLICK)
                trans_gui = False
            elif rot_gui:
                self.drawGL(gl_sg.DRAW_ROT_CLICK)
                rot_gui = False
            else:
                self.drawGL(gl_sg.DRAW_BONE_CLICK)
                done = True
            gl_sg.glMatrixMode(gl_sg.GL_PROJECTION)
            gl_sg.glPopMatrix()
            
            gl_sg.glFlush()
            hits = gl_sg.glRenderMode(gl_sg.GL_RENDER)
            gl_sg.glMatrixMode(gl_sg.GL_MODELVIEW)
        
        hit_list = {}
        return_list = []
        for h in hits:
            idx = int(h.names[0])
            if idx in self.id_mesh_intercept_table:
                hit_list[h.near] = self.id_mesh_intercept_table[idx]
        tmp_list = hit_list.keys()
        tmp_list.sort()
        for k in tmp_list:
            return_list.append(hit_list[k])
        return return_list
    
    def setCameraOrientPos(self, x_angle, y_angle, ref_vec, zoom_vec):
        self.x_ref_node.angle = x_angle
        self.y_ref_node.angle = y_angle
        self.pos_ref_node.vector = ref_vec
        self.cam_zoom_node.vector = zoom_vec
        
        matrix = Euler([x_angle, y_angle, 0.0], True).toMatrix4('yxz')
        self.axis_node.matrix = matrix.asColArray()
    
    def setBinds(self, win):
        # Self Binds
        self.Bind(wx.EVT_SIZE, self.onSize)
        self.Bind(wx.EVT_LEFT_DOWN, win.onGLLeftClick)
        self.Bind(wx.EVT_RIGHT_DOWN, win.onGLRightClick)
        self.Bind(wx.EVT_MIDDLE_DOWN, win.onGLMiddleClick)
        self.Bind(wx.EVT_MOTION, win.onGLMouseMotion)
        self.Bind(wx.EVT_MOUSEWHEEL, win.onGLScroll)
        self.Bind(wx.EVT_KEY_DOWN, win.onKeyPress)
        self.Bind(wx.EVT_KEY_UP, win.onKeyPress)
    
    def setSensorMeshOrientPos(self, bone):
        cam_mat = -self.getCameraMat()
        tmp_vec = (cam_mat * Vector3([0.0, 0.0, NEAR])).normalizeCopy()
        
        self.sensor_mesh.position = (bone.getPosition() + tmp_vec).asArray()
        self.sensor_mesh.orient = bone.vs_node.getSensorOrientDir().asColArray()


### wxPanel ### (ID's 116-155)
class PosePanel(wx.Panel):
    
    """A wxPython Panel object.
    
    Attributes:
        _is_enabled: A boolean that denotes whether or not the panel is enabled.
        _text_ids: A list of all the IDs of wx.StaticText objects the panel has.
        calibrate_button: A wx.Button that calibrates the sensors to the bones'
            pose orientation.
        name_text: An instance of wx.TextCtrl with the name of a selected Bone
            object.
        orient_choice_box: A wx.Choice instance that has a list of possible
            orientations.
        output_choice_box: A wx.Choice instance that has a list of
            VirtualSensorNode objects' names.
        parent_choice_box: A wx.Choice instance that has a list of Bone objects'
            names.
        set_bone_length: A wx.FloatSpin instance used for denoting the length of
            a selected Bone object
        w_face_name = A string denoting the default typeface name.
        w_point_size = An integer denoting the default point size.
        w_set_rot: A wx.FloatSpin instance used for denoting the w-value or
            angle-value in an orientation.
        x_set_pos: A wx.FloatSpin instance used for denoting the x-value in
            a vector.
        x_set_rot: A wx.FloatSpin instance used for denoting the x-value or
            x-axis in an orientation.
        x_set_sensor_rot: A wx.FloatSpin instance used for denoting the x-value
            of the orientation of the SensorMeshNode object.
        y_set_pos: A wx.FloatSpin instance used for denoting the y-value in
            a vector.
        y_set_rot: A wx.FloatSpin instance used for denoting the y-value or
            y-axis in an orientation.
        y_set_sensor_rot: A wx.FloatSpin instance used for denoting the y-value
            of the orientation of the SensorMeshNode object.
        z_set_pos: A wx.FloatSpin instance used for denoting the z-value in
            a vector.
        z_set_rot: A wx.FloatSpin instance used for denoting the z-value or
            z-axis in an orientation.
        z_set_sensor_rot: A wx.FloatSpin instance used for denoting the z-value
            of the orientation of the SensorMeshNode object.
    """
    def __init__(self, parent):
        """Initializes the PosePanel class.
        
        Args:
            parent: A reference to another wxPython object.
        """
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)
        
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.SetSizer(box_sizer)
        
        self._is_enabled = True
        self._is_skel_enabled = False
        
        # ID's for StaticText
        self._text_ids = range(131, 149)
        id0, id1, id2, id3, id4, id5, id6, id7, id8, id9, id10, id11, id12, id13, id14, id15, id16, id17 = self._text_ids
        
        # Node Graph Dropbox
        node_grid = wx.GridSizer(1, 2, 0, -165) # rows, cols, vGap, hGap
        self.output_choice_box = wx.Choice(self, 116, size=(150, 18), choices=["None"])
        self.output_choice_box.SetSelection(0)
        node_grid.AddMany([(wx.StaticText(self, id4, "Output Node:"), 0,
                            wx.ALIGN_CENTER_VERTICAL), (self.output_choice_box, 0)])
        
        # Sensor Pose Orientation
        sensor_grid = wx.GridSizer(2, 1)
        
        sensor_text_grid = wx.BoxSizer(wx.HORIZONTAL)
        self.sensor_orient_check = wx.CheckBox(self, wx.NewId())
        
        sensor_text_grid.Add(self.sensor_orient_check, 0)
        sensor_text_grid.AddSpacer((10, 0))
        sensor_text_grid.Add(wx.StaticText(self, id0, "Sensor Pose Orientation:"), 0)
        
        sensor_vals_grid = wx.GridSizer(1, 3, 0, 6)
        x_vals_grid = wx.GridSizer(1, 2, 0, -54)
        y_vals_grid = wx.GridSizer(1, 2, 0, -54)
        z_vals_grid = wx.GridSizer(1, 2, 0, -54)
        self.x_set_sensor_rot = float_spin.FloatSpin(self, 117, size=(65, -1), digits=3)
        self.y_set_sensor_rot = float_spin.FloatSpin(self, 118, size=(65, -1), digits=3)
        self.z_set_sensor_rot = float_spin.FloatSpin(self, 119, size=(65, -1), digits=3)
        
        x_vals_grid.AddMany([   (wx.StaticText(self, id1, "X"), 0, wx.ALIGN_CENTER_VERTICAL),
                                (self.x_set_sensor_rot, 0)])
        y_vals_grid.AddMany([   (wx.StaticText(self, id2, "Y"), 0, wx.ALIGN_CENTER_VERTICAL),
                                (self.y_set_sensor_rot, 0)])
        z_vals_grid.AddMany([   (wx.StaticText(self, id3, "Z"), 0, wx.ALIGN_CENTER_VERTICAL),
                                (self.z_set_sensor_rot, 0)])
        
        sensor_vals_grid.AddMany([(x_vals_grid, 0), (y_vals_grid, 0), (z_vals_grid, 0)])
        
        sensor_grid.AddMany([(sensor_text_grid, 0), (sensor_vals_grid, 0)])
        
        # Name Box
        name_grid = wx.GridSizer(1, 2, 0, -245)
        self.name_text = wx.TextCtrl(self, 120, "Name", size=(150, 18))
        name_grid.AddMany([ (wx.StaticText(self, id5, "Name:"), 0, wx.ALIGN_CENTER_VERTICAL),
                            (self.name_text, 0)])
        
        # Parent Node Dropbox
        parent_grid = wx.GridSizer(1, 2, 0, -180)
        self.parent_choice_box = wx.Choice(self, 121, size=(150, 18), choices=["None"])
        self.parent_choice_box.SetSelection(0)
        parent_grid.AddMany([   (wx.StaticText(self, id6, "Parent Bone:"), 0, wx.ALIGN_CENTER_VERTICAL),
                                (self.parent_choice_box, 0)])
        
        # Bone Length
        length_grid = wx.GridSizer(1, 2, 0, -185)
        self.set_bone_length = float_spin.FloatSpin(self, 122, size=(65, -1), min_val=0.1, increment=0.1, digits=2)
        length_grid.AddMany([   (wx.StaticText(self, id7, "Bone Length:"), 0, wx.ALIGN_CENTER_VERTICAL),
                                (self.set_bone_length, 0)])
        
        # Pose Orientation
        pose_grid = wx.GridSizer(3, 1, 10)
        pose_choice_grid = wx.GridSizer(1, 2, 0, 6)
        self.orient_choice_box = wx.Choice(self, 123, size=(90, 18), choices=[  "Euler XYZ",
                                                                                "Euler XZY",
                                                                                "Euler YXZ",
                                                                                "Euler YZX",
                                                                                "Euler ZXY",
                                                                                "Euler ZYX",
                                                                                "Quaternion",
                                                                                "Axis Angle"])
        self.orient_choice_box.SetSelection(0)
        
        pose_choice_grid.AddMany([  (wx.StaticText(self, id8, "Pose Orientation:"), 0, wx.ALIGN_CENTER_VERTICAL),
                                    (self.orient_choice_box, 0)])
        
        pose_vals_grid = wx.GridSizer(1, 4, 0, 6)
        x_vals_grid = wx.GridSizer(1, 2, 0, -54)
        y_vals_grid = wx.GridSizer(1, 2, 0, -54)
        z_vals_grid = wx.GridSizer(1, 2, 0, -54)
        w_vals_grid = wx.GridSizer(1, 2, 0, -54)
        
        self.x_set_rot = float_spin.FloatSpin(self, 124, size=(65, -1), digits=3)
        self.y_set_rot = float_spin.FloatSpin(self, 125, size=(65, -1), digits=3)
        self.z_set_rot = float_spin.FloatSpin(self, 126, size=(65, -1), digits=3)
        self.w_set_rot = float_spin.FloatSpin(self, 127, size=(65, -1), digits=3)
        self.w_set_rot.Disable()
        
        x_vals_grid.AddMany([   (wx.StaticText(self, id9, "X"), 0, wx.ALIGN_CENTER_VERTICAL),
                                (self.x_set_rot, 0)])
        y_vals_grid.AddMany([   (wx.StaticText(self, id10, "Y"), 0, wx.ALIGN_CENTER_VERTICAL),
                                (self.y_set_rot, 0)])
        z_vals_grid.AddMany([   (wx.StaticText(self, id11, "Z"), 0, wx.ALIGN_CENTER_VERTICAL),
                                (self.z_set_rot, 0)])
        w_vals_grid.AddMany([   (wx.StaticText(self, id12, "W"), 0, wx.ALIGN_CENTER_VERTICAL),
                                (self.w_set_rot, 0)])
        
        w_text = self.FindWindowById(id12)
        w_text.Show(False)
        font = w_text.GetFont()
        self.w_face_name = font.GetFaceName()
        self.w_point_size = font.GetPointSize()
        self.w_set_rot.Show(False)
        
        pose_vals_grid.AddMany([(x_vals_grid, 0), (y_vals_grid, 0), (z_vals_grid, 0), (w_vals_grid, 0)])
        
        pose_grid.AddMany([(pose_choice_grid, 0), (pose_vals_grid, 0)])
        
        # Offset
        offset_grid = wx.GridSizer(2, 1)
        
        offset_vals_grid = wx.GridSizer(1, 3, 0, 6)
        x_vals_grid = wx.GridSizer(1, 2, 0, -54)
        y_vals_grid = wx.GridSizer(1, 2, 0, -54)
        z_vals_grid = wx.GridSizer(1, 2, 0, -54)
        self.x_set_pos = float_spin.FloatSpin(self, 128, size=(65, -1), increment=0.1, digits=2)
        self.y_set_pos = float_spin.FloatSpin(self, 129, size=(65, -1), increment=0.1, digits=2)
        self.z_set_pos = float_spin.FloatSpin(self, 130, size=(65, -1), increment=0.1, digits=2)
        
        x_vals_grid.AddMany([   (wx.StaticText(self, id13, "X"), 0, wx.ALIGN_CENTER_VERTICAL),
                                (self.x_set_pos, 0)])
        y_vals_grid.AddMany([   (wx.StaticText(self, id14, "Y"), 0, wx.ALIGN_CENTER_VERTICAL),
                                (self.y_set_pos, 0)])
        z_vals_grid.AddMany([   (wx.StaticText(self, id15, "Z"), 0, wx.ALIGN_CENTER_VERTICAL),
                                (self.z_set_pos, 0)])
        
        offset_vals_grid.AddMany([(x_vals_grid, 0), (y_vals_grid, 0), (z_vals_grid, 0)])
        
        offset_grid.AddMany([(wx.StaticText(self, id16, "Offset:"), 0), (offset_vals_grid, 0)])
        
        # Calibrate Bone
        self.calibrate_button = wx.Button(self, 131, "Calibrate Sensors", size=(120, -1), style=wx.WANTS_CHARS)
        
        # Add stuff to sizer
        box_sizer.AddSpacer((0, 5))
        box_sizer.AddMany([(node_grid, 0, wx.EXPAND | wx.ALL, 5), (sensor_grid, 0, wx.EXPAND | wx.ALL, 5)])
        box_sizer.Add(wx.StaticLine(self, id17), 0, wx.EXPAND | wx.ALL, 5)
        box_sizer.AddMany([
            (name_grid, 0, wx.EXPAND | wx.ALL, 5),
            (parent_grid, 0, wx.EXPAND | wx.ALL, 5),
            (length_grid, 0, wx.EXPAND | wx.ALL, 5),
            (pose_grid, 0, wx.EXPAND | wx.ALL, 5),
            (offset_grid, 0, wx.EXPAND | wx.ALL, 5)
        ])
        box_sizer.AddSpacer((0, 10))
        box_sizer.Add(self.calibrate_button, 0, wx.ALIGN_CENTER)
        box_sizer.AddSpacer((0, 10))
    
    def disableBoneProperties(self):
        if not self._is_skel_enabled:
            # StaticText Disable
            for id in range(4, 18):
                text_id = self._text_ids[id]
                if id == 5 or (id > 7 and id < 17):
                    if id == 16:
                        self.FindWindowById(text_id).SetLabel('Position:')
                    continue
                self.FindWindowById(text_id).Disable()
            
            # CheckBox Disable
            self.sensor_orient_check.Disable()
            
            # SpinCtrl Disable
            self.x_set_sensor_rot.Disable()
            self.y_set_sensor_rot.Disable()
            self.z_set_sensor_rot.Disable()
            
            self.set_bone_length.Disable()
            
            # Choice Disable
            self.parent_choice_box.Disable()
            
            self.output_choice_box.Disable()
            
            self._is_skel_enabled = True
    
    def disableInput(self):
        if self._is_enabled:
            self._is_enabled = False
            # StaticText Disable
            for id in self._text_ids:
                self.FindWindowById(id).Disable()
            
            # CheckBox Disable
            self.sensor_orient_check.Disable()
            
            # SpinCtrl Disable
            self.x_set_sensor_rot.Disable()
            self.y_set_sensor_rot.Disable()
            self.z_set_sensor_rot.Disable()
            
            self.set_bone_length.Disable()
            
            self.x_set_rot.Disable()
            self.y_set_rot.Disable()
            self.z_set_rot.Disable()
            self.w_set_rot.Disable()
            
            self.x_set_pos.Disable()
            self.y_set_pos.Disable()
            self.z_set_pos.Disable()
            
            # TextCtrl Disable
            self.name_text.Disable()
            
            # Choice Disable
            self.parent_choice_box.Disable()
            
            self.output_choice_box.Disable()
            
            self.orient_choice_box.Disable()
    
    def disableSensorCheck(self):
        self.sensor_orient_check.Disable()
        self.onCheck(None)
    
    def enableBoneProperties(self):
        if self._is_skel_enabled:
            # StaticText Enable
            for id in range(4, 18):
                text_id = self._text_ids[id]
                if id == 5 or (id > 7 and id < 17):
                    if id == 16:
                        self.FindWindowById(text_id).SetLabel('Offest:')
                    continue
                self.FindWindowById(text_id).Enable()
            
            # CheckBox Enable
            self.sensor_orient_check.Enable()
            
            # SpinCtrl Enable
            self.x_set_sensor_rot.Enable()
            self.y_set_sensor_rot.Enable()
            self.z_set_sensor_rot.Enable()
            
            self.set_bone_length.Enable()
            
            # Choice Enable
            self.parent_choice_box.Enable()
            
            self.output_choice_box.Enable()
            
            self._is_skel_enabled = False
    
    def enableInput(self):
        if not self._is_enabled:
            self._is_enabled = True
            # StaticText Enable
            for id in self._text_ids[4:]:
                self.FindWindowById(id).Enable()
            
            # SpinCtrl Enable
            self.set_bone_length.Enable()
            
            self.x_set_rot.Enable()
            self.y_set_rot.Enable()
            self.z_set_rot.Enable()
            self.w_set_rot.Enable()
            
            self.x_set_pos.Enable()
            self.y_set_pos.Enable()
            self.z_set_pos.Enable()
            
            # TextCtrl Enable
            self.name_text.Enable()
            
            # Choice Enable
            self.parent_choice_box.Enable()
            
            self.output_choice_box.Enable()
            
            self.orient_choice_box.Enable()
            
            # CheckBox Enable
            if self.output_choice_box.GetSelection() != 0:
                self.enableSensorCheck()
    
    def enableSensorCheck(self):
        self.sensor_orient_check.Enable()
        self.onCheck(self.sensor_orient_check)
    
    def onCheck(self, event=None):
        id0, id1, id2, id3 = self._text_ids[:4]
        if event is None or not event.IsChecked():
            self.FindWindowById(id0).Disable()
            self.FindWindowById(id1).Disable()
            self.FindWindowById(id2).Disable()
            self.FindWindowById(id3).Disable()
            self.x_set_sensor_rot.Disable()
            self.y_set_sensor_rot.Disable()
            self.z_set_sensor_rot.Disable()
        else:
            self.FindWindowById(id0).Enable()
            self.FindWindowById(id1).Enable()
            self.FindWindowById(id2).Enable()
            self.FindWindowById(id3).Enable()
            self.x_set_sensor_rot.Enable()
            self.y_set_sensor_rot.Enable()
            self.z_set_sensor_rot.Enable()
    
    def reset(self):
        # SpinCtrl Resets
        self.x_set_sensor_rot.SetToDefaultValue()
        self.y_set_sensor_rot.SetToDefaultValue()
        self.z_set_sensor_rot.SetToDefaultValue()
        
        self.set_bone_length.SetToDefaultValue()
        
        self.x_set_rot.SetToDefaultValue()
        self.y_set_rot.SetToDefaultValue()
        self.z_set_rot.SetToDefaultValue()
        self.w_set_rot.SetToDefaultValue()
        
        self.x_set_pos.SetToDefaultValue()
        self.y_set_pos.SetToDefaultValue()
        self.z_set_pos.SetToDefaultValue()
        
        # Text Resets
        self.name_text.SetValue("Name")
        
        # CheckBox Resets
        self.sensor_orient_check.SetValue(False)
        
        # Choice Resets
        self.output_choice_box.SetSelection(0)
        
        self.parent_choice_box.SetSelection(0)
    
    def setBinds(self, win):
        """Sets the binds for the PosePanel class and its attributes.
        
        Args:
            win: A reference to the main window, a wxPython object.
        """
        # Self Binds
        self.Bind(wx.EVT_KEY_DOWN, win.onKeyPress)
        self.Bind(wx.EVT_KEY_UP, win.onKeyPress)
        
        # CheckBox Binds
        self.sensor_orient_check.Bind(wx.EVT_CHECKBOX, self.onCheck)
        self.sensor_orient_check.Bind(wx.EVT_CHECKBOX, win.onSenorCheck)
        
        # SpinCtrl Binds
        self.x_set_sensor_rot.Bind(wx.EVT_SPINCTRL, win.onSensorPose)
        self.y_set_sensor_rot.Bind(wx.EVT_SPINCTRL, win.onSensorPose)
        self.z_set_sensor_rot.Bind(wx.EVT_SPINCTRL, win.onSensorPose)
        
        self.set_bone_length.Bind(wx.EVT_SPINCTRL, win.onBonelength)
        
        self.x_set_rot.Bind(wx.EVT_SPINCTRL, win.onPoseOrient)
        self.y_set_rot.Bind(wx.EVT_SPINCTRL, win.onPoseOrient)
        self.z_set_rot.Bind(wx.EVT_SPINCTRL, win.onPoseOrient)
        self.w_set_rot.Bind(wx.EVT_SPINCTRL, win.onPoseOrient)
        
        self.x_set_pos.Bind(wx.EVT_SPINCTRL, win.onOffset)
        self.y_set_pos.Bind(wx.EVT_SPINCTRL, win.onOffset)
        self.z_set_pos.Bind(wx.EVT_SPINCTRL, win.onOffset)
        
        # Text Binds
        self.name_text.Bind(wx.EVT_KILL_FOCUS, win.onNameChange)
        
        # Choice Binds
        self.parent_choice_box.Bind(wx.EVT_CHOICE, win.onParentChoice)
        
        self.output_choice_box.Bind(wx.EVT_CHOICE, win.onOutputChoice)
        
        self.orient_choice_box.Bind(wx.EVT_CHOICE, win.onOrientChoice)
        
        # Button Binds
        self.calibrate_button.Bind(wx.EVT_BUTTON, win.onCalibrate)
        
        # Key Input Binds
        self.output_choice_box.Bind(wx.EVT_KEY_DOWN, win.onKeyPress)
        self.output_choice_box.Bind(wx.EVT_KEY_UP, win.onKeyPress)
        
        self.sensor_orient_check.Bind(wx.EVT_KEY_DOWN, win.onKeyPress)
        self.sensor_orient_check.Bind(wx.EVT_KEY_UP, win.onKeyPress)
        
        self.parent_choice_box.Bind(wx.EVT_KEY_DOWN, win.onKeyPress)
        self.parent_choice_box.Bind(wx.EVT_KEY_UP, win.onKeyPress)
        
        self.orient_choice_box.Bind(wx.EVT_KEY_DOWN, win.onKeyPress)
        self.orient_choice_box.Bind(wx.EVT_KEY_UP, win.onKeyPress)
        
        self.calibrate_button.Bind(wx.EVT_KEY_DOWN, win.onKeyPress)
        self.calibrate_button.Bind(wx.EVT_KEY_UP, win.onKeyPress)
        
        # Mouse Input Binds
        self.output_choice_box.Bind(wx.EVT_MOUSEWHEEL, win.onGLScroll)
        
        self.x_set_sensor_rot.Bind(wx.EVT_MOUSEWHEEL, win.onGLScroll)
        self.y_set_sensor_rot.Bind(wx.EVT_MOUSEWHEEL, win.onGLScroll)
        self.z_set_sensor_rot.Bind(wx.EVT_MOUSEWHEEL, win.onGLScroll)
        
        self.parent_choice_box.Bind(wx.EVT_MOUSEWHEEL, win.onGLScroll)
        
        self.orient_choice_box.Bind(wx.EVT_MOUSEWHEEL, win.onGLScroll)
        
        self.set_bone_length.Bind(wx.EVT_MOUSEWHEEL, win.onGLScroll)
        
        self.x_set_rot.Bind(wx.EVT_MOUSEWHEEL, win.onGLScroll)
        self.y_set_rot.Bind(wx.EVT_MOUSEWHEEL, win.onGLScroll)
        self.z_set_rot.Bind(wx.EVT_MOUSEWHEEL, win.onGLScroll)
        self.w_set_rot.Bind(wx.EVT_MOUSEWHEEL, win.onGLScroll)
        
        self.x_set_pos.Bind(wx.EVT_MOUSEWHEEL, win.onGLScroll)
        self.y_set_pos.Bind(wx.EVT_MOUSEWHEEL, win.onGLScroll)
        self.z_set_pos.Bind(wx.EVT_MOUSEWHEEL, win.onGLScroll)
    
    def setBoneProperties(self, win):
        # Get bone
        bone = win.selected_obj
        
        # Set ambient color
        bone.setAmbientColor(anim_utils.BONE_SELECT)
        
        # Enable properties
        self.enableBoneProperties()
        self.enableInput()
        
        # Remove name from parent_choice_box
        bone_name = bone.getName()
        name_idx = self.parent_choice_box.FindString(bone_name)
        self.parent_choice_box.Delete(name_idx)
        
        # Check bone's virtual sensor node
        node = bone.vs_node
        if node is not None and self.output_choice_box.SetStringSelection(node.name):
            pass
        else:
            self.output_choice_box.SetSelection(0)
            # Set sensor's pose orientation property
            self.x_set_sensor_rot.SetToDefaultValue()
            self.y_set_sensor_rot.SetToDefaultValue()
            self.z_set_sensor_rot.SetToDefaultValue()
        win.onOutputChoice()
        
        # Set name property
        self.name_text.SetValue(bone_name)
        
        # Set parent property
        par_bone = bone.parent
        par_is_bone = type(par_bone) is anim_utils.Bone
        if par_is_bone:
            par_bone_name = par_bone.getName()
            if not self.parent_choice_box.SetStringSelection(par_bone_name):
                self.parent_choice_box.SetSelection(0)
        else:
            self.parent_choice_box.SetSelection(0)
        
        # Set length property
        length = bone.getLength()
        if global_measure_unit == UNIT_CENTIMETERS:
            length *= 2.54
        self.set_bone_length.SetValue(length)
        
        # Set pose orientation property
        win.onOrientChoice()
        
        # Set offset property
        offset = bone.getOffset()
        if global_measure_unit == UNIT_CENTIMETERS:
            offset *= 2.54
        x_pos, y_pos, z_pos = offset.asArray()
        self.x_set_pos.SetValue(x_pos)
        self.y_set_pos.SetValue(y_pos)
        self.z_set_pos.SetValue(z_pos)
        
        # Set GUI meshes to the bone's position
        bone_pos_array = bone.getPosition().asArray()
        bone_pose_array = bone.getPoseOrientation().asColArray()
        
        win.gl_canvas.translate_mesh.position = bone_pos_array
        win.gl_canvas.translate_mesh.orientation = bone_pose_array
        
        if par_is_bone:
            win.gl_canvas.translate_mesh.parent_orient = \
                par_bone.getPoseOrientation().asColArray()
        else:
            win.gl_canvas.translate_mesh.parent_orient = Matrix4().asColArray()
        
        win.gl_canvas.rotate_mesh.position = bone_pos_array
        win.gl_canvas.rotate_mesh.orientation = bone_pose_array
        
        # Set sensor mesh position and orientation
        if self.sensor_orient_check.IsChecked():
            win.gl_canvas.setSensorMeshOrientPos(bone)
        
        if win.recorded_session is None:
            if win.is_translate_mode:
                win.gl_canvas.translate_mesh.setBools(win.manipulate_bone)
            elif win.is_rotate_mode:
                win.gl_canvas.rotate_mesh.setBools(win.manipulate_bone)
        else:
            self.disableInput()
    
    def setSkeletonProperties(self, win):
        # Get skeleton
        skel = win.selected_obj
        
        # Set ambient color
        skel.setAmbientColor(anim_utils.BONE_SELECT)
        
        # Reset properties
        self.reset()
        win.onSenorCheck(self.sensor_orient_check)
        self.disableSensorCheck()
        
        # Set name property
        self.name_text.SetValue(skel.getName())
        
        # Set pose orientation property
        win.onOrientChoice()
        
        # Set offset property
        pos = skel.getPosition()
        if global_measure_unit == UNIT_CENTIMETERS:
            pos *= 2.54
        x_pos, y_pos, z_pos = pos.asArray()
        self.x_set_pos.SetValue(x_pos)
        self.y_set_pos.SetValue(y_pos)
        self.z_set_pos.SetValue(z_pos)
        
        if win.recorded_session is None:
            self.enableInput()
            self.disableBoneProperties()
        else:
            self.disableInput()


### wxPanel ### (ID's 156-175)
class LivePanel(wx.Panel):
    
    """A wxPython Panel object.
    
    Attributes:
        _text_ids: A list of all the IDs of wx.StaticText objects the panel has.
        stream_button: A wx.Button instance that starts/stops streaming of data.
        deselect_button: A wx.Button instance that deselects everything in
            device_list.
        failed_list: A list of TSSensor objects that failed to start streaming.
        play_button: A wx.Button instance that starts/stops a playback of a
            recorded session.
        playback_rate: A wx.FloatSpin instance used for denoting the value at
            which speed to play a recorded session.
        record_button: A wx.Button instance that starts/stops recording data.
        record_rate: A wx.FloatSpin instance used for denoting the value of the
            rate at which to record data.
        select_button: A wx.Button instance that selects everything in
            device_list.
        device_list: A wx.CheckListBox instance that holds a list of names of
            active input devices.
        interval: A wx.FloatSpin instance used for denoting a interval value for
            streaming data.
    """
    def __init__(self, parent):
        """Initializes the LivePanel class.
        
        Args:
            parent: A reference to another wxPython object.
        """
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)
        
        w, h = RIGHT_PANEL_SIZE
        
        # ID's for StaticText
        self._text_ids = range(163, 168)
        id0, id1, id2, id3, id4 = self._text_ids
        
        # Play
        wx.StaticText(self, id0, "Playback Rate:", (5, 30))
        self.playback_rate = float_spin.FloatSpin(self, 156, (87, 27),(60, -1), value=1.0, min_val=0.1, increment=0.1, digits=2)
        
        self.play_button = wx.Button(self, 157, "Play", (32, 52), (100, -1), style=wx.WANTS_CHARS)
        
        self.do_interpolation = wx.CheckBox(self, 158, "Interpolate Data", (15, 78))
        self.do_interpolation.SetValue(True)
        
        # Record
        wx.StaticText(self, id1, "Capture Rate:", ((w / 2) - 5, 30))
        self.record_rate = float_spin.FloatSpin(self, 159, ((w / 2) + 75, 27), (60, -1), value=0.0, min_val=0.0, increment=0.1, digits=2)
        wx.StaticText(self, id2, "fps", ((w / 2) + 137, 30))
        
        self.record_button = wx.Button(self, 160, "Record", ((w / 2) + 34, 52), (100, -1), style=wx.WANTS_CHARS)
        
        # Streaming
        wx.StaticText(self, id3, "Wait:", ((w / 2) - 86, 117))
        self.interval = wx.SpinCtrl(self, 161, '', ((w / 2) - 51, 114), (60, -1), wx.SP_WRAP, 0, 1000000, 0)
        wx.StaticText(self, id4, "microseconds", ((w / 2) + 11, 117))
        
        self.stream_button = wx.Button(self, 162, "Start Streaming", ((w / 2) - 70, 142), style=wx.WANTS_CHARS)
        
        self.device_list = wx.CheckListBox(self, 168, ((w / 2) - 130, 180), (150, 190))
        self.select_button = wx.Button(self, 169, "Select All", ((w / 2) + 25, 185), style=wx.WANTS_CHARS)
        self.deselect_button = wx.Button(self, 170, "Deselect All", ((w / 2) + 25, 215), style=wx.WANTS_CHARS)
        
        self.failed_list = []
    
    def disableStream(self):
        # StaticText Disable
        for id in self._text_ids[3:]:
            self.FindWindowById(id).Disable()
        
        self.interval.Disable()
        self.stream_button.Disable()
    
    def disablePlay(self):
        self.FindWindowById(self._text_ids[0]).Disable()
        
        self.playback_rate.Disable()
        self.play_button.Disable()
        self.do_interpolation.Disable()
    
    def disableRecord(self):
        # StaticText Disable
        for id in self._text_ids[1:3]:
            self.FindWindowById(id).Disable()
        
        self.record_rate.Disable()
        self.record_button.Disable()
    
    def disableSelect(self):
        self.device_list.Disable()
        self.select_button.Disable()
        self.deselect_button.Disable()
    
    def enableStream(self):
        # StaticText Enable
        for id in self._text_ids[3:]:
            self.FindWindowById(id).Enable()
        
        self.interval.Enable()
        self.stream_button.Enable()
    
    def enablePlay(self):
        self.FindWindowById(self._text_ids[0]).Enable()
        
        self.playback_rate.Enable()
        self.play_button.Enable()
        self.do_interpolation.Enable()
    
    def enableRecord(self):
        # StaticText Enable
        for id in self._text_ids[1:3]:
            self.FindWindowById(id).Enable()
        
        self.record_rate.Enable()
        self.record_button.Enable()
    
    def enableSelect(self):
        self.device_list.Enable()
        self.select_button.Enable()
        self.deselect_button.Enable()
        self.resetSelect()
    
    def onDeselectAll(self, event=None):
        for i in range(self.device_list.GetCount()):
            self.device_list.Check(i, False)
    
    def onSelectAll(self, event=None):
        for i in range(self.device_list.GetCount()):
            self.device_list.Check(i)
    
    def playDisable(self):
        """Disables everything but the play button while playing a session."""
        # StaticText Disable
        self.FindWindowById(self._text_ids[0]).Disable()
        
        self.playback_rate.Disable()
    
    def playEnable(self):
        """Enables everything back after done playing a session."""
        # StaticText Enable
        self.FindWindowById(self._text_ids[0]).Enable()
        
        self.playback_rate.Enable()
    
    def recordDisable(self):
        """Disables everything but the record button while recording."""
        # StaticText Disable
        for id in self._text_ids[1:]:
            self.FindWindowById(id).Disable()
        
        self.record_rate.Disable()
        
        self.stream_button.Disable()
    
    def recordEnable(self):
        """Enables everything after recording."""
        # StaticText Disable
        for id in self._text_ids[1:]:
            self.FindWindowById(id).Enable()
        
        self.record_rate.Enable()
        
        self.stream_button.Enable()
    
    def resetSelect(self):
        for i in range(self.device_list.GetCount()):
            self.device_list.SetItemBackgroundColour(i, (255, 255, 255))
    
    def setBinds(self, win):
        """Sets the binds for the LivePanel class and its attributes.
        
        Args:
            win: A reference to the main window, a wxPython object.
        """
        # Self Binds
        self.Bind(wx.EVT_KEY_DOWN, win.onKeyPress)
        self.Bind(wx.EVT_KEY_UP, win.onKeyPress)
        
        # Button Binds
        self.play_button.Bind(wx.EVT_BUTTON, win.onPlayButton)
        
        self.record_button.Bind(wx.EVT_BUTTON, win.onRecordButton)
        
        self.stream_button.Bind(wx.EVT_BUTTON, win.onStreamButton)
        
        self.select_button.Bind(wx.EVT_BUTTON, self.onSelectAll)
        
        self.deselect_button.Bind(wx.EVT_BUTTON, self.onDeselectAll)
        
        # Key Input Binds
        self.play_button.Bind(wx.EVT_KEY_DOWN, win.onKeyPress)
        self.play_button.Bind(wx.EVT_KEY_UP, win.onKeyPress)
        
        self.record_button.Bind(wx.EVT_KEY_DOWN, win.onKeyPress)
        self.record_button.Bind(wx.EVT_KEY_UP, win.onKeyPress)
        
        self.stream_button.Bind(wx.EVT_KEY_DOWN, win.onKeyPress)
        self.stream_button.Bind(wx.EVT_KEY_UP, win.onKeyPress)
        
        # Mouse Input Binds
        self.playback_rate.Bind(wx.EVT_MOUSEWHEEL, win.onGLScroll)
        
        self.record_rate.Bind(wx.EVT_MOUSEWHEEL, win.onGLScroll)
        
        self.interval.Bind(wx.EVT_MOUSEWHEEL, win.onGLScroll)
        
        self.device_list.Bind(wx.EVT_MOUSEWHEEL, win.onGLScroll)
    
    def threadCallback(self, device, success):
        """A function that is used to call a callback function that is in a
            thread.
        """
        wx.CallAfter(self.updateCheckList, device, success)
    
    def updateCheckList(self, device, success):
        """A function that is used to update the device_list items indicating
            which failed/succeeded to start streaming.
        """
        device_name = device.device_type + '-' + device.serial_number_hex
        idx = self.device_list.FindString(device_name)
        if success:
            if device in self.failed_list:
                self.failed_list.remove(device)
                self.device_list.SetItemBackgroundColour(idx, (255, 255, 255))
                self.device_list.Refresh()
                great_grand_parent = self.GetGrandParent().GetParent()
                for bone in great_grand_parent.bone_list.values():
                    node = bone.vs_node
                    if node is not None:
                        tmp_device = node.getInputDevice()
                        if tmp_device is not None:
                            if device.serial_number == tmp_device.serial_number:
                                bone.setAmbientColor()
                # Refresh the glcanvas
                great_grand_parent.gl_canvas.Refresh()
                app.Yield(True)
        else:
            if device not in self.failed_list:
                self.failed_list.append(device)
                self.device_list.SetItemBackgroundColour(idx, (255, 0, 0))
                self.device_list.Refresh()
                great_grand_parent = self.GetGrandParent().GetParent()
                for bone in great_grand_parent.bone_list.values():
                    node = bone.vs_node
                    if node is not None:
                        tmp_device = node.getInputDevice()
                        if tmp_device is not None:
                            if device.serial_number == tmp_device.serial_number:
                                bone.setAmbientColor(anim_utils.BONE_STREAM_FAIL)
                # Refresh the glcanvas
                great_grand_parent.gl_canvas.Refresh()
                app.Yield(True)


### wxPanel ### (ID's 101-105)
class RightPanel(wx.Panel):
    
    """A wxPython Panel object.
    
    Attributes:
        live_panel: An instance of wx.Panel used for creating and playing
            sessions.
        notebook: An instance of wx.Notebook.
        pose_panel: An instance of wx.Panel used for interacting with bones in
            pose mode.
        session_choice_box: A wx.Choice instance that has a list of
            RecordSession objects' names.
    """
    def __init__(self, parent):
        """Initializes the RightPanel class.
        
        Args:
            parent: A reference to another wxPython object.
        """
        wx.Panel.__init__(self, parent, -1, style=0)
        
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(box_sizer)
        
        ## Session Section ##
        session_grid = wx.GridSizer(2, 1) # rows, cols
        self.session_choice_box = wx.Choice(self, 101, size=(175, -1),
            choices=["None"])
        self.session_choice_box.SetSelection(0)
        
        session_grid.AddMany(
            [(wx.StaticText(self, 102, "Current Session:"), 0, wx.ALIGN_CENTER),
                (self.session_choice_box, 0, wx.ALIGN_CENTER)])
        
        ## Notebook Section ##
        self.notebook = wx.Notebook(self, 103, style=wx.WANTS_CHARS)
        self.pose_panel = PosePanel(self.notebook)
        self.live_panel = LivePanel(self.notebook)
        self.notebook.AddPage(self.pose_panel, "Pose")
        self.notebook.AddPage(self.live_panel, "Live")
        
        ## Image Section ##
        img = wx.Image(os.path.join(_dir_path, "media\\Mocap_Banner.jpg"),
            wx.BITMAP_TYPE_JPEG)
        img = img.ConvertToBitmap()
        
        ## Box Sizer ##
        box_sizer.Add(wx.StaticBitmap(self, -1, img), 0, wx.EXPAND | wx.ALL)
        box_sizer.Add(session_grid, 0, wx.EXPAND | wx.ALL, 5)
        box_sizer.Add(self.notebook, 0, wx.EXPAND | wx.ALL, 5)
    
    def disableChoice(self):
        self.FindWindowById(102).Disable()
        self.session_choice_box.Disable()
    
    def enableChoice(self):
        self.FindWindowById(102).Enable()
        self.session_choice_box.Enable()
    
    def setBinds(self, win):
        """Sets the binds for the RightPanel class and its attributes.
        
        Args:
            win: A reference to the main window, a wxPython object.
        """
        # Self Binds
        self.Bind(wx.EVT_KEY_DOWN, win.onKeyPress)
        self.Bind(wx.EVT_KEY_UP, win.onKeyPress)
        
        # Key Input Binds
        self.session_choice_box.Bind(wx.EVT_KEY_DOWN, win.onKeyPress)
        self.session_choice_box.Bind(wx.EVT_KEY_UP, win.onKeyPress)
        
        self.notebook.Bind(wx.EVT_KEY_DOWN, win.onKeyPress)
        self.notebook.Bind(wx.EVT_KEY_UP, win.onKeyPress)
        
        # Choice Binds
        self.session_choice_box.Bind(wx.EVT_CHOICE, win.onSessionChoice)
        
        # Mouse Input Binds
        self.session_choice_box.Bind(wx.EVT_MOUSEWHEEL, win.onGLScroll)
        
        # Notebook Binds
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING, win.onSetMode)
        
        # Panel Binds
        self.pose_panel.setBinds(win)
        
        self.live_panel.setBinds(win)


### wxPanel ### (ID's 106-115)
class BottomPanel(wx.Panel):
    
    """A wxPython Panel object.
    
    Attributes:
        cur_fps: A float denoting the current frames per second.
        cur_fps_text: An instance of wx.StaticText that displays the current
            frames per second.
        cur_frame: An integer denoting what the current frame is.
        cur_frame_text: An instance of wx.StaticText that displays the current
            frame.
        cur_num_frames: An integer denoting the number of frames there are
        cur_num_frame_text: An instance of wx.StaticText that displays the
            current number of frames there are.
            currently.
        cur_time: A float denoting what the current elapsed time is.
        cur_time_text: An instance of wx.StaticText that displays the current
            time that has elapsed.
        fps: A float denoting the requested frames per second.
        fps_text: An instance of wx.StaticText that displays the requested
            frames per second.
        frame_slider: An instance of wx.Slider.
        num_frames: An integer denoting the number of frames there are.
        num_frames_text: An instance of wx.StaticText that displays the number
            of frames there are.
    """
    def __init__(self, parent):
        """Initializes the BottomPanel class.
        
        Args:
            parent: A reference to another wxPython object.
        """
        wx.Panel.__init__(self, parent, -1, style=0)
        
        self.play_box_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.record_box_sizer = wx.BoxSizer(wx.VERTICAL)
        self.record_inner_box_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        ## Slider Section ##
        self.cur_frame = 0
        self.num_frames = 0
        
        text = "Frame: " + str(self.cur_frame)
        self.cur_frame_text = wx.StaticText(self, 106, text)
        
        self.frame_slider = wx.Slider(self, 107, 0, 0, 100,
            style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS)
        
        text = "Num Frames: " + str(self.num_frames)
        self.num_frames_text = wx.StaticText(self, 108, text)
        
        ## Recording Section ##
        self.cur_time = 0.00
        self.cur_num_frames = 0
        self.fps = 0
        self.cur_fps = 0
        
        text = "Time: " + str(self.cur_time)
        self.cur_time_text = wx.StaticText(self, 109, text)
        text = "Num Frames: " + str(self.cur_num_frames)
        self.cur_num_frame_text = wx.StaticText(self, 110, text)
        text = "Requested FPS: " + str(self.fps)
        self.fps_text = wx.StaticText(self, 111, text)
        text = "FPS: " + str(self.cur_fps)
        self.cur_fps_text = wx.StaticText(self, 112, text)
        
        ## Play Box Sizer ##
        self.play_box_sizer.AddSpacer((5, 0))
        self.play_box_sizer.Add(self.cur_frame_text, 0, wx.ALIGN_CENTER)
        self.play_box_sizer.AddSpacer((30, 0))
        self.play_box_sizer.Add(self.frame_slider, 4, wx.EXPAND | wx.ALL)
        self.play_box_sizer.AddSpacer((5, 0))
        self.play_box_sizer.Add(self.num_frames_text, 0, wx.ALIGN_CENTER)
        self.play_box_sizer.AddSpacer((30, 0))
        
        ## Record Box Sizer ##
        self.record_inner_box_sizer.AddStretchSpacer()
        self.record_inner_box_sizer.Add(self.cur_time_text, 0,
            wx.ALIGN_CENTER | wx.EXPAND | wx.ALL)
        self.record_inner_box_sizer.AddStretchSpacer()
        self.record_inner_box_sizer.Add(self.cur_num_frame_text, 0,
            wx.ALIGN_CENTER | wx.EXPAND | wx.ALL)
        self.record_inner_box_sizer.AddStretchSpacer()
        self.record_inner_box_sizer.Add(self.fps_text, 0,
            wx.ALIGN_CENTER | wx.EXPAND | wx.ALL)
        self.record_inner_box_sizer.AddStretchSpacer()
        self.record_inner_box_sizer.Add(self.cur_fps_text, 0,
            wx.ALIGN_CENTER | wx.EXPAND | wx.ALL)
        self.record_inner_box_sizer.AddStretchSpacer()
        
        self.record_box_sizer.AddSpacer((0, 10))
        self.record_box_sizer.Add(self.record_inner_box_sizer, 0,
            wx.EXPAND | wx.ALL)
    
    def noShow(self):
        self.cur_frame_text.Show(False)
        
        self.num_frames_text.Show(False)
        
        self.frame_slider.Show(False)
        
        self.cur_time_text.Show(False)
        
        self.cur_num_frame_text.Show(False)
        
        self.fps_text.Show(False)
        
        self.cur_fps_text.Show(False)
    
    def reset(self):
        self.cur_frame = 0
        self.num_frames = 0
        self.cur_time = 0.00
        self.cur_num_frames = 0
        self.fps = 0
        self.cur_fps = 0
        
        text = "Frame: " + str(self.cur_frame)
        self.cur_frame_text.SetLabel(text)
        
        text = "Num Frames: " + str(self.num_frames)
        self.num_frames_text.SetLabel(text)
        
        self.frame_slider.SetValue(self.cur_frame)
        self.frame_slider.SetMax(self.cur_frame)
        
        text = "Time: " + str(self.cur_time)
        self.cur_time_text.SetLabel(text)
        
        text = "Num Frames: " + str(self.cur_num_frames)
        self.cur_num_frame_text.SetLabel(text)
        
        text = "Requested FPS: " + str(self.fps)
        self.fps_text.SetLabel(text)
        
        text = "FPS: " + str(self.cur_fps)
        self.cur_fps_text.SetLabel(text)
    
    def setBinds(self, win):
        """Sets the binds for the BottomPanel class.
        
        Args:
            win: A reference to the main window, a wxPython object.
        """
        # Self Binds
        self.Bind(wx.EVT_KEY_DOWN, win.onKeyPress)
        self.Bind(wx.EVT_KEY_UP, win.onKeyPress)
    
    def setupPlay(self, max_frame):
        self.cur_frame = 0
        self.num_frames = max_frame
        
        text = "Frame: " + str(self.cur_frame)
        self.cur_frame_text.SetLabel(text)
        
        text = "Num Frames: " + str(self.num_frames)
        self.num_frames_text.SetLabel(text)
        
        self.frame_slider.SetMax(max_frame)
        self.frame_slider.SetValue(self.cur_frame)
    
    def setupRecord(self, req_fps):
        self.cur_time = 0.00
        self.cur_num_frames = 0
        self.fps = req_fps
        self.cur_fps = 0
        
        text = "Time: " + str(self.cur_time)
        self.cur_time_text.SetLabel(text)
        
        text = "Num Frames: " + str(self.cur_num_frames)
        self.cur_num_frame_text.SetLabel(text)
        
        text = "Requested FPS: " + str(self.fps)
        self.fps_text.SetLabel(text)
        
        text = "FPS: " + str(self.cur_fps)
        self.cur_fps_text.SetLabel(text)
    
    def showPlay(self):
        self.SetSizer(self.play_box_sizer, False)
        
        self.cur_frame_text.Show(True)
        
        self.num_frames_text.Show(True)
        
        self.frame_slider.Show(True)
        
        self.cur_time_text.Show(False)
        
        self.cur_num_frame_text.Show(False)
        
        self.fps_text.Show(False)
        
        self.cur_fps_text.Show(False)
        
        self.SendSizeEvent()
    
    def showRecord(self):
        self.SetSizer(self.record_box_sizer, False)
        
        self.cur_frame_text.Show(False)
        
        self.num_frames_text.Show(False)
        
        self.frame_slider.Show(False)
        
        self.cur_time_text.Show(True)
        
        self.cur_num_frame_text.Show(True)
        
        self.fps_text.Show(True)
        
        self.cur_fps_text.Show(True)
        
        self.SendSizeEvent()
    
    def updatePlay(self, new_frame):
        self.cur_frame = new_frame
        
        text = "Frame: %d" % self.cur_frame
        self.cur_frame_text.SetLabel(text)
        
        self.frame_slider.SetValue(new_frame)
    
    def updateRecord(self, time, frames):
        self.cur_time = time
        if frames is not None:
            self.cur_num_frames = frames
        if time > 0:
            self.cur_fps = self.cur_num_frames / self.cur_time
        
        text = "Time: %0.1f s" % ((self.cur_time * 100) / 100.0)
        self.cur_time_text.SetLabel(text)
        
        text = "Num Frames: %d" % self.cur_num_frames
        self.cur_num_frame_text.SetLabel(text)
        
        text = "FPS: %0.1f" % ((self.cur_fps * 100) / 100.0)
        self.cur_fps_text.SetLabel(text)


### wxDialog ### (ID's 171-185)
class ColorSettings(wx.Dialog):
    
    """A wxPython Dialog that creates the window for Color Settings.
    
    Attributes:
        bg_color1: A wx.ColourSelect instance that is used for the first color
            of the background.
        bg_color2: A wx.ColourSelect instance that is used for the second color
            of the background.
        bone_head_color: A wx.ColourSelect instance that is used for the color
            of the head of a bone.
        bone_tail_color: A wx.ColourSelect instance that is used for the color
            of the tail of a bone.
        grid_alpha =  A wx.Slider instance that is used for the alpha value
            of the grid.
        grid_color: A wx.ColourSelect instance that is used for the color
            of the grid.
        horizontal_style: A wx.RadioButton instance that indicates a horizontal
            style.
        vertical_style: A wx.RadioButton instance that indicates a vertical
            style.
    """
    def __init__(self, parent, color_list):
        """Initializes the ColorSettings class.
        
        Args:
            parent: A reference to another wxPython object.
            color_list: A list that contains the colors of what objects that can
                be changed.
        """
        wx.Dialog.__init__(self, parent, -1, "Color Settings", size=(195, 310))
        self.SetIcon(parent.GetIcon())
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        
        head, tail, grid, bg1, bg2 = color_list
        
        ## Color Selection Section ##
        color_grid = wx.GridSizer(5, 2, 5, 5) # rows, cols
        
        self.bone_head_color = colour_sel.ColourSelect(self, 171, '', head)
        self.bone_tail_color = colour_sel.ColourSelect(self, 172, '', tail)
        self.grid_color = colour_sel.ColourSelect(self, 173, '', grid)
        wx.StaticText(self, -1, "Alpha of the grid", (5, 110))
        self.grid_alpha = wx.Slider(self, 174, -1, 0, 100, (92, 112), (92, 16))
        self.grid_alpha.SetValue(gl_sg.global_grid_alpha * 100)
        self.bg_color1 = colour_sel.ColourSelect(self, 175, '', bg1)
        self.bg_color2 = colour_sel.ColourSelect(self, 176, '', bg2)
        self.horizontal_style = wx.RadioButton(self, 177, 'Horizontal',
            (20, 225))
        self.vertical_style = wx.RadioButton(self, 178, 'Vertical', (100, 225))
        if gl_sg.global_bg_style == gl_sg.HORIZONTAL:
            self.horizontal_style.SetValue(True)
        else:
            self.vertical_style.SetValue(True)
        
        color_grid.AddMany(
            [(wx.StaticText(self, -1, "Color of the head of the bone"), 0,
                wx.ALIGN_CENTER_VERTICAL), (self.bone_head_color, 0, wx.ALL),
            (wx.StaticText(self, -1, "Color of the tail of the bone"), 0,
                wx.ALIGN_CENTER_VERTICAL), (self.bone_tail_color, 0, wx.ALL),
            (wx.StaticText(self, -1, "Color of the grid"), 0,
                wx.ALIGN_CENTER_VERTICAL), (self.grid_color, 0, wx.ALL)])
        color_grid.AddSpacer((0, 0))
        color_grid.AddSpacer((0, 0))
        color_grid.AddMany(
            [(wx.StaticText(self, -1, "Color1 of the background"), 0,
                wx.ALIGN_CENTER_VERTICAL), (self.bg_color1, 0, wx.ALL),
            (wx.StaticText(self, -1, "Color2 of the background"), 0,
                wx.ALIGN_CENTER_VERTICAL), (self.bg_color2, 0, wx.ALL)])
        
        sizer.Add(color_grid, 0, wx.ALL, 5)
        
        ## Button Box ##
        btn_sizer = wx.StdDialogButtonSizer()
        
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btn_sizer.AddButton(btn)
        
        btn = wx.Button(self, wx.ID_CANCEL)
        btn_sizer.AddButton(btn)
        btn_sizer.Realize()
        
        tmp_text = wx.StaticText(self, -1, "Gradient direction")
        font = tmp_text.GetFont()
        font.SetUnderlined(True)
        tmp_text.SetFont(font)
        
        sizer.Add(tmp_text, 0, wx.ALIGN_CENTER)
        sizer.AddSpacer((0, 35))
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER)


### wxTextEntryDialog ###
class SessionName(wx.TextEntryDialog):
    
    """A wxPython TextEntryDialog that creates the window for naming the
    recorded session.
    
    Attributes:
        new_name: A string that represents the new name for the session.
        session_list: A list that contains the names of stored sessions.
    """
    def __init__(self, parent, name, sessions):
        """Initializes the SessionName class.
        
        Args:
            parent: A reference to another wxPython object.
            name : A string reference to a default name of the session.
            sessions: A list that contains the names of stored sessions.
        """
        wx.TextEntryDialog.__init__(self, parent, "Name:", "Session Name", name,
            style=wx.OK)
        
        self.SetIcon(parent.GetIcon())
        
        self.session_list = sessions
        self.new_name = name
        
        self.Bind(wx.EVT_TEXT, self.onNameChange)
        
        btn = self.GetChildren()[2]
        btn.Bind(wx.EVT_ENTER_WINDOW, self.onNameCheck)
        
    def onNameChange(self, event=None):
        self.new_name = event.GetString()
        event.Skip()
    
    def onNameCheck(self, event=None):
        name = self.new_name
        if name in self.session_list:
            cnt = 1
            tmp_name = name + '_' + str(cnt)
            while tmp_name in self.session_list:
                cnt += 1
                tmp_name = name + '_' + str(cnt)
            self.SetValue(tmp_name)
        event.Skip()


### wxWizard ###
class SkeletonWizard(wizard.Wizard):
    def __init__(self, parent, id, title="Skeleton Wizard", pos=wx.DefaultPosition):
        
        self.male_img = wx.Image(os.path.join(_dir_path, "media\\Proportion-Ratios-Male.png"), wx.BITMAP_TYPE_PNG)
        self.female_img = wx.Image(os.path.join(_dir_path, "media\\Proportion-Ratios-Female.png"), wx.BITMAP_TYPE_PNG)
        self.male_img = self.male_img.ConvertToBitmap()
        self.female_img = self.female_img.ConvertToBitmap()
        wizard.Wizard.__init__(self, parent, id, title, self.male_img, pos)
        self.SetIcon(wx.Icon(os.path.join(_dir_path, "media\\3Space_Icon.ico"), wx.BITMAP_TYPE_ICO))
        
        # Build pages
        first_page = wizard.WizardPageSimple(self)
        second_page = wizard.WizardPageSimple(self)
        self.first_page = first_page
        
        # Build chain
        wizard.WizardPageSimple_Chain(first_page, second_page)
        
        # First Page
        txt = ("This wizard is used for helping the user create a\n"
                "skeleton to the scale of the person wearing the\n"
                "Mocap Suit.")
        wx.StaticText(first_page, label=txt, pos=(10, 10))
        wx.StaticText(first_page, label="Sex:", pos=(10, 60))
        self.male_radio = wx.RadioButton(first_page, label="Male", pos=(20, 80), style=wx.RB_GROUP)
        self.female_radio = wx.RadioButton(first_page, label="Female", pos=(70, 80))
        wx.StaticText(first_page, label="Height:", pos=(10, 100))
        self.height = float_spin.FloatSpin(first_page, pos=(20, 120), size=(60, -1), value=177.8, min_val=1, digits=2)
        self.centimeter_radio = wx.RadioButton(first_page, label="centimeters", pos=(85, 125), style=wx.RB_GROUP)
        self.inch_radio = wx.RadioButton(first_page, label="inches", pos=(165, 125))
        self.replace_check = wx.CheckBox(first_page, label="Replace Skeleton(s)", pos=(10, 150))
        
        # Second Page
        sizer = wx.BoxSizer(wx.VERTICAL)
        second_page.SetSizer(sizer)
        txt = ("Here you may change the name of the bones and\n"
                "choose which output node will manipulate the bone.")
        intro = wx.StaticText(second_page, label=txt)
        sizer.Add(intro, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(wx.StaticLine(second_page), 0, wx.EXPAND | wx.ALL, 5)
        self.name_table = []
        self.output_table = []
        for i in range(18):
            self.name_table.append(wx.TextCtrl(second_page, size=(120, 18), style=wx.TE_PROCESS_ENTER))
            self.output_table.append(wx.Choice(second_page, size=(140, -1), choices=["None"]))
        for i in range(18):
            bone_sizer = wx.BoxSizer(wx.HORIZONTAL)
            bone_sizer.AddStretchSpacer()
            bone_sizer.Add(self.name_table[i], 0, wx.ALIGN_CENTER_VERTICAL)
            bone_sizer.AddSpacer((5, 0))
            bone_sizer.Add(self.output_table[i], 0, wx.ALIGN_CENTER_VERTICAL)
            bone_sizer.AddStretchSpacer()
            sizer.Add(bone_sizer, 0)
            if i < 17:
                sizer.AddSpacer((0, 3))
        
        self.FitToPage(second_page)
        
        # Fix for some bug in TextCtrl or Wizard
        self.ShowPage(second_page)
        self.ShowPage(first_page, False)
        
        # Binds
        self.male_radio.Bind(wx.EVT_RADIOBUTTON, self.onRadio)
        self.female_radio.Bind(wx.EVT_RADIOBUTTON, self.onRadio)
        self.centimeter_radio.Bind(wx.EVT_RADIOBUTTON, self.onRadio)
        self.inch_radio.Bind(wx.EVT_RADIOBUTTON, self.onRadio)
    
    def initNamesOutputs(self, output_list):
        for i in range(18):
            self.name_table[i].SetValue(anim_utils.NAME_LIST[i])
            self.output_table[i].AppendItems(output_list)
            self.output_table[i].SetSelection(0)
    
    def getNamesOutputs(self, output_list):
        name_dict = {}
        for i in range(18):
            name = self.name_table[i].GetValue()
            output = self.output_table[i].GetStringSelection()
            if output in output_list:
                name_dict[anim_utils.NAME_LIST[i]] = (name, output_list[output])
            else:
                name_dict[anim_utils.NAME_LIST[i]] = (name, None)
        return name_dict
    
    def onRadio(self, event=None):
        evt_id = event.GetId()
        if evt_id == self.male_radio.GetId():
            self.SetBitmap(self.male_img)
            self.Refresh()
        elif evt_id == self.female_radio.GetId():
            self.SetBitmap(self.female_img)
            self.Refresh()
        elif evt_id == self.centimeter_radio.GetId():
            h = self.height.GetValue()
            self.height.SetValue(h * 2.54)
        else:
            h = self.height.GetValue()
            self.height.SetValue(h / 2.54)


### wxDialog ###
class SkeletonBoneChooser(wx.Dialog):
    
    """ A wxPython Dialog that creates the window for SkeletonBoneChooser.
    
        Attributes:
            hip_choice_box: A wx.Choice instance that has a list of Bone
                objects' names.
            l_foot_choice_box: A wx.Choice instance that has a list of Bone
                objects' names.
            r_foot_choice_box: A wx.Choice instance that has a list of Bone
                objects' names.
            skeleton_choice_box: A wx.Choice instance that has a list of
                Skeleton objects' names.
    """
    def __init__(self, parent, skel_list, bone_list):
        """ Initializes the SkeletonBoneChooser class.
        
            Args:
                parent: A reference to another wxPython object.
                skel_list: A list that contains the names of Skeleton objects.
                bone_list: A list that contains the names of Bone objects.
        """
        wx.Dialog.__init__(self, parent, -1, "Pedestrian Settings", size=(195, 310))
        self.SetIcon(parent.GetIcon())
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        
        ## Skeleton Selection Section ##
        self.skeleton_choice_box = wx.Choice(self, -1, size=(150, -1), choices=skel_list)
        sizer.AddSpacer((0, 15))
        sizer.AddMany([ (wx.StaticText(self, -1, "Skeleton"), 0, wx.ALIGN_CENTER),
                        (self.skeleton_choice_box, 0, wx.ALIGN_CENTER)])
        sizer.AddSpacer((0, 15))
        
        ## Bone Selection Section ##
        # Hip
        hip_list = bone_list[:1]
        for b in bone_list:
            if b.lower() in anim_utils.HIP_LIST:
                hip_list.append(b)
        self.hip_choice_box = wx.Choice(self, -1, size=(150, -1), choices=hip_list)
        # Left Foot
        l_foot_list = bone_list[:1]
        for b in bone_list:
            if b.lower() in anim_utils.LEFT_FOOT_LIST:
                l_foot_list.append(b)
        self.l_foot_choice_box = wx.Choice(self, -1, size=(150, -1), choices=l_foot_list)
        # Right Foot
        r_foot_list = bone_list[:1]
        for b in bone_list:
            if b.lower() in anim_utils.RIGHT_FOOT_LIST:
                r_foot_list.append(b)
        self.r_foot_choice_box = wx.Choice(self, -1, size=(150, -1), choices=r_foot_list)
        
        sizer.AddMany([ (wx.StaticText(self, -1, "Hip Bone"), 0, wx.ALIGN_CENTER),
                        (self.hip_choice_box, 0, wx.ALIGN_CENTER)])
        sizer.AddSpacer((0, 15))
        sizer.AddMany([ (wx.StaticText(self, -1, "Left Foot Bone"), 0, wx.ALIGN_CENTER),
                        (self.l_foot_choice_box, 0, wx.ALIGN_CENTER)])
        sizer.AddSpacer((0, 15))
        sizer.AddMany([ (wx.StaticText(self, -1, "Right Foot Bone"), 0, wx.ALIGN_CENTER),
                        (self.r_foot_choice_box, 0, wx.ALIGN_CENTER)])
        
        ## Button Box ##
        btn_sizer = wx.StdDialogButtonSizer()
        
        apply_btn = wx.Button(self, wx.ID_APPLY)
        apply_btn.SetDefault()
        btn_sizer.AddButton(apply_btn)
        
        done_btn = wx.Button(self, wx.ID_OK, "Done")
        btn_sizer.AddButton(done_btn)
        done_btn.Disable()
        btn_sizer.Realize()
        
        sizer.AddSpacer((0, 35))
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER)
        
        ## Set Selections ##
        if len(skel_list) > 2:
            self.skeleton_choice_box.SetSelection(0)
            self.hip_choice_box.Disable()
            self.l_foot_choice_box.Disable()
            self.r_foot_choice_box.Disable()
            self.hip_choice_box.SetSelection(0)
            self.l_foot_choice_box.SetSelection(0)
            self.r_foot_choice_box.SetSelection(0)
        else:
            self.skeleton_choice_box.SetSelection(1)
            hip_idx = hip_list.index(parent.skeleton_list[skel_list[1]].getHipBone().getName())
            l_foot_idx = l_foot_list.index(parent.skeleton_list[skel_list[1]].getFootBoneLeft().getName())
            r_foot_idx = r_foot_list.index(parent.skeleton_list[skel_list[1]].getFootBoneRight().getName())
            self.hip_choice_box.SetSelection(hip_idx)
            self.l_foot_choice_box.SetSelection(l_foot_idx)
            self.r_foot_choice_box.SetSelection(r_foot_idx)
        
        ## Binds ##
        self.skeleton_choice_box.Bind(wx.EVT_CHOICE, self.onChoice)
        self.hip_choice_box.Bind(wx.EVT_CHOICE, self.onChoice)
        self.l_foot_choice_box.Bind(wx.EVT_CHOICE, self.onChoice)
        self.r_foot_choice_box.Bind(wx.EVT_CHOICE, self.onChoice)
        apply_btn.Bind(wx.EVT_BUTTON, parent.onSkeletonBoneChooserButton)
        done_btn.Bind(wx.EVT_BUTTON, parent.onSkeletonBoneChooserButton)
    
    def onChoice(self, event=None):
        evt_id = event.GetId()
        choice_str = event.GetString()
        if evt_id == self.skeleton_choice_box.GetId():
            if choice_str == "None":
                self.hip_choice_box.Disable()
                self.l_foot_choice_box.Disable()
                self.r_foot_choice_box.Disable()
                self.hip_choice_box.SetSelection(0)
                self.l_foot_choice_box.SetSelection(0)
                self.r_foot_choice_box.SetSelection(0)
            else:
                self.hip_choice_box.Enable()
                self.l_foot_choice_box.Enable()
                self.r_foot_choice_box.Enable()
        elif evt_id == self.hip_choice_box.GetId():
            if choice_str != "None":
                if choice_str == self.l_foot_choice_box.GetStringSelection():
                    self.hip_choice_box.SetSelection(0)
                elif choice_str == self.r_foot_choice_box.GetStringSelection():
                    self.hip_choice_box.SetSelection(0)
        elif evt_id == self.l_foot_choice_box.GetId():
            if choice_str != "None":
                if choice_str == self.hip_choice_box.GetStringSelection():
                    self.l_foot_choice_box.SetSelection(0)
                elif choice_str == self.r_foot_choice_box.GetStringSelection():
                    self.l_foot_choice_box.SetSelection(0)
        elif evt_id == self.r_foot_choice_box.GetId():
            if choice_str != "None":
                if choice_str == self.hip_choice_box.GetStringSelection():
                    self.r_foot_choice_box.SetSelection(0)
                elif choice_str == self.l_foot_choice_box.GetStringSelection():
                    self.r_foot_choice_box.SetSelection(0)


### wxDialog ###
class AngleCalculator(wx.Dialog):
    def __init__(self, parent, skeleton_name, is_stream):
        wx.Dialog.__init__(self, parent, -1, "Angle Calculator")
        self.SetIcon(parent.GetIcon())
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.update_timer = wx.Timer(self)
        
        self.angle_list = [
            "",
            "Ankle(Bend,Flexion)",
            "Elbow(Flexion)",
            "Forearm(Supination)",
            "Hip(Adduction,Flexion,Rotation)",
            "Knee(Flexion)",
            "Neck(Bend,Flexion,Rotation)",
            "Shoulder(Adduction,Flexion,Rotation)",
            "Spine(Bend,Flexion,Rotation)",
            "Sternoclavicular(Adduction,Flexion)",
            "Wrist(Bend,Flexion)",
            "QuaternionDifference",
            "MatrixDifference"
            ]
        self.joint_list = [""]
        skeleton = parent.skeleton_list[skeleton_name]
        bone_list = skeleton.getSkeletonBoneList()
        bone_list.sort()
        for bone in bone_list:
            if type(parent.bone_list[bone].parent) is anim_utils.Bone:
                self.joint_list.append(bone + "->" + parent.bone_list[bone].parent.getName())
        self.skel_name = skeleton_name
        
        self.is_update = is_stream
        self.log_list = {}
        self.log_data = []
        
        self.gbs = wx.GridBagSizer(5, 5)
        
        self.gbs.Add(wx.StaticText(self, -1, "Slot"), (0, 0), flag=wx.ALIGN_CENTER)
        self.gbs.Add(wx.StaticText(self, -1, "Joint"), (0, 1), flag=wx.ALIGN_CENTER)
        self.gbs.Add(wx.StaticText(self, -1, "Angle type"), (0, 2), flag=wx.ALIGN_CENTER)
        self.gbs.Add(wx.StaticText(self, -1, "Output preview"), (0, 3), (1, 15), flag=wx.ALIGN_CENTER)
        
        for i in range(1, 17):
            label_str = str(i) + '.'
            if i < 10:
                label_str = '  ' + label_str
            self.gbs.Add(wx.CheckBox(self, -1, label=label_str, style=wx.ALIGN_RIGHT), (i, 0), flag=wx.ALIGN_CENTER)
            self.gbs.Add(wx.Choice(self, -1, size=(220, -1), choices=self.joint_list), (i, 1))
            self.gbs.Add(wx.Choice(self, -1, size=(220, -1), choices=self.angle_list), (i, 2))
            self.gbs.Add(wx.StaticText(self, -1, ""), (i, 3), (1, 15), flag=wx.ALIGN_CENTER)
        
        sizer.Add(self.gbs, 0, wx.ALL, 10)
        
        ## Button Box ##
        btn_sizer = wx.StdDialogButtonSizer()
        
        ok_btn = wx.Button(self, wx.ID_OK)
        ok_btn.SetDefault()
        btn_sizer.AddButton(ok_btn)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL)
        btn_sizer.AddButton(cancel_btn)
        btn_sizer.Realize()
        
        sizer.AddSpacer((0, 35))
        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT)
        
        self.SetSizerAndFit(sizer)
        
        sx, sy = self.GetSize()
        for i in range(24, 466, 26):
            wx.StaticLine(self, -1, (5, i), (sx - 16, -1))
        x = [47, 271, 496]
        for i in range(3):
            wx.StaticLine(self, -1, (x[i], 10), (-1, sy - 100), wx.LI_VERTICAL)
        
        csv_format = wx.RadioButton(self, label="CSV Format", pos=(35, 460), style=wx.RB_GROUP)
        xml_format = wx.RadioButton(self, label="XML Format", pos=(120, 460))
        
        self.log_joint = wx.CheckBox(self, label="Log Joint", pos=(250, 460), style=wx.ALIGN_RIGHT)
        self.log_type = wx.CheckBox(self, label="Log Type", pos=(320, 460), style=wx.ALIGN_RIGHT)
        self.log_joint.SetValue(True)
        self.log_type.SetValue(True)
        
        file_name = os.path.join(_file_path, "Log_" + time.asctime().replace(' ', '_').replace(':', '.') + ".csv")
        self.path = file_browse.FileBrowseButton(self, -1, (15, 481), (500, -1), toolTip="", startDirectory=_file_path, initialValue=file_name, fileMask="*.csv", fileMode=wx.SAVE)
        
        self.update_timer.Start()
        ## Binds ##
        for i in range(1, 17):
            self.gbs.FindItemAtPosition((i, 0)).GetWindow().Bind(wx.EVT_CHECKBOX, self.onCheck)
            self.gbs.FindItemAtPosition((i, 0)).GetWindow().Disable()
            self.gbs.FindItemAtPosition((i, 1)).GetWindow().Bind(wx.EVT_CHOICE, self.onChoice)
            self.gbs.FindItemAtPosition((i, 2)).GetWindow().Bind(wx.EVT_CHOICE, self.onChoice)
        csv_format.Bind(wx.EVT_RADIOBUTTON, self.onRadio)
        xml_format.Bind(wx.EVT_RADIOBUTTON, self.onRadio)
        self.Bind(wx.EVT_TIMER, self.onTimeUpdate, self.update_timer)
    
    def onCheck(self, event):
        check_box = event.GetEventObject()
        row, col = self.gbs.GetItemPosition(check_box)
        if event.IsChecked():
            if row not in self.log_list:
                joint_choice = self.gbs.FindItemAtPosition((row, 1)).GetWindow()
                angle_choice = self.gbs.FindItemAtPosition((row, 2)).GetWindow()
                self.log_list[row] = [joint_choice.GetStringSelection(), angle_choice.GetSelection()]
        else:
            if row in self.log_list:
                del self.log_list[row]
    
    def onChoice(self, event):
        self.gbs.Layout()
        choice_box = event.GetEventObject()
        row, col = self.gbs.GetItemPosition(choice_box)
        if col == 1:
            angle_choice = self.gbs.FindItemAtPosition((row, 2)).GetWindow()
            if choice_box.GetSelection() > 0 and angle_choice.GetSelection() > 0:
                self.gbs.FindItemAtPosition((row, 0)).GetWindow().Enable()
            else:
                check_box = self.gbs.FindItemAtPosition((row, 0)).GetWindow()
                command = wx.CommandEvent(wx.wxEVT_COMMAND_CHECKBOX_CLICKED)
                command.SetInt(0)
                command.SetEventObject(check_box)
                check_box.Command(command)
                check_box.Disable()
        elif col == 2:
            joint_choice = self.gbs.FindItemAtPosition((row, 1)).GetWindow()
            if choice_box.GetSelection() > 0 and joint_choice.GetSelection() > 0:
                self.gbs.FindItemAtPosition((row, 0)).GetWindow().Enable()
            else:
                check_box = self.gbs.FindItemAtPosition((row, 0)).GetWindow()
                command = wx.CommandEvent(wx.wxEVT_COMMAND_CHECKBOX_CLICKED)
                command.SetInt(0)
                command.SetEventObject(check_box)
                check_box.Command(command)
                check_box.Disable()
    
    def onRadio(self, event):
        label = event.GetEventObject().GetLabel()
        if label == "CSV Format":
            file_name = os.path.join(_file_path, "Log_" + time.asctime().replace(' ', '_').replace(':', '.') + ".csv")
            self.path.textControl.SetValue(file_name)
            self.path.fileMask = "*.csv"
        else:
            file_name = os.path.join(_file_path, "Log_" + time.asctime().replace(' ', '_').replace(':', '.') + ".xml")
            self.path.textControl.SetValue(file_name)
            self.path.fileMask = "*.xml"
    
    def onLogData(self):
        data = []
        for i in self.log_list:
            joint_choice, angle_choice = self.log_list[i]
            if len(joint_choice) > 0 and angle_choice > 0:
                string_data = self.outputUpdate(joint_choice, angle_choice, False)
                string_data.insert(0, str(i))
                data.append(string_data)
        
        self.log_data.append(data)
    
    def onTimeUpdate(self, event):
        if self.is_update:
            for i in range(1, 17):
                joint_choice = self.gbs.FindItemAtPosition((i, 1)).GetWindow()
                angle_choice = self.gbs.FindItemAtPosition((i, 2)).GetWindow()
                output = self.gbs.FindItemAtPosition((i, 3)).GetWindow()
                if joint_choice.GetSelection() > 0 and angle_choice.GetSelection() > 0:
                    output_string = self.outputUpdate(joint_choice.GetStringSelection(), angle_choice.GetSelection())
                    output.SetLabel(output_string)
                elif output.GetLabel() != "":
                    output.SetLabel("")
    
    def outputUpdate(self, joint, angle_type, preview=True):
        child_name, parent_name = joint.split('->')
        parent_bone = self.GetParent().bone_list[parent_name]
        child_bone = self.GetParent().bone_list[child_name]
        skeleton = self.GetParent().skeleton_list[self.skel_name]
        timestamp, joint_vaule = anim_utils.calculateJointVaule(parent_bone, child_bone, angle_type)
        
        if angle_type == 1:     # Ankle
            flexion, bend, junk_z = joint_vaule
            if child_bone == skeleton.getFootBoneRight():
                bend *= -1
            output_string = '{:0.1f}, {:0.1f}'.format(bend, flexion)
        elif angle_type == 2:   # Elbow
            junk_x, flexion, junk_z = joint_vaule
            if child_bone == skeleton.getLowerArmBoneRight():
                flexion *= -1
            output_string = '{:0.1f}'.format(flexion)
        elif angle_type == 3:   # Forearm
            supination, junk_y, junk_z = joint_vaule
            output_string = '{:0.1f}'.format(supination)
        elif angle_type == 4:   # Hip
            flexion, rotation, adduction = joint_vaule
            if child_bone == skeleton.getUpperLegBoneLeft():
                rotation *= -1
            else:
                adduction *= -1
            output_string = '{:0.1f}, {:0.1f}, {:0.1f}'.format(adduction, flexion, rotation)
        elif angle_type == 5:   # Knee
            flexion, junk_y, junk_z = joint_vaule
            flexion *= -1
            output_string = '{:0.1f}'.format(flexion)
        elif angle_type == 6:   # Neck
            flexion, rotation, bend = joint_vaule
            flexion *= -1
            bend *= -1
            output_string = '{:0.1f}, {:0.1f}, {:0.1f}'.format(bend, flexion, rotation)
        elif angle_type == 7:   # Shoulder
            rotation, flexion, adduction = joint_vaule
            if child_bone == skeleton.getUpperArmBoneRight():
                flexion *= -1
                adduction *= -1
            output_string = '{:0.1f}, {:0.1f}, {:0.1f}'.format(adduction, flexion, rotation)
        elif angle_type == 8:   # Spine
            flexion, rotation, bend = joint_vaule
            flexion *= -1
            bend *= -1
            output_string = '{:0.1f}, {:0.1f}, {:0.1f}'.format(bend, flexion, rotation)
        elif angle_type == 9:   # Sternoclavicular
            junk_x, flexion, adduction = joint_vaule
            if child_bone == skeleton.getShoulderBoneRight():
                flexion *= -1
                adduction *= -1
            output_string = '{:0.1f}, {:0.1f}'.format(adduction, flexion)
        elif angle_type == 10:  # Wrist
            junk_x, bend, flexion = joint_vaule
            if child_bone == skeleton.getHandBoneRight():
                bend *= -1
                flexion *= -1
            output_string = '{:0.1f}, {:0.1f}'.format(bend, flexion)
        elif angle_type == 11:  # Quaternion Difference
            if preview:
                output_string = '{:s}'.format(joint_vaule)
            else:
                output_string = '{:0.4f};{:0.4f};{:0.4f};{:0.4f}'.format(*joint_vaule.asArray())
        else:                   # Matrix Difference
            if preview:
                output_string = '{:.24s} ... '.format(joint_vaule)
            else:
                output_string = '{:0.4f};{:0.4f};{:0.4f};{:0.4f};{:0.4f};{:0.4f};{:0.4f};{:0.4f};{:0.4f}'.format(*joint_vaule.asRowArray())
        
        if not preview:
            if not self.log_joint.IsChecked():
                joint = ""
            if not self.log_type.IsChecked():
                angle_type = 0
            output_string = [str(timestamp), joint, self.angle_list[angle_type].replace(',', ';'), output_string.replace(', ', ';')]
        
        return output_string
    
    def writeLogFile(self):
        log_name = self.path.GetValue()
        if log_name[-3:] == 'csv':
            log_fp = open(log_name, 'wb')
            logger = csv.writer(log_fp)
            logger.writerow(['JointSlot', 'Timestamp', 'Joint', 'AngleType', 'Output'])
            for ld in self.log_data:
                logger.writerows(ld)
            log_fp.flush()
            log_fp.close()
        else:
            root = ng.et.Element("Root")
            frame_count = 0
            for ld in self.log_data:
                frame = ng.et.Element("FrameData", {"FRAME": str(frame_count)})
                for d in ld:
                    id, timestamp, joint, ang_type, output = d
                    joint_data = ng.et.Element("JointData")
                    joint_data.append(ng.et.Element("JointSlot", {"ID": id}))
                    joint_data.append(ng.et.Element("Timestamp", {"TIME": timestamp}))
                    joint_data.append(ng.et.Element("JointName", {"NAME": joint}))
                    joint_data.append(ng.et.Element("AngleType", {"TYPE": ang_type}))
                    output_data = ng.et.Element("Data")
                    if ang_type == self.angle_list[-2]:
                        quat = output.split(';')
                        output_data.append(ng.et.Element("Quaternion", {"X": quat[0], "Y": quat[1], "Z": quat[2], "W": quat[3]}))
                    elif ang_type == self.angle_list[-1]:
                        mat = output.split(';')
                        output_data.append(ng.et.Element("Matrix", {
                            "R0C0": mat[0],
                            "R0C1": mat[1],
                            "R0C2": mat[2],
                            "R1C0": mat[3],
                            "R1C1": mat[4],
                            "R1C2": mat[5],
                            "R2C0": mat[6],
                            "R2C1": mat[7],
                            "R2C2": mat[8]
                        }))
                    else:
                        type_list = ang_type.rstrip(')').split('(')[1].split(';')
                        val_list = output.split(';')
                        for i in range(len(type_list)):
                            output_data.append(ng.et.Element(type_list[i], {"VALUE": val_list[i]}))
                    joint_data.append(output_data)
                    frame.append(joint_data)
                root.append(frame)
                frame_count += 1
            ng.indent(root)
            xmlTree = ng.et.ElementTree(root)
            xmlTree.write(log_name, "us-ascii", True)


### wxFrame ### (ID's 0-100)
class MainWindow(wx.Frame):
    
    """ A wxPython Frame.
        
        Attributes:
            bone_list: A dictionary of all Bone objects currently aware of.
            bottom_panel: An instance of BottomPanel.
            f_count: An integer that denotes what frame is currently being
                shown.
            gl_canvas: An instance of SceneCanvas.
            has_closed: A boolean that denotes if the window has been closed.
            is_stream: A boolean that denotes if streaming is being performed.
            is_bone: A boolean that denotes if the selected object is a Bone
                object.
            is_free_mode: A boolean that denotes if the GUI is set for free
                translation.
            is_live_mode: A boolean that denotes if the application is in Live
                mode.
            is_logging: A boolean that denotes if the application is logging
                data.
            is_multi_sel: A boolean that denotes if more than one Bone object is
                selected.
            is_ped_track: A boolean that denotes if the application is
                performing pedestrian tracking.
            is_playing: A boolean that denotes if a recorded session is being
                played.
            is_recording: A boolean that denotes if a session is being recorded.
            is_redraw: A boolean that denotes whether to manually redraw the
                RightPanel.
            is_refresh: A boolean that denotes whether to manually refresh the
                window.
            is_rotate_mode: A boolean that denotes if the GUI is set for
                performing rotation.
            is_skeleton: A boolean that denotes if the selected object is a
                Skeleton object.
            is_translate_mode: A boolean that denotes if the GUI is set for
                performing translation.
            live_panel: An instance of LivePanel.
            logger: An instance of animator_utils.Logger.
            logging_window = An instance of a window that wishes to do some
                logging.
            manipulate_bone: A string that indicates if a manipulation object
                has been selected.
            menu_bar: An instance of wx.MenuBar.
            node_graph_window: An instance of node_graph.MainWindow
            output_list: A dictionary of all VirtualSensorNode objects currently
                aware of.
            play_rate: A float that denotes the value at which speed to play
                back the recorded data.
            pop_up: An instance of wx.Menu.
            pose_panel: An instance of PosePanel.
            recorded_session: An instance of animator_utils.RecordSession.
            recorder: An instance of animator_utils.Recorder.
            recording_rate: A float that denotes the value of the recording
                speed.
            right_panel: An instance of RightPanel.
            root_node: An instance of SkelNode.
            selected_obj: An instance of Bone, Skeleton, or a set of Bone
                objects.
            session_list: A dictionary of all RecordSession objects currently
                aware of.
            skeleton_list: A dictionary of all Skeleton objects currently aware
                of.
            start_time_play: A float denoting the start time of playing data.
            start_time_record: A float denoting the start time of recording
                data.
            update_timer: A wx.Timer instance that is used to update the Frame.
    """
    def __init__(self, parent=None, id=-1, title="YEI Mocap - Pose Mode"):
        """ Initializes the MainWindow class.
            
            Args:
                parent: A reference to another wxPython object (default is None)
                id: An integer denoting an ID for the window  (default is -1)
                title: A string denoting the title of the window
                    (default is "YEI Mocap - Pose Mode")
        """
        wx.Frame.__init__(self, parent, id, title, size=MAIN_SIZE, style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)
        
        self.SetMinSize(MAIN_SIZE)
        
        self.SetIcon(wx.Icon(os.path.join(_dir_path, "media\\3Space_Icon.ico"), wx.BITMAP_TYPE_ICO))
        
        # List of our saved sessions
        self.session_list = {}
        
        # Our root bone node
        self.root_node = anim_utils.SkelNode()
        
        # Current session
        self.recorded_session = None
        
        self.recorder = None
        self.logger = None
        
        # Current object selected
        self.selected_obj = None
        
        # Current manipulation
        self.manipulate_bone = ''
        
        # Playback frame rate
        self.play_rate = -1
        
        # Frame time
        self.start_time_play = 0
        self.start_time_record = 0
        
        # Closing indicator
        self.has_closed = False
        
        # Timer
        self.update_timer = wx.Timer(self)
        self.update_timer.Start()
        
        # OpenGL Canvas
        self.gl_canvas = SceneCanvas(self)
        
        # Inner BoxSizer
        inner_box = wx.BoxSizer(wx.HORIZONTAL)
        inner_box.Add(self.gl_canvas, 4, wx.EXPAND)
        
        # Right Panel
        self.right_panel = RightPanel(self)
        inner_box.Add(self.right_panel, 0, wx.EXPAND)
        self.right_panel.SetMinSize(RIGHT_PANEL_SIZE)
        
        # Pose Panel
        self.pose_panel = self.right_panel.pose_panel
        self.pose_panel.disableInput()
        
        # Live Panel
        self.live_panel = self.right_panel.live_panel
        
        # Logging Window
        self.logging_window = None
        
        # Booleans for the GUI
        self.is_free_mode = False
        self.is_translate_mode = False
        self.is_rotate_mode = False
        
        # Boolean for update
        self.is_redraw = False
        self.is_refresh = False
        
        # Booleans for live mode
        self.is_stream = False
        self.is_live_mode = False
        self.is_playing = False
        self.is_ped_track = False
        self.is_recording = False
        self.is_logging = False
        
        # Booleans for object selection
        self.is_bone = False
        self.is_skeleton = False
        self.is_multi_sel = False
        
        # Outer BoxSizer
        outer_box = wx.BoxSizer(wx.VERTICAL)
        outer_box.Add(inner_box, 4, wx.EXPAND)
        
        # Bottom Panel
        self.bottom_panel = BottomPanel(self)
        outer_box.Add(self.bottom_panel, 0, wx.EXPAND)
        self.bottom_panel.SetMinSize(BOTTOM_PANEL_SIZE)
        
        # Node Graph Frame
        self.node_graph_window = ng.MainWindow(self)
        
        ## Binds ##
        self.Bind(wx.EVT_ACTIVATE, self.onFocus)
        self.Bind(wx.EVT_SIZE, self.onWinSize)
        self.Bind(wx.EVT_MOUSEWHEEL, self.onGLScroll)
        self.Bind(wx.EVT_TIMER, self.onTimeUpdate, self.update_timer)
        self.Bind(wx.EVT_CLOSE, self.onAppClose)
        self.Bind(wx.EVT_KEY_DOWN, self.onKeyPress)
        self.Bind(wx.EVT_KEY_UP, self.onKeyPress)
        
        # GLCanvas Binds
        self.gl_canvas.setBinds(self)
        
        # Right Panel Binds
        self.right_panel.setBinds(self)
        
        # Bottom Panel Binds
        self.bottom_panel.setBinds(self)
        
        # Frame Layout
        self.SetAutoLayout(True)
        self.SetSizer(outer_box)
        self.Layout()
        
        # File Menu (ID's 0-5)
        file_menu = wx.Menu()
        
        # File Menu - About
        # Information about this program
        menu_item = file_menu.Append(0, "&About")
        self.Bind(wx.EVT_MENU, self.onAbout, menu_item)
        
        # File Menu - User Wizard
        # Wizard for using the Mocap Studio
        # menu_item = file_menu.Append(1, "User &Wizard")
        # self.Bind(wx.EVT_MENU, self.onWizard, menu_item)
        # File Menu - Separator
        file_menu.AppendSeparator()
        
        # File Menu - Exit
        menu_item = file_menu.Append(2, "E&xit") # Terminate the program
        self.Bind(wx.EVT_MENU, self.onExit, menu_item)
        
        # Import Menu (ID's 6-15)
        import_menu = wx.Menu()
        
        # Import Menu - BVH
        menu_item = import_menu.Append(6, "BVH") # Imports a .bvh file
        self.Bind(wx.EVT_MENU, self.onImport, menu_item)
        
        # Import Menu - TSS
        menu_item = import_menu.Append(7, "TSH") # Imports a .tsh file
        self.Bind(wx.EVT_MENU, self.onImport, menu_item)
        
        # Export Menu (ID's 16-25)
        export_menu = wx.Menu()
        
        # Export Menu - BVH
        bvh_menu = wx.Menu()
        export_menu.AppendMenu(16, "BVH", bvh_menu)
        menu_item = bvh_menu.Append(1601, "Current Session") # Exports a .bvh file
        self.Bind(wx.EVT_MENU, self.onExport, menu_item)
        menu_item = bvh_menu.Append(1602, "Choose Sessions") # Exports multiple .bvh files
        self.Bind(wx.EVT_MENU, self.onExport, menu_item)
        
        # Export Menu - TSH
        tsh_menu = wx.Menu()
        export_menu.AppendMenu(17, "TSH", tsh_menu)
        menu_item = tsh_menu.Append(1701, "Current Session") # Exports a .tsh file
        self.Bind(wx.EVT_MENU, self.onExport, menu_item)
        menu_item = tsh_menu.Append(1702, "Choose Sessions") # Exports multiple .tsh files
        self.Bind(wx.EVT_MENU, self.onExport, menu_item)
        
        # NodeGraph Menu (ID's 26-30)
        node_graph_menu = wx.Menu()
        
        # NodeGraph Menu - Configure
        # Configures the node graph
        menu_item = node_graph_menu.Append(26, "Configure Node Graph")
        self.Bind(wx.EVT_MENU, self.onNodeGraphOpen, menu_item)
        self.node_graph_window.Bind(wx.EVT_CLOSE, self.onNodeGraphClose)
        
        # Settings Menu (ID's 31-55)
        settings_menu = wx.Menu()
        
        # Settings Menu - Configure
        # Configures the colors of the mocap studio
        menu_item = settings_menu.Append(31, "Color Settings")
        self.Bind(wx.EVT_MENU, self.onSettings, menu_item)
        
        # Settings Menu - Logo
        # Shows the YEI logo or not
        menu_item = settings_menu.AppendCheckItem(32, "Show Logo")
        settings_menu.Check(32, global_draw_logo)
        self.Bind(wx.EVT_MENU, self.onSettings, menu_item)
        
        # Settings Menu - Unknowns
        # Tells whether or not to check the unknown com ports
        menu_item = settings_menu.AppendCheckItem(33, "Check Unknown COMs")
        settings_menu.Check(33, sc.global_check_unknown)
        self.Bind(wx.EVT_MENU, self.onSettings, menu_item)
        
        # Settings Menu - Interpolation
        # The interpolation settings of the mocap studio
        interp_menu = wx.Menu()
        settings_menu.AppendMenu(34, "Interpolation Settings", interp_menu)
        menu_item = interp_menu.AppendCheckItem(35, "Export Interpolation")
        interp_menu.Check(35, global_export_interp)
        self.Bind(wx.EVT_MENU, self.onSettings, menu_item)
        method_menu = wx.Menu()
        interp_menu.AppendMenu(36, "Interpolation Method", method_menu)
        menu_item = method_menu.AppendRadioItem(SLERP, "Slerp")
        self.Bind(wx.EVT_MENU, self.onSettings, menu_item)
        # menu_item = method_menu.AppendRadioItem(SQUAD, "Squad")
        # self.Bind(wx.EVT_MENU, self.onSettings, menu_item)
        method_menu.Check(global_interp_method, True)
        
        # Settings Menu - Unit
        # The unit settings of the mocap studio
        unit_menu = wx.Menu()
        settings_menu.AppendMenu(39, "Unit Settings", unit_menu)
        unit_export_menu = wx.Menu()
        unit_menu.AppendMenu(40, "Export Settings", unit_export_menu)
        menu_item = unit_export_menu.AppendRadioItem(EXPORT_CENTIMETERS, "Centimeters")
        self.Bind(wx.EVT_MENU, self.onSettings, menu_item)
        menu_item = unit_export_menu.AppendRadioItem(EXPORT_INCHES, "Inches")
        self.Bind(wx.EVT_MENU, self.onSettings, menu_item)
        unit_export_menu.Check(global_export_unit, True)
        unit_measure_menu = wx.Menu()
        unit_menu.AppendMenu(43, "Measure Units", unit_measure_menu)
        menu_item = unit_measure_menu.AppendRadioItem(UNIT_CENTIMETERS, "Centimeters")
        self.Bind(wx.EVT_MENU, self.onSettings, menu_item)
        menu_item = unit_measure_menu.AppendRadioItem(UNIT_INCHES, "Inches")
        self.Bind(wx.EVT_MENU, self.onSettings, menu_item)
        unit_measure_menu.Check(global_measure_unit, True)
        
        # Settings Menu - Bones
        # The bone view settings of the mocap studio
        bone_menu = wx.Menu()
        settings_menu.AppendMenu(46, "Bone View", bone_menu)
        menu_item = bone_menu.AppendRadioItem(VIEW_NORMAL, "Normal")
        self.Bind(wx.EVT_MENU, self.onSettings, menu_item)
        menu_item = bone_menu.AppendRadioItem(VIEW_LINES, "Lines")
        self.Bind(wx.EVT_MENU, self.onSettings, menu_item)
        menu_item = bone_menu.AppendRadioItem(VIEW_POINTS, "Points")
        self.Bind(wx.EVT_MENU, self.onSettings, menu_item)
        bone_menu.Check(global_bone_view, True)
        
        # Settings Menu - Pedestrian Tracking
        # Allows the mocap studio to use pedestrian tracking
        position_menu = wx.Menu()
        settings_menu.AppendMenu(50, "Position Settings", position_menu)
        menu_item = position_menu.Append(51, "Pedestrian Settings")
        self.Bind(wx.EVT_MENU, self.onSettings, menu_item)
        menu_item = position_menu.AppendCheckItem(52, "Pedestrian Tracking")
        self.Bind(wx.EVT_MENU, self.onSettings, menu_item)
        position_menu.Check(52, self.is_ped_track)
        
        # Settings Menu - Calibration Timer
        # Puts the calibration process on a timer
        menu_item = settings_menu.AppendCheckItem(53, "Calibration Timer")
        settings_menu.Check(53, global_calibration_timer)
        self.Bind(wx.EVT_MENU, self.onSettings, menu_item)
        
        # Settings Menu - Wireless Retries
        # Allows the user to change the number of system wireless retries
        menu_item = settings_menu.Append(54, "Wireless Retries")
        self.Bind(wx.EVT_MENU, self.onSettings, menu_item)
        
        # Settings Menu - Reset
        # Resets the settings of the mocap studio
        menu_item = settings_menu.Append(55, "Reset Settings")
        self.Bind(wx.EVT_MENU, self.onSettings, menu_item)
        
        # Scripts Menu (ID's 56-60)
        scripts_menu = wx.Menu()
        
        # Scripts Menu - TSH to XML
        # Converts a tsh file to an xml file
        menu_item = scripts_menu.Append(56, "TSH to XML")
        self.Bind(wx.EVT_MENU, self.onScripts, menu_item)
        
        # # Scripts Menu - TSH to CSV
        # # Converts a tsh file to an csv file
        # menu_item = scripts_menu.Append(57, "TSH to CSV")
        # self.Bind(wx.EVT_MENU, self.onScripts, menu_item)
        
        # Scripts Menu - Angle Calculator
        # Calculates angles between bones
        menu_item = scripts_menu.Append(58, "Angle Calculator")
        self.Bind(wx.EVT_MENU, self.onScripts, menu_item)
        
        # Scene & Popup Menu (ID's 61-70 & 96-100)
        self.pop_up = wx.Menu()
        scene_menu = wx.Menu()
        self.pop_up.Bind(wx.EVT_KEY_DOWN, self.onKeyPress)
        
        add_menu = wx.Menu()
        scene_menu.AppendMenu(61, "Add", add_menu)
        self.pop_up.AppendMenu(96, "Add", add_menu)
        menu_item = add_menu.Append(961, "Bone")
        self.Bind(wx.EVT_MENU, self.onAddBone, menu_item)
        menu_item = add_menu.Append(962, "Skeleton")
        self.Bind(wx.EVT_MENU, self.onAddSkeleton, menu_item)
        
        delete_menu = wx.Menu()
        scene_menu.AppendMenu(62, "Delete", delete_menu)
        self.pop_up.AppendMenu(97, "Delete", delete_menu)
        menu_item = delete_menu.Append(971, "Bone")
        self.Bind(wx.EVT_MENU, self.onDeleteBone, menu_item)
        menu_item = delete_menu.Append(972, "Skeleton")
        self.Bind(wx.EVT_MENU, self.onDeleteSkeleton, menu_item)
        
        copy_menu = wx.Menu()
        scene_menu.AppendMenu(63, "Copy", copy_menu)
        self.pop_up.AppendMenu(98, "Copy", copy_menu)
        menu_item = copy_menu.Append(981, "Bone")
        self.Bind(wx.EVT_MENU, self.onCopyBone, menu_item)
        menu_item = copy_menu.Append(982, "Skeleton")
        self.Bind(wx.EVT_MENU, self.onCopySkeleton, menu_item)
        
        menu_item = scene_menu.Append(64, "Reset Position")
        self.Bind(wx.EVT_MENU, self.onSettings, menu_item)
        
        # Menubar
        self.menu_bar = wx.MenuBar()
        self.menu_bar.Append(file_menu, "&File")
        self.menu_bar.Append(scene_menu, "&Scene")
        self.menu_bar.Append(import_menu, "&Import")
        self.menu_bar.Append(export_menu, "&Export")
        self.menu_bar.Append(node_graph_menu, "&Node Graph")
        self.menu_bar.Append(settings_menu, "Se&ttings")
        self.menu_bar.Append(scripts_menu, "S&cripts")
        
        self.SetMenuBar(self.menu_bar)
        
        self.Bind(wx.EVT_MENU_CLOSE, self.onMenuClose)
        
        # Bone List
        self.bone_list = {}
        
        # Skeleton List
        self.skeleton_list = {}
        
        # Device List
        device_list = sc.global_sensor_list.values()
        new_list = []
        for device in device_list:
            new_list.append(device.device_type + "-" + device.serial_number_hex)
        new_list.sort()
        self.live_panel.device_list.SetItems(new_list)
        self.live_panel.onSelectAll(None)
        
        # Output List
        self.output_list = {}
        
        # Show
        self.CenterOnScreen()
        self.Show()
        self.bottom_panel.noShow()
    
    # Frame Bind Functions
    def onAbout(self, event=None):
        about_dialog = ng.CustomAboutDialog(self, -1, "About YEI Mocap Studio", VERSION, (350, 200))
        about_dialog.CenterOnScreen()
        time_interval = self.update_timer.GetInterval()
        self.update_timer.Stop()
        about_dialog.ShowModal()
        self.update_timer.Start(time_interval)
        about_dialog.Destroy()
    
    def onAddBone(self, event=None):
        """ Adds a Bone object to the world.
            
            Args:
                event: A wxPython event.
        """
        count = 0
        tmp_name = "Bone" + str(count)
        # Check and see if there is a bone of that name
        while tmp_name in self.bone_list:
            count += 1
            tmp_name = "Bone" + str(count)
        
        # Calculate position for new bone based on mouse position
        if type(event.GetEventObject()) is wx.Menu:
            new_bone_pos = self.gl_canvas.getMouseInWorld(self.mouse_pos)
        else:
            new_bone_pos = Vector3()
        
        # Add bone to the list of bones
        tmp_bone = anim_utils.Bone(tmp_name, pos=new_bone_pos)
        self.gl_canvas.addMesh(tmp_bone)
        
        # Update ambient color
        tmp_bone.setAmbientColor()
        self.bone_list[tmp_name] = tmp_bone
        tmp_list = self.bone_list.keys()
        tmp_list.sort()
        self.pose_panel.parent_choice_box.SetItems(["None"] + tmp_list)
        self.root_node.appendChild(tmp_bone)
    
    def onAddSkeleton(self, event=None):
        """ Adds a Skeleton object to the world.
            
            Args:
                event: A wxPython event.
        """
        # Calculate position for new skeleton based on mouse position
        if type(event.GetEventObject()) is wx.Menu:
            new_skel_pos = self.gl_canvas.getMouseInWorld(self.mouse_pos)
        else:
            new_skel_pos = Vector3()
        
        if self.onWizard():
            # Update new skeleton's position
            self.root_node.children[-1].setPosition(new_skel_pos)
    
    def onAppClose(self, event=None):
        if not self.has_closed:
            self.Unbind(wx.EVT_TIMER)
            self.update_timer.Stop()
            self.has_closed = True
            if self.is_recording:
                self.recorder.keep_recording = False
            self.node_graph_window.onAppClose(event)
        self.Destroy()
    
    def onCopyBone(self, event=None):
        """ Copies Bone object(s) in the world.
            
            Args:
                event: A wxPython event.
        """
        if self.selected_obj is not None and not self.is_skeleton:
            # Calculate position for new bone based on mouse position
            if type(event.GetEventObject()) is wx.Menu:
                new_bone_pos = self.gl_canvas.getMouseInWorld(self.mouse_pos)
            else:
                new_bone_pos = Vector3()
            
            if not self.is_bone:
                # Remove bones from the bone list and camera
                tmp_list = [b for b in self.selected_obj]
                while len(tmp_list) > 0:
                    bone = anim_utils.findRoot(tmp_list)
                    copy_bones = anim_utils.copyBone(bone, tmp_list, self.bone_list.keys())
                    copy_bones[0].setOffset(new_bone_pos)
                    for b in copy_bones:
                        self.gl_canvas.addMesh(b)
                        
                        self.bone_list[b.getName()] = b
                        if b.parent is None:
                            b.setOffset(b.offset + new_bone_pos)
                            self.root_node.appendChild(b)
            
            else:
                # Reset the GUI modes
                self.resetGUIModes()
                
                if self.pose_panel.sensor_orient_check.IsChecked():
                    self.pose_panel.sensor_orient_check.SetValue(False)
                    self.onSenorCheck(self.pose_panel.sensor_orient_check)
                
                # Get the name and pose of the bone being copied
                self.selected_obj.setAmbientColor()
                name = self.selected_obj.getName() + "_Copy"
                pose = self.selected_obj.getPoseOrientation()
                tmp_len = self.selected_obj.getLength()
                
                # Add bone to the list of bones
                i = 0
                while name in self.bone_list:
                    name = name.rstrip('0123456789')
                    name += str(i)
                    i += 1
                bone = anim_utils.Bone(name, tmp_len, new_bone_pos, pose)
                self.gl_canvas.addMesh(bone)
                
                self.bone_list[name] = bone
                self.root_node.appendChild(bone)
                
                self.is_bone = False
                self.manipulate_bone = ''
                self.pose_panel.disableInput()
            
            self.selected_obj = None
            tmp_list = self.bone_list.keys()
            tmp_list.sort()
            self.pose_panel.parent_choice_box.SetItems(["None"] + tmp_list)
            self.pose_panel.reset()
    
    def onCopySkeleton(self, event=None):
        """ Copies Skeleton object(s) in the world.
            
            Args:
                event: A wxPython event.
        """
        if self.is_skeleton:
            canvas = self.gl_canvas
            # Calculate position for new skeleton based on mouse position
            if type(event.GetEventObject()) is wx.Menu:
                new_skel_pos = self.gl_canvas.getMouseInWorld(self.mouse_pos)
            else:
                new_skel_pos = Vector3()
            
            # Get the name and pose of the skeleton being copied
            self.selected_obj.setAmbientColor()
            skel_name = self.selected_obj.getName() + "_Copy"
            pose = self.selected_obj.getPoseOrientation()
            
            # Check and see if there is a skeleton of that name
            i = 0
            while skel_name in self.skeleton_list:
                skel_name = skel_name.rstrip('0123456789')
                skel_name += str(i)
                i += 1
            
            # Create and build skeleton
            skel = anim_utils.Skeleton(skel_name, pose, new_skel_pos)
            self.selected_obj.buildSkeletonCopy(skel, self.bone_list, canvas)
            
            canvas.addMesh(skel)
            
            self.skeleton_list[skel_name] = skel
            self.root_node.appendChild(skel)
            
            self.is_skeleton = False
            self.selected_obj = None
            tmp_list = self.bone_list.keys()
            tmp_list.sort()
            self.pose_panel.parent_choice_box.SetItems(["None"] + tmp_list)
            self.pose_panel.reset()
            self.pose_panel.disableInput()
    
    def onDeleteBone(self, event=None):
        """ Deletes Bone object(s) from the world.
            
            Args:
                event: A wxPython event.
        """
        if self.selected_obj is not None:
            canvas = self.gl_canvas
            if not self.is_bone:
                # Remove bones from the bone list and camera
                for bone in self.selected_obj:
                    name = bone.getName()
                    bone.delVSNode()
                    del self.bone_list[name]
                    canvas.delMesh(bone.mesh)
                    bone.parent.children.remove(bone)
                    for child in bone.children:
                        self.root_node.appendChild(child)
                        for c in range(len(child.mesh.children) - 1, -1, -1):
                            del child.mesh.children[c]
            else:
                # Reset the GUI modes
                self.resetGUIModes()
                
                if self.pose_panel.sensor_orient_check.IsChecked():
                    self.pose_panel.sensor_orient_check.SetValue(False)
                    self.onSenorCheck(self.pose_panel.sensor_orient_check)
                
                # Remove bone from the bone list and camera
                name = self.selected_obj.getName()
                self.selected_obj.delVSNode()
                del self.bone_list[name]
                canvas.delMesh(self.selected_obj.mesh)
                self.selected_obj.parent.children.remove(self.selected_obj)
                for child in self.selected_obj.children:
                    self.root_node.appendChild(child)
                    for c in range(len(child.mesh.children) - 1, -1, -1):
                        del child.mesh.children[c]
            
            self.is_bone = False
            self.selected_obj = None
            self.manipulate_bone = ''
            self.pose_panel.output_choice_box.SetSelection(0)
            self.pose_panel.name_text.SetValue("Name")
            self.pose_panel.disableInput()
    
    def onDeleteSkeleton(self, event=None):
        """ Deletes Bone object(s) from the world.
            
            Args:
                event: A wxPython event.
        """
        if self.is_skeleton:
            canvas = self.gl_canvas
            # Reset the GUI modes
            self.resetGUIModes()
            
            self.selected_obj.delete(canvas, self.bone_list)
            
            name = self.selected_obj.getName()
            del self.skeleton_list[name]
            
            self.selected_obj = None
            self.is_skeleton = False
            self.pose_panel.reset()
            self.pose_panel.disableInput()
    
    def onExit(self, event=None):
        self.Close(True)  # Close the frame.
    
    def onExport(self, event=None):
        """ Calls an exporter script based on what was selected.
            
            Args:
                event: A wxPython event.
            
            Yields:
                A file with motion capture data in the format selected.
        """
        
        evt_id = event.GetId()
        
        if evt_id == 1601 or evt_id == 1701:
            no_session = False
            file_msg = "Save file as ..."
            file_style = wx.SAVE | wx.CHANGE_DIR | wx.OVERWRITE_PROMPT
            
            if self.recorded_session is None:
                no_session = True
                self.recorded_session = anim_utils.RecordSession("CaptureSession", 0.01666667)
                self.recorded_session.recordSingleFrame(self.bone_list.values())
                for bone in self.bone_list.values():
                    record_bone = anim_utils.BoneState()
                    record_bone.bone_length = bone.getLength()
                    record_bone.pose_orient = bone.getPoseOrientation()
                    if type(bone.parent) is anim_utils.SkelNode:
                        record_bone.parent = None
                    else:
                        record_bone.parent = bone.parent.getName()
                    record_bone.offset = bone.getOffset()
                    
                    if bone.vs_node is not None:
                        record_bone.vs_name = bone.vs_node.name
                    
                    for child in bone.children:
                        record_bone.children.append(child.getName())
                    name = bone.getName()
                    self.recorded_session.recorded_bone_list[name] = record_bone
                
                for child in self.root_node.children:
                    self.recorded_session.root_bone_list.append(child.getName())
            
            file_name = self.recorded_session.name
            if evt_id == 1601: # Export BVH
                wild_card = "BVH files (*.bvh)|*.bvh"
                file_open = wx.FileDialog(self, message=file_msg, defaultDir=_file_path, defaultFile=file_name, wildcard=wild_card, style=file_style)
                
                time_interval = self.update_timer.GetInterval()
                self.update_timer.Stop()
                val = file_open.ShowModal()
                if val == wx.ID_OK:
                    path = file_open.GetPath()
                    ex_bvh.saveBVH(path, self.recorded_session, self.menu_bar.IsChecked(35), self.menu_bar.IsChecked(EXPORT_CENTIMETERS))
                
                self.update_timer.Start(time_interval)
                file_open.Destroy()
            
            elif evt_id == 1701: # Export TSH
                wild_card = "TSH files (*.tsh)|*.tsh"
                file_open = wx.FileDialog(self, message=file_msg, defaultDir=_file_path, defaultFile=file_name, wildcard=wild_card, style=file_style)
                
                time_interval = self.update_timer.GetInterval()
                self.update_timer.Stop()
                val = file_open.ShowModal()
                if val == wx.ID_OK:
                    path = file_open.GetPath()
                    # Get Capture frequency
                    cap_freq = self.recorded_session.capture_rate
                    
                    # Construct TSHSkels
                    skels = []
                    skel_num = 0
                    for r_name in self.recorded_session.root_bone_list:
                        if r_name not in self.recorded_session.recorded_bone_list:
                            skels.append(im_tsh.TSHSkel(r_name))
                            skeleton = self.root_node.getNode(r_name)
                            for child in skeleton.children:
                                self.tshBuildHeiarchy(child.getName(), skels[-1])
                        else:
                            skels.append(im_tsh.TSHSkel("TSHSkel" + str(skel_num)))
                            skel_num += 1
                            self.tshBuildHeiarchy(r_name, skels[-1])
                    for frame in range(len(self.recorded_session.frame_data)):
                        for skel in skels:
                            for bone in skel.bones:
                                b_name = bone.name
                                bone.frames.append(im_tsh.TSHFrame())
                                b_frame = None
                                if self.menu_bar.IsChecked(35):
                                    b_frame = self.recorded_session.interpolateData(b_name, frame)
                                else:
                                    keyframe = self.recorded_session.getKeyframe(b_name, frame)
                                    b_frame = keyframe.start_frame_data
                                
                                bone.frames[-1].orient = b_frame[0]
                                bone.frames[-1].position = b_frame[1]
                                if b_frame[1] is None:
                                    bone.frames[-1].position = Vector3()
                                if global_export_unit == EXPORT_CENTIMETERS:
                                    bone.frames[-1].position *= 2.54
                    
                    # Save
                    ex_tsh.saveTSH(path, cap_freq, skels)
                    
                    # Save XML file
                    nodes = len(base_ng.global_input_nodes)
                    nodes += len(base_ng.global_output_nodes)
                    if nodes > 0:
                        message = ("Do you want to save the Node Graph Configuration?")
                        val = wx.MessageBox(message, "Save", wx.YES_NO)
                        if val == wx.YES:
                            self.node_graph_window.onSave(path[:-4] + ".xml")
                
                self.update_timer.Start(time_interval)
                file_open.Destroy()
            
            if no_session:
                self.recorded_session = None
        elif evt_id == 1602 or evt_id == 1702:
            dir_msg = "Choose a directory:"
            dir_path = _file_path
            dir_open = wx.DirDialog(self, message=dir_msg, defaultPath=dir_path)
            
            time_interval = self.update_timer.GetInterval()
            self.update_timer.Stop()
            val = dir_open.ShowModal()
            if val == wx.ID_OK:
                path = dir_open.GetPath()
                session_name_list = self.session_list.keys()
                dlg = wx.MultiChoiceDialog(self, "Choose what sessions you want to save:", "Save Sessions", session_name_list)
                if dlg.ShowModal() == wx.ID_OK:
                    session_save_list = [session_name_list[i] for i in dlg.GetSelections()]
                    for session_name in session_save_list:
                        file_path = os.path.join(path, session_name)
                        session = self.session_list[session_name]
                        if evt_id == 1602:
                            ex_bvh.saveBVH(file_path + ".bvh", session, self.menu_bar.IsChecked(35), self.menu_bar.IsChecked(EXPORT_CENTIMETERS))
                        elif evt_id == 1702:
                            # Get Capture frequency
                            cap_freq = session.capture_rate
                            
                            # Construct TSHSkels
                            skels = []
                            skel_num = 0
                            for r_name in session.root_bone_list:
                                if r_name not in session.recorded_bone_list:
                                    skels.append(im_tsh.TSHSkel(r_name))
                                    skeleton = self.root_node.getNode(r_name)
                                    for child in skeleton.children:
                                        self.tshBuildHeiarchy(child.getName(), skels[-1])
                                else:
                                    skels.append(im_tsh.TSHSkel("TSHSkel" + str(skel_num)))
                                    skel_num += 1
                                    self.tshBuildHeiarchy(r_name, skels[-1])
                            for frame in range(len(session.frame_data)):
                                for skel in skels:
                                    for bone in skel.bones:
                                        b_name = bone.name
                                        bone.frames.append(im_tsh.TSHFrame())
                                        b_frame = None
                                        if self.menu_bar.IsChecked(35):
                                            b_frame = session.interpolateData(b_name, frame)
                                        else:
                                            keyframe = session.getKeyframe(b_name, frame)
                                            b_frame = keyframe.start_frame_data
                                        
                                        bone.frames[-1].orient = b_frame[0]
                                        bone.frames[-1].position = b_frame[1]
                                        if b_frame[1] is None:
                                            bone.frames[-1].position = Vector3()
                                        if global_export_unit == EXPORT_CENTIMETERS:
                                            bone.frames[-1].position *= 2.54
                            
                            # Save
                            ex_tsh.saveTSH(file_path + ".tsh", cap_freq, skels)
            
            self.update_timer.Start(time_interval)
            dir_open.Destroy()
    
    def onFocus(self, event=None):
        if event.GetActive():
            if sc.global_updated_sensors:
                device_list = sc.global_sensor_list.values()
                new_list = []
                for device in device_list:
                    new_list.append(device.device_type + "-" + device.serial_number_hex)
                new_list.sort()
                self.live_panel.device_list.SetItems(new_list)
                self.live_panel.onSelectAll(event)
            sc.global_updated_sensors = False
            
            self.updateOutputChoice()
            if self.is_bone:
                node = self.selected_obj.vs_node
                if node:
                    name = node.name
                    self.pose_panel.output_choice_box.SetStringSelection(name)
                    if node.getInputDevice() is not None:
                        self.pose_panel.enableSensorCheck()
                    else:
                        self.pose_panel.sensor_orient_check.SetValue(False)
                        self.pose_panel.disableSensorCheck()
                    self.onSenorCheck(self.pose_panel.sensor_orient_check)
        self.is_refresh = True
        
        event.Skip()
    
    def onImport(self, event=None):
        """ Calls an importer script based on what was selected.
            
            Args:
                event: A wxPython event.
            
            Yields:
                A RecordSession that can be played and edited to create another
                session.
        """
        evt_id = event.GetId()
        if evt_id == 6: # Import BVH
            wild_card = "BVH files (*.bvh)|*.bvh"
            file_open = wx.FileDialog(self, message="Choose a *.bvh file", defaultDir=_file_path, wildcard=wild_card, style=wx.OPEN | wx.CHANGE_DIR)
            
            session = None
            time_interval = self.update_timer.GetInterval()
            self.update_timer.Stop()
            val = file_open.ShowModal()
            if val == wx.ID_OK:
                path = file_open.GetPath()
                data = im_bvh.loadBVH(path, self.menu_bar.IsChecked(UNIT_CENTIMETERS))
                name, frame_rate, anim_data, recorded_list, root_list = data
                # Create a session and add it to the session choices
                choice_box = self.right_panel.session_choice_box
                if choice_box.FindString(name) != wx.NOT_FOUND:
                    name += '_'
                    num = 0
                    while choice_box.FindString(name) != wx.NOT_FOUND:
                        name = name.rstrip('0123456789')
                        name += str(num)
                        num += 1
                choice_box.Append(name)
                choice_box.SetSelection(choice_box.GetCount() - 1)
                
                session = anim_utils.RecordSession(name, frame_rate)
                session.createFromBVH(anim_data)
                session.recorded_bone_list = recorded_list
                session.root_bone_list = root_list
                self.session_list[name] = session
                self.live_panel.record_rate.SetValue(int(round(frame_rate ** -1)))
                self.onSessionChoice(event)
            self.update_timer.Start(time_interval)
            
            file_open.Destroy()
        
        elif evt_id == 7: # Import TSH
            wild_card = "TSH files (*.tsh)|*.tsh"
            file_open = wx.FileDialog(self, message = "Choose a *.tsh file", defaultDir=_file_path, wildcard=wild_card, style=wx.OPEN | wx.CHANGE_DIR)
            
            session = None
            time_interval = self.update_timer.GetInterval()
            self.update_timer.Stop()
            val = file_open.ShowModal()
            if val == wx.ID_OK:
                path = file_open.GetPath()
                name, session_info, skeletons = im_tsh.loadTSH(path, self.menu_bar.IsChecked(UNIT_CENTIMETERS))
                print "Loaded TSH File"
                print "Filesize: ", session_info.file_size
                print "TSH Version: %d.%d" % (session_info.num_version, session_info.num_subversion)
                print "Number of Skeletons: ", session_info.num_skeletons
                num_frames = session_info.num_frames
                print "Number of Frames: ", num_frames
                cap_freq = session_info.capture_frequency
                print "Capture Rate: ", cap_freq
                session = anim_utils.RecordSession(name, cap_freq)
                
                is_old = session_info.num_version < 1
                
                # Create keyframe_data
                session.createFromTSH(num_frames, skeletons)
                
                # Create recorded_bone_list and root_bone_list
                for skel in skeletons:
                    skel_name = skel.name
                    for bone in skel.bones:
                        b_name = bone.name
                        par_name = bone.parent_name
                        if not b_name in session.recorded_bone_list:
                            session.recorded_bone_list[b_name] = anim_utils.BoneState()
                        cur_bone_state = session.recorded_bone_list[b_name]
                        
                        if par_name == skel_name or len(par_name) == 0:
                            session.root_bone_list.append(b_name)
                        else:
                            cur_bone_state.parent = par_name
                            if par_name in session.recorded_bone_list:
                                tmp_bone = session.recorded_bone_list[par_name]
                                tmp_bone.children.append(b_name)
                            elif len(skel_name) > 1:
                                pass
                            else:
                                session.recorded_bone_list[par_name] = anim_utils.BoneState()
                                tmp_bone = session.recorded_bone_list[par_name]
                                tmp_bone.children.append(b_name)
                        
                        cur_bone_state.pose_orient = bone.pose_orient
                        cur_bone_state.bone_length = bone.length
                        cur_bone_state.vs_name = bone.vs_name
                        cur_bone_state.offset = bone.offset
                        if is_old:
                            cur_bone_state.vs_pose = bone.vs_pose
                            cur_bone_state.sensor_pose = bone.sensor_pose
                
                # Set up application to use new session
                choice_box = self.right_panel.session_choice_box
                if choice_box.FindString(name) != wx.NOT_FOUND:
                    name += '_0'
                    num = 0
                    while choice_box.FindString(name) != wx.NOT_FOUND:
                        name = name.rstrip('0123456789')
                        name += str(num)
                choice_box.Append(name)
                session.name = name
                self.session_list[name] = session
                
                self.live_panel.record_rate.SetValue(int(round(cap_freq ** -1)))
                choice_box.SetSelection(choice_box.GetCount() - 1)
                
                # Load XML file
                try:
                    tmp_file = open(path[:-4] + ".xml")
                    tmp_file.close()
                    message = "Do you want to load the Node Graph Configuration associated with this file?"
                    val = wx.MessageBox(message, "Load", wx.YES_NO)
                    if val == wx.YES:
                        self.node_graph_window.onLoad(path[:-4] + ".xml")
                        self.updateOutputChoice()
                except:
                    pass
                
                self.onSessionChoice(event)
                
                if is_old:
                    message = "This is an older version of the TSH file.\nPlease re-export the TSH file and the Node Graph XML file to update."
                    val = wx.MessageBox(message, "Warning!!!", wx.OK | wx.ICON_WARNING)
                
            self.update_timer.Start(time_interval)
            
            file_open.Destroy()
    
    def onKeyPress(self, event=None):
        """ Captures input from the keyboard.
            
            Args:
                event: A wxPython event.
        """
        pressed_key = event.GetKeyCode()
        if event.GetEventType() == wx.EVT_KEY_DOWN.typeId:
            canvas = self.gl_canvas
            
            # Key presses for the camera
            if pressed_key == wx.WXK_DOWN:
                canvas.setCameraOrientPos(0.0, 0.0, [0.0, 0.0, 0.0], [0.0, 0.0, -80.0])
            
            elif pressed_key == wx.WXK_UP:
                canvas.setCameraOrientPos(90.0, 0.0, [0.0, 0.0, 0.0], [0.0, 0.0, -80.0])
            
            elif pressed_key == wx.WXK_LEFT:
                canvas.setCameraOrientPos(0.0, 90.0, [0.0, 0.0, 0.0], [0.0, 0.0, -80.0])
            
            elif pressed_key == wx.WXK_RIGHT:
                canvas.setCameraOrientPos(0.0, -90.0, [0.0, 0.0, 0.0], [0.0, 0.0, -80.0])
            
            # Key presses for adding and deleting bones
            elif pressed_key == wx.WXK_SPACE:
                self.PopupMenu(self.pop_up, self.mouse_pos)
            
            # Key presses for selecting multiple bones
            elif pressed_key == wx.WXK_SHIFT:
                self.is_multi_sel = True
            
            # Key presses for resetting the position of skeletons
            elif pressed_key == wx.WXK_HOME:
                for skel in self.skeleton_list.values():
                    skel.resetPedTracking()
            
            elif self.recorded_session is None:
                check = self.pose_panel.sensor_orient_check
                # Key presses for changing the mode
                if pressed_key == ord('T'):  # Translate Mode
                    self.manipulate_bone = ''
                    
                    # Reset the GUI modes
                    self.resetGUIModes(check.IsChecked())
                    
                    if self.is_bone:
                        self.is_translate_mode = True
                        canvas.mask ^= gl_sg.DRAW_GUI_TRANS
                        canvas.mask &= ~gl_sg.DRAW_SENSOR
                
                elif pressed_key == ord('R'):  # Rotate Mode
                    self.manipulate_bone = ''
                    
                    # Reset the GUI modes
                    self.resetGUIModes(check.IsChecked())
                    
                    if self.is_bone:
                        self.is_rotate_mode = True
                        canvas.mask ^= gl_sg.DRAW_GUI_ROT
                        canvas.mask &= ~gl_sg.DRAW_SENSOR
                
                elif pressed_key == ord('F'):  # Free Translate Mode
                    self.manipulate_bone = ''
                    
                    # Reset the GUI modes
                    self.resetGUIModes(check.IsChecked())
                    
                    if self.is_bone:
                        self.is_free_mode = True
                        canvas.mask &= ~gl_sg.DRAW_SENSOR
        
        else:
            # Key releases for selecting multiple bones
            if pressed_key == wx.WXK_SHIFT:
                self.is_multi_sel = False
    
    def onMenuClose(self, event=None):
        self.is_refresh = True
        event.Skip()
    
    def onNodeGraphClose(self, event=None):
        self.node_graph_window.Show(False)
    
    def onNodeGraphOpen(self, event=None):
        self.node_graph_window.Show()
        self.node_graph_window.SetFocus()
        if not self.node_graph_window.IsActive():
            self.node_graph_window.Restore()
        self.node_graph_window.side_panel.updatePanel()
    
    def onScripts(self, event=None):
        """ Allows user to change the settings of the Mocap Studio.
            
            Args:
                event: A wxPython event.
        """
        
        evt_id = event.GetId()
        
        time_interval = self.update_timer.GetInterval()
        self.update_timer.Stop()
        
        if evt_id == 56: # TSH to XML
            wild_card = "TSH files (*.tsh)|*.tsh"
            file_open = wx.FileDialog(self, message="Choose a *.tsh file", defaultDir=_file_path, wildcard=wild_card, style=wx.OPEN | wx.CHANGE_DIR)
            
            val = file_open.ShowModal()
            if val == wx.ID_OK:
                path = file_open.GetPaths()[0]
                tsh_to_xml.exportAsXML(path,
                    self.menu_bar.IsChecked(EXPORT_CENTIMETERS))
            
            file_open.Destroy()
        
        elif evt_id == 58: # Angle Calculator
            skel_name = self.skeleton_list.keys()[0]
            ang_calc = AngleCalculator(self, skel_name, self.is_stream)
            val = ang_calc.ShowModal()
            ang_calc.update_timer.Stop()
            if val == wx.ID_OK:
                if len(ang_calc.log_list) > 0:
                    self.is_logging = True
                    if self.logging_window is not None:
                        self.logging_window.Destroy()
                    self.logging_window = ang_calc
            else:
                ang_calc.Destroy()
        
        self.update_timer.Start(time_interval)
    
    def onSetMode(self, event=None):
        """ Sets what mode the Mocap Studio is in.
            
            Args:
                event: A wxPython event.
        """
        self.is_live_mode = not self.is_live_mode
        if self.is_live_mode:
            self.SetTitle("YEI Mocap - Live Mode")
            if self.recorded_session is not None:
                self.bottom_panel.showPlay()
                self.live_panel.enablePlay()
                self.live_panel.disableRecord()
                self.live_panel.disableStream()
                self.live_panel.disableSelect()
            else:
                self.bottom_panel.showRecord()
                self.live_panel.disablePlay()
                self.live_panel.disableRecord()
                self.live_panel.enableStream()
                self.live_panel.enableSelect()
            
            self.toggleBoneMenus(False)
            
            # Reset the GUI modes
            self.resetGUIModes()
            
            if self.pose_panel.sensor_orient_check.IsChecked():
                self.pose_panel.sensor_orient_check.SetValue(False)
                self.onSenorCheck(self.pose_panel.sensor_orient_check)
            
            if self.selected_obj is not None:
                if type(self.selected_obj) is set:
                    for b in self.selected_obj:
                        b.setAmbientColor()
                else:
                    self.selected_obj.setAmbientColor()
                    if self.is_skeleton:
                        self.is_skeleton = False
                    if self.is_bone:
                        self.is_bone = False
                        tmp_list = self.bone_list.keys()
                        tmp_list.sort()
                        self.pose_panel.parent_choice_box.SetItems(["None"] + tmp_list)
                self.pose_panel.reset()
                self.pose_panel.disableInput()
                self.selected_obj = None
        
        else:
            self.SetTitle("YEI Mocap - Pose Mode")
            self.bottom_panel.noShow()
            if self.recorded_session is None:
                for bone in self.bone_list.values():
                    bone.setOrientation(Matrix4())
            if self.is_playing:
                self.onPlayButton(None)
            elif self.is_recording:
                self.onRecordButton(None)
            elif self.is_stream:
                self.onStreamButton(None)
            
            self.toggleBoneMenus(True)
            
        self.bottom_panel.SendSizeEvent()
    
    def onSettings(self, event=None):
        """ Allows user to change the settings of the Mocap Studio.
            
            Args:
                event: A wxPython event.
        """
        global global_draw_logo, global_export_interp, global_interp_method
        global global_export_unit, global_measure_unit, global_bone_view
        global global_calibration_timer
        
        evt_id = event.GetId()
        
        time_interval = self.update_timer.GetInterval()
        self.update_timer.Stop()
        
        if evt_id > 43 and not self.is_live_mode:
            # Reset the GUI modes
            self.resetGUIModes()
            
            if self.pose_panel.sensor_orient_check.IsChecked():
                self.pose_panel.sensor_orient_check.SetValue(False)
                self.onSenorCheck(self.pose_panel.sensor_orient_check)
            
            if self.selected_obj is not None:
                if type(self.selected_obj) is set:
                    for b in self.selected_obj:
                        b.setAmbientColor()
                else:
                    self.selected_obj.setAmbientColor()
                    if self.is_skeleton:
                        self.is_skeleton = False
                    if self.is_bone:
                        self.is_bone = False
                        tmp_list = self.bone_list.keys()
                        tmp_list.sort()
                        self.pose_panel.parent_choice_box.SetItems(["None"] + tmp_list)
                self.pose_panel.reset()
                self.pose_panel.disableInput()
                self.selected_obj = None
        
        if evt_id == 31:
            head_color = [i * 255 for i in gl_sg.global_head_color]
            tail_color = [i * 255 for i in gl_sg.global_tail_color]
            grid_color = [i * 255 for i in gl_sg.global_grid_color]
            bg_color1 = [i * 255 for i in gl_sg.global_bg_color1]
            bg_color2 = [i * 255 for i in gl_sg.global_bg_color2]
            
            color_list = [head_color, tail_color, grid_color, bg_color1, bg_color2]
            color_menu = ColorSettings(self, color_list)
            
            start_stream = False
            if self.is_stream:
                self.onStreamButton(event)
                start_stream = True
            val = color_menu.ShowModal()
            
            if val == wx.ID_OK:
                head_color = color_menu.bone_head_color.GetColour()
                tail_color = color_menu.bone_tail_color.GetColour()
                grid_color = color_menu.grid_color.GetColour()
                gl_sg.global_grid_alpha = color_menu.grid_alpha.GetValue() / (color_menu.grid_alpha.GetMax() * 1.0)
                bg_color1 = color_menu.bg_color1.GetColour()
                bg_color2 = color_menu.bg_color2.GetColour()
                if color_menu.horizontal_style.GetValue():
                    gl_sg.global_bg_style = gl_sg.HORIZONTAL
                else:
                    gl_sg.global_bg_style = gl_sg.VERTICAL
                
                gl_sg.global_head_color = [i / 255.0 for i in head_color]
                gl_sg.global_tail_color = [i / 255.0 for i in tail_color]
                gl_sg.global_grid_color = [i / 255.0 for i in grid_color]
                gl_sg.global_bg_color1 = [i / 255.0 for i in bg_color1]
                gl_sg.global_bg_color2 = [i / 255.0 for i in bg_color2]
            
            color_menu.Destroy()
            
            if start_stream:
                self.onStreamButton(event)
        
        elif evt_id == 32:
            global_draw_logo = not global_draw_logo
            self.gl_canvas.logo_node.do_draw = global_draw_logo
        
        elif evt_id == 33:
            sc.global_check_unknown = not sc.global_check_unknown
        
        elif evt_id == 35:
            global_export_interp = not global_export_interp
        
        elif evt_id == SLERP:
            global_interp_method = SLERP
        
        elif evt_id == SQUAD:
            global_interp_method = SQUAD
        
        elif evt_id == EXPORT_CENTIMETERS:
            global_export_unit = EXPORT_CENTIMETERS
        
        elif evt_id == EXPORT_INCHES:
            global_export_unit = EXPORT_INCHES
        
        elif evt_id == UNIT_CENTIMETERS:
            global_measure_unit = UNIT_CENTIMETERS
        
        elif evt_id == UNIT_INCHES:
            global_measure_unit = UNIT_INCHES
        
        elif evt_id == VIEW_NORMAL:
            global_bone_view = VIEW_NORMAL
            for bone in self.bone_list.values():
                bone.mesh.draw_method = gl_sg.NORMAL_DRAW
        
        elif evt_id == VIEW_LINES:
            global_bone_view = VIEW_LINES
            for bone in self.bone_list.values():
                bone.mesh.draw_method = gl_sg.LINES_DRAW
        
        elif evt_id == VIEW_POINTS:
            global_bone_view = VIEW_POINTS
            for bone in self.bone_list.values():
                bone.mesh.draw_method = gl_sg.POINTS_DRAW
        
        elif evt_id == 51:
            skel_list = self.skeleton_list.keys()
            
            bone_list = self.bone_list.keys()
            
            skel_list.sort()
            skel_list.insert(0, 'None')
            bone_list.sort()
            bone_list.insert(0, 'None')
            
            dlg = SkeletonBoneChooser(self, skel_list, bone_list)
            
            dlg.ShowModal()
        
        elif evt_id == 52:
            if len(self.skeleton_list) == 0:
                message = "There must be a skeleton created for pedestrian tracking to work."
                caption = "Pedestrian Tracking Requirements"
                wx.MessageBox(message, caption, wx.OK)
                
                self.menu_bar.Check(evt_id, False)
                
                self.update_timer.Start(time_interval)
                    
                # Refresh the glcanvas
                self.gl_canvas.Refresh()
                return
            error_text = (
                "All skeletons must have their hip, left foot, and right foot bones set from the Pedestrian Settings window.\n\n"
                "Pedestrian tracking will not work if this is not done.\n\n"
                "These Skeletons do not meet the requirements:"
            )
            is_error = False
            for skel in self.skeleton_list.values():
                h_bone = skel.getHipBone()
                lf_bone = skel.getFootBoneLeft()
                rf_bone = skel.getFootBoneRight()
                if h_bone is None or lf_bone is None or rf_bone is None:
                    if not is_error:
                        is_error = True
                    error_text += "\n\t" + skel.getName()
                else:
                    skel.setFootPosLeft(lf_bone.getPosition())
                    skel.setFootPosRight(rf_bone.getPosition())
            
            if is_error:
                caption = "Pedestrian Tracking Requirements"
                wx.MessageBox(error_text, caption, wx.OK | wx.ICON_ERROR)
                
                self.menu_bar.Check(evt_id, False)
                
                self.update_timer.Start(time_interval)
                    
                # Refresh the glcanvas
                self.gl_canvas.Refresh()
                return
            
            self.is_ped_track = not self.is_ped_track
            if self.is_ped_track:
                message = "Please note that at least one foot needs to be touching the ground."
                caption = "Pedestrian Tracking Limitations"
                wx.MessageBox(message, caption, wx.OK)
        
        elif evt_id == 53:
            global_calibration_timer = not global_calibration_timer
        
        elif evt_id == 54:
            timer_dlg = wx.TextEntryDialog(self, "Number of retries:", "Wireless Retries", str(sc.getWirelessRetries()), style=wx.OK)
            if timer_dlg.ShowModal() == wx.ID_OK:
                try:
                    sc.setWirelessRetries(int(timer_dlg.GetValue()))
                except:
                    pass
        
        elif evt_id == 55:
            self.menu_bar.Check(32, True)
            global_draw_logo = True
            self.gl_canvas.logo_node.do_draw = global_draw_logo
            self.menu_bar.Check(33, True)
            self.menu_bar.Check(35, True)
            global_export_interp = True
            self.menu_bar.Check(SLERP, True)
            global_interp_method = SLERP
            self.menu_bar.Check(EXPORT_CENTIMETERS, True)
            global_export_unit = EXPORT_CENTIMETERS
            self.menu_bar.Check(UNIT_CENTIMETERS, True)
            global_measure_unit = UNIT_CENTIMETERS
            sc.global_check_unknown = True
            gl_sg.global_head_color = [0, 0.7, 0.7]
            gl_sg.global_tail_color = [0.95, 0.45, 0]
            gl_sg.global_bg_color1 = [0.5, 0.5, 1.0]
            gl_sg.global_bg_color2 = [0.1, 0.1, 0.1]
            gl_sg.global_bg_style = gl_sg.HORIZONTAL
            gl_sg.global_grid_color = [1, 1, 1]
            gl_sg.global_grid_alpha = 0.5
            self.menu_bar.Check(52, False)
            self.is_ped_track = False
        
        elif evt_id == 64:
            for skel in self.skeleton_list.values():
                skel.resetPedTracking()
        
        self.update_timer.Start(time_interval)
            
        # Refresh the glcanvas
        self.gl_canvas.Refresh()
    
    def onSkeletonBoneChooserButton(self, event=None):
        evt_id = event.GetId()
        if evt_id == wx.ID_APPLY:
            dlg = event.GetEventObject().GetParent()
            skel_name = dlg.skeleton_choice_box.GetStringSelection()
            skeleton = None
            if skel_name in self.skeleton_list:
                skeleton = self.skeleton_list[skel_name]
            
            if skeleton is not None:
                hip_name = dlg.hip_choice_box.GetStringSelection()
                l_foot_name = dlg.l_foot_choice_box.GetStringSelection()
                r_foot_name = dlg.r_foot_choice_box.GetStringSelection()
                if hip_name in self.bone_list:
                    skeleton.setHipBone(self.bone_list[hip_name])
                if l_foot_name in self.bone_list:
                    skeleton.setFootBoneLeft(self.bone_list[l_foot_name])
                if r_foot_name in self.bone_list:
                    skeleton.setFootBoneRight(self.bone_list[r_foot_name])
                
                dlg.FindWindowById(wx.ID_OK).Enable()
        
        event.Skip()
    
    def onTimeUpdate(self, event=None):
        """ Updates the SensorCanvas object and Bone objects.
            
            Args:
                event: A wxPython event.
        """
        canvas = self.gl_canvas
        if self.is_redraw:
            w, h = canvas.size
            self.right_panel.notebook.SetSize((-1, h - 118))
            self.live_panel.device_list.SetSize((150, h - 325))
            self.is_redraw = False
        if self.is_live_mode:
            for skel in self.skeleton_list.values():
                skel.resetLowestPoint()
            if self.recorded_session is not None:
                frame = self.bottom_panel.cur_frame
                # Set the Position/Orientation of each Bone based on the current
                # frame of the session
                session_data = {}
                if self.live_panel.do_interpolation.GetValue():
                    # Interpolate the frame's keyframes using slerp
                    for b_name in self.recorded_session.frame_data[frame]:
                        keyframe = self.recorded_session.getKeyframe(b_name, frame)
                        session_data[b_name] = self.recorded_session.interpolateData(b_name, frame)
                else:
                    # Just get the raw data
                    for b_name in self.recorded_session.frame_data[frame]:
                        keyframe = self.recorded_session.getKeyframe(b_name, frame)
                        session_data[b_name] = keyframe.start_frame_data
                
                self.root_node.update(frame_data=session_data)
                # Check if we are playing a session
                if self.is_playing:
                    elapsed_time = time.clock() - self.start_time_play
                    if elapsed_time >= self.play_rate:
                        frame += int(round((elapsed_time / self.play_rate) - (elapsed_time - self.play_rate)))
                        self.start_time_play = time.clock()
                    if frame >= self.bottom_panel.num_frames:
                        frame = 0
                        self.start_time_play = time.clock()
                else:
                    frame = self.bottom_panel.frame_slider.GetValue()
                # Update Frame Slider
                self.bottom_panel.updatePlay(frame)
            
            elif self.is_recording:
                base_ng.refreshOutputsRec()
                
                self.root_node.update(self.is_stream)
                if self.is_ped_track:
                    for skel in self.skeleton_list.values():
                        skel.pedTrack()
                
                elapsed_time = time.clock() - self.start_time_record
                self.recorded_frames = int(round(elapsed_time / self.recording_rate))
                
                # Update the Bottom Panel
                self.bottom_panel.updateRecord(elapsed_time, self.recorded_frames)
            
            else:
                self.root_node.update(self.is_stream)
                if self.is_ped_track:
                    for skel in self.skeleton_list.values():
                        skel.pedTrack()
        
        else:
            self.root_node.update()
        
        # Check what mode we are currently in
        if self.is_bone and self.recorded_session is None:
            bone = self.selected_obj
            if self.is_rotate_mode:
                canvas.rotate_mesh.position = bone.getPosition().asArray()
                canvas.rotate_mesh.orientation = bone.getPoseOrientation().asColArray()
                
            elif self.is_translate_mode:
                canvas.translate_mesh.position = bone.getPosition().asArray()
                canvas.translate_mesh.orientation = bone.getPoseOrientation().asColArray()
                if type(bone.parent) is anim_utils.Bone:
                    tmp_par = bone.parent
                    canvas.translate_mesh.parent_orient = tmp_par.getPoseOrientation().asColArray()
                else:
                    canvas.translate_mesh.parent_orient = Matrix4().asColArray()
            
            else:
                if bone.vs_node is not None:
                    if self.pose_panel.sensor_orient_check.IsChecked():
                        canvas.setSensorMeshOrientPos(bone)
        
        # Refresh the glcanvas
        canvas.Refresh()
        
        event.Skip()
    
    def onWinSize(self, event=None):
        self.is_redraw = True
        event.Skip()
    
    def onWizard(self, event=None):
        wiz_win = SkeletonWizard(self, -1)
        wiz_win.CenterOnScreen()
        node_list = self.output_list.keys()
        node_list.sort()
        wiz_win.initNamesOutputs(node_list)
        time_interval = self.update_timer.GetInterval()
        self.update_timer.Stop()
        val = False
        if wiz_win.RunWizard(wiz_win.first_page):
            val = True
            # If a bone was selected need to add it back to right_panel parent
            # list
            if self.selected_obj is not None:
                if self.is_bone:
                    self.is_bone = False
                    self.manipulate_bone = ''
                    self.selected_obj.setAmbientColor()
                    self.pose_panel.reset()
                    self.pose_panel.disableInput()
                    if self.pose_panel.sensor_orient_check.IsChecked():
                        self.pose_panel.sensor_orient_check.SetValue(False)
                        self.onSenorCheck(self.pose_panel.sensor_orient_check)
                elif self.is_skeleton:
                    self.is_skeleton = False
                    self.selected_obj.setAmbientColor()
                    self.pose_panel.reset()
                    self.pose_panel.disableInput()
                else:
                    for b in self.selected_obj:
                        b.setAmbientColor()
                
                self.selected_obj = None
            
            
            # Reset the GUI modes
            self.resetGUIModes()
            
            canvas = self.gl_canvas
            
            if wiz_win.replace_check.IsChecked():
                # Copy old bones virtual sensor properties
                old_dic = {}
                has_vs_nodes = False
                for b in self.bone_list:
                    bone = self.bone_list[b]
                    vs_name = ""
                    if bone.vs_node is not None:
                        has_vs_nodes = True
                        vs_name = bone.vs_node.name
                    old_dic[b] = vs_name
                
                # Clear the lists of bones and skeletons
                self.bone_list.clear()
                self.skeleton_list.clear()
                self.root_node.children = []
                
                # Reset Mocap Studio draw settings
                canvas.resetMeshSettings()
            
            # Check and see if there is a skeleton of that name
            i = 0
            skel_name = "Skeleton"
            while skel_name in self.skeleton_list:
                skel_name = skel_name.rstrip('0123456789')
                skel_name += str(i)
                i += 1
            
            skel = anim_utils.Skeleton(skel_name)
            canvas.addMesh(skel)
            
            self.skeleton_list[skel_name] = skel
            self.root_node.appendChild(skel)
            
            bone_properties = wiz_win.getNamesOutputs(self.output_list)
            
            height = wiz_win.height.GetValue()
            if wiz_win.centimeter_radio.GetValue():
                height /= 2.54
            if wiz_win.male_radio.GetValue():
                for b_name in anim_utils.MALE_BONE_RATIOS:
                    skel.buildSkeleton(b_name, height, anim_utils.MALE_BONE_RATIOS, self.bone_list, canvas, bone_properties)
            else:
                for b_name in anim_utils.FEMALE_BONE_RATIOS:
                    skel.buildSkeleton(b_name, height, anim_utils.FEMALE_BONE_RATIOS, self.bone_list, canvas, bone_properties)
            
            if wiz_win.replace_check.IsChecked():
                # Reassign virtual sensor properties if possible
                bad_bones = []
                for b in self.bone_list:
                    bone = self.bone_list[b]
                    if b in old_dic:
                        vs_name = old_dic[b]
                        if vs_name in self.output_list:
                            bone.addVSNode(self.output_list[vs_name])
                    elif has_vs_nodes:
                        bad_bones.append(bone)
                
                # Create a Dialog window to tell user of vs nodes and chose
                # nodes
                if len(bad_bones) > 0:
                    message = (
                        "Some bones failed to be paired with the sensors\n"
                        "in the Node Graph Window. These bones are:\n"
                    )
                    for b in bad_bones:
                        message += "\t" + b.getName() + "\n"
                    message += (
                        "\nFor each of these bones, select and choose the\n"
                        "appropriate output node from the Output Node\n"
                        "list in the Pose tab and set the Sensor Pose\n"
                        "Orientation to match the orientation the sensor\n"
                        "is in on the actor."
                    )
                    
                    caption = "Failed Sensor Pairing"
                    
                    val = wx.MessageBox(message, caption, wx.OK)
            
            tmp_list = self.bone_list.keys()
            tmp_list.sort()
            self.pose_panel.parent_choice_box.SetItems(['None'] + tmp_list)
            self.pose_panel.parent_choice_box.SetSelection(0)
            
            self.root_node.update()
            
            # Offset for lowest point
            skel.resetLowestPoint()
            skel.lowestPointOffest()
        
        self.update_timer.Start(time_interval)
        
        wiz_win.Destroy()
        return val
    
    # Canvas Bind Functions
    def onGLLeftClick(self, event=None):
        """ Captures when the left mouse button is pressed.
            
            Used for selecting Bone objects.
            
            Args:
                event: A wxPython event.
        """
        canvas = self.gl_canvas
        selected_list = []
        self.CaptureMouse()
        self.cur_mx, self.cur_my = event.GetPosition()
        canvas.SetFocus()
        if not self.is_live_mode:
            global_draw_lock.acquire()
            selected_list = canvas.selectGL(self.cur_mx, self.cur_my)
            global_draw_lock.release()
            
            if self.selected_obj is not None:
                if type(self.selected_obj) is set:
                    for bone in self.selected_obj:
                        bone.setAmbientColor()
                else:
                    self.selected_obj.setAmbientColor()
        
        if len(selected_list) > 0:
            self.is_bone = type(self.selected_obj) is anim_utils.Bone
            
            # Add old removed name back to list
            if self.is_bone:
                tmp_list = self.bone_list.keys()
                tmp_list.sort()
                self.pose_panel.parent_choice_box.SetItems(["None"] + tmp_list)
                self.pose_panel.parent_choice_box.SetSelection(0)
            
            # Update Interface boxes
            for sel in selected_list:
                if type(sel) is anim_utils.Bone:
                    if self.is_multi_sel and self.selected_obj is not None:
                        if self.is_skeleton:
                            self.pose_panel.reset()
                            self.pose_panel.disableInput()
                            self.ReleaseMouse()
                            return
                        elif self.is_bone:
                            self.manipulate_bone = ''
                            self.pose_panel.reset()
                            self.pose_panel.disableInput()
                            
                            # Reset the GUI modes
                            self.resetGUIModes()
                            
                            tmp_bone = self.selected_obj
                            self.selected_obj = set([])
                            self.selected_obj.add(tmp_bone)
                            self.is_bone = False
                        self.selected_obj.add(sel)
                        for bone in self.selected_obj:
                            bone.setAmbientColor(anim_utils.BONE_SELECT)
                        self.ReleaseMouse()
                        return
                    else:
                        self.selected_obj = sel
                        self.manipulate_bone = ''
                        self.is_bone = True
                        self.is_skeleton = False
                    break
                elif type(sel) is anim_utils.Skeleton:
                    # Reset the GUI modes
                    self.resetGUIModes()
                    
                    self.selected_obj = sel
                    self.manipulate_bone = ''
                    self.is_bone = False
                    self.is_skeleton = True
                    break
                
                else:
                    self.manipulate_bone = sel
                    break
            
            if self.is_bone:
                self.pose_panel.setBoneProperties(self)
            elif self.is_skeleton:
                self.pose_panel.setSkeletonProperties(self)
        
        else:
            # Reset select settings
            self.is_bone = False
            self.is_skeleton = False
            self.manipulate_bone = ''
            self.selected_obj = None
            
            # Reset pose panel
            tmp_list = self.bone_list.keys()
            tmp_list.sort()
            self.pose_panel.parent_choice_box.SetItems(["None"] + tmp_list)
            self.pose_panel.sensor_orient_check.SetValue(False)
            self.onSenorCheck(self.pose_panel.sensor_orient_check)
            self.pose_panel.reset()
            self.pose_panel.disableInput()
            
            # Reset the GUI modes
            self.resetGUIModes()
        
        self.ReleaseMouse()
    
    def onGLRightClick(self, event=None):
        """ Captures when the right mouse button is pressed.
            
            Used for when rotating the world.
            
            Args:
                event: A wxPython event.
        """
        canvas = self.gl_canvas
        self.CaptureMouse()
        canvas.x, canvas.y = event.GetPosition()
        canvas.SetFocus()
        canvas.x_last = canvas.x
        canvas.y_last = canvas.y
        self.ReleaseMouse()
        
        # This is used for fixing some GLCanvas bug that causes it not to
        # refresh properly
        if self.is_refresh:
            x, y = self.GetPositionTuple()
            self.MoveXY(x - 1, y)
            self.MoveXY(x, y)
            self.is_refresh = False
    
    def onGLMiddleClick(self, event=None):
        """ Captures when the middle mouse button is pressed.
            
            Used for when translating the world.
            
            Args:
                event: A wxPython event.
        """
        canvas = self.gl_canvas
        self.CaptureMouse()
        canvas.x_trans, canvas.y_trans = event.GetPosition()
        canvas.SetFocus()
        canvas.x_trans_last = canvas.x_trans
        canvas.y_trans_last = canvas.y_trans
        self.ReleaseMouse()
        
        # This is used for fixing some GLCanvas bug that causes it not to
        # refresh properly
        if self.is_refresh:
            x, y = self.GetPositionTuple()
            self.MoveXY(x - 1, y)
            self.MoveXY(x, y)
            self.is_refresh = False
    
    def onGLMouseMotion(self, event=None):
        """ Captures the movement of the mouse.
            
            Args:
                event: A wxPython event.
        """
        
        # Check if an object is selected
        self.mouse_pos = event.GetPosition()
        if event.Dragging():
            left_down = event.LeftIsDown()
            right_down = event.RightIsDown()
            middle_down = event.MiddleIsDown()
            if left_down and not right_down and not middle_down:
                if self.is_bone:
                    global_draw_lock.acquire()
                    
                    self.gl_canvas.SetCurrent()
                    # Get Screen Position and Width and Height
                    self.old_mx, self.old_my = self.cur_mx, self.cur_my
                    self.cur_mx, self.cur_my = event.GetPosition()
                    width, height = self.gl_canvas.size
                    
                    global_draw_lock.release()
                    
                    bone = self.selected_obj
                    is_par_root = type(bone.parent) is anim_utils.SkelNode
                    
                    # Check what mode we are in and preform actions accordingly
                    if self.is_free_mode:
                        # Calculate new position for bone based on mouse
                        # position
                        bone_new_pos = self.gl_canvas.getMouseInWorld(self.mouse_pos)
                        
                        # Place the bone at our new position
                        if is_par_root:
                            if global_measure_unit == UNIT_CENTIMETERS:
                                bone_new_pos *= 2.54
                            x_pos, y_pos, z_pos = bone_new_pos.asArray()
                        else:
                            par_pos = bone.parent.getPosition()
                            pos = bone_new_pos - par_pos
                            if global_measure_unit == UNIT_CENTIMETERS:
                                pos *= 2.54
                            x_pos, y_pos, z_pos = pos.asArray()
                        
                        # Update the right panel
                        self.pose_panel.x_set_pos.SetValue(x_pos)
                        self.pose_panel.y_set_pos.SetValue(y_pos)
                        self.pose_panel.z_set_pos.SetValue(z_pos)
                        self.onOffset(event)
                    else:
                        # Get some needed Bone properties
                        bone_pos = bone.getPosition()
                        bone_pose = bone.getPoseOrientation()
                        if not is_par_root:
                            par_pos = bone.parent.getPosition()
                        
                        new_pos = (self.cur_mx, self.cur_my)
                        old_pos = (self.old_mx, self.old_my)
                        
                        cam_mat = -self.gl_canvas.getCameraMat()
                        cam_pos = self.gl_canvas.getCameraPos(cam_mat)
                        cam_look = self.gl_canvas.getCameraLook(cam_mat, cam_pos, bone_pos)
                        cam_offset = self.gl_canvas.getCameraOffset(cam_look, cam_pos, bone_pos)
                        plane_norm = (-cam_look).normalizeCopy()
                        
                        
                        # Calculate a new_ray and old_ray from camera
                        new_ray = self.gl_canvas.getMouseRay(cam_mat, new_pos)
                        old_ray = self.gl_canvas.getMouseRay(cam_mat, old_pos)
                        
                        # Orthogonal vectors
                        x_vec = Vector3(UNIT_X)
                        y_vec = Vector3(UNIT_Y)
                        z_vec = Vector3(UNIT_Z)
                        
                        
                        # Calculate a plane towards the camera based on axis to
                        # be manipulated, create two rays from the camera to
                        # that plane calculate our difference from the rays and
                        # change bone according to the mode
                        if self.manipulate_bone == 'scale':
                            y_vec = (bone_pose * y_vec).normalizeCopy()
                            tmp_vec = plane_norm.cross(y_vec).normalizeCopy()
                            plane_norm = y_vec.cross(tmp_vec).normalizeCopy()
                            
                            new_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(new_ray)
                            old_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(old_ray)
                            
                            if new_scale > 0.0 and old_scale > 0.0:
                                new_project_pos = cam_offset + (new_ray * new_scale)
                                old_project_pos = cam_offset + (old_ray * old_scale)
                                tmp_vec = new_project_pos - old_project_pos
                                new_len = tmp_vec.dot(y_vec) + bone.length
                                if global_measure_unit == UNIT_CENTIMETERS:
                                    new_len *= 2.54
                                self.pose_panel.set_bone_length.SetValue(new_len)
                                self.onBonelength(event)
                        
                        elif self.is_translate_mode:
                            if self.manipulate_bone == 'x_trans':
                                x_vec = (bone_pose * x_vec).normalizeCopy()
                                tmp_vec = plane_norm.cross(x_vec).normalizeCopy()
                                plane_norm = x_vec.cross(tmp_vec).normalizeCopy()
                                
                                new_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(new_ray)
                                old_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(old_ray)
                                
                                if new_scale > 0.0 and old_scale > 0.0:
                                    new_project_pos = cam_offset + (new_ray * new_scale)
                                    old_project_pos = cam_offset + (old_ray * old_scale)
                                    if not is_par_root:
                                        new_project_pos = new_project_pos - par_pos
                                        old_project_pos = old_project_pos - par_pos
                                    
                                    tmp_vec = new_project_pos - old_project_pos
                                    trans_vec = x_vec * tmp_vec.dot(x_vec)
                                    bone.translate(trans_vec)
                            
                            elif self.manipulate_bone == 'y_trans':
                                y_vec = (bone_pose * y_vec).normalizeCopy()
                                tmp_vec = plane_norm.cross(y_vec).normalizeCopy()
                                plane_norm = y_vec.cross(tmp_vec).normalizeCopy()
                                
                                new_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(new_ray)
                                old_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(old_ray)
                                
                                if new_scale > 0.0 and old_scale > 0.0:
                                    new_project_pos = cam_offset + (new_ray * new_scale)
                                    old_project_pos = cam_offset + (old_ray *old_scale)
                                    
                                    if not is_par_root:
                                        new_project_pos = new_project_pos - par_pos
                                        old_project_pos = old_project_pos - par_pos
                                    
                                    tmp_vec = new_project_pos - old_project_pos
                                    trans_vec = y_vec * tmp_vec.dot(y_vec)
                                    bone.translate(trans_vec)
                            
                            elif self.manipulate_bone == 'z_trans':
                                z_vec = (bone_pose * z_vec).normalizeCopy()
                                tmp_vec = plane_norm.cross(z_vec).normalizeCopy()
                                plane_norm = z_vec.cross(tmp_vec).normalizeCopy()
                                
                                new_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(new_ray)
                                old_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(old_ray)
                                
                                if new_scale > 0.0 and old_scale > 0.0:
                                    new_project_pos = cam_offset + (new_ray * new_scale)
                                    old_project_pos = cam_offset + (old_ray * old_scale)
                                    
                                    if not is_par_root:
                                        new_project_pos = new_project_pos - par_pos
                                        old_project_pos = old_project_pos - par_pos
                                    
                                    tmp_vec = new_project_pos - old_project_pos
                                    trans_vec = z_vec * tmp_vec.dot(z_vec)
                                    bone.translate(trans_vec)
                            
                            elif not is_par_root:
                                par_pose = bone.parent.getPoseOrientation()
                                if self.manipulate_bone == 'x_par_trans':
                                    x_vec = (par_pose * x_vec).normalizeCopy()
                                    tmp_vec = plane_norm.cross(x_vec).normalizeCopy()
                                    plane_norm = x_vec.cross(tmp_vec).normalizeCopy()
                                    
                                    new_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(new_ray)
                                    old_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(old_ray)
                                    
                                    if new_scale > 0.0 and old_scale > 0.0:
                                        new_project_pos = cam_offset + (new_ray * new_scale)
                                        old_project_pos = cam_offset + (old_ray * old_scale)
                                        
                                        new_project_pos = new_project_pos - par_pos
                                        old_project_pos = old_project_pos - par_pos
                                        
                                        tmp_vec = new_project_pos - old_project_pos
                                        trans_vec = x_vec * tmp_vec.dot(x_vec)
                                        bone.translate(trans_vec)
                                
                                elif self.manipulate_bone == 'y_par_trans':
                                    y_vec = (par_pose * y_vec).normalizeCopy()
                                    tmp_vec = plane_norm.cross(y_vec).normalizeCopy()
                                    plane_norm = y_vec.cross(tmp_vec).normalizeCopy()
                                    
                                    new_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(new_ray)
                                    old_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(old_ray)
                                    
                                    if new_scale > 0.0 and old_scale > 0.0:
                                        new_project_pos = cam_offset + (new_ray * new_scale)
                                        old_project_pos = cam_offset + (old_ray * old_scale)
                                        
                                        new_project_pos = new_project_pos - par_pos
                                        old_project_pos = old_project_pos - par_pos
                                        
                                        tmp_vec = new_project_pos - old_project_pos
                                        trans_vec = y_vec * tmp_vec.dot(y_vec)
                                        bone.translate(trans_vec)
                                
                                elif self.manipulate_bone == 'z_par_trans':
                                    z_vec = (par_pose * z_vec).normalizeCopy()
                                    tmp_vec = plane_norm.cross(z_vec).normalizeCopy()
                                    plane_norm = z_vec.cross(tmp_vec).normalizeCopy()
                                    
                                    new_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(new_ray)
                                    old_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(old_ray)
                                    
                                    if new_scale > 0.0 and old_scale > 0.0:
                                        new_project_pos = cam_offset + (new_ray * new_scale)
                                        old_project_pos = cam_offset + (old_ray * old_scale)
                                        
                                        new_project_pos = new_project_pos - par_pos
                                        old_project_pos = old_project_pos - par_pos
                                        
                                        tmp_vec = new_project_pos - old_project_pos
                                        trans_vec = z_vec * tmp_vec.dot(z_vec)
                                        bone.translate(trans_vec)
                            
                            else:
                                if self.manipulate_bone == 'x_par_trans':
                                    tmp_vec = plane_norm.cross(x_vec).normalizeCopy()
                                    plane_norm = x_vec.cross(tmp_vec).normalizeCopy()
                                    
                                    new_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(new_ray)
                                    old_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(old_ray)
                                    
                                    if new_scale > 0.0 and old_scale > 0.0:
                                        new_project_pos = cam_offset + (new_ray * new_scale)
                                        old_project_pos = cam_offset + (old_ray * old_scale)
                                        
                                        tmp_vec = new_project_pos - old_project_pos
                                        trans_vec = x_vec * tmp_vec
                                        bone.translate(trans_vec)
                                
                                elif self.manipulate_bone == 'y_par_trans':
                                    tmp_vec = plane_norm.cross(y_vec).normalizeCopy()
                                    plane_norm = y_vec.cross(tmp_vec).normalizeCopy()
                                    
                                    new_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(new_ray)
                                    old_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(old_ray)
                                    
                                    if new_scale > 0.0 and old_scale > 0.0:
                                        new_project_pos = cam_offset + (new_ray * new_scale)
                                        old_project_pos = cam_offset + (old_ray * old_scale)
                                        
                                        tmp_vec = new_project_pos - old_project_pos
                                        trans_vec = y_vec * tmp_vec
                                        bone.translate(trans_vec)
                                
                                elif self.manipulate_bone == 'z_par_trans':
                                    tmp_vec = plane_norm.cross(z_vec).normalizeCopy()
                                    plane_norm = z_vec.cross(tmp_vec).normalizeCopy()
                                    
                                    new_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(new_ray)
                                    old_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(old_ray)
                                    
                                    if new_scale > 0.0 and old_scale > 0.0:
                                        new_project_pos = cam_offset + (new_ray * new_scale)
                                        old_project_pos = cam_offset + (old_ray * old_scale)
                                        
                                        tmp_vec = new_project_pos - old_project_pos
                                        trans_vec = z_vec * tmp_vec
                                        bone.translate(trans_vec)
                            
                            # Update the Right Panel's bone offset
                            b_pos = bone.getOffset()
                            if global_measure_unit == UNIT_CENTIMETERS:
                                b_pos *= 2.54
                            x, y, z = b_pos.asArray()
                            self.pose_panel.x_set_pos.SetValue(x)
                            self.pose_panel.y_set_pos.SetValue(y)
                            self.pose_panel.z_set_pos.SetValue(z)
                        
                        elif self.is_rotate_mode:
                            new_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(new_ray)
                            old_scale = -plane_norm.dot(cam_offset) / plane_norm.dot(old_ray)
                                
                            new_project_pos = cam_offset + new_ray * new_scale
                            old_project_pos = cam_offset + old_ray * old_scale
                            
                            if new_scale > 0.0 and old_scale > 0.0:
                                new_project_pos.normalize()
                                old_project_pos.normalize()
                                tmp_axis = AxisAngle()
                                
                                dir_vec = new_project_pos - old_project_pos
                                tmp_len = dir_vec.length()
                                tmp_len = max(min(tmp_len, 1.0), -1.0)
                                tmp_ang = math.asin(tmp_len)
                                
                                dir_vec.normalize()
                                tmp_vec = old_project_pos.cross(dir_vec)
                                tmp_vec.normalize()
                                dot_val = tmp_vec.dot(plane_norm)
                                if dot_val < 0.0:
                                    tmp_ang *= -1
                                
                                if self.manipulate_bone == 'x_rot':
                                    tmp_axis = AxisAngle([1, 0, 0, tmp_ang])
                                
                                elif self.manipulate_bone == 'y_rot':
                                    tmp_axis = AxisAngle([0, 1, 0, tmp_ang])
                                
                                elif self.manipulate_bone == 'z_rot':
                                    tmp_axis = AxisAngle([0, 0, 1, tmp_ang])
                                
                                old_pose = bone_pose
                                bone.setPoseOrientation(old_pose * tmp_axis.toMatrix4())
                                
                                # Update the selected sensor's children to new
                                # pose orientation
                                bone_pose = bone.getPoseOrientation()
                                for child in bone.children:
                                    child.setOffset(bone_pose * -old_pose * child.getOffset())
                                
                                # Update the Right Panel's bone pose
                                orient_box = self.pose_panel.orient_choice_box
                                orient_type = orient_box.GetStringSelection()
                                orient = orient_type.split(' ')
                                if orient[0] == 'Euler':
                                    euler = bone_pose.toEuler(orient[1])
                                    pitch, yaw, roll = euler.asDegreeArray()
                                    self.pose_panel.x_set_rot.SetValue(pitch)
                                    self.pose_panel.y_set_rot.SetValue(yaw)
                                    self.pose_panel.z_set_rot.SetValue(roll)
                                    self.pose_panel.w_set_rot.SetValue(0.0)
                                
                                elif orient[0] == 'Axis':
                                    axis = bone_pose.toAxisAngle()
                                    x, y, z, ang = axis.asDegreeArray()
                                    self.pose_panel.x_set_rot.SetValue(x)
                                    self.pose_panel.y_set_rot.SetValue(y)
                                    self.pose_panel.z_set_rot.SetValue(z)
                                    self.pose_panel.w_set_rot.SetValue(ang)
                                
                                else:
                                    quat = bone_pose.toQuaternion()
                                    x, y, z, w = quat.asArray()
                                    self.pose_panel.x_set_rot.SetValue(x)
                                    self.pose_panel.y_set_rot.SetValue(y)
                                    self.pose_panel.z_set_rot.SetValue(z)
                                    self.pose_panel.w_set_rot.SetValue(w)
            
            elif right_down and not left_down and not middle_down:
                self.gl_canvas.x_last = self.gl_canvas.x
                self.gl_canvas.y_last = self.gl_canvas.y
                
                # Get Screen Position
                self.gl_canvas.x, self.gl_canvas.y = event.GetPosition()
                self.gl_canvas.Refresh()
            
            elif middle_down and not left_down and not right_down:
                self.gl_canvas.x_trans_last = self.gl_canvas.x_trans
                self.gl_canvas.y_trans_last = self.gl_canvas.y_trans
                
                # Get Screen Position
                self.gl_canvas.x_trans, self.gl_canvas.y_trans = event.GetPosition()
                self.gl_canvas.Refresh()
    
    def onGLScroll(self, event=None):
        """ Captures the scroll wheel of the mouse.
            
            Used for zooming the camera.
            
            Args:
                event: A wxPython event.event.GetWheelRotation()
        """
        offset = event.GetWheelRotation() / 30.0
        x_zoom, y_zoom, z_zoom = self.gl_canvas.cam_zoom_node.vector
        z_zoom += offset
        if z_zoom > 0:
            z_zoom = 0.0
        self.gl_canvas.cam_zoom_node.vector = [x_zoom, y_zoom, z_zoom]
        
        # This is used for fixing some GLCanvas bug that causes it not to
        # refresh properly
        if self.is_refresh:
            x, y = self.GetPositionTuple()
            self.MoveXY(x - 1, y)
            self.MoveXY(x, y)
            self.is_refresh = False
    
    # Right Panel Bind Functions
    def onSessionChoice(self, event=None):
        """ Updates the world based on what session has been selected.
            
            Args:
                event: A wxPython event.
        """
        
        session_sel = self.right_panel.session_choice_box.GetStringSelection()
        
        if session_sel == "None":
            if self.recorded_session is not None:
                # Set the session's skeleton to an initial pose
                for skel in self.skeleton_list.values():
                    skel.resetLowestPoint()
                for bone in self.bone_list.values():
                    bone.setOrientation(Matrix4())
                self.root_node.update()
            
            self.recorded_session = None
            self.play_rate = -1
            self.bottom_panel.reset()
            self.toggleBoneMenus(True)
            self.pose_panel.calibrate_button.Enable()
            
            if self.is_live_mode:
                self.bottom_panel.showRecord()
                self.live_panel.disablePlay()
                self.live_panel.disableRecord()
                self.live_panel.enableStream()
                self.live_panel.enableSelect()
        else:
            if self.is_live_mode:
                if self.is_stream:
                    self.onStreamButton(None)
                self.bottom_panel.showPlay()
                self.live_panel.enablePlay()
                self.live_panel.disableRecord()
                self.live_panel.disableStream()
                self.live_panel.disableSelect()
            self.toggleBoneMenus(False)
            self.recorded_session = self.session_list[session_sel]
            max_frame = len(self.recorded_session.frame_data) - 1
            self.bottom_panel.setupPlay(max_frame)
            if self.menu_bar.IsChecked(SLERP):
                self.recorded_session.interp_method = anim_utils.RecordSession.SLERP
            
            # Reset pose panel
            if self.selected_obj is not None:
                self.selected_obj = None
                self.is_bone = False
                self.is_skeleton = False
                self.manipulate_bone = ''
                self.pose_panel.reset()
                self.pose_panel.disableInput()
                if self.pose_panel.sensor_orient_check.IsChecked():
                    self.pose_panel.sensor_orient_check.SetValue(False)
                    self.onSenorCheck(self.pose_panel.sensor_orient_check)
            
            self.pose_panel.calibrate_button.Disable()
            
            self.is_ped_track = False
            self.menu_bar.Check(52, False)
            
            # Reset the GUI modes
            self.resetGUIModes()
            
            # Clear the lists of bones
            self.bone_list.clear()
            self.skeleton_list.clear()
            self.root_node.children = []
            
            # Reset Mocap Studio draw settings
            canvas = self.gl_canvas
            camera = canvas.cam_node
            for k in canvas.id_mesh_intercept_table.keys():
                if k > 10:
                    del canvas.id_mesh_intercept_table[k]
            canvas.master_id = 11
            camera.children = camera.children[:1]
            
            # Create the root_node's immediate children, then use them to
            # rebuild the simulation state
            for bone_name in self.recorded_session.root_bone_list:
                self.loadBoneTree(self.root_node, bone_name)
            
            tmp_list = self.recorded_session.recorded_bone_list.keys()
            tmp_list.sort()
            self.pose_panel.parent_choice_box.SetItems(['None'] + tmp_list)
            self.pose_panel.parent_choice_box.SetSelection(0)
    
    # Live Panel Bind Functions
    def onStreamButton(self, event=None):
        """ Starts/Stops the streaming of data.
            
            Args:
                event: A wxPython event.
        """
        self.live_panel.device_list.DeselectAll()
        if self.is_stream:
            time_interval = self.update_timer.GetInterval()
            self.update_timer.Stop()
            did_stop = base_ng.stopStream()
            self.update_timer.Start(time_interval)
            if not did_stop:
                return
            self.live_panel.failed_list = []
            self.live_panel.enableSelect()
            self.live_panel.disableRecord()
            self.live_panel.interval.Enable()
            self.live_panel.stream_button.SetLabel("Start Streaming")
            
            self.toggleExportImportMenus(True)
        
        else:
            for skel in self.skeleton_list.values():
                skel.resetLowestPoint()
            
            if self.node_graph_window.config_win.IsShown():
                self.node_graph_window.config_win.onClose(None)
            val = self.live_panel.interval.GetValue()
            filter = []
            for device in self.live_panel.device_list.GetCheckedStrings():
                dev_type, id_hex = device.rsplit('-', 1)
                filter.append(sc.global_sensor_list[int(id_hex, 16)])
            time_interval = self.update_timer.GetInterval()
            self.update_timer.Stop()
            did_start = base_ng.startStream(val, filter, self.live_panel.threadCallback)
            self.live_panel.onDeselectAll(None)
            checked_list = [device.device_type + '-' + device.serial_number_hex for device in base_ng.global_sensor_filter]
            self.live_panel.device_list.SetCheckedStrings(checked_list)
            self.update_timer.Start(time_interval)
            
            for skel in self.skeleton_list.values():
                skel.lowestPointOffest()
            if not did_start:
                self.live_panel.failed_list = []
                return
            self.live_panel.disableSelect()
            self.live_panel.enableRecord()
            self.live_panel.interval.Disable()
            self.live_panel.stream_button.SetLabel("Stop Streaming")
            
            self.toggleExportImportMenus(False)
        
        self.is_stream = not self.is_stream
    
    def onPlayButton(self, event=None):
        """ Starts/Stops the playing of a recorded session.
            
            Args:
                event: A wxPython event.
        """
        if self.is_playing:
            self.toggleExportImportMenus(True)
            self.toggleBoneMenus(True)
            self.right_panel.enableChoice()
            self.live_panel.play_button.SetLabel("Play")
            self.live_panel.playEnable()
            self.bottom_panel.frame_slider.Enable()
        
        else:
            if self.recorded_session is not None:
                playback_rate = self.live_panel.playback_rate.GetValue()
                cap_rate = self.recorded_session.capture_rate
                self.play_rate = (cap_rate / playback_rate)
                self.toggleExportImportMenus(False)
                self.toggleBoneMenus(False)
                self.live_panel.play_button.SetLabel("Stop Playback")
                self.live_panel.playDisable()
                self.right_panel.disableChoice()
                self.bottom_panel.frame_slider.Disable()
                self.start_time_play = time.clock()
            else:
                return
        
        self.is_playing = not self.is_playing
    
    def onRecordButton(self, event=None):
        """ Starts/Stops the recording of a session.
            
            Args:
                event: A wxPython event.
        """
        if self.is_recording:
            self.recorder.total_frames = self.recorded_frames
            choice_box = self.right_panel.session_choice_box
            name = self.recorder.session.name
            name_dlg = SessionName(self, name, choice_box.GetItems())
            time_interval = self.update_timer.GetInterval()
            self.update_timer.Stop()
            time.sleep(1)
            base_ng.stopRec()
            self.recorder.start()
            rec_dlg = wx.ProgressDialog("Recording Progress", "Building the captured data", maximum=2147483647, parent=self, style=wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME)
            
            while True:
                self.recorder.record_lock.acquire()
                if not self.recorder.keep_recording:
                    self.recorder.record_lock.release()
                    break
                self.recorder.record_lock.release()
                wx.MilliSleep(50)
                rec_dlg.UpdatePulse()
            rec_dlg.Destroy()
            
            if self.logging_window is not None:
                self.logger = anim_utils.Logger(self.logging_window.writeLogFile)
                self.logger.start()
                log_dlg = wx.ProgressDialog("Logging Progress", "Building the logged data", maximum=self.recorded_frames, parent=self, style=wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME)
                
                while True:
                    self.logger.log_lock.acquire()
                    if not self.logger.keep_logging:
                        self.logger.log_lock.release()
                        self.logging_window.Destroy()
                        self.logging_window = None
                        break
                    self.logger.log_lock.release()
                    wx.MilliSleep(50)
                    log_dlg.UpdatePulse()
                log_dlg.Destroy()
            
            if name_dlg.ShowModal() == wx.ID_OK:
                name = name_dlg.GetValue()
                self.recorder.session.name = name
            
            for sensor in base_ng.global_sensor_filter:
                sensor.clearRecordingData()
            
            print 'avg capture rate = ' + str(len(self.recorder.session.frame_data) / self.bottom_panel.cur_time)
            print 'avg capture rate for bones:'
            for key in self.recorder.session.bone_frame_counter:
                fps = str(self.recorder.session.bone_frame_counter[key] / self.bottom_panel.cur_time)
                print key + ": " + fps
            self.update_timer.Start(time_interval)
            try:
                name_dlg.Destroy()
            except:
                print "Failed to destroy the Session Name dialog."
            
            self.session_list[name] = self.recorder.session
            choice_box.Append(name)
            self.live_panel.record_button.SetLabel("Record")
            self.node_graph_window.onStopRecording()
            
            self.right_panel.enableChoice()
            self.live_panel.enableSelect()
            self.live_panel.recordEnable()
        
        else:
            cap_rate = self.live_panel.record_rate.GetValue()
            if cap_rate > 0:
                base_ng.startRec()
                self.right_panel.disableChoice()
                self.live_panel.disableSelect()
                self.bottom_panel.setupRecord(cap_rate)
                self.live_panel.record_button.SetLabel("Stop Recording")
                self.live_panel.recordDisable()
                self.recording_rate = cap_rate ** -1
                self.recorder = anim_utils.Recorder(self.recording_rate, self.root_node, self.bone_list.values(), self.is_ped_track, self.logging_window)
                self.node_graph_window.onStartRecording()
                self.start_time_record = time.clock()
                self.recorded_frames = 0
                wx.Bell()
            else:
                return
        
        self.is_recording = not self.is_recording
    
    # Pose Panel Bind Functions
    def onBonelength(self, event=None):
        b_len = self.pose_panel.set_bone_length.GetValue()
        if global_measure_unit == UNIT_CENTIMETERS:
            b_len /= 2.54
        self.selected_obj.setLength(b_len)
        # Update the selected sensor's children to new bone length
        for child in self.selected_obj.children:
            tmp_pos = self.selected_obj.getPoseOrientation() * Vector3(UNIT_Y) * self.selected_obj.getLength()
            val = child.getOffset().cross(tmp_pos).length()
            if val <= 0.00001 or val >= -0.00001:
                child.setOffset(tmp_pos)
    
    def onCalibrate(self, event=None):
        """ Calibrates the sensors to the bones to receive accurate data.
            
            Args:
                event: A wxPython event.
        """
        if len(sc.global_sensor_list) <= 0:
            return
        message = ("1. Make sure all devices you are using are on.\n\n"
                    "2. Make sure device(s) are within a range of\n10 to 20 feet of the receiver(s), for best results.\n\n"
                    "3. Make sure device(s) are stationary before\ncontinuing, because this could take a few\nseconds to finish.")
        caption = "Things to check before calibrating"
        
        time_interval = self.update_timer.GetInterval()
        self.update_timer.Stop()
        val = wx.MessageBox(message, caption, wx.OK | wx.CANCEL)
        
        if val == wx.CANCEL:
            self.update_timer.Start(time_interval)
            return
        
        if global_calibration_timer:
            wait_val = 5
            timer_dlg = wx.TextEntryDialog(self, "Seconds to wait:", "Calibration Timer", "5", style=wx.OK)
            if timer_dlg.ShowModal() == wx.ID_OK:
                try:
                    wait_val = int(timer_dlg.GetValue())
                except:
                    pass
            time.sleep(wait_val)
        
        is_errors = False
        
        for b in self.bone_list.values():
            if is_errors:
                break
            node = b.vs_node
            if node is not None:
                device = node.getInputDevice()
                if device is not None:
                    device_node = node.getInputDeviceNode()
                    if device_node:
                        is_errors = not device_node.calibrateInputNode()
                else:
                    if device is not None:
                        message = "Device (%s) is not connected" % (device.serial_number_hex)
                        caption = "Device Not Connected"
                        wx.MessageBox(message, caption, wx.OK | wx.ICON_ERROR)
                        is_errors = True
                        break
        if is_errors:
            error_text = "Possible reasons:\n\tDevice is not turned on\n\tDevice is out of range, get closer to receiver\n\tReceiver has gotten in a bad state, or it is not plugged in"
            message = "Calibrating devices failed!\n%s\nTry again?" % (error_text)
            caption = "Calibration Failed"
            answer = wx.MessageBox(message, caption, wx.OK | wx.ICON_ERROR | wx.CANCEL)
            if answer == wx.OK:
                self.onCalibrate(event)
        else:
            message = "Calibrating devices succeeded!"
            caption = "Calibration Success"
            answer = wx.MessageBox(message, caption, wx.OK)
            self.update_timer.Start(time_interval)
    
    def onNameChange(self, event=None):
        new_name = self.pose_panel.name_text.GetValue()
        if self.is_bone:
            if new_name in self.bone_list:
                self.pose_panel.name_text.SetValue(self.selected_obj.getName())
            else:
                del self.bone_list[self.selected_obj.getName()]
                self.selected_obj.setName(new_name)
                self.bone_list[new_name] = self.selected_obj
        elif self.is_skeleton:
            if new_name in self.skeleton_list:
                self.pose_panel.name_text.SetValue(self.selected_obj.getName())
            else:
                del self.skeleton_list[self.selected_obj.getName()]
                self.selected_obj.setName(new_name)
                self.skeleton_list[new_name] = self.selected_obj
    
    def onOffset(self, event=None):
        x_pos = self.pose_panel.x_set_pos.GetValue()
        y_pos = self.pose_panel.y_set_pos.GetValue()
        z_pos = self.pose_panel.z_set_pos.GetValue()
        
        new_pos = Vector3([x_pos, y_pos, z_pos])
        if global_measure_unit == UNIT_CENTIMETERS:
            new_pos *= 1 / 2.54
        
        if self.is_bone:
            self.selected_obj.setOffset(new_pos)
        else:
            self.selected_obj.setPosition(new_pos)
    
    def onOrientChoice(self, event=None):
        """ Updates the pose_panel on what pose orientation was selected.
            
            Args:
                event: A wxPython event.
        """
        orient_type = self.pose_panel.orient_choice_box.GetStringSelection()
        orient_type = orient_type.split(' ')
        bone_pose = self.selected_obj.getPoseOrientation()
        id = self.pose_panel._text_ids[12]
        tmp_win = self.pose_panel.FindWindowById(id)
        if orient_type[0] == 'Euler':
            self.pose_panel.w_set_rot.Disable()
            x, y, z = bone_pose.toEuler(orient_type[1]).asDegreeArray()
            self.pose_panel.x_set_rot.SetValue(x)
            self.pose_panel.y_set_rot.SetValue(y)
            self.pose_panel.z_set_rot.SetValue(z)
            self.pose_panel.w_set_rot.SetToDefaultValue()
            self.pose_panel.w_set_rot.Show(False)
            tmp_win.Show(False)
        else:
            self.pose_panel.w_set_rot.Show(True)
            tmp_win.Show(True)
            tmp_font = tmp_win.GetFont()
            if orient_type[0] == 'Axis':
                self.pose_panel.w_set_rot.Enable()
                x, y, z, ang = bone_pose.toAxisAngle().asDegreeArray()
                self.pose_panel.x_set_rot.SetValue(x)
                self.pose_panel.y_set_rot.SetValue(y)
                self.pose_panel.z_set_rot.SetValue(z)
                self.pose_panel.w_set_rot.SetValue(ang)
                if tmp_font.GetFaceName() != "Symbol":
                    tmp_font.SetFaceName("Symbol")
                    tmp_font.SetPointSize(12)
                    tmp_win.SetLabel("q")
                    
                    tmp_win.SetFont(tmp_font)
                    self.pose_panel.Layout()
            else:
                self.pose_panel.w_set_rot.Enable()
                x, y, z, w = bone_pose.toQuaternion().asArray()
                self.pose_panel.x_set_rot.SetValue(x)
                self.pose_panel.y_set_rot.SetValue(y)
                self.pose_panel.z_set_rot.SetValue(z)
                self.pose_panel.w_set_rot.SetValue(w)
                if tmp_font.GetFaceName() == "Symbol":
                    tmp_font.SetFaceName(self.pose_panel.w_face_name)
                    tmp_font.SetPointSize(self.pose_panel.w_point_size)
                    tmp_win.SetLabel("W")
                    
                    tmp_win.SetFont(tmp_font)
                    self.pose_panel.Layout()
    
    def onOutputChoice(self, event=None):
        choice = self.pose_panel.output_choice_box.GetStringSelection()
        if choice == "None":
            node = self.selected_obj.vs_node
            if node is not None:
                self.selected_obj.delVSNode()
            self.pose_panel.sensor_orient_check.SetValue(False)
            self.onSenorCheck(self.pose_panel.sensor_orient_check)
            self.pose_panel.disableSensorCheck()
        else:
            node = self.output_list[choice]
            self.selected_obj.addVSNode(node)
            device = node.getInputDevice()
            if device is not None:
                self.pose_panel.enableSensorCheck()
                # Set sensor's pose orientation property
                pitch, yaw, roll = node.getSensorOrientDir().toEuler().asDegreeArray()
                self.pose_panel.x_set_sensor_rot.SetValue(pitch)
                self.pose_panel.y_set_sensor_rot.SetValue(yaw)
                self.pose_panel.z_set_sensor_rot.SetValue(roll)
            else:
                self.pose_panel.sensor_orient_check.SetValue(False)
                # Reset sensor's pose orientation property
                self.pose_panel.x_set_sensor_rot.SetToDefaultValue()
                self.pose_panel.y_set_sensor_rot.SetToDefaultValue()
                self.pose_panel.z_set_sensor_rot.SetToDefaultValue()
                self.pose_panel.disableSensorCheck()
            self.onSenorCheck(self.pose_panel.sensor_orient_check)
    
    def onParentChoice(self, event=None):
        """ Updates the selected_obj's parent to what was chosen.
            
            Args:
                event: A wxPython event.
        """
        # Get the selected choice name
        choice_name = self.pose_panel.parent_choice_box.GetStringSelection()
        if choice_name == "None":
            par_bone = self.selected_obj.parent
            par_is_bone = type(par_bone) is anim_utils.Bone
            if par_is_bone:
                # Make the bone a "root bone"
                for i in range(len(par_bone.children)):
                    if par_bone.children[i].getName() == self.selected_obj.getName():
                        del self.selected_obj.parent.children[i]
                        self.selected_obj.setOffset(self.selected_obj.getPosition())
                        break
                self.root_node.appendChild(self.selected_obj)
                
                # Update the Right Panel's bone offset
                x, y, z = self.selected_obj.getOffset().asArray()
                self.pose_panel.x_set_pos.SetValue(x)
                self.pose_panel.y_set_pos.SetValue(y)
                self.pose_panel.z_set_pos.SetValue(z)
        else:
            for r_node in self.bone_list.values():
                if r_node == self.selected_obj:
                    continue
                tmp_node = r_node.getNode(choice_name)
                if tmp_node:
                    # If the removed object has a parent already
                    sel_par_bone = self.selected_obj.parent
                    for i in range(len(sel_par_bone.children)):
                        if sel_par_bone.children[i].getName() == self.selected_obj.getName():
                            del sel_par_bone.children[i]
                            break
                    par_bone = tmp_node.parent
                    while par_bone:
                        if par_bone == self.selected_obj:
                            if sel_par_bone:
                                par_name = sel_par_bone.getName()
                            else:
                                par_name = "None"
                            tmp_box = self.pose_panel.parent_choice_box
                            tmp_box.SetStringSelection(par_name)
                            return
                        par_bone = par_bone.parent
                    tmp_node.appendChild(self.selected_obj)
                    self.selected_obj.setOffset(tmp_node.getPoseOrientation() * Vector3(UNIT_Y) * tmp_node.length)
                    
                    # Update the Right Panel's bone offset
                    x, y, z = self.selected_obj.getOffset().asArray()
                    self.pose_panel.x_set_pos.SetValue(x)
                    self.pose_panel.y_set_pos.SetValue(y)
                    self.pose_panel.z_set_pos.SetValue(z)
                    break
            else:
                return
    
    def onPoseOrient(self, event=None):
        """ Updates the selected_obj to the new pose orientation given.
            
            Args:
                event: A wxPython event.
        """
        orient_type = self.pose_panel.orient_choice_box.GetStringSelection()
        orient_type = orient_type.split(' ')
        old_pose = self.selected_obj.getPoseOrientation()
        if orient_type[0] == 'Euler':
            pitch = self.pose_panel.x_set_rot.GetValue()
            yaw = self.pose_panel.y_set_rot.GetValue()
            roll = self.pose_panel.z_set_rot.GetValue()
            tmp_mat = Euler([pitch, yaw, roll], True).toMatrix4(orient_type[1])
            self.selected_obj.setPoseOrientation(tmp_mat)
        
        elif orient_type[0] == 'Axis':
            x = self.pose_panel.x_set_rot.GetValue()
            y = self.pose_panel.y_set_rot.GetValue()
            z = self.pose_panel.z_set_rot.GetValue()
            ang = self.pose_panel.w_set_rot.GetValue()
            tmp_axis = AxisAngle([x, y, z, ang], True)
            self.selected_obj.setPoseOrientation(tmp_axis.toMatrix4())
        
        else:
            x = self.pose_panel.x_set_rot.GetValue()
            y = self.pose_panel.y_set_rot.GetValue()
            z = self.pose_panel.z_set_rot.GetValue()
            w = self.pose_panel.w_set_rot.GetValue()
            tmp_quat = Quaternion([x, y, z, w])
            tmp_quat.normalize()
            self.selected_obj.setPoseOrientation(tmp_quat.toMatrix4())
        
        # Update the selected sensor's children to new pose orientation
        if self.is_bone:
            for child in self.selected_obj.children:
                child.setOffset(self.selected_obj.getPoseOrientation() * -old_pose * child.getOffset())
    
    def onSenorCheck(self, event=None):
        if event is None or not event.IsChecked():
            self.gl_canvas.mask &= ~gl_sg.DRAW_SENSOR
        else:
            # Reset the GUI modes
            self.resetGUIModes()
            self.gl_canvas.mask |= gl_sg.DRAW_SENSOR
        if type(event) is wx.CommandEvent:
            event.Skip()
    
    def onSensorPose(self, event=None):
        pitch = self.pose_panel.x_set_sensor_rot.GetValue()
        yaw = self.pose_panel.y_set_sensor_rot.GetValue()
        roll = self.pose_panel.z_set_sensor_rot.GetValue()
        tmp_euler = Euler([pitch, yaw, roll], True)
        
        self.selected_obj.vs_node.setSensorOrientDir(tmp_euler.toMatrix4())
    
    # Helper Functions
    def loadBoneTree(self, par_bone, bone_name, skel_name=None):
        """ Creates a skeleton of Bone objects in the world.
            
            Args:
                par_bone: A reference to a SkelNode or Bone object.
                bone_name: A string of a name of a bone.
        """
        
        # Set itself up
        if bone_name not in self.recorded_session.recorded_bone_list:
            tmp_skel = anim_utils.Skeleton(bone_name)
            
            # Set skeleton mesh up
            self.gl_canvas.addMesh(tmp_skel)
            
            # Add Skeleton to our skeleton list
            self.skeleton_list[bone_name] = tmp_skel
            
            # Set parent up
            par_bone.appendChild(tmp_skel)
            
            # Set children up
            for r_bone_name in self.recorded_session.recorded_bone_list:
                r_bone = self.recorded_session.recorded_bone_list[r_bone_name]
                if r_bone.parent == bone_name:
                    self.loadBoneTree(tmp_skel, r_bone_name, bone_name)
        else:
            tmp_bone = None
            record_bone = self.recorded_session.recorded_bone_list[bone_name]
            sensor_name = record_bone.vs_name
            if sensor_name in self.output_list:
                vsn = self.output_list[sensor_name]
                if record_bone.sensor_pose is not None:
                    vsn.setSensorOrientDir(record_bone.sensor_pose.toMatrix4())
                if record_bone.vs_pose is not None:
                    vsn.setSensorCalibrate(record_bone.vs_pose)
                
                tmp_bone = anim_utils.Bone(bone_name, record_bone.bone_length, p_orient=record_bone.pose_orient, vs_node=vsn)
            else:
                tmp_bone = anim_utils.Bone(bone_name, record_bone.bone_length, p_orient=record_bone.pose_orient)
            
            # Set parent up
            if type(par_bone) is anim_utils.SkelNode:
                skel_name = "Skeleton"
                i = 0
                while skel_name in self.skeleton_list:
                    skel_name = skel_name.rstrip('0123456789')
                    skel_name += str(i)
                    i += 1
                skeleton = anim_utils.Skeleton(skel_name)
                
                # Set skeleton mesh up
                self.gl_canvas.addMesh(skeleton)
                
                # Add Skeleton to our skeleton list
                self.skeleton_list[skel_name] = skeleton
                
                par_bone.appendChild(skeleton)
                skeleton.appendChild(tmp_bone)
                
                # Set Skeleton's bones based from name
                skeleton.setSkeletonBone(tmp_bone)
            
            else:
                par_bone.appendChild(tmp_bone)
                
                # Get Skeleton from our skeleton list
                skeleton = self.skeleton_list[skel_name]
                
                # Set Skeleton's bones based from name
                skeleton.setSkeletonBone(tmp_bone)
            
            # Set Up initial position
            frame = self.recorded_session.frame_data[0][bone_name]
            keyframe = self.recorded_session.getKeyframe(bone_name, frame)
            tmp_bone.setOrientation(keyframe.start_frame_data[0].toMatrix4())
            tmp_bone.setPosition(keyframe.start_frame_data[1])
            
            # Set bone mesh up
            self.gl_canvas.addMesh(tmp_bone)
        
            # Update ambient color
            tmp_bone.setAmbientColor()
            
            # Add Bone to our bone list
            self.bone_list[bone_name] = tmp_bone
            
            # Set children up
            for child_str in record_bone.children:
                self.loadBoneTree(tmp_bone, child_str, skel_name)
            
            # Apply offset to bone
            tmp_bone.setOffset(record_bone.offset)
    
    def toggleBoneMenus(self, value):
        self.menu_bar.Enable(61, value)
        self.menu_bar.Enable(62, value)
        self.menu_bar.Enable(63, value)
        self.pop_up.Enable(96, value)
        self.pop_up.Enable(97, value)
        self.pop_up.Enable(98, value)
    
    def toggleExportImportMenus(self, value):
        self.menu_bar.Enable(6, value)
        self.menu_bar.Enable(7, value)
        self.menu_bar.Enable(16, value)
        self.menu_bar.Enable(17, value)
    
    def tshBuildHeiarchy(self, bone_name, cur_skel):
        """ Builds a skeleton heiarchy out of the Bone objects.
            
            Called only for exporting a TSH file.
            
            Args:
                bone_name: A string denoting the name of a Bone object.
                cur_skel: A reference to a TSHSkel object.
        """
        cur_skel.bones.append(im_tsh.TSHBone(bone_name))
        cur_tsh_bone = cur_skel.bones[-1]
        cur_session_bone = self.recorded_session.recorded_bone_list[bone_name]
        if cur_session_bone.parent is not None:
            cur_tsh_bone.parent_name = cur_session_bone.parent
        else:
            cur_tsh_bone.parent_name = ""
        cur_tsh_bone.pose_orient = cur_session_bone.pose_orient
        cur_tsh_bone.offset = cur_session_bone.offset
        cur_tsh_bone.length = cur_session_bone.bone_length
        if global_export_unit == EXPORT_CENTIMETERS:
            cur_tsh_bone.offset *= 2.54
            cur_tsh_bone.length *= 2.54
        cur_tsh_bone.vs_name = cur_session_bone.vs_name
        for child_name in cur_session_bone.children:
            self.tshBuildHeiarchy(child_name, cur_skel)
    
    def resetGUIModes(self, check_val=False):
        if self.is_translate_mode:
            self.is_translate_mode = False
            self.gl_canvas.mask ^= gl_sg.DRAW_GUI_TRANS
            self.gl_canvas.translate_mesh.setBools()
        
        elif self.is_rotate_mode:
            self.is_rotate_mode = False
            self.gl_canvas.mask ^= gl_sg.DRAW_GUI_ROT
            self.gl_canvas.rotate_mesh.setBools()
        
        elif self.is_free_mode:
            self.is_free_mode = False
        
        if check_val:
            self.gl_canvas.mask ^= gl_sg.DRAW_SENSOR
    
    def updateOutputChoice(self):
        """Updates the output_list."""
        tmp_list = base_ng.global_output_nodes
        self.output_list.clear()
        for output in tmp_list:
            if type(output) is base_ng.VirtualSensorNode:
                self.output_list[output.name] = output
        
        for bone in self.bone_list.values():
            node = bone.vs_node
            if node is not None:
                if node.name in self.output_list:
                    if bone.getAmbientColor() == anim_utils.BONE_STREAM_FAIL:
                        bone.delVSNode()
                        bone.addVSNode(self.output_list[node.name])
                        bone.setAmbientColor(anim_utils.BONE_STREAM_FAIL)
                    else:
                        bone.delVSNode()
                        bone.addVSNode(self.output_list[node.name])
        
        tmp_list = self.output_list.keys()
        tmp_list.sort()
        self.pose_panel.output_choice_box.SetItems(["None"] + tmp_list)
        self.pose_panel.output_choice_box.SetSelection(0)


### Main Code ###
if __name__ == '__main__':
    # freeze_support()
    # Read configuration file for set-update
    try:
        config_file = open(os.path.join(_user_path, _config_name), 'r')
        
        for line in config_file.readlines():
            line = line.strip()
            var, val = line.split(' = ')
            if var == "bg_style":
                if val.upper() == "HORIZONTAL":
                    gl_sg.global_bg_style = gl_sg.HORIZONTAL
                else:
                    gl_sg.global_bg_style = gl_sg.VERTICAL
            elif var == "head_color":
                str_list = val.strip("[]").split(", ")
                gl_sg.global_head_color = [float(i) for i in str_list]
            elif var == "tail_color":
                str_list = val.strip("[]").split(", ")
                gl_sg.global_tail_color = [float(i) for i in str_list]
            elif var == "grid_color":
                str_list = val.strip("[]").split(", ")
                gl_sg.global_grid_color = [float(i) for i in str_list]
            elif var == "grid_alpha":
                gl_sg.global_grid_alpha = float(val)
            elif var == "bg_color1":
                str_list = val.strip("[]").split(", ")
                gl_sg.global_bg_color1 = [float(i) for i in str_list]
            elif var == "bg_color2":
                str_list = val.strip("[]").split(", ")
                gl_sg.global_bg_color2 = [float(i) for i in str_list]
            elif var == "draw_logo":
                if val.lower() == "true":
                    global_draw_logo = True
                else:
                    global_draw_logo = False
            elif var == "check_unknown":
                if val.lower() == "true":
                    sc.global_check_unknown = True
                else:
                    sc.global_check_unknown = False
            elif var == "export_interp":
                if val.lower() == "true":
                    global_export_interp = True
                else:
                    global_export_interp = False
            elif var == "interp_method":
                if val.lower() == "slerp":
                    global_interp_method = SLERP
                if val.lower() == "squad":
                    global_interp_method = SQUAD
            elif var == "export_unit":
                if val.lower() == "centimeters":
                    global_export_unit = EXPORT_CENTIMETERS
                if val.lower() == "inches":
                    global_export_unit = EXPORT_INCHES
            elif var == "measure_unit":
                if val.lower() == "centimeters":
                    global_measure_unit = UNIT_CENTIMETERS
                if val.lower() == "inches":
                    global_measure_unit = UNIT_INCHES
            elif var == "bone_view":
                if val.lower() == "normal":
                    global_bone_view = VIEW_NORMAL
                if val.lower() == "lines":
                    global_bone_view = VIEW_LINES
                if val.lower() == "points":
                    global_bone_view = VIEW_POINTS
            elif var == "calibration_timer":
                if val.lower() == "true":
                    global_calibration_timer = True
                else:
                    global_calibration_timer = False
            elif var == "wireless_retries":
                sc.setWirelessRetries(int(val))
        config_file.close()
    except:
        print "No configuration file."
    
    if "-nochain" in sys.argv:
        anim_utils.DRAW_CHILDREN = False
    
    # Create an "Application" (initializes the WX system)
    app = wx.PySimpleApp()
    
    # Check for 3 Space Sensors and Dongles
    if "-nofind" not in sys.argv:
        base_ng.initBaseScript()
    
    # Create a frame for use in our application
    frame = MainWindow()
    
    # Run the application's loop
    if "-profile" in sys.argv:
        import cProfile
        cProfile.run('app.MainLoop()', 'profiledata')
        import pstats
        p = pstats.Stats('profiledata')
        p.strip_dirs().sort_stats('cumulative').print_stats(50)
    else:
        app.MainLoop()
    
    # Destroying the objects
    print "Destroying Frame"
    del frame
    print "Destroying App"
    del app
    print "Destroyed!!!"
    
    # Save out the configuration of the Mocap Studio
    try:
        config_file = open(os.path.join(_user_path, _config_name), 'w')
        
        val = ""
        if gl_sg.global_bg_style == gl_sg.HORIZONTAL:
            val = "HORIZONTAL"
        else:
            val = "VERTICAL"
        config_file.write("bg_style = " + val + "\n")
        config_file.write("head_color = " + str(gl_sg.global_head_color) + "\n")
        config_file.write("tail_color = " + str(gl_sg.global_tail_color) + "\n")
        config_file.write("grid_color = " + str(gl_sg.global_grid_color) + "\n")
        config_file.write("grid_alpha = " + str(gl_sg.global_grid_alpha) + "\n")
        config_file.write("bg_color1 = " + str(gl_sg.global_bg_color1) + "\n")
        config_file.write("bg_color2 = " + str(gl_sg.global_bg_color2) + "\n")
        if global_draw_logo:
            val = "True"
        else:
            val = "False"
        config_file.write("draw_logo = " + val + "\n")
        if sc.global_check_unknown:
            val = "True"
        else:
            val = "False"
        config_file.write("check_unknown = " + val + "\n")
        if global_export_interp:
            val = "True"
        else:
            val = "False"
        config_file.write("export_interp = " + val + "\n")
        if global_interp_method == SLERP:
            val = "Slerp"
        elif global_interp_method == SQUAD:
            val = "Squad"
        config_file.write("interp_method = " + val + "\n")
        if global_export_unit == EXPORT_CENTIMETERS:
            val = "Centimeters"
        elif global_export_unit == EXPORT_INCHES:
            val = "Inches"
        config_file.write("export_unit = " + val + "\n")
        if global_measure_unit == UNIT_CENTIMETERS:
            val = "Centimeters"
        elif global_measure_unit == UNIT_INCHES:
            val = "Inches"
        config_file.write("measure_unit = " + val + "\n")
        if global_bone_view == VIEW_NORMAL:
            val = "Normal"
        elif global_bone_view == VIEW_LINES:
            val = "Lines"
        elif global_bone_view == VIEW_POINTS:
            val = "Points"
        config_file.write("bone_view = " + val + "\n")
        if global_calibration_timer:
            val = "True"
        else:
            val = "False"
        config_file.write("calibration_timer = " + val + "\n")
        config_file.write("wireless_retries = " + str(sc.getWirelessRetries()))
        
        config_file.close()
    except:
        print IOError('Failed to create a configuration file.')
    
    if "-nolog" not in sys.argv:
        # Close the log file
        try:
            log_file.close()
        except:
            print IOError('Failed to close the log file. May have not been created.')








