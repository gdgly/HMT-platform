#!/usr/bin/env python2.7

"""Parses a BVH file into useful information the Mocap Studio can use."""


import animator_utils as anim_utils
from math_lib import *
import math


### Globals ###
global_root_bone_list = {}
global_joint_bone_list = {}
global_frame_order_list = []
global_file_tokens = []
global_anim_data = []


### Classes ###
class BVHBone(object):
    
    """ Holds information about a bone being loaded from a BVH file.
        
        Attributes:
            name: A string of the name of a bone loaded from a BVH file.
            length: A float of a bone's length loaded from a BVH file.
            orient: The orientation of a bone loaded from a BVH file. An
                instance of Quaternion.
            offset: The offset of a bone loaded from a BVH file from it's
                parent. An instance of Vector3.
            end_site: The end of a branch of the BVH hierarchy loaded. An
                instance of Vector3.
            parent: A reference to an instance of a BVHBone if the bone loaded
                from a BVH file has a parent.
            channels: A list of the channels the bone loaded from a BVH file
                has.
            children: A list of instances of BVHBone if the bone loaded from a
                BVH file has children.
            cur_anim: A list of the orientation and position of the bone loaded
                from a BVH file.
    """
    def __init__(self):
        """Initalizes the BVHBone class."""
        self.name = None
        self.length = 0.0
        self.orient = None
        self.offset = None
        self.end_site = None
        self.parent = None
        self.channels = None
        self.children = []
        self.cur_anim = None


### Helper Functions ###
def loadBVHBone(cur_bone, start_line, in_centimeters):
    """ Creates a skeleton using a BVH hierarchy using recursion.
        
        Args:
            cur_bone: An instance of BVHBone.
            start_line: An integer indicating where we are at in the BVH file.
            in_centimeters: A boolean that indicates whether or not the units
                are in centimeters.
        
        Returns:
            An integer to tell where to start from in the file.
    """
    global global_root_bone_list, global_joint_bone_list
    global global_frame_order_list, global_file_tokens
    
    # Add bone to necessary global lists and set bone's name
    cur_bone.name = global_file_tokens[start_line][1]
    if global_file_tokens[start_line][0] == "ROOT":
        global_root_bone_list[cur_bone.name] = cur_bone
    else:
        global_joint_bone_list[cur_bone.name] = cur_bone
    
    global_frame_order_list.append(cur_bone)
    
    # Set bone's offset, parent's length, and parent bone's orient
    start_line += 2 # "Read" two lines
    line = global_file_tokens[start_line][1:]
    pos = []
    for i in line:
        pos.append(float(i))
    cur_bone.offset = Vector3(pos)
    if in_centimeters:
        cur_bone.offset *= 1 / 2.54
    
    if cur_bone.parent:
        cur_bone.parent.length += cur_bone.offset.length()
    
    # Set bone's channel
    start_line += 1 # "Read" one line
    cur_bone.channels = global_file_tokens[start_line][2:]
    
    # Either load children or return
    start_line += 1 # "Read" one line
    if global_file_tokens[start_line][0] == "End":
        start_line += 2
        line = global_file_tokens[start_line][1:]
        pos = []
        for i in line:
            pos.append(float(i))
        cur_bone.end_site = Vector3(pos)
        cur_bone.length += cur_bone.end_site.length()
        if in_centimeters:
            cur_bone.end_site *= 1 / 2.54
            cur_bone.length *= 1 / 2.54
        start_line += 3
    else:
        line = global_file_tokens[start_line][0]
        while line == "JOINT" or line == "ROOT":
            if line == "JOINT":
                cur_bone.children.append(BVHBone())
                cur_bone.children[-1].parent = cur_bone
                start_line = loadBVHBone(cur_bone.children[-1], start_line, in_centimeters)
            else:
                start_line = loadBVHBone(BVHBone(), start_line, in_centimeters)
            line = global_file_tokens[start_line][0]
        start_line += 1
    
    if len(cur_bone.children) > 0:
        cur_bone.length /= len(cur_bone.children)
    
    if global_file_tokens[start_line][0] == "ROOT":
        return loadBVHBone(BVHBone(), start_line, in_centimeters)
    else:
        return start_line


def setBVHOrient(cur_bone):
    """ Creates Quaternion orientations for the BVHBones using recursion.
        
        Args:
            cur_bone: An instance of BVHBone.
        
        Yields:
            All the BVHBones created to have a Quaternion orientation.
    """
    # Do stuff to get cur_bone's orientation correct *have Chris do :)
    # Compute average direction vector
    x_vec = Vector3(UNIT_X)
    y_vec = Vector3()
    z_vec = Vector3(UNIT_Z)
    if cur_bone.end_site:
        y_vec = cur_bone.end_site.normalizeCopy()
    else:
        for child in cur_bone.children:
            y_vec = y_vec + child.offset.normalizeCopy()
        y_vec.normalize()
    
    # Compute orthogonal vectors
    if abs(y_vec._vec_array[0]) > abs(y_vec._vec_array[2]):
        x_vec = (y_vec.cross(z_vec)).normalizeCopy()
        z_vec = (x_vec.cross(y_vec)).normalizeCopy()
    else:
        z_vec = (x_vec.cross(y_vec)).normalizeCopy()
        x_vec = (y_vec.cross(z_vec)).normalizeCopy()
    
    # Build matrix
    tmp_mat = -Matrix3(x_vec.asArray() + y_vec.asArray() + z_vec.asArray())
    
    # Store!
    cur_bone.orient = tmp_mat.toQuaternion()
    
    for child in cur_bone.children:
        setBVHOrient(child)


