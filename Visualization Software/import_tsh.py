#!/usr/bin/env python2.7

"""Parses a TSH binary file into useful information the Mocap Studio can use."""

# 3-Space Heiarchy Importer
#### TSH LAYOUT ####
##  -HEADER-      ##
##  -SKELETON1-   ##
##       -BONE1-  ##
##       -BONE2-  ##
##      ...       ##
##  -SKELETON2-   ##
##       -BONE1-  ##
##       -BONE2-  ##
##       ...      ##
##  ...           ##
##  -FRAMEDATA-   ##
####################

import struct
from math_lib import *


### Globals ###
global_tsh_skels = []


### Classes ###
class TSHInfo(object):
    
    """ Holds information about the TSH file being loaded.
        
        Attributes:
            file_size: An uint denoting the size of the file.
            num_version: An ushort denoting the version of the file.
            num_subversion: An ushort denoting the subversion of the file.
            num_skeletons: An ushort denoting the number of skeletons in the
                file.
            num_frames: An uint64 denoting the number of frames the file holds.
            capture_frequency: A float32 denoting the capture rate of the
                animation in the file.
    """
    def __init__(self):
        """Initalizes the TSHInfo class."""
        file_size = None
        num_version = None
        num_subversion = None
        num_skeletons = None
        num_frames = None
        capture_frequency = None


class TSHSkel(object):
    
    """ Holds information about a skeleton being loaded from a TSH file.
        
        Attributes:
            name: A string of the name of a skeleton loaded from a TSH file.
            bones: A list of bones that make up the skeleton. Each an instance
                of TSHBone.
    """
    def __init__(self, name):
        """ Initalizes the TSHSkel class.
            
            Args:
                name: A string that denotes the name of the skeleton.
        """
        self.name = name
        self.bones = []


class TSHBone(object):
    
    """ Holds information about a bone being loaded from a TSH file.
        
        Attributes:
            name: A string of the name of a bone loaded from a TSH file.
            parent_name: A string of the parent of a bone loaded from a TSH
                file. Is equal to "" if bone has no parent.
            pose_orient: The orientation of a bone loaded from a TSH file. An
                instance of Quaternion.
            offset: The offset of a bone loaded from a TSH file from it's
                parent. An instance of Vector3.
            length: A float of a bone's length loaded from a TSH file.
            vs_name: A string denoting the name of a virtual sensor loaded from
                a TSH file.
            vs_pose: The orientation a virtual sensor loaded from a TSH file. An
                instance of Quaternion. Used for Version 0.2 or earlier.
            sensor_pose: The orientation of a sensor mesh loaded from a TSH
                file. An instance of Euler. Used for Version 0.2 or earlier.
            frames: A list of the orientation and position of the bone loaded
                from a TSH file. Each an instance of TSHFrame.
    """
    def __init__(self, name):
        """ Initalizes the TSHSkel class.
            
            Args:
                name: A string that denotes the name of the bone.
        """
        self.name = name
        self.parent_name = ""
        self.pose_orient = None
        self.offset = None
        self.length = None
        self.vs_name = ""
        self.vs_pose = None         # Used for Version 0.2 or earlier.
        self.sensor_pose = None     # Used for Version 0.2 or earlier.
        self.frames = []


class TSHFrame(object):
    
    """ Holds information about a frame being loaded from a TSH file.
        
        Attributes:
            position: The positional data of the frame loaded from a TSH file.
                An instance of Vector3.
            orient: The orientation data of the frame loaded from a TSH file. An
                instance of Quaternion.
    """
    def __init__(self):
        """Initalizes the TSHFrame class."""
        self.position = None
        self.orient = None


