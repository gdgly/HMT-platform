#!/usr/bin/env python2.7

""" A scene graph that uses OpenGL calls.
    
    Creates a tree for scenes so objects are drawn in the correct order.
"""



import os
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.arrays import ArrayDatatype
from OpenGL.arrays import vbo
import numpy

try:
    from PIL import Image
except ImportError, err:
    import Image



### Static Globals ###
FILE_PATH = os.getcwd() + "\\media\\"
BONE_SCALE = 1
HORIZONTAL = 10
VERTICAL = 11
NORMAL_DRAW = 0
POINTS_DRAW = 1
LINES_DRAW= 2
MESH_DRAW= 4
_IDENTITY_MATRIX = (
    1, 0, 0, 0,
    0, 1, 0, 0,
    0, 0, 1, 0,
    0, 0, 0, 1
)
_ZERO_POSITION = (0, 0, 0)


# Mask Definitions
DRAW_ALL = -1
DRAW_RENDER = 1
DRAW_BONE_CLICK = 2
DRAW_SENSOR = 4
DRAW_ARROW_X = 8
DRAW_ARROW_Y = 16
DRAW_ARROW_Z = 32
DRAW_GUI_TRANS = 64
DRAW_TRANS_CLICK = 128
DRAW_GUI_ROT = 256
DRAW_ROT_CLICK = 512

### Globals ###
global_head_color = [0, 0.7, 0.7]
global_tail_color = [0.95, 0.45, 0]
global_bg_color1 = [0.5, 0.5, 1.0]
global_bg_color2 = [0.1, 0.1, 0.1]
global_bg_style = HORIZONTAL
global_grid_color = [1, 1, 1]
global_grid_alpha = 0.5
global_gl_version_list = None


### Classes ###
class SNode(object):
    
    """ Is a basic Scene Node that has the bare essentials to be on the graph.
        
        Is usually used for root nodes.
        
        Attributes:
            parent: A reference to another node on the graph. Is None if root.
            children: A list of references to other nodes on the graph that call
                this node its parent.
            mask: An integer that is used to determine whether to draw or not
                based on the mode of the graph.
    """
    
    __slots__ = ('children', 'mask', 'parent')
    
    def __init__(self, mask_val=DRAW_RENDER, parent=None):
        """ Initializes the SNode class.
            
            Args:
                mask_val: Initial indication of what modes this can be drawn in
                    (default is DRAW_RENDER)
                parent: Initial indication of a parent for the node
                    (default is None)
        """
        self.parent = parent
        self.children = []
        self.mask = mask_val
    
    def appendChild(self, child):
        """ Adds a reference to another node to its children list and removes
            former parent from the node and makes it the parent of the node.
            
            Args:
                child: A reference to another node on the graph to be added to
                    the children list.
            
            Returns:
                The reference of the node added to the children list. Updated
                with it's new parent.
        """
        # Check if we make a loop
        tmp_node = self
        while tmp_node is not None and tmp_node != child:
            tmp_node = tmp_node.parent
        if tmp_node is None:
            # Automate detachment from former parent (if any)
            parent_node = child.parent
            if parent_node is not None:
                for c in range(len(parent_node.children) - 1, -1, -1):
                    if parent_node.children[c] == child:
                        if c == len(parent_node.children) - 1:
                            parent_node.children = parent_node.children[:c]
                            break
                        else:
                            parent_node.children = parent_node.children[:c] + parent_node.children[c + 1:]
                            break
            # Attach the child
            self.children.append(child)
            self.children[-1].parent = self
        return child
    
    def draw(self, mask_val=DRAW_ALL):
        """ Draws the node to the screen and calls its children's draw function.
            
            Args:
                mask_val: Initial indication of what mode the graph is in
                    (default is DRAW_ALL)
        """
        if self.mask & mask_val:
            for child in self.children:
                child.draw(mask_val)


class TranslateNode(SNode):
    
    """ Is a Scene Node that translates in the world.
        
        Attributes:
            vector: A list of floats denoting a vector to travel along. Format
                goes as follows: [X, Y, Z]
    """
    
    __slots__ = ('vector')
    
    def __init__(self, vector, mask_val=DRAW_RENDER, parent=None):
        """ Initializes the TranslateNode class.
            
            Args:
                vector: Initial direction to travel along.
                mask_val: Initial indication of what modes this can be drawn in
                    (default is DRAW_RENDER)
                parent: Initial indication of a parent for the node
                    (default is None)
        """
        SNode.__init__(self, mask_val, parent)
        self.vector = vector
    
    def draw(self, mask_val=DRAW_ALL):
        """ Draws the node to the screen and applies the translation along the
            vector before calling it's children's draw function so it's children
            are affected by the translation.
            
            Args:
                mask_val: Initial indication of what mode the graph is in
                    (default is DRAW_ALL)
        """
        if self.mask & mask_val:
            glPushMatrix()
            glTranslate(*self.vector)
            for child in self.children:
                child.draw(mask_val)
            glPopMatrix()


class RotateNode(SNode):
    
    """ Is a Scene Node that rotates in the world using axis angles.
        
        Attributes:
            angle:  A float denoting the amount to rotate in degrees.
            axis: A list of floats denoting an axis to rotate along. Format goes
                as follows: [X, Y, Z]
    """
    
    __slots__ = ('angle', 'axis')
    
    def __init__(self, ang, axis, mask_val=DRAW_RENDER, parent=None):
        """ Initializes the RotateNode class.
            
            Args:
                ang: Initial angle to rotate by.
                axis: Initial axis to rotate along.
                mask_val: Initial indication of what modes this can be drawn in
                    (default is DRAW_RENDER)
                parent: Initial indication of a parent for the node
                    (default is None)
        """
        SNode.__init__(self, mask_val, parent)
        self.angle = ang
        self.axis = axis
    
    def draw(self, mask_val=DRAW_ALL):
        """ Draws the node to the screen and applies the rotation before calling
            it's children's draw function so it's children are affected by the
            rotation.
            
            Args:
                mask_val: Initial indication of what mode the graph is in
                    (default is DRAW_ALL)
        """
        if self.mask & mask_val:
            glPushMatrix()
            glRotate(self.angle, *self.axis)
            for child in self.children:
                child.draw(mask_val)
            glPopMatrix()


class TransformMatrixNode(SNode):
    
    """ Is a Scene Node that translates and/or rotates and/or scales in the
        world using a 4x4 matrix.
        
        Attributes:
            matrix: A list of floats denoting a 4x4 matrix. The matrix is stored
                in column major. For example:
                    matrix = [
                        matrix[0], matrix[4], matrix[8], matrix[12],
                        matrix[1], matrix[5], matrix[9], matrix[13],
                        matrix[2], matrix[6], matrix[10], matrix[14],
                        matrix[3], matrix[7], matrix[11], matrix[15]
                    ]
    """
    
    __slots__ = ('matrix')
    
    def __init__(self, mat=[1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1], mask_val=DRAW_RENDER, parent=None):
        """ Initializes the TransformMatrixNode class.
            
            Args:
                mat: Initial indication of a matrix to transfrom by
                    (default is the Identity Matrix)
                mask_val: Initial indication of what modes this can be drawn in
                    (default is DRAW_RENDER)
                parent: Initial indication of a parent for the node
                    (default is None)
        """
        SNode.__init__(self, mask_val, parent)
        self.matrix = mat
    
    def draw(self, mask_val=DRAW_ALL):
        """ Draws the node to the screen and applies the transfromation before
            calling it's children's draw function so it's children are affected
            by the transfromation.
            
            Args:
                mask_val: Initial indication of what mode the graph is in
                    (default is DRAW_ALL)
        """
        if self.mask & mask_val:
            glPushMatrix()
            glMultMatrixf(self.matrix)
            for child in self.children:
                child.draw(mask_val)
            glPopMatrix()


class ScaleNode(SNode):
    
    """ Is a Scene Node that scales in the world.
        
        Attributes:
            scale: A list of floats denoting how much to scale each axis. Format
                goes as follows: [X_SCALE, Y_SCALE, Z_SCALE]
    """
    
    __slots__ = ('scale')
    
    def __init__(self, scale, mask_val=DRAW_RENDER, parent=None):
        """ Initializes the ScaleNode class.
            
            Args:
                scale: Initial list to scale by.
                mask_val: Initial indication of what modes this can be drawn in
                    (default is DRAW_RENDER)
                parent: Initial indication of a parent for the node
                    (default is None)
        """
        SNode.__init__(self, mask_val, parent)
        self.scale = scale
    
    def draw(self, mask_val=DRAW_ALL):
        """ Draws the node to the screen and applies the scaling before calling
            it's children's draw function so it's children are affected by the
            scaling.
            
            Args:
                mask_val: Initial indication of what mode the graph is in
                    (default is DRAW_ALL)
        """
        if self.mask & mask_val:
            glPushMatrix()
            glScalef(*self.scale)
            for child in self.children:
                child.draw(mask_val)
            glPopMatrix()