def setAnimation(bone, orient):
    """ Creates animation data for a BVHBone traversing through the skeleton.
        
        Args:
            bone: The bone we are currently looking at. An instance of BVHBone.
            orient: The animation orientation of the bone. An instance of
                Quaternion.
        
        Yields:
            Animation data for all BVHBones in the skeleton.
    """
    global global_anim_data
    for child in bone.children:
        child.cur_anim = [orient * child.cur_anim[0], child.cur_anim[1]]
        setAnimation(child, child.cur_anim[0])
        
    global_anim_data[-1][bone.name] = bone.cur_anim


### Functions ###
def loadBVH(file_name, in_centimeters):
    """ Loads in a BVH file and creates a skeleton(s) with animation data.
        
        Args:
            file_name: A string that represents the name and path of the BVH
                file that is to be loaded.
            in_centimeters: A boolean that indicates whether or not the units
                are in centimeters.
        
        Returns:
            A tuple of consisting of the file name, frame rate, animation data,
                bone list, and root bone list of the BVH file read in.
    """
    global global_root_bone_list, global_joint_bone_list
    global global_frame_order_list, global_file_tokens, global_anim_data
    
    # Reset Globals
    global_root_bone_list = {}
    global_joint_bone_list = {}
    global_frame_order_list = []
    global_file_tokens = []
    global_anim_data = []
    
    # Opening file to import
    try:
        bvh_file = open(file_name, 'r')
        file_name = file_name.split('\\')[-1][:-4]
    except:
        print "Failed to load file:\n\t" + file_name
        return [None] * 5
    
    # Read in lines of file and split by white spaces
    read_lines = bvh_file.readlines()
    for line in read_lines:
        line = line.strip().split()
        if line:
            global_file_tokens.append(line)

    # Check if valid BVH file
    top_line = global_file_tokens.pop(0)
    if top_line[0].lower() == 'hierarchy':
        print 'Importing BVH file'
    else:
        print "ERROR! Not a BVH file or a valid BVH file."
        return [None] * 5

    # Bone dictionary
    root_list = []
    bone_list = {}
    
    # Motion data info
    num_frames = -1
    frame_rate = -1
    
    # Build the heiarch(ies)y
    cur_line = loadBVHBone(BVHBone(), 0, in_centimeters)
    
    # Set initial pose orientation for all bones
    for r_bone in global_root_bone_list.values():
        setBVHOrient(r_bone)
    
    # Parse animation data
    # Animation-Wide data
    cur_line += 1
    num_frames = int(global_file_tokens[cur_line][1])
    cur_line += 1
    frame_rate = float(global_file_tokens[cur_line][-1])
    cur_line += 1
    
    # Frame Data
    while cur_line < len(global_file_tokens):
        global_anim_data.append({})
        cur_frame_elem_idx = 0
        for bone in global_frame_order_list:
            tmp_quat = Quaternion()
            tmp_vec = None
            for channel in bone.channels:
                val = float(global_file_tokens[cur_line][cur_frame_elem_idx])
                if channel == "Xposition":
                    if tmp_vec is None:
                        tmp_vec = [0.0] * 3
                    tmp_vec[0] = val
                elif channel == "Yposition":
                    if tmp_vec is None:
                        tmp_vec = [0.0] * 3
                    tmp_vec[1] = val
                elif channel == "Zposition":
                    if tmp_vec is None:
                        tmp_vec = [0.0] * 3
                    tmp_vec[2] = val
                elif channel == "Xrotation":
                    val = math.radians(val)
                    x_quat = Euler([val, 0.0, 0.0]).toQuaternion('xyz')
                    tmp_quat = tmp_quat * x_quat
                elif channel == "Yrotation":
                    val = math.radians(val)
                    y_quat = Euler([0.0, val, 0.0]).toQuaternion('xyz')
                    tmp_quat = tmp_quat * y_quat
                elif channel == "Zrotation":
                    val = math.radians(val)
                    z_quat = Euler([0.0, 0.0, val]).toQuaternion('xyz')
                    tmp_quat = tmp_quat * z_quat
                cur_frame_elem_idx += 1
            if tmp_vec is not None:
                tmp_vec = Vector3(tmp_vec)
                if in_centimeters:
                    tmp_vec *= 1 / 2.54
            bone.cur_anim = [tmp_quat, tmp_vec]
        
        # Set up bone's animation to be independent of parent's animation
        for r_bone in global_root_bone_list.values():
            setAnimation(r_bone, r_bone.cur_anim[0])
        cur_line += 1
    
    # Set up application constructs and return
    for bone in global_frame_order_list:
        bone_state = anim_utils.BoneState()
        bone_state.bone_length = bone.length
        bone_state.pose_orient = bone.orient.toMatrix4()
        bone_state.offset = bone.offset
        for child in bone.children:
            bone_state.children.append(child.name)
        if bone.parent:
            bone_state.parent = bone.parent.name
        else:
            root_list.append(bone.name)
        bone_list[bone.name] = bone_state
    
    bvh_file.close()
    
    return file_name, frame_rate, global_anim_data, bone_list, root_list



