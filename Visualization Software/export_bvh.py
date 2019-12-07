#!/usr/bin/env python2.7

"""Writes a BVH file using information from the Mocap Studio."""

from math_lib import *


### Helper Functions ###
def buildHierarchy(bone_name, bone_list, in_centimeters, tabby=""):
    """ Builds a BVH hierarchy using recursion.
        
        Args:
            bone_name: A string that represents the name of the bone.
            bone_list: A list of all the bones that are used in the recorded
                session.
            in_centimeters: A boolean that indicates whether or not the units
                are in centimeters.
            tabby: A string of tabs used to correctly space in the hierarchy
                (default is "")
        
        Returns:
            A string that is the hierarchy of the bones in the session being
            saved.
    """
    str_list = []
    
    bone = bone_list[bone_name]

    # Write type and name of bone
    if bone.parent == None or bone.parent not in bone_list:
        str_list.append(tabby + "ROOT " + bone_name + "\n")
    else:
        str_list.append(tabby + "JOINT " + bone_name + "\n")
    str_list.append(tabby + "{\n")
    
    # Write the bone's offset
    str_list.append(tabby + "\tOFFSET\t")
    offset = bone.offset
    if in_centimeters:
        offset *= 2.54
    offset = offset.asArray()
    str_list.append("%.4f\t%.4f\t%.4f\n" % tuple(offset))
    
    # Write the bone's channels
    str_list.append(tabby + "\tCHANNELS ")
    if bone.parent == None or bone.parent not in bone_list:
        str_list.append("6 Xposition Yposition Zposition Zrotation Yrotation Xrotation\n")
    else:
        str_list.append("3 Zrotation Yrotation Xrotation\n")
    
    # Write the bone's children
    if len(bone.children) > 0:
        for child in bone.children:
            str_list.append(buildHierarchy(child, bone_list, in_centimeters, tabby + "\t"))
    else:
        cur_length = Vector3([0.0, bone.bone_length, 0.0])
        cur_orient = bone.pose_orient
        offset = (cur_orient * cur_length)
        if in_centimeters:
            offset *= 2.54
        offset = offset.asArray()
        str_list.append((tabby + "\tEnd Site\n" + tabby + "\t{\n" + tabby + "\t\tOFFSET\t"))
        str_list.append("%.4f\t%.4f\t%.4f\n" % tuple(offset))
        str_list.append(tabby + "\t}\n")
    
    str_list.append(tabby + "}\n")
    return "".join(str_list)


def buildFrame(cur_frame, bone_name, session, orient, interpolate, in_centimeters):
    """ Builds the motion data for the BVH file.
        
        Args:
            cur_frame: A dictionary of bones with orientation and position data.
            bone_name: A string of the bone's name that is currently being used.
            session: A RecordSession instance.
            orient: The orientation of the current bone's parent. A Quaternion
                instance.
            interpolate: A boolean that indicates whether or not to interpolate
                the data.
            in_centimeters: A boolean that indicates whether or not the units
                are in centimeters.
        
        Returns:
            A string of the orientation and position of all the bones at the
            current frame.
    """
    str_list = []
    
    bone = session.recorded_bone_list[bone_name]
    bone_frame_data = None
    if interpolate:
        bone_frame_data = session.interpolateData(bone_name, cur_frame)
    else:
        keyframe = session.getKeyframe(bone_name, cur_frame)
        bone_frame_data = keyframe.start_frame_data
    if bone.parent == None or bone.parent not in session.recorded_bone_list:
        # Write the position data
        pos_data = bone_frame_data[1]
        if in_centimeters:
            pos_data *= 2.54
        pos_data = pos_data.asArray()
        str_list.append("%.4f\t%.4f\t%.4f\t" % tuple(pos_data))
    
    # Write rotation data
    local_quat = -orient * bone_frame_data[0]
    rots = local_quat.toEuler('xyz').asDegreeArray()
    rots.reverse()
    str_list.append("%.4f\t%.4f\t%.4f\t" % tuple(rots))
    
    # Write children's data
    for child in bone.children:
        str_list.append(buildFrame(cur_frame, child, session, bone_frame_data[0], interpolate, in_centimeters))
    return "".join(str_list)


def findSkeletonChild(skel_name, bone_list):
    skel_children = []
    for bone_name in bone_list:
        if bone_list[bone_name].parent == skel_name:
            skel_children.append(bone_name)
    return skel_children


### Functions ###
def saveBVH(file_name, session, interpolate, in_centimeters):
    """ Saves the session given as a BVH file.
        
        Args:
            file_name: A string that has the path and file name for the BVH
                file.
            session: A RecordSession instance.
            interpolate: A boolean that indicates whether or not to interpolate
                the data.
            in_centimeters: A boolean that indicates whether or not the units
                are in centimeters.
        
        Yields:
            A complete BVH file at the location of the path given and with the
            name given.
    """
    try:
        bvh_file = open(file_name, 'w')
    except:
        print "Failed to save file:\n\t" + file_name
        return None
    
    # Build Bone Hierarchy
    bvh_file.write("HIERARCHY\n")
    for root_bone in session.root_bone_list:
        if root_bone not in session.recorded_bone_list:
            skel_children = findSkeletonChild(root_bone, session.recorded_bone_list)
            for child_bone in skel_children:
                bvh_file.write(buildHierarchy(child_bone, session.recorded_bone_list, in_centimeters))
        else:
            bvh_file.write(buildHierarchy(root_bone, session.recorded_bone_list, in_centimeters))
    
    # Build Motion Data
    bvh_file.write("MOTION\nFrames: " + str(len(session.frame_data)) + "\nFrame Time: " + str(session.capture_rate) + "\n")
    for frame in range(len(session.frame_data)):
        for root_bone in session.root_bone_list:
            if root_bone not in session.recorded_bone_list:
                skel_children = findSkeletonChild(root_bone, session.recorded_bone_list)
                for child_bone in skel_children:
                    bvh_file.write(buildFrame(frame, child_bone, session, Quaternion(), interpolate, in_centimeters))
            else:
                bvh_file.write(buildFrame(frame, root_bone, session, Quaternion(), interpolate, in_centimeters))
        bvh_file.write("\n")
    
    bvh_file.close()