class MeshNode(SNode):
    
    """ Is a Scene Node that creates a mesh to be drawn in the world.
        
        Attributes:
            mat_col_amb: A tuple denoting the color ambience of the mesh. Format
                goes as follows: (RED, GREEN, BLUE, ALPHA)
            mat_col_dif: A tuple denoting the color diffusion of the mesh.
                Format goes as follows: (RED, GREEN, BLUE, ALPHA)
            mat_col_spec: A tuple denoting the color specular of the mesh.
                Format goes as follows: (RED, GREEN, BLUE, ALPHA)
            mat_shine: A float denoting how much the mesh will look shiny.
            use_texture: A boolean denoting whether or not the mesh has a
                texture.
            image_id: An integer that denotes the number of textures used.
            id: An integer that is used when picking to denote object has been
                picked.
    """
    
    __slots__ = ('id', 'image_id', 'mat_col_amb', 'mat_col_dif', 'mat_col_spec', 'mat_shine', 'use_texture')
    
    def __init__(self, id=None, mat_col_amb=(0.2, 0.2, 0.2, 1.0), mat_col_dif=(0.8, 0.8, 0.8, 1.0), mat_col_spec=(1.0, 1.0, 1.0, 1.0), mat_shine=50.0, mask_val=DRAW_RENDER, parent=None):
        """ Initializes the MeshNode class.
            
            Args:
                id: Initial indication of the id for the mesh (default is None)
                mat_col_amb: Initial indication of the color ambience of the
                    mesh (default is (0.2, 0.2, 0.2, 1.0))
                mat_col_dif: Initial indication of the color diffusion of the
                    mesh (default is (0.8, 0.8, 0.8, 1.0))
                mat_col_spec: Initial indication of the color specular of the
                    mesh (default is (1.0, 1.0, 1.0, 1.0))
                mat_shine: Initial indication for the shininess the mesh
                    (default is 50.0)
                mask_val: Initial indication of what modes this can be drawn in
                    (default is DRAW_RENDER)
                parent: Initial indication of a parent for the node
                    (default is None)
        """
        SNode.__init__(self, mask_val, parent)
        self.mat_col_amb = mat_col_amb
        self.mat_col_dif = mat_col_dif
        self.mat_col_spec = mat_col_spec
        self.mat_shine = mat_shine
        self.use_texture = False
        self.image_id = 0
        self.id = id
    
    def loadTexture(self, texture_name):
        self.image_id = loadImage(texture_name)
        self.use_texture = True
    
    def draw(self, mask_val=DRAW_ALL):
        """ Draws the node to the screen and applies the settings for the mesh
            before calling it's children's draw function.
            
            Args:
                mask_val: Initial indication of what mode the graph is in
                    (default is DRAW_ALL)
        """
        if self.mask & mask_val:
            if self.use_texture:
                glEnable(GL_TEXTURE_2D)
                glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
                glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
                glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
                glBindTexture(GL_TEXTURE_2D, self.image_id)
            glPushAttrib(GL_LIGHTING_BIT)
            glMaterial(GL_FRONT, GL_AMBIENT, self.mat_col_amb)
            glMaterial(GL_FRONT, GL_DIFFUSE, self.mat_col_dif)
            glMaterial(GL_FRONT, GL_SPECULAR, self.mat_col_spec)
            glMaterial(GL_FRONT, GL_SHININESS, self.mat_shine)
            if self.id:
                glLoadName(self.id)
            glPushMatrix()
            self.drawMesh()
            if self.use_texture:
                glDisable(GL_TEXTURE_2D)
            glPopAttrib()
            for child in self.children:
                child.draw(mask_val)
            glPopMatrix()
    
    def drawMesh(self):
        """Used in classes that inherit from this class."""
        pass


class GlBackground(SNode):
    
    """ Is a Scene Node that creates and draws a background to be used, using
        GL_QUADS. Has the ability to do gradients.
    """
    def draw(self, mask_val=DRAW_ALL):
        """ Draws the node to the screen.
            
            Args:
                mask_val: Initial indication of what mode the graph is in
                    (default is DRAW_ALL)
        """
        global global_bg_color1, global_bg_color2, global_bg_style
        if self.mask & mask_val:
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_LIGHTING)
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            glTranslated(0.0, 0.0, -1.0)
            glBegin(GL_QUADS)
            if global_bg_style == HORIZONTAL:
                glColor3f(*global_bg_color1)
                glVertex2f(1.0, 1.0)
                glVertex2f(-1.0, 1.0)
                glColor3f(*global_bg_color2)
                glVertex2f(-1.0, -1.0)
                glVertex2f(1.0, -1.0)
                glEnd()
            else:
                glColor3f(*global_bg_color1)
                glVertex2f(-1.0, 1.0)
                glVertex2f(-1.0, -1.0)
                glColor3f(*global_bg_color2)
                glVertex2f(1.0, -1.0)
                glVertex2f(1.0, 1.0)
                glEnd()
            glPopMatrix()
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_LIGHTING)
            glMatrixMode(GL_MODELVIEW)
            
            for child in self.children:
                child.draw(mask_val)


class GlPlane(SNode):
    
    """ Is a Scene Node that creates and draws a grid to be used as a plane
        using GL_LINES.
    """
    def draw(self, mask_val=DRAW_ALL):
        """ Draws the node to the screen.
            
            Args:
                mask_val: Initial indication of what mode the graph is in
                    (default is DRAW_ALL)
        """
        global global_grid_color, global_grid_alpha
        if self.mask & mask_val:
            glDisable(GL_LIGHTING)
            glEnable(GL_BLEND)
            glEnable(GL_LINE_SMOOTH)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glBegin(GL_LINES)
            for x in range(-120, 132, 12):
                if x == 0:
                    glColor4f(0, 0, 1, global_grid_alpha)
                else:
                    glColor4f(*(global_grid_color + [global_grid_alpha]))
                glVertex3f(x, 0.0, -120)
                glVertex3f(x, 0.0, 120)
            for z in range(-120, 132, 12):
                if z == 0:
                    glColor4f(1, 0, 0, global_grid_alpha)
                else:
                    glColor4f(*(global_grid_color + [global_grid_alpha]))
                glVertex3f(-120, 0.0, z)
                glVertex3f(120, 0.0, z)
            
            glEnd()
            glDisable(GL_LINE_SMOOTH)
            glDisable(GL_BLEND)
            glEnable(GL_LIGHTING)


class GlAxis(SNode):
    
    """ Is a Scene Node that creates and draws a set of axes to represent
        orientation the camera is in using GL_LINES.
        
        Attributes:
            trans_matrix: A list of floats denoting a 4x4 matrix. The matrix is
                stored in column major. For example:
                    matrix = [
                        matrix[0], matrix[4], matrix[8], matrix[12],
                        matrix[1], matrix[5], matrix[9], matrix[13],
                        matrix[2], matrix[6], matrix[10], matrix[14],
                        matrix[3], matrix[7], matrix[11], matrix[15]
                    ]
            matrix: A list of floats denoting a 4x4 matrix. The matrix is stored
                in column major.
    """
    
    __slots__ = ('matrix', 'trans_matrix')
    
    def __init__(self, mask_val=DRAW_RENDER):
        """ Initializes the GlAxis class.
            
            Args:
                mask_val: Initial indication of what modes this can be drawn in
                    (default is DRAW_RENDER)
        """
        SNode.__init__(self, mask_val)
        self.matrix = _IDENTITY_MATRIX
        self.trans_matrix = [
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.85, -0.85, -0.3, 1.0
        ]
    
    def draw(self, mask_val=DRAW_ALL):
        """ Draws the node to the screen.
            
            Args:
                mask_val: Initial indication of what mode the graph is in
                    (default is DRAW_ALL)
        """
        if self.mask & mask_val:
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_LIGHTING)
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            
            gluOrtho2D(-1, 1, -1, 1)
            
            glMatrixMode(GL_MODELVIEW)
            
            glPushMatrix()
            glMultMatrixf(self.trans_matrix)
            glMultMatrixf(self.matrix)
            
            line_size = 0.09
            glBegin(GL_LINES)
            # X axis
            glColor3f(1.0, 0.0, 0.0)
            # Shaft
            glVertex3f(0.0, 0.0, 0.0)
            glVertex3f(line_size, 0.0, 0.0)
            # Head-Bottom
            glVertex3f((line_size / 5.0) * 4, 0.0, line_size / 5.0)
            glVertex3f((line_size / 5.0) * 4, 0.0, -line_size / 5.0)
            # Head-Side1
            glVertex3f((line_size / 5.0) * 4, 0.0, -line_size / 5.0)
            glVertex3f(line_size, 0.0, 0.0)
            # Head-Side2
            glVertex3f((line_size / 5.0) * 4, 0.0, line_size / 5.0)
            glVertex3f(line_size, 0.0, 0.0)
            
            # Y axis
            glColor3f(0.0, 1.0, 0.0)
            # Shaft
            glVertex3f(0.0, 0.0, 0.0)
            glVertex3f(0.0, line_size, 0.0)
            # Head-Bottom
            glVertex3f(line_size / 5.0, (line_size / 5.0) * 4, 0.0)
            glVertex3f(-line_size / 5.0, (line_size / 5.0) * 4, 0.0)
            # Head-Side1
            glVertex3f(-line_size / 5.0, (line_size / 5.0) * 4, 0.0)
            glVertex3f(0.0, line_size, 0.0)
            # Head-Side2
            glVertex3f(line_size / 5.0, (line_size / 5.0) * 4, 0.0)
            glVertex3f(0.0, line_size, 0.0)
            
            # Z axis
            glColor3f(0.0, 0.0, 1.0)
            # Shaft
            glVertex3f(0.0, 0.0, 0.0)
            glVertex3f(0.0, 0.0, line_size)
            # Head-Bottom
            glVertex3f(line_size / 5.0, 0.0, (line_size / 5.0) * 4)
            glVertex3f(-line_size / 5.0, 0.0, (line_size / 5.0) * 4)
            # Head-Side1
            glVertex3f(-line_size / 5.0, 0.0, (line_size / 5.0) * 4)
            glVertex3f(0.0, 0.0, line_size)
            # Head-Side2
            glVertex3f(line_size / 5.0, 0.0, (line_size / 5.0) * 4)
            glVertex3f(0.0, 0.0, line_size)
            
            glEnd()
            glPopMatrix()
            
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)
            
            glEnable(GL_LIGHTING)
            glEnable(GL_DEPTH_TEST)