### Functions ###
def loadTSH(file_name, in_centimeters):
    """ Loads in a TSH file and creates a skeleton(s) with animation data.
        
        Args:
            file_name: A string that represents the name and path of the TSH
                file that is to be loaded.
            in_centimeters: A boolean that indicates whether or not the units
                are in centimeters.
        
        Returns:
            A tuple of consisting of the file name, file information, and
                skeleton list the TSH file read in.
    """
    global global_tsh_skels
    global_tsh_skels = []
    
    # Open File
    try:
        in_file = open(file_name, 'rb')
        file_name = file_name.split("\\")[-1][:-4]
    except:
        print "Failed to load file:\n\t" + file_name
        return [None] * 3
    
    # Load File
    ## READ HEADER ##
    ###############################
    ## uint file size            ##
    ## ushort num version        ##
    ## ushort num subversion     ##
    ## ushort num skeletons      ##
    ## uint64 num frames         ##
    ## float32 capture frequency ##
    ###############################
    cur_bytes = in_file.read(22)
    if len(cur_bytes) < 22:
        print "Header size is wrong size."
        return [None] * 3
    file_info = TSHInfo()
    file_info.file_size = struct.unpack("I", cur_bytes[:4])[0]
    file_info.num_version = struct.unpack("H", cur_bytes[4:6])[0]
    file_info.num_subversion = struct.unpack("H", cur_bytes[6:8])[0]
    file_info.num_skeletons = struct.unpack("H", cur_bytes[8:10])[0]
    file_info.num_frames = struct.unpack("Q", cur_bytes[10:18])[0]
    file_info.capture_frequency = struct.unpack("f", cur_bytes[18:])[0]
    
    while True:
        # Get the chunk identifier
        ########################
        ## 0 = Skeleton Chunk ##
        ## 1 = Bone Chunk     ##
        ## 2 = Frame Chunk    ##
        ########################
        
        cur_bytes = in_file.read(1)
        if len(cur_bytes) < 1:
            break
        chunk_id = ord(struct.unpack("c", cur_bytes)[0])
        
        # Skeleton Chunk
        ###########################
        ## charStr Skeleton Name ##
        ###########################
        if chunk_id == 0:
            skel_name = ""
            name_byte = in_file.read(1)
            while ord(name_byte) != 0:
                skel_name = skel_name + name_byte
                name_byte = in_file.read(1)
            global_tsh_skels.append(TSHSkel(skel_name))
            
        # Bone Chunk
        ##########################################
        ## charStr bone name                    ##
        ## charStr parent name //"" = no parent ##
        ## float32 bone length                  ##
        ## float32 pose orient X                ##
        ## float32 pose orient Y                ##
        ## float32 pose orient Z                ##
        ## float32 pose orient W                ##
        ## float32 offset X                     ##
        ## float32 offset Y                     ##
        ## float32 offset Z                     ##
        ## charStr vs name //"" = no vs node    ##
        #####  If version is earlier than 1  #####
        ## float32 vs pose orient X             ##
        ## float32 vs pose orient Y             ##
        ## float32 vs pose orient Z             ##
        ## float32 vs pose orient W             ##
        ## float32 sensor pose orient X         ##
        ## float32 sensor pose orient Y         ##
        ## float32 sensor pose orient Z         ##
        ##########################################
        elif chunk_id == 1:
            # Bone Name
            bone_name = ""
            name_byte = in_file.read(1)
            while ord(name_byte) != 0:
                bone_name = bone_name + name_byte
                name_byte = in_file.read(1)
            global_tsh_skels[-1].bones.append(TSHBone(bone_name))
            cur_bone = global_tsh_skels[-1].bones[-1]
            
            # Parent Bone Name
            parent_name = ""
            name_byte = in_file.read(1)
            while ord(name_byte) != 0:
                parent_name = parent_name + name_byte
                name_byte = in_file.read(1)
            
            if len(parent_name) > 0:
                cur_bone.parent_name = parent_name
            
            # Bone Length
            cur_bone.length = struct.unpack("f", in_file.read(4))[0]
            if in_centimeters:
                cur_bone.length *= 1 /2.54
            
            # Bone Pose Orient
            quat = []
            i = 0
            while i < 4:
                quat.append(struct.unpack("f", in_file.read(4))[0])
                i += 1
            cur_bone.pose_orient = Quaternion(quat).toMatrix4()
            
            # Bone Offset
            pos = []
            i = 0
            while i < 3:
                pos.append(struct.unpack("f", in_file.read(4))[0])
                i += 1
            cur_bone.offset = Vector3(pos)
            if in_centimeters:
                cur_bone.offset *= 1 / 2.54
            
            # Virtual Sensor Name
            vs_name = ""
            name_byte = in_file.read(1)
            while ord(name_byte) != 0:
                vs_name = vs_name + name_byte
                name_byte = in_file.read(1)
            if len(vs_name) > 0:
                cur_bone.vs_name = vs_name
                
                if file_info.num_version < 1:
                    # Virtual Sensor Pose Orient
                    quat = []
                    i = 0
                    while i < 4:
                        quat.append(struct.unpack("f", in_file.read(4))[0])
                        i += 1
                    if quat == [0.0, 0.0, 0.0, 0.0]:
                        cur_bone.vs_pose = None
                    else:
                        cur_bone.vs_pose = Quaternion(quat)
                    
                    # Sensor Pose Orient
                    euler = []
                    i = 0
                    while i < 3:
                        euler.append(struct.unpack("f", in_file.read(4))[0])
                        i += 1
                    cur_bone.sensor_pose = Euler(euler, True)
        
        # Animation Data Chunk
        ########################################################################
        ## float32 [num_frames][numSkels][numBones][0:3] Position              #
        ## float32 [num_frames][numSkels][numBones][3:7] Orientation (X,Y,Z,W) #
        ########################################################################
        elif chunk_id == 2:
            for frame in range(file_info.num_frames):
                for skel in global_tsh_skels:
                    for bone in skel.bones:
                        bone.frames.append(TSHFrame())
                        cur_frame = bone.frames[-1]
                        
                        # Position
                        pos = []
                        i = 0
                        while i < 3:
                            pos.append(struct.unpack("f", in_file.read(4))[0])
                            i += 1
                        
                        cur_frame.position = Vector3(pos)
                        if in_centimeters:
                            cur_frame.position *= 1 / 2.54
                        
                        # Orientation
                        quat = []
                        i = 0
                        while i < 4:
                            quat.append(struct.unpack("f", in_file.read(4))[0])
                            i += 1
                        cur_frame.orient = Quaternion(quat)
    
    in_file.close()
    
    # Return Structures
    return file_name, file_info, global_tsh_skels




