#!/usr/bin/env python2.7

"""Parses a TSH binary file and converts it to an XML file."""


import struct
import xml.etree.ElementTree as et
from math_lib import *

def exportAsXML(file_name, in_centimeters):
    """ Loads in a TSH file and creates a skeleton(s) with animation data.
        
        Args:
            file_name: A string that represents the name and path of the TSH
                file that is to be loaded.
            in_centimeters: A boolean that indicates whether or not the units
                are in centimeters.
        
        Yeilds:
            An XML file of the TSH file given.
    """
    tsh_skels = []
    
    dir_path = ''
    # Open File
    try:
        in_file = open(file_name, 'rb')
        file_list = file_name.split("\\")
        for f in file_list[:-1]:
            dir_path += f + "\\"
        file_name = file_list[-1][:-4]
    except:
        print "Failed to load file:\n\t" + file_name
        return
    
    
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
        return
    
    file_size = struct.unpack("I", cur_bytes[:4])[0]
    num_version = struct.unpack("H", cur_bytes[4:6])[0]
    num_subversion = struct.unpack("H", cur_bytes[6:8])[0]
    num_skeletons = struct.unpack("H", cur_bytes[8:10])[0]
    num_frames = struct.unpack("Q", cur_bytes[10:18])[0]
    capture_frequency = struct.unpack("f", cur_bytes[18:])[0]
    
    root = et.Element("tsh_xml", {"VERSION": str(num_version) + "." + str(num_subversion)})
    
    parent_tree = {}
    
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
        
        if chunk_id != 1:
            for b in parent_tree:
                bone = parent_tree[b][0]
                for l in parent_tree[b][1]:
                    bone.append(l)
            
            parent_tree = {}
        
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
            tsh_skels.append([skel_name, []])
            units = "Inches"
            if in_centimeters:
                units = "Centimeters"
            
            skel_dic = {"NAME": skel_name, "UNITS": units}
            skel = et.Element("Skeleton", skel_dic)
            root.append(skel)
        
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
            tsh_skels[-1][-1].append(bone_name)
            
            bone_dic = {"NAME": bone_name}
            bone = et.Element("Bone", bone_dic)
            
            # Parent Bone Name
            parent_name = ""
            name_byte = in_file.read(1)
            while ord(name_byte) != 0:
                parent_name = parent_name + name_byte
                name_byte = in_file.read(1)
            if parent_name in parent_tree:
                parent_tree[parent_name][1].append(bone)
                parent_tree[bone_name] = [bone, []]
            else:
                skel.append(bone)
                parent_tree[bone_name] = [bone, []]
            
            # Bone Length
            length = struct.unpack("f", in_file.read(4))[0]
            if in_centimeters:
                length *= 1 /2.54
            bone.append(et.Element("Length", {"VALUE": str(length)}))
            
            # Bone Pose Orient
            quat = []
            i = 0
            while i < 4:
                quat.append(struct.unpack("f", in_file.read(4))[0])
                i += 1
            
            bone.append(et.Element("Pose_Orient", {
                "X": str(quat[0]),
                "Y": str(quat[1]),
                "Z": str(quat[2]),
                "W": str(quat[3])
            }))
            
            # Bone Offset
            pos = []
            i = 0
            while i < 3:
                pos.append(struct.unpack("f", in_file.read(4))[0])
                i += 1
            offset = Vector3(pos)
            if in_centimeters:
                offset *= 1 / 2.54
            
            bone.append(et.Element("Offest", {
                "X": str(offset.x),
                "Y": str(offset.y),
                "Z": str(offset.z)
            }))
            
            # Virtual Sensor Name
            vs_name = ""
            name_byte = in_file.read(1)
            while ord(name_byte) != 0:
                vs_name = vs_name + name_byte
                name_byte = in_file.read(1)
            if len(vs_name) > 0:
                vs = et.Element("Virtual_Sensor", {"NAME": vs_name})
                
                if num_version < 1:
                    # Virtual Sensor Pose Orient
                    quat = []
                    i = 0
                    while i < 4:
                        quat.append(struct.unpack("f", in_file.read(4))[0])
                        i += 1
                    vs.append(et.Element("Calibration_Orient", {
                        "X": str(quat[0]),
                        "Y": str(quat[1]),
                        "Z": str(quat[2]),
                        "W": str(quat[3])
                    }))
                    
                    # Sensor Pose Orient
                    euler = []
                    i = 0
                    while i < 3:
                        euler.append(struct.unpack("f", in_file.read(4))[0])
                        i += 1
                    vs.append(et.Element("Tare_Orient", {
                        "X": str(euler[0]),
                        "Y": str(euler[1]),
                        "Z": str(euler[2])
                    }))
                
                bone.append(vs)
        
        # Animation Data Chunk
        ########################################################################
        ## float32 [num_frames][numSkels][numBones][0:3] Position              #
        ## float32 [num_frames][numSkels][numBones][3:7] Orientation (X,Y,Z,W) #
        ########################################################################
        elif chunk_id == 2:
            cap_list = []
            for i in range(num_skeletons):
                cap = et.Element("Capture_Data", {
                    "NAME": file_name,
                    "FRAMES": str(num_frames),
                    "RATE": str(capture_frequency)
                })
                cap_list.append(cap)
            for f in range(num_frames):
                frame = et.Element("Frame", {"NUMBER": str(f)})
                for s in range(num_skeletons):
                    if cap_list[s].get("SKELETON_NAME") is None:
                        name = tsh_skels[s][0]
                        cap_list[s].set("SKELETON_NAME", name)
                    for b in tsh_skels[s][1]:
                        bone_data = et.Element("Bone_Data", {"NAME": b})
                        
                        # Position
                        pos = []
                        i = 0
                        while i < 3:
                            pos.append(struct.unpack("f", in_file.read(4))[0])
                            i += 1
                        pos = Vector3(pos)
                        if in_centimeters:
                            pos *= 1 / 2.54
                        
                        bone_data.append(et.Element("Position", {
                            "X": str(pos.x),
                            "Y": str(pos.y),
                            "Z": str(pos.z)
                        }))
                        
                        # Orientation
                        quat = []
                        i = 0
                        while i < 4:
                            quat.append(struct.unpack("f", in_file.read(4))[0])
                            i += 1
                        bone_data.append(et.Element("Orientation", {
                            "X": str(quat[0]),
                            "Y": str(quat[1]),
                            "Z": str(quat[2]),
                            "W": str(quat[3])
                        }))
                        frame.append(bone_data)
                    cap_list[s].append(frame)
            for i in range(num_skeletons):
                root.append(cap_list[i])
    in_file.close()
    
    
    # Write File
    try:
        out_file = open(dir_path + file_name + ".tsh.xml", 'w')
        indent(root)
        et.ElementTree(root).write(out_file, "us-ascii", True)
    except:
        print "Failed to create file:\n\t" + file_name + ".tsh.xml"
        return
    
    out_file.close()


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


## Main ##
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        print sys.argv
        exportAsXML(sys.argv[1], False)
    elif len(sys.argv) == 3:
        print sys.argv
        exportAsXML(sys.argv[1], sys.argv[2])
    else:
        print "Improper argument(s)"