class TranslationMeshNode(SNode):
    
    """ Is a Scene Node that creates and draws translation axes at the origin of
        a bone in the world.
        
        Attributes:
            position: A list of floats denoting a position in the world. Format
                goes as follows: [X, Y, Z]
            orientation: A list of floats denoting a 4x4 orientation matrix. The
                matrix is stored in column major. For example:
                    matrix = [
                        matrix[0], matrix[4], matrix[8], matrix[12],
                        matrix[1], matrix[5], matrix[9], matrix[13],
                        matrix[2], matrix[6], matrix[10], matrix[14],
                        matrix[3], matrix[7], matrix[11], matrix[15]
                    ]
            parent_orient: A list of floats denoting a 4x4 orientation matrix.
                The matrix is stored in column major.
            scale: A boolean that denotes whether the user selected the scale
                mesh.
            x_trans: A boolean that denotes whether the user selected the local
                x axis mesh.
            y_trans: A boolean that denotes whether the user selected the local
                y axis mesh.
            z_trans: A boolean that denotes whether the user selected the local
                z axis mesh.
            x_par_trans: A boolean that denotes whether the user selected the
                parent's local x axis mesh.
            y_par_trans: A boolean that denotes whether the user selected the
                parent's local y axis mesh.
            z_par_trans: A boolean that denotes whether the user selected the
                parent's local z axis mesh.
    """
    
    __slots__ = (
        'orientation',
        'parent_orient',
        'position',
        'scale',
        'x_par_trans',
        'x_trans',
        'y_par_trans',
        'y_trans',
        'z_par_trans',
        'z_trans'
    )
    
    def __init__(self, pos=_ZERO_POSITION, orient=_IDENTITY_MATRIX, par_orient=_IDENTITY_MATRIX, mask_val=DRAW_GUI_TRANS | DRAW_TRANS_CLICK, parent=None):
        """ Initializes the TranslationMeshNode class.
            
            Args:
                pos: Initial indication of a position
                    (default is _ZERO_POSITION)
                orient: Initial indication of an orientation matrix
                    (default is _IDENTITY_MATRIX)
                par_orient: Initial indication of an orientation matrix
                    (default is _IDENTITY_MATRIX)
                mask_val: Initial indication of what modes this can be drawn in
                    (default is DRAW_GUI_TRANS | DRAW_TRANS_CLICK)
                parent: Initial indication of a parent for the node
                    (default is None)
        """
        SNode.__init__(self, mask_val, parent)
        self.position = pos
        self.orientation = orient
        self.parent_orient = par_orient
        self.scale = False
        self.x_trans = False
        self.y_trans = False
        self.z_trans = False
        self.x_par_trans = False
        self.y_par_trans = False
        self.z_par_trans = False
    
    def setBools(self, string=''):
        """ Sets the booleans based on what is passed in.
            
            Args:
                string: A string that denotes what boolean has been set
                    (default is '')
        """
        if string == 'scale':
            self.scale = True
            self.x_trans = False
            self.y_trans = False
            self.z_trans = False
            self.x_par_trans = False
            self.y_par_trans = False
            self.z_par_trans = False
        elif string == 'x_trans':
            self.scale = False
            self.x_trans = True
            self.y_trans = False
            self.z_trans = False
            self.x_par_trans = False
            self.y_par_trans = False
            self.z_par_trans = False
        elif string == 'y_trans':
            self.scale = False
            self.x_trans = False
            self.y_trans = True
            self.z_trans = False
            self.x_par_trans = False
            self.y_par_trans = False
            self.z_par_trans = False
        elif string == 'z_trans':
            self.scale = False
            self.x_trans = False
            self.y_trans = False
            self.z_trans = True
            self.x_par_trans = False
            self.y_par_trans = False
            self.z_par_trans = False
        elif string == 'x_par_trans':
            self.scale = False
            self.x_trans = False
            self.y_trans = False
            self.z_trans = False
            self.x_par_trans = True
            self.y_par_trans = False
            self.z_par_trans = False
        elif string == 'y_par_trans':
            self.scale = False
            self.x_trans = False
            self.y_trans = False
            self.z_trans = False
            self.x_par_trans = False
            self.y_par_trans = True
            self.z_par_trans = False
        elif string == 'z_par_trans':
            self.scale = False
            self.x_trans = False
            self.y_trans = False
            self.z_trans = False
            self.x_par_trans = False
            self.y_par_trans = False
            self.z_par_trans = True
        else:
            self.scale = False
            self.x_trans = False
            self.y_trans = False
            self.z_trans = False
            self.x_par_trans = False
            self.y_par_trans = False
            self.z_par_trans = False
    
    def draw(self, mask_val=DRAW_ALL):
        """ Draws the node to the screen.
            
            Args:
                mask_val: Initial indication of what mode the graph is in
                    (default is DRAW_ALL)
        """
        if DRAW_GUI_TRANS & mask_val:
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_LIGHTING)
        
        if self.mask & mask_val:
            glPushMatrix()
            # Position the TranslationMeshNode
            glTranslate(*self.position)
            
            # Orient the TranslationMeshNode parent
            glPushMatrix()
            glMultMatrixf(self.parent_orient)
            glEnable(GL_CULL_FACE)
            glCullFace(GL_FRONT)
            
            # Translate axes of parent orient of bone
            # Parent X axis
            if self.x_par_trans:
                glColor3f(1, 0.25, 0.25)
            else:
                glColor3f(1, 0.5, 0.5)
            glLoadName(5)
            glPushMatrix()
            glScalef(4.0, 2.0, 2.0)
            glTranslate(0.5, 0.0, 0.0)
            glutSolidCube(0.5)
            glScalef(0.5, 0.5, 0.5)
            glTranslate(0.4, 0.0, 0.0)
            glRotate(90, 0, 1, 0)
            glRotate(45, 0, 0, 1)
            glutSolidCone(1.0, 1.0, 4, 1)
            glPopMatrix()
            
            # Parent Y axis
            if self.y_par_trans:
                glColor3f(0.25, 1, 0.25)
            else:
                glColor3f(0.5, 1, 0.5)
            glLoadName(6)
            glPushMatrix()
            glScalef(2.0, 4.0, 2.0)
            glTranslate(0.0, 0.5, 0.0)
            glutSolidCube(0.5)
            glScalef(0.5, 0.5, 0.5)
            glTranslate(0.0, 0.4, 0.0)
            glRotate(-90, 1, 0, 0)
            glRotate(45, 0, 0, 1)
            glutSolidCone(1.0, 1.0, 4, 1)
            glPopMatrix()
            
            # Parent Z axis
            if self.z_par_trans:
                glColor3f(0.25, 0.25, 1)
            else:
                glColor3f(0.5, 0.5, 1)
            glLoadName(7)
            glPushMatrix()
            glScalef(2.0, 2.0, 4.0)
            glTranslate(0.0, 0.0, 0.5)
            glutSolidCube(0.5)
            glScalef(0.5, 0.5, 0.5)
            glTranslate(0.0, 0.0, 0.4)
            glRotate(45, 0, 0, 1)
            glutSolidCone(1.0, 1.0, 4, 1)
            glPopMatrix()
            
            glDisable(GL_CULL_FACE)
            glPopMatrix()
            
            # Orient the TranslationMeshNode
            glPushMatrix()
            glMultMatrixf(self.orientation)
            
            # Translate axes of local orient of bone
            # X axis
            if self.x_trans:
                glColor3f(1, 0, 0)
            else:
                glColor3f(0.5, 0, 0)
            glLoadName(2)
            glPushMatrix()
            glScalef(2.0, 1.0, 1.0)
            glTranslate(0.75, 0.0, 0.0)
            glutSolidCube(0.5)
            glScalef(0.5, 0.5, 0.5)
            glTranslate(0.5, 0.0, 0.0)
            glRotate(90, 0, 1, 0)
            glRotate(45, 0, 0, 1)
            glutSolidCone(1.0, 1.0, 4, 1)
            glPopMatrix()
            
            # Y axis
            if self.y_trans:
                glColor3f(0, 1, 0)
            else:
                glColor3f(0, 0.5, 0)
            glLoadName(3)
            glPushMatrix()
            glScalef(1.0, 2.0, 1.0)
            glTranslate(0.0, 0.75, 0.0)
            glutSolidCube(0.5)
            glScalef(0.5, 0.5, 0.5)
            glTranslate(0.0, 0.5, 0.0)
            glRotate(-90, 1, 0, 0)
            glRotate(45, 0, 0, 1)
            glutSolidCone(1.0, 1.0, 4, 1)
            glPopMatrix()
            
            # Z axis
            if self.z_trans:
                glColor3f(0, 0, 1)
            else:
                glColor3f(0, 0, 0.5)
            glLoadName(4)
            glPushMatrix()
            glScalef(1.0, 1.0, 2.0)
            glTranslate(0.0, 0.0, 0.75)
            glutSolidCube(0.5)
            glScalef(0.5, 0.5, 0.5)
            glTranslate(0.0, 0.0, 0.5)
            glRotate(45, 0, 0, 1)
            glutSolidCone(1.0, 1.0, 4, 1)
            glPopMatrix()
            
            # Scale length of bone
            if self.scale:
                glColor3f(1, 0, 1)
            else:
                glColor3f(0.5, 0, 0.5)
            glLoadName(1)
            glPushMatrix()
            glTranslate(0.0, 5.0, 0.0)
            glutSolidCube(0.5)
            glPopMatrix()
            glPopMatrix()
            
            glPopMatrix()
        
        if DRAW_GUI_TRANS & mask_val:
            glEnable(GL_LIGHTING)
            glEnable(GL_DEPTH_TEST)


