#!/usr/bin/env python2.7

"""Writes a TSH binary file using information from the Mocap Studio."""


# 3-Space Heiarchy Exporter
#### TSH LAYOUT ####
##  -HEADER-      ##
##  -SKELETON1-   ##
##       -BONE1-  ##
##       -BONE2-  ##
##       ...      ##
##  -SKELETON2-   ##
##       -BONE1-  ##
##       -BONE2-  ##
##       ...      ##
##  ...           ##
##  -FRAMEDATA-   ##
####################

import struct


### Static Globals ###
# Can be updated to reflect advances in format version
# (Read as "EXPORT_VERSION.EXPORT_SUBVERSION")
EXPORT_VERSION = 1
EXPORT_SUBVERSION = 0


### Functions ###
# Chunk IDs
########################
## 0 = Skeleton Chunk ##
## 1 = Bone Chunk     ##
## 2 = Frame Chunk    ##
########################

def saveTSH(file_name, cap_frequency, tsh_skels):
    """ Saves the skeleton and animation given as a TSH file.
        
        Args:
            file_name: A string that has the path and file name for the TSH
                file.
            cap_frequency: A float that represents the capture rate of the
                animation being saved.
            tsh_skels: A list of skeletons. Each an instance of TSHSkel.
        
        Yields:
            A complete TSH file at the location of the path given and with the
            name given.
    """
    # Open File
    try:
        out_file = open(file_name, 'wb')
    except:
        print "Failed to save file:\n\t" + file_name
        return None
        
    ## WRITE HEADER ##
    ###############################
    ## uint file size            ##
    ## ushort num version        ##
    ## ushort num subversion     ##
    ## ushort num skeletons      ##
    ## uint64 num frames         ##
    ## float32 capture frequency ##
    ###############################
    
    # Size of header
    header_size = 22
    
    heiarchy_size = 0
    for skel in tsh_skels:
        # Size of skel's charStr + chunk ID
        heiarchy_size += len(skel.name) + 2
        for bone in skel.bones:
            # Size of bone name's charStr + chunk ID
            heiarchy_size += len(bone.name) + 2
            # Size of parent name's charStr
            heiarchy_size += len(bone.parent_name) + 1
            # Size of bone's pose orient + offset + length
            heiarchy_size += 36
            # Size of virtual sensor name's charStr + pose orient
            heiarchy_size += len(bone.vs_name) + 17
            # Size of sensor mesh's pose orient
            heiarchy_size += 9
            # Size of all frames contained in the bone
            heiarchy_size += (28 * len(bone.frames))
            
    # The chunk ID for the frame section
    heiarchy_size += 1
    file_size = header_size + heiarchy_size
    # File Size
    out_file.write(struct.pack("I", file_size))
    # Versions
    out_file.write(struct.pack("H", EXPORT_VERSION))
    out_file.write(struct.pack("H", EXPORT_SUBVERSION))
    # Number Skeletons
    out_file.write(struct.pack("H", len(tsh_skels)))
    # Number Frames
    num_frames = len(tsh_skels[0].bones[0].frames)
    out_file.write(struct.pack("Q", num_frames))
    # Capture Frequency
    out_file.write(struct.pack("f", cap_frequency))
    
    ## WRITE HEIARCHY ##
    ###########################
    ## charStr Skeleton Name ##
    ###########################
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
    ##########################################
    
    for skel in tsh_skels:
        # Chunk ID
        out_file.write(chr(0))
        
        # Skeleton Name
        for letter in skel.name:
            out_file.write(letter)
        out_file.write(chr(0)) # Null terminator
        for bone in skel.bones:
            # Chunk ID
            out_file.write(chr(1))
            
            # Bone Name
            for letter in bone.name:
                out_file.write(letter)
            out_file.write(chr(0)) # Null terminator
            
            # Parent Name
            for letter in bone.parent_name:
                out_file.write(letter)
            out_file.write(chr(0)) # Null terminator
           
           # Bone Length
            out_file.write(struct.pack("f", bone.length))
            
            # Bone Pose Orient
            x, y, z, w = bone.pose_orient.toQuaternion().asArray()
            out_file.write(struct.pack("f", x)) # X
            out_file.write(struct.pack("f", y)) # Y
            out_file.write(struct.pack("f", z)) # Z
            out_file.write(struct.pack("f", w)) # W
            
            # Bone Offset
            x, y, z = bone.offset.asArray()
            out_file.write(struct.pack("f", x)) # X
            out_file.write(struct.pack("f", y)) # Y
            out_file.write(struct.pack("f", z)) # Z
            
            # Virtual Sensor Name
            for letter in bone.vs_name:
                out_file.write(letter)
            out_file.write(chr(0)) # Null terminator
    
    ## WRITE FRAME DATA ##
    # Animation Data Chunk
    #########################################################################
    ## float32 [num_frames][numSkels][numBones][0:3] Position              ##
    ## float32 [num_frames][numSkels][numBones][3:7] Orientation (X,Y,Z,W) ##
    #########################################################################
    # Chunk ID
    out_file.write(chr(2))
    for cur_frame in range(num_frames):
        for skel in tsh_skels:
            for bone in skel.bones:
                # Position
                x, y, z = bone.frames[cur_frame].position.asArray()
                out_file.write(struct.pack("f", x)) # X
                out_file.write(struct.pack("f", y)) # Y
                out_file.write(struct.pack("f", z)) # Z
                
                # Orientation
                x, y, z, w = bone.frames[cur_frame].orient.asArray()
                out_file.write(struct.pack("f", x)) # X
                out_file.write(struct.pack("f", y)) # Y
                out_file.write(struct.pack("f", z)) # Z
                out_file.write(struct.pack("f", w)) # W
 
    out_file.close()