class RotationMeshNode(SNode):
    
    """ Is a Scene Node that creates and draws rotation axes at the origin of
        a bone in the world.
        
        Attributes:
            position: A list of floats denoting a position in the world. Format
                goes as follows: [X, Y, Z]
            orientation: A list of floats denoting a 4x4 orientation matrix. The
                matrix is stored in column major. For example:
                    matrix = [
                        matrix[0], matrix[4], matrix[8], matrix[12],
                        matrix[1], matrix[5], matrix[9], matrix[13],
                        matrix[2], matrix[6], matrix[10], matrix[14],
                        matrix[3], matrix[7], matrix[11], matrix[15]
                    ]
            scale: A boolean that denotes whether the user selected the scale
                mesh.
            x_rot: A boolean that denotes whether the user selected the local x
                axis mesh.
            y_rot: A boolean that denotes whether the user selected the local y
                axis mesh.
            z_rot: A boolean that denotes whether the user selected the local z
                axis mesh.
    """
    
    __slots__ = ('orientation', 'position', 'scale', 'x_rot', 'y_rot', 'z_rot')
    
    def __init__(self, pos=_ZERO_POSITION, orient=_IDENTITY_MATRIX, mask_val=DRAW_GUI_ROT | DRAW_ROT_CLICK, parent=None):
        """ Initializes the RotationMeshNode class.
            
            Args:
                pos: Initial indication of a position
                    (default is _ZERO_POSITION)
                orient: Initial indication of an orientation matrix
                    (default is _IDENTITY_MATRIX)
                mask_val: Initial indication of what modes this can be drawn in
                    (default is DRAW_GUI_ROT | DRAW_ROT_CLICK)
                parent: Initial indication of a parent for the node
                    (default is None)
        """
        SNode.__init__(self, mask_val, parent)
        self.position = pos
        self.orientation = orient
        self.scale = False
        self.x_rot = False
        self.y_rot = False
        self.z_rot = False
    
    def setBools(self, string=''):
        """ Sets the booleans based on what is passed in.
            
            Args:
                string: A string that denotes what boolean has been set
                    (default is '')
        """
        if string == 'scale':
            self.scale = True
            self.x_rot = False
            self.y_rot = False
            self.z_rot = False
        elif string == 'x_rot':
            self.scale = False
            self.x_rot = True
            self.y_rot = False
            self.z_rot = False
        elif string == 'y_rot':
            self.scale = False
            self.x_rot = False
            self.y_rot = True
            self.z_rot = False
        elif string == 'z_rot':
            self.scale = False
            self.x_rot = False
            self.y_rot = False
            self.z_rot = True
        else:
            self.scale = False
            self.x_rot = False
            self.y_rot = False
            self.z_rot = False
    
    def draw(self, mask_val=DRAW_ALL):
        """ Draws the node to the screen.
            
            Args:
                mask_val: Initial indication of what mode the graph is in
                    (default is DRAW_ALL)
        """
        if DRAW_GUI_ROT & mask_val:
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_LIGHTING)
        
        if self.mask & mask_val:
            glPushMatrix()
            # Position and Orient the RotationMeshNode
            glTranslate(*self.position)
            glMultMatrixf(self.orientation)
            
            # Rotate axes of local orient of bone
            # X axis
            glLoadName(8)
            glBegin(GL_LINES)
            glColor3f(1, 0, 0)
            glVertex3f(0.0, 0.0, 0.0)
            glVertex3f(4.0, 0.0, 0.0)
            glEnd()
            if not self.x_rot:
                glColor3f(0.5, 0, 0)
            glPushMatrix()
            glTranslate(3.0, 0.0, 0.0)
            glRotate(90, 0, 1, 0)
            glutSolidTorus(0.25, 0.75, 4, 16)
            glPopMatrix()
            
            # Y axis
            glLoadName(9)
            glBegin(GL_LINES)
            glColor3f(0, 1, 0)
            glVertex3f(0.0, 0.0, 0.0)
            glVertex3f(0.0, 4.0, 0.0)
            glEnd()
            if not self.y_rot:
                glColor3f(0, 0.5, 0)
            glPushMatrix()
            glTranslate(0.0, 3.0, 0.0)
            glRotate(-90, 1, 0, 0)
            glutSolidTorus(0.25, 0.75, 4, 16)
            glPopMatrix()
            
            # Z axis
            glLoadName(10)
            glBegin(GL_LINES)
            glColor3f(0, 0, 1)
            glVertex3f(0.0, 0.0, 0.0)
            glVertex3f(0.0, 0.0, 4.0)
            glEnd()
            if not self.z_rot:
                glColor3f(0, 0, 0.5)
            glPushMatrix()
            glTranslate(0.0, 0.0, 3.0)
            glutSolidTorus(0.25, 0.75, 4, 16)
            glPopMatrix()
            
            # Scale length of bone
            if self.scale:
                glColor3f(1, 0, 1)
            else:
                glColor3f(0.5, 0, 0.5)
            glLoadName(1)
            glPushMatrix()
            glTranslate(0.0, 5.0, 0.0)
            glutSolidCube(0.5)
            glPopMatrix()
            
            glPopMatrix()
        
        if DRAW_GUI_ROT & mask_val:
            glEnable(GL_LIGHTING)
            glEnable(GL_DEPTH_TEST)


class SkeletonMeshNode(MeshNode):
    
    """ Is a Mesh Node that creates a bone mesh to be drawn in the world.
        
        Attributes:
            position: A list of floats denoting a position in the world. Format
                goes as follows: [X, Y, Z]
            quad : An instance of gluNewQuadric. Used for doing GLU calls.
    """
    
    __slots__ = ('position', 'quad')
    
    def __init__(self, id, pos=_ZERO_POSITION, mask=DRAW_RENDER | DRAW_BONE_CLICK, par=None):
        """ Initializes the SkeletonMeshNode class.
            
            Args:
                id: Initial indication of the id of the skeleton.
                pos: Initial indication of the position of the skeleton
                    (default is _ZERO_POSITION)
                mask: Initial indication of what modes this can be drawn in
                    (default is DRAW_RENDER | DRAW_BONE_CLICK)
                parent: Initial indication of a parent for the node
                    (default is None)
        """
        MeshNode.__init__(self, id, mat_col_dif=(1.0, 1.0, 1.0, 1.0), mask_val=mask, parent=par)
        self.position = pos
        self.quad = gluNewQuadric()
        
    def drawMesh(self):
        """Draws the skeleton mesh."""
        glPushMatrix()
        # Translate Skeleton
        glTranslate(*self.position)
        
        # X-Axis
        glPushMatrix()
        glRotate(90, 0, 1, 0)
        glRotate(45, 0, 0, 1)
        glTranslate(0, 0, -0.175)
        glMaterial(GL_FRONT, GL_DIFFUSE, [1, 0, 0, 1])
        gluCylinder(self.quad, .25, .25, 2, 4, 4)
        glTranslate(0, 0, 2)
        gluDisk(self.quad, 0, .25, 4, 4)
        glPopMatrix()
        
        # Y-Axis
        glPushMatrix()
        glRotate(-90, 1, 0, 0)
        glRotate(45, 0, 0, 1)
        glTranslate(0, 0, -0.175)
        glMaterial(GL_FRONT, GL_DIFFUSE, [0, 1, 0, 1])
        gluCylinder(self.quad, .25, .25, 2, 4, 4)
        glTranslate(0, 0, 2)
        gluDisk(self.quad, 0, .25, 4, 4)
        glPopMatrix()
        
        # Z-Axis
        glPushMatrix()
        glRotate(45, 0, 0, 1)
        glTranslate(0, 0, -0.175)
        glMaterial(GL_FRONT, GL_DIFFUSE, [0, 0, 1, 1])
        gluCylinder(self.quad, .25, .25, 2, 4, 4)
        glTranslate(0, 0, 2)
        gluDisk(self.quad, 0, .25, 4, 4)
        glPopMatrix()
        
        glPopMatrix()
    
    def appendChild(self, child):
        """ Adds a reference to another node to its children list and if node is
            an instance of BoneMeshNode it sets its position to _ZERO_POSITION.
            
            Args:
                child: A reference to another node on the graph to be added to
                    the children list.
            
            Returns:
                The reference of the node added to the children list. Updated
                with it's new parent.
            """
        return_node = SNode.appendChild(self, child)
        if type(child) is BoneMeshNode:
            child.position = _ZERO_POSITION
        return return_node


class OBJMeshNode(MeshNode):
    
    """ Is a Mesh Node that loads a object file and creates a mesh to be drawn
        in the world.
        
        Attributes:
            face_list: A list that contains the coordinates for the vertices.
            final_verts: A list that contains the list of values for the
                vertices.
            final_norms: A list that contains the list of values for the
                normals.
    """
    
    __slots__ = ('face_list', 'final_norms', 'final_verts', 'normal_buffer', 'vertex_buffer')
    
    def __init__(self, file_name, id=None, mat_col_amb=(0.2, 0.2, 0.2, 1.0), mat_col_dif=(0.8, 0.8, 0.8, 1.0), mat_col_spec=(1.0, 1.0, 1.0, 1.0), mat_shine=50.0, mask_val=DRAW_RENDER, parent=None):
        """ Initializes the OBJMeshNode class.
            
            Args:
                file_name: Initial indication of the path and file name of the
                    object file.
                id: Initial indication of the id for the mesh (default is None)
                mat_col_amb: Initial indication of the color ambience of the
                    mesh (default is (0.2, 0.2, 0.2, 1.0))
                mat_col_dif: Initial indication of the color diffusion of the
                    mesh (default is (0.7, 0.7, 0.7, 1.0))
                mat_col_spec: Initial indication of the color specular of the
                    mesh (default is (1.0, 1.0, 1.0, 1.0))
                mat_shine: Initial indication for the shininess the mesh
                    (default is 50.0)
                mask_val: Initial indication of what modes this can be drawn in
                    (default is DRAW_RENDER)
                parent: Initial indication of a parent for the node
                    (default is None)
        """
        if id is None:
            MeshNode.__init__(self, len(file_name), mat_col_amb, mat_col_dif, mat_col_spec, mat_shine, mask_val, parent)
        else:
            MeshNode.__init__(self, id, mat_col_amb, mat_col_dif, mat_col_spec, mat_shine, mask_val, parent)
        self.face_list = []
        self.final_verts = []
        self.final_norms = []
        self.normal_buffer = None
        self.vertex_buffer = None
        self.loadMesh(file_name)
    
    def loadMesh(self, file_name):
        """ Loads in a object file.
            
            Args:
                file_name: A string that denotes the path and file name of the
                    object file.
        """
        vert_list = []
        norm_list = []
        vert_dict = {}
        
        # Load the obj file
        obj_file = open(FILE_PATH + file_name, "r")
        while True:
            line = obj_file.readline()
            if len(line) == 0:
                break
            mesh_type = ""
            i = 0
            while not len(line[i].strip()) == 0:
                mesh_type += line[i]
                i += 1
            
            if mesh_type == 'v':
                vert = [float(f) for f in line[i:].strip().split(' ')]
                vert_list.append(vert)
            elif mesh_type == 'vn':
                norm = [float(f) for f in line[i:].strip().split(' ')]
                norm_list.append(norm)
            elif mesh_type == 'f':
                face_verts = []
                face_coords = []
                face_norms = []
                face_groups = line[i:].strip().split(' ')
                
                for f in face_groups:
                    splits = f.split('/')
                    face_verts.append(int(splits[0]) - 1)
                    if len(splits) > 1:
                        if len(splits[1]) > 0:
                            face_coords.append(int(splits[1]) - 1)
                        else:
                            face_coords.append(0)
                        if len(splits) > 2:
                            face_norms.append(int(splits[2]) - 1)
                        else:
                            face_norms.append(0)
                    else:
                        face_coords.append(0)
                        face_norms.append(0)
                
                for i in range(len(face_verts)):
                    key = (face_verts[i], face_norms[i])
                    final_index = -1
                    if vert_dict.has_key(key):
                        final_index = vert_dict[key]
                    else:
                        final_index = len(self.final_verts)
                        self.final_verts.append(vert_list[face_verts[i]])
                        self.final_norms.append(norm_list[face_norms[i]])
                        vert_dict[key] = final_index
                    face_verts[i] = final_index
                
                for i in range(1, len(face_groups) - 1):
                    self.face_list.append(face_verts[0])
                    self.face_list.append(face_verts[i])
                    self.face_list.append(face_verts[i + 1])
        
        # Load vertices to the buffer
        numpy_data = numpy.array(self.final_verts, dtype=numpy.float32)
        self.vertex_buffer = vbo.VBO(numpy_data)
        
        # Load normals to the buffer
        numpy_data = numpy.array(self.final_norms, dtype=numpy.float32)
        self.normal_buffer = vbo.VBO(numpy_data)
        
        obj_file.close()
    
    drawMesh=None
    
    def _drawMeshGLArray(self):
        """Draws the object mesh using arrays."""
        # Bind vertices to the buffer
        glEnableClientState(GL_VERTEX_ARRAY)
        self.vertex_buffer.bind()
        
        glVertexPointer(3, GL_FLOAT, 0, self.vertex_buffer)
        
        # Bind normals to the buffer
        glEnableClientState(GL_NORMAL_ARRAY)
        self.normal_buffer.bind()
        
        glNormalPointer(GL_FLOAT, 0, self.normal_buffer)
        
        # Draw faces
        glDrawElementsui(GL_TRIANGLES, self.face_list)
        
        # Disable the client states and empty the buffers
        self.normal_buffer.unbind()
        glDisableClientState(GL_NORMAL_ARRAY)
        
        self.vertex_buffer.unbind()
        glDisableClientState(GL_VERTEX_ARRAY)
    
    def _drawMeshGLVert(self):
        """Draws the object mesh using verts."""
        glBegin(GL_TRIANGLES)
        for f in range(0, len(self.face_list), 3):
            curVert = self.final_verts[self.face_list[f]]
            curNorm = self.final_norms[self.face_list[f]]
            glNormal3f(curNorm[0], curNorm[1], curNorm[2])
            glVertex3f(curVert[0], curVert[1], curVert[2])
            curVert = self.final_verts[self.face_list[f + 1]]
            curNorm = self.final_norms[self.face_list[f + 1]]
            glNormal3f(curNorm[0], curNorm[1], curNorm[2])
            glVertex3f(curVert[0], curVert[1], curVert[2])
            curVert = self.final_verts[self.face_list[f + 2]]
            curNorm = self.final_norms[self.face_list[f + 2]]
            glNormal3f(curNorm[0], curNorm[1], curNorm[2])
            glVertex3f(curVert[0], curVert[1], curVert[2])
        glEnd()


class BoneMeshNode(OBJMeshNode):
    
    """ Is a Scene Node that creates a bone mesh to be drawn in the world.
        
        Attributes:
            draw_method: An integer that is used to determine how to draw the
                bone.
            length: A float that denotes the length of the bone.
            orientation: A list of floats denoting a 4x4 orientation matrix. The
                matrix is stored in column major. For example:
                    matrix = [
                        matrix[0], matrix[4], matrix[8], matrix[12],
                        matrix[1], matrix[5], matrix[9], matrix[13],
                        matrix[2], matrix[6], matrix[10], matrix[14],
                        matrix[3], matrix[7], matrix[11], matrix[15]
                    ]
            position: A list of floats denoting a position in the world. Format
                goes as follows: [X, Y, Z]
            quad : An instance of gluNewQuadric. Used for doing GLU calls.
            scale : A list of floats denoting the scale of the bone in the
                world. Format goes as follows: [X, Y, Z]
    """
    
    __slots__ = ('draw_method', 'length', 'orientation', 'position', 'quad', 'scale')
    
    def __init__(self, id, length=1, pos=_ZERO_POSITION, orient=_IDENTITY_MATRIX, draw_method=NORMAL_DRAW, mask=DRAW_RENDER | DRAW_BONE_CLICK, par=None, file_name=None, scale=[1, 1, 1]):
        """ Initializes the BoneMeshNode class.
            
            Args:
                id: Initial indication of the id of the bone.
                length: Initial indication of the length of the bone
                    (default is 1)
                pos: Initial indication of the position of the bone
                    (default is origin)
                orient: Initial indication of a matrix to orient by
                    (default is the Identity Matrix)
                mask: Initial indication of what modes this can be drawn in
                    (default is DRAW_RENDER | DRAW_BONE_CLICK)
                parent: Initial indication of a parent for the node
                    (default is None)
                file_name: Initial indication of the path and file name of the
                    object file (default is None)
        """
        if draw_method == MESH_DRAW and file_name is not None:
            OBJMeshNode.__init__(self, file_name, id=id, mat_col_amb=(0.0, 0.0, 0.6, 1.0), mask_val=mask, parent=par)
        else:
            if draw_method == MESH_DRAW:
                draw_method = NORMAL_DRAW
            MeshNode.__init__(self, id=id, mat_col_amb=(0.0, 0.0, 0.6, 1.0), mask_val=mask, parent=par)
        self.orientation = orient # Assume as a rotation matrix
        self.length = length
        self.position = pos
        self.draw_method = draw_method
        self.quad = gluNewQuadric()
        self.scale = scale
        
    def drawMesh(self):
        """Draws the bone mesh."""
        global global_head_color, global_tail_color
        if self.draw_method == NORMAL_DRAW:
            glPushMatrix()
            # Translate Bone
            glTranslate(*self.position)
            
            # Set up local orientation
            glMultMatrixf(self.orientation)
            
            # Draw Head
            glMaterial(GL_FRONT, GL_DIFFUSE, global_head_color + [1])
            glutSolidCube(2)
            
            # Rotate to make Tail point up and Scale
            glRotate(-90, 1, 0, 0)
            glScalef(BONE_SCALE, BONE_SCALE, BONE_SCALE)
            
            # Scale Tail to length
            glScalef(1.0, 1.0, self.length)
            
            # Draw Tail
            glMaterial(GL_FRONT, GL_DIFFUSE, global_tail_color + [1])
            glutSolidCone(1.0, 1.0, 4, 1)
            
            # Undo Rotation and Scales
            glPopMatrix()
        elif self.draw_method == POINTS_DRAW:
            glPushMatrix()
            # Translate Points to base position
            glTranslate(*self.position)
            
            # Orient Points
            glMultMatrixf(self.orientation)
            
            # Translate Point1 to position
            glPushMatrix()
            glTranslate(1, 0, 0)
            # Draw Point1
            glMaterial(GL_FRONT, GL_DIFFUSE, global_head_color + [1])
            gluSphere(self.quad, 0.5, 8, 8)
            # Undo Translate of Point1
            glPopMatrix()
            
            # Translate Point2 to position
            glPushMatrix()
            glTranslate(-1, 0, 0)
            # Draw Point2
            glMaterial(GL_FRONT, GL_DIFFUSE, global_head_color + [1])
            gluSphere(self.quad, 0.5, 8, 8)
            # Undo Translate of Point2
            glPopMatrix()
            
            # Translate Point3 to top position
            glPushMatrix()
            glTranslate(0, self.length * BONE_SCALE, 0)
            # Draw Point3
            glMaterial(GL_FRONT, GL_DIFFUSE, global_tail_color + [1])
            gluSphere(self.quad, 0.5, 8, 8)
            # Undo Translate of Point3
            glPopMatrix()
            
            # Undo Rotation and Translation
            glPopMatrix()
        elif self.draw_method == LINES_DRAW:
            glPushMatrix()
            # Translate Bone
            glTranslate(*self.position)
            
            # Set up local orientation
            glMultMatrixf(self.orientation)
            
            # Rotate to make Tail point up and Scale
            
            glRotate(-90, 1, 0, 0)
            glRotate(45, 0, 0, 1)
            glMaterial(GL_FRONT, GL_DIFFUSE, global_head_color + [1])
            gluCylinder(self.quad, .5, .5, self.length * BONE_SCALE, 4, 4)
            gluDisk(self.quad, 0, .5, 4, 4)
            
            glTranslate(0, 0, self.length * BONE_SCALE)
            glMaterial(GL_FRONT, GL_DIFFUSE, global_tail_color + [1])
            gluDisk(self.quad, 0, .5, 4, 4)
            
            # Undo Rotation and Scales
            glPopMatrix()
        elif self.draw_method == MESH_DRAW:
            glPushMatrix()
            # Translate Bone
            glTranslate(*self.position)
            
            # Set up local orientation
            glMultMatrixf(self.orientation)
            glScalef(*self.scale)
            
            OBJMeshNode.drawMesh(self)
            
            # Undo Rotation and Scales
            glPopMatrix()
    
    def appendChild(self, child):
        """ Adds a reference to another node to its children list and if node is
            an instance of BoneMeshNode it sets its position to _ZERO_POSITION.
            
            Args:
                child: A reference to another node on the graph to be added to
                    the children list.
            
            Returns:
                The reference of the node added to the children list. Updated
                with it's new parent.
        """
        return_node = SNode.appendChild(self, child)
        if type(child) is BoneMeshNode:
            child.position = _ZERO_POSITION
        return return_node


class GluCylinderNode(MeshNode):
    
    """ Is a Scene Node that creates a cylinder mesh to be drawn in the world.
        
        Attributes:
            height: A float that denotes the height of the cylinder.
            orientation: A list of floats denoting a 4x4 orientation matrix. The
                matrix is stored in column major. For example:
                    matrix = [
                        matrix[0], matrix[4], matrix[8], matrix[12],
                        matrix[1], matrix[5], matrix[9], matrix[13],
                        matrix[2], matrix[6], matrix[10], matrix[14],
                        matrix[3], matrix[7], matrix[11], matrix[15]
                    ]
            position: A list of floats denoting a position in the world. Format
                goes as follows: [X, Y, Z]
            quad: An instance of gluNewQuadric. Used for doing GLU calls.
            radius: A float that denotes the radius of the cylinder.
            slices: An integer that denotes how many slices the cylinder has.
            stacks: An integer that denotes how many stacks the cylinder has.
    """
    
    __slots__ = ('height', 'orientation', 'position', 'quad', 'radius', 'slices', 'stacks')
    
    def __init__(self, radius=1, height=2, slices=6, stacks=6, pos=_ZERO_POSITION, orient=_IDENTITY_MATRIX, id=None, mat_col_amb=(0.2, 0.2, 0.2, 1.0), mat_col_dif=(0.7, 0.7, 0.7, 1.0), mat_col_spec=(1.0, 1.0, 1.0, 1.0), mat_shine=50.0, mask_val=DRAW_RENDER, parent=None):
        """ Initializes the GluCylinderNode class.
            
            Args:
                radius: Initial indication of the radius of the bone
                    (default is 1)
                height: Initial indication of the height of the bone
                    (default is 2)
                slices: Initial indication of the slices of the bone
                    (default is 20)
                stacks: Initial indication of the stacks of the bone
                    (default is 20)
                pos: Initial indication of the pos of the bone
                    (default is _ZERO_POSITION)
                orient: Initial indication of a matrix to orient by
                    (default is _IDENTITY_MATRIX)
                id: Initial indication of the id for the mesh (default is None)
                mat_col_amb: Initial indication of the color ambience of the
                    mesh (default is (0.2, 0.2, 0.2, 1.0))
                mat_col_dif: Initial indication of the color diffusion of the
                    mesh (default is (0.7, 0.7, 0.7, 1.0))
                mat_col_spec: Initial indication of the color specular of the
                    mesh (default is (1.0, 1.0, 1.0, 1.0))
                mat_shine: Initial indication for the shininess the mesh
                    (default is 50.0)
                mask_val: Initial indication of what modes this can be drawn in
                    (default is DRAW_RENDER)
                parent: Initial indication of a parent for the node
                    (default is None)
        """
        MeshNode.__init__(self, id, mat_col_amb, mat_col_dif, mat_col_spec, mat_shine, mask_val, parent)
        self.radius = radius
        self.height = height
        self.slices = slices
        self.stacks = stacks
        self.position = pos
        self.orientation = orient
        self.quad = gluNewQuadric()
    
    def drawMesh(self):
        """Draws the cylinder mesh."""
        glPushMatrix()
        glTranslate(*self.position)
        glMultMatrixf(self.orientation)
        if type(self.parent) is BoneMeshNode:
            glRotate(-90, 1, 0, 0)
        gluCylinder(self.quad, self.radius, self.radius, self.height, self.slices, self.stacks)
        glPopMatrix()


class GluSphereNode(MeshNode):
    
    """ Is a Scene Node that creates a solid sphere mesh to be drawn in the
        world.
        
        Attributes:
            position: A list of floats denoting a position in the world. Format
                goes as follows: [X, Y, Z]
            quad: An instance of gluNewQuadric. Used for doing GLU calls.
            radius: A float that denotes the radius of the sphere.
            slices: An integer that denotes how many slices the sphere has.
            stacks: An integer that denotes how many stacks the sphere has.
    """
    
    __slots__ = ('position', 'quad', 'radius', 'slices', 'stacks')
    
    def __init__(self, radius=1, slices=20, stacks=20, pos=_ZERO_POSITION, id=None, mat_col_amb=(0.2, 0.2, 0.2, 1.0), mat_col_dif=(0.8, 0.8, 0.8, 1.0), mat_col_spec=(1.0, 1.0, 1.0, 1.0), mat_shine=50.0, mask_val=DRAW_RENDER, parent=None):
        """ Initializes the GluSphereNode class.
            
            Args:
                radius: Initial indication of the radius of the bone
                    (default is 1)
                slices: Initial indication of the slices of the bone
                    (default is 20)
                stacks: Initial indication of the stacks of the bone
                    (default is 20)
                pos: Initial indication of the pos of the bone
                    (default is (0, 0, 0))
                id: Initial indication of the id for the mesh (default is None)
                mat_col_amb: Initial indication of the color ambience of the
                    mesh (default is (0.2, 0.2, 0.2, 1.0))
                mat_col_dif: Initial indication of the color diffusion of the
                    mesh (default is (0.8, 0.8, 0.8, 1.0))
                mat_col_spec: Initial indication of the color specular of the
                    mesh (default is (1.0, 1.0, 1.0, 1.0))
                mat_shine: Initial indication for the shininess the mesh
                    (default is 50.0)
                mask_val: Initial indication of what modes this can be drawn in
                    (default is DRAW_RENDER)
                parent: Initial indication of a parent for the node
                    (default is None)
        """
        MeshNode.__init__(self, id, mat_col_amb, mat_col_dif, mat_col_spec, mat_shine, mask_val, parent)
        self.radius = radius
        self.slices = slices
        self.stacks = stacks
        self.position = pos
        self.quad = gluNewQuadric()
    
    def drawMesh(self):
        """Draws a solid sphere."""
        glPushMatrix()
        glTranslate(*self.position)
        gluSphere(self.quad, self.radius, self.slices, self.stacks)
        glPopMatrix()


class GlutCubeNode(MeshNode):
    
    """ Is a Scene Node that creates a solid cube mesh to be drawn in the world.
    """
    def drawMesh(self):
        """Draws a solid cube mesh with side lengths of 1 unit."""
        glutSolidCube(1.0)


class GlutSphereNode(MeshNode):
    
    """ Is a Scene Node that creates a solid sphere mesh to be drawn in the
        world.
        
        Attributes:
            position: A list of floats denoting a position in the world. Format
                goes as follows: [X, Y, Z]
            radius: A float that denotes the radius of the sphere.
            slices: An integer that denotes how many slices the sphere has.
            stacks: An integer that denotes how many stacks the sphere has.
    """
    
    __slots__ = ('position', 'radius', 'slices', 'stacks')
    
    def __init__(self, radius=1, slices=20, stacks=20, pos=_ZERO_POSITION, id=None, mat_col_amb=(0.2, 0.2, 0.2, 1.0), mat_col_dif=(0.8, 0.8, 0.8, 1.0), mat_col_spec=(1.0, 1.0, 1.0, 1.0), mat_shine=50.0, mask_val=DRAW_RENDER, parent=None):
        """ Initializes the GlutSphereNode class.
            
            Args:
                radius: Initial indication of the radius of the bone
                    (default is 1)
                slices: Initial indication of the slices of the bone
                    (default is 20)
                stacks: Initial indication of the stacks of the bone
                    (default is 20)
                pos: Initial indication of the pos of the bone
                    (default is (0, 0, 0))
                id: Initial indication of the id for the mesh (default is None)
                mat_col_amb: Initial indication of the color ambience of the
                    mesh (default is (0.2, 0.2, 0.2, 1.0))
                mat_col_dif: Initial indication of the color diffusion of the
                    mesh (default is (0.8, 0.8, 0.8, 1.0))
                mat_col_spec: Initial indication of the color specular of the
                    mesh (default is (1.0, 1.0, 1.0, 1.0))
                mat_shine: Initial indication for the shininess the mesh
                    (default is 50.0)
                mask_val: Initial indication of what modes this can be drawn in
                    (default is DRAW_RENDER)
                parent: Initial indication of a parent for the node
                    (default is None)
        """
        MeshNode.__init__(self, id, mat_col_amb, mat_col_dif, mat_col_spec, mat_shine, mask_val, parent)
        self.radius = radius
        self.slices = slices
        self.stacks = stacks
        self.position = pos
    
    def drawMesh(self):
        """Draws a solid sphere."""
        glPushMatrix()
        glTranslate(*self.position)
        glutSolidSphere(self.radius, self.slices, self.stacks)
        glPopMatrix()


class GlutWireSphereNode(MeshNode):
    
    """ Is a Scene Node that creates a wire sphere mesh to be drawn in the
        world.
    """
    def drawMesh(self):
        """ Draws a wire sphere mesh with a radius of 1 unit, slices of 5 units,
            and stacks of 5 units.
        """
        glutWireSphere(1.0, 5, 5)


class GlutTeapotNode(MeshNode):
    
    """ Is a Scene Node that creates a solid teapot mesh to be drawn in the
        world.
    """
    def drawMesh(self):
        """Draws a solid teapot mesh with a scale of 1 unit."""
        glutSolidTeapot(1.0)


class GlutConeNode(MeshNode):
    
    """ Is a Scene Node that creates a solid cone mesh to be drawn in the world.
    """
    def drawMesh(self):
        """ Draws a solid cone mesh with a radius of 1 unit, height of 1 unit,
            slices of 20 units, and stacks of 20 units.
        """
        glutSolidCone(1.0, 1.0, 20, 20)


class LogoQuadNode(SNode):
    
    """ A Scene Node that creates a quad from a picture file.
        
        Attributes:
            do_draw: A boolean that denotes whether or not to draw.
            gl_height: A float that denotes the height of the image.
            gl_width: A float that denotes the width of the image.
            image_id: An integer that denotes the number of textures used.
            trans_matrix: A list of floats denoting a 4x4 matrix. The matrix is
                stored in column major. For example:
                    matrix = [
                        matrix[0], matrix[4], matrix[8], matrix[12],
                        matrix[1], matrix[5], matrix[9], matrix[13],
                        matrix[2], matrix[6], matrix[10], matrix[14],
                        matrix[3], matrix[7], matrix[11], matrix[15]
                    ]
    """
    
    __slots__ = ('do_draw', 'gl_height', 'gl_width', 'image_id', 'trans_matrix')
    
    def __init__(self, do_draw=True):
        """ Initializes the LogoQuadNode class.
            
            Args:
                do_draw: A boolean that denotes whether or not to draw.
                    (default is True)
        """
        SNode.__init__(self)
        self.image_id = 0
        self.do_draw = do_draw
        self.trans_matrix = [
            0.03, 0.0, 0.0, 0.0,
            0.0, -0.03, 0.0, 0.0,
            0.0, 0.0, 0.03, 0.0,
            0.95, 0.95, 0.0, 1.0
        ]
        self.gl_width = 1.0
        self.gl_height = 1.0
    
    def loadTexture(self, texture_name):
        self.image_id = loadImage(texture_name)
    
    def draw(self, mask_val=DRAW_ALL):
        """ Draws the node to the screen and calls it's children's draw
            function.
            
            Args:
                mask_val: Initial indication of what mode the graph is in
                    (default is DRAW_ALL)
        """
        if self.mask & mask_val and self.do_draw:
            # Setup Texture for rendering
            glColor4f(1, 1, 1, 1)
            
            glEnable(GL_ALPHA_TEST)
            glAlphaFunc(GL_GREATER, 0.1)
            
            glDisable(GL_COLOR_MATERIAL)
            
            glEnable(GL_TEXTURE_2D)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
            glBindTexture(GL_TEXTURE_2D, self.image_id)
            
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_LIGHTING)
            
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            
            height_ratio = max((self.gl_height * 1.0) / self.gl_width, 0.0000000001)
            width_ratio = 1.0
            if (height_ratio > 1):
                width_ratio = 1.0 / height_ratio
                height_ratio = 1.0
            gluOrtho2D(0.0, width_ratio, 0.0, height_ratio)
            self.trans_matrix[12] = 0.95 * width_ratio
            self.trans_matrix[13] = 0.95 * height_ratio
            
            glMatrixMode(GL_MODELVIEW)
            
            glPushMatrix()
            glMultMatrixf(self.trans_matrix)
            
            glBegin(GL_QUADS);
            glTexCoord2f(0.0, 0.0)
            glVertex2f(-1.0, -1.0)
            glTexCoord2f(1.0, 0.0)
            glVertex2f(1.0, -1.0)
            glTexCoord2f(1.0, 1.0)
            glVertex2f(1.0, 1.0)
            glTexCoord2f(0.0, 1.0)
            glVertex2f(-1.0, 1.0)
            glEnd()
            glPopMatrix()
            
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)
            
            glEnable(GL_LIGHTING)
            glEnable(GL_DEPTH_TEST)
            glDisable(GL_TEXTURE_2D)
            glDisable(GL_ALPHA_TEST)


### Sensor Object Meshes ###
class SensorMeshNode(SNode):
    
    """ A Scene Node that creates a sensor mesh using an OBJ mesh file.
        
        Attributes:
            init_orient: A list of floats denoting a 4x4 matrix. The matrix is
                stored in column major. For example:
                    matrix = [
                        matrix[0], matrix[4], matrix[8], matrix[12],
                        matrix[1], matrix[5], matrix[9], matrix[13],
                        matrix[2], matrix[6], matrix[10], matrix[14],
                        matrix[3], matrix[7], matrix[11], matrix[15]
                    ]
            interactive_mode: A boolean that indicates whether to draw the
                object's children.
            obj_node: An instance of an OBJMeshNode object. 
            orient: A list of floats denoting a 4x4 matrix. The matrix is stored
                in column major.
            position: A list of floats denoting a position in the world. Format
                goes as follows: [X, Y, Z]
            scale : A list of floats denoting the scale of the object in the
                world. Format goes as follows: [X, Y, Z]
            sensor_orient: A list of floats denoting a 4x4 matrix. The matrix is
                stored in column major.
            ts_sensor: A reference to a 3-Space Sensor object.
    """
    
    __slots__ = ('init_orient', 'interactive_mode', 'obj_node', 'orient', 'position', 'scale', 'sensor_orient', 'ts_sensor')
    
    def __init__(self, file_name=""):
        """ Initializes the SensorMeshNode class.
            
             Args:
                file_name: A string that denotes the path and file name of the
                    object file.
        """
        SNode.__init__(self, DRAW_SENSOR)
        self.obj_node = OBJMeshNode(file_name, mat_col_dif=(0.3, 0.3, 0.3, 1.0))
        self.init_orient = [0, 0, 1, 0, 0, -1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1]
        self.orient = _IDENTITY_MATRIX
        self.sensor_orient = _IDENTITY_MATRIX
        self.position = _ZERO_POSITION
        self.scale = [1, 1, 1]
        self.ts_sensor = None
        self.interactive_mode = False
    
    def draw(self, mask_val=DRAW_ALL):
        """ Draws the node to the screen and applies the settings for the mesh
            before calling it's children's draw function.
            
            Args:
                mask_val: Initial indication of what mode the graph is in
                    (default is DRAW_ALL)
        """
        if self.mask & mask_val:
            glPushMatrix()
            glTranslate(*self.position)
            if self.interactive_mode:
                glPushMatrix()
                glMultMatrixf(self.sensor_orient)
            glMultMatrixf(self.orient)
            glPushMatrix()
            glMultMatrixf(self.init_orient)
            glScalef(*self.scale)
            self.obj_node.draw(mask_val)
            glPopMatrix()
            for child in self.children:
                child.draw(mask_val)
            if self.interactive_mode:
                glPopMatrix()
            glPopMatrix()


class SensorAxisNode(SNode):
    
    """ A Scene Node that creates an arrow mesh using OpenGL calls.
        
        Attributes:
            orient: A list of floats denoting a 4x4 matrix. The matrix is
                stored in column major. For example:
                    matrix = [
                        matrix[0], matrix[4], matrix[8], matrix[12],
                        matrix[1], matrix[5], matrix[9], matrix[13],
                        matrix[2], matrix[6], matrix[10], matrix[14],
                        matrix[3], matrix[7], matrix[11], matrix[15]
                    ]
    """
    
    __slots__ = ('orient')
    
    def __init__(self, mask):
        """Initializes the SensorAxisNode class."""
        if mask != DRAW_ARROW_X and mask != DRAW_ARROW_Y and mask != DRAW_ARROW_Z:
            raise TypeError("Mask must be either DRAW_ARROW_X or DRAW_ARROW_Y or DRAW_ARROW_Z")
        SNode.__init__(self, mask_val=DRAW_RENDER | mask)
        self.orient = _IDENTITY_MATRIX
    
    def draw(self, mask_val=DRAW_ALL):
        """ Draws the node to the screen.
            
            Args:
                mask_val: Initial indication of what mode the graph is in
                    (default is DRAW_ALL)
        """
        if self.mask & mask_val:
            if self.mask & DRAW_ARROW_X:
                glPushMatrix()
                glMultMatrixf(self.orient)
                
                glMaterial(GL_FRONT, GL_DIFFUSE, [1, 0, 0, 1])
                glPushMatrix()
                glTranslate(25.0, 0.0, 0.0)
                glPushMatrix()
                glScalef(25.0, 5.0, 5.0)
                glutSolidCube(1.0)
                glPopMatrix()
                glTranslate(12.5, 0.0, 0.0)
                glScalef(9.0, 7.0, 7.0)
                glRotate(90, 0, 1, 0)
                glRotate(45, 0, 0, 1)
                glutSolidCone(1.0, 1.0, 4, 1)
                glPopMatrix()
                
                glPopMatrix()
            if self.mask & DRAW_ARROW_Y:
                glPushMatrix()
                glMultMatrixf(self.orient)
                
                glMaterial(GL_FRONT, GL_DIFFUSE, [0, 1, 0, 1])
                glPushMatrix()
                glTranslate(0.0, 25.0, 0.0)
                glPushMatrix()
                glScalef(5.0, 25.0, 5.0)
                glutSolidCube(1.0)
                glPopMatrix()
                glTranslate(0.0, 12.5, 0.0)
                glScalef(7.0, 9.0, 7.0)
                glRotate(-90, 1, 0, 0)
                glRotate(45, 0, 0, 1)
                glutSolidCone(1.0, 1.0, 4, 1)
                glPopMatrix()
                
                glPopMatrix()
            if self.mask & DRAW_ARROW_Z:
                glPushMatrix()
                glMultMatrixf(self.orient)
                
                glMaterial(GL_FRONT, GL_DIFFUSE, [0, 0, 1, 1])
                glPushMatrix()
                glTranslate(0.0, 0.0, -25.0)
                glPushMatrix()
                glScalef(5.0, 5.0, -25.0)
                glutSolidCube(1.0)
                glPopMatrix()
                glTranslate(0.0, 0.0, -12.5)
                glScalef(7.0, 7.0, -9.0)
                glRotate(45, 0, 0, 1)
                glutSolidCone(1.0, 1.0, 4, 1)
                glPopMatrix()
                
                glPopMatrix()


### Helper Functions ###
def getGLVersion():
    """ Retrieves the version of OpenGL currently running on the host machine.
        
        Returns:
            A list of three integers indicating the version of OpenGL. The list
            is laid out as such:
                [Major_Number, Minor_Number, Release_Number]
            
            A list of [0, 0, 0] is returned if the version could not be
            retrieved.
    """
    global global_gl_version_list
    if global_gl_version_list is None:
        ver_string = glGetString(GL_VERSION)
        if ver_string is None:
            OBJMeshNode.drawMesh = OBJMeshNode._drawMeshGLVert
            global_gl_version_list = [0, 0, 0]
        else:
            vs_split = ver_string.split('.')
            try:
                major = int(vs_split[0])
            except:
                major = 0
            try:
                minor = int(vs_split[1])
            except:
                minor = 0
            try:
                release = int(vs_split[2].split(' ')[0])
            except:
                release = 0
            
            if major > 1 or (major == 1 and minor >= 3):
                OBJMeshNode.drawMesh = OBJMeshNode._drawMeshGLArray
            else:
                OBJMeshNode.drawMesh = OBJMeshNode._drawMeshGLVert
            
            global_gl_version_list = [major, minor, release]
        return global_gl_version_list
    else:
        return global_gl_version_list


def loadImage(image_name):
    """ From http://pyopengl.sourceforge.net/context/tutorials/nehe6.xhtml
        Loads an image file as a 2D texture using PIL.
        
        Args:
            image_name: A string that denotes the path and name of a image to be
                used as a texture.
        Returns:
                An integer that denotes the number of textures.
    """
    pil_img = Image.open(image_name)
    image = numpy.array(list(pil_img.getdata()), numpy.uint8)
    ix, iy = pil_img.size[0], pil_img.size[1]
    id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, id)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
    return id






