#!/usr/bin/env python2.7

"""Is a script that holds the classes used by the animator.py script."""

import sys
import time
import datetime
import threading
import wx
import re

import gl_scene_graph as gl_sg
from math_lib import *
import base_node_graph as base_ng

## Static Globals ##
NAMES_DEFAULT = 0
NAMES_3DSMAX = 1
NAMES_CLINIC = 2
MALE_BONE_RATIOS = {
    "Hips":[0.086, Matrix4(), Vector3(),
        {
            "Chest": [0.172, Matrix4(), None,
                {
                    "Neck": [0.103, Matrix4(), None,
                        {
                            "Head": [4, Matrix4(MATRIX4_90_X), None]
                        }
                    ],
                    "L_Shoulder": [0.079, Matrix4(MATRIX4_NEG_90_Z), None,
                        {
                            "L_Upper_Arm": [0.159, Matrix4(MATRIX4_NEG_90_Z), None,
                                {
                                    "L_Lower_Arm": [0.143, Matrix4(MATRIX4_NEG_90_Z), None,
                                        {
                                            "L_Hand": [0.107, Matrix4(MATRIX4_NEG_90_Z), None]
                                        }
                                    ]
                                }
                            ]
                        }
                    ],
                    "R_Shoulder": [0.079, Matrix4(MATRIX4_90_Z), None,
                        {
                            "R_Upper_Arm": [0.159, Matrix4(MATRIX4_90_Z), None,
                                {
                                    "R_Lower_Arm": [0.143, Matrix4(MATRIX4_90_Z), None,
                                        {
                                            "R_Hand": [0.107, Matrix4(MATRIX4_90_Z), None]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ],
            "L_Upper_Leg": [0.239, Matrix4(MATRIX4_180_Z), Vector3([0.049, 0, 0]),
                {
                    "L_Lower_Leg": [0.232, Matrix4(MATRIX4_180_Z), None,
                        {
                            "L_Foot": [0.139, Matrix4(MATRIX4_90_X), None]
                        }
                    ]
                }
            ],
            "R_Upper_Leg": [0.239, Matrix4(MATRIX4_180_Z), Vector3([-0.049, 0, 0]),
                {
                    "R_Lower_Leg": [0.232, Matrix4(MATRIX4_180_Z), None,
                        {
                            "R_Foot": [0.139, Matrix4(MATRIX4_90_X), None]
                        }
                    ]
                }
            ]
        }
    ]
}
FEMALE_BONE_RATIOS = {
    "Hips":[0.085, Matrix4(), Vector3(),
        {
            "Chest": [0.171, Matrix4(), None,
                {
                    "Neck": [0.103, Matrix4(), None,
                        {
                            "Head": [4, Matrix4(MATRIX4_90_X), None]
                        }
                    ],
                    "L_Shoulder": [0.075, Matrix4(MATRIX4_NEG_90_Z), None,
                        {
                            "L_Upper_Arm": [0.16, Matrix4(MATRIX4_NEG_90_Z), None,
                                {
                                    "L_Lower_Arm": [0.142, Matrix4(MATRIX4_NEG_90_Z), None,
                                        {
                                            "L_Hand": [0.105, Matrix4(MATRIX4_NEG_90_Z), None]
                                        }
                                    ]
                                }
                            ]
                        }
                    ],
                    "R_Shoulder": [0.075, Matrix4(MATRIX4_90_Z), None,
                        {
                            "R_Upper_Arm": [0.16, Matrix4(MATRIX4_90_Z), None,
                                {
                                    "R_Lower_Arm": [0.142, Matrix4(MATRIX4_90_Z), None,
                                        {
                                            "R_Hand": [0.105, Matrix4(MATRIX4_90_Z), None]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ],
            "L_Upper_Leg": [0.235, Matrix4(MATRIX4_180_Z), Vector3([0.054, 0, 0]),
                {
                    "L_Lower_Leg": [0.227, Matrix4(MATRIX4_180_Z), None,
                        {
                            "L_Foot": [0.125, Matrix4(MATRIX4_90_X), None]
                        }
                    ]
                }
            ],
            "R_Upper_Leg": [0.235, Matrix4(MATRIX4_180_Z), Vector3([-0.054, 0, 0]),
                {
                    "R_Lower_Leg": [0.227, Matrix4(MATRIX4_180_Z), None,
                        {
                            "R_Foot": [0.125, Matrix4(MATRIX4_90_X), None]
                        }
                    ]
                }
            ]
        }
    ]
}
BONE_SELECT = (0.6, 0.6, 0.0, 1.0)
BONE_STREAM_FAIL = (0.6, 0.0, 0.0, 1.0)
NAME_LIST = [
    'Head',
    'Neck',
    'Chest',
    'Hips',
    'L_Shoulder',
    'R_Shoulder',
    'L_Upper_Arm',
    'L_Lower_Arm',
    'L_Hand',
    'R_Upper_Arm',
    'R_Lower_Arm',
    'R_Hand',
    'L_Upper_Leg',
    'L_Lower_Leg',
    'L_Foot',
    'R_Upper_Leg',
    'R_Lower_Leg',
    'R_Foot'
]
HIP_LIST = ['hip', 'hips', 'pelvis', 'waist']
CHEST_LIST = ['chest', 'sternum', 'spine', 'back']
NECK_LIST = ['neck']
HEAD_LIST = ['head', 'skull', 'cranium']
LEFT_SHOULDER_LIST = [
    'l_shoulder',
    'l_clavicle',
    'l_collar',
    'l_scapula',
    'lshoulder',
    'lclavicle',
    'lcollar',
    'lscapula',
    'left_shoulder',
    'left_clavicle',
    'left_collar',
    'left_scapula',
    'leftshoulder',
    'leftclavicle',
    'leftcollar',
    'leftscapula'
]
LEFT_UP_ARM_LIST = [
    'l_upper_arm',
    'l_up_arm',
    'l_u_arm',
    'l_humerus',
    'l_arm',
    'lupperarm',
    'luparm',
    'luarm',
    'lhumerus',
    'larm',
    'left_upper_arm',
    'left_up_arm',
    'left_u_arm',
    'left_humerus',
    'left_arm',
    'leftupperarm',
    'leftuparm',
    'leftuarm',
    'lefthumerus',
    'leftarm'
]
LEFT_LOW_ARM_LIST = [
    'l_lower_arm',
    'l_low_arm',
    'l_l_arm',
    'l_ulna', 
    'l_radius',
    'l_fore_arm', 
    'llowerarm',
    'llowarm', 
    'llarm', 
    'lulna', 
    'lradius', 
    'lforearm', 
    'left_lower_arm',
    'left_low_arm',
    'left_l_arm',
    'left_ulna',
    'left_radius',
    'left_fore_arm',
    'leftlowerarm',
    'leftlowarm',
    'leftlarm',
    'leftulna',
    'leftradius',
    'leftforearm'
]
LEFT_HAND_LIST = ['l_hand', 'lhand', 'left_hand', 'lefthand']
LEFT_UP_LEG_LIST = [
    'l_upper_leg',
    'l_up_leg',
    'l_u_leg',
    'l_femur',
    'l_thigh',
    'lupperleg',
    'lupleg',
    'luleg',
    'lfemur',
    'lthigh',
    'left_upper_leg',
    'left_up_leg',
    'left_u_leg',
    'left_femur',
    'left_thigh',
    'leftupperleg',
    'leftupleg',
    'leftuleg',
    'leftfemur',
    'leftthigh'
]
LEFT_LOW_LEG_LIST = [
    'l_lower_leg',
    'l_low_leg',
    'l_l_leg',
    'l_tibia',
    'l_fibula',
    'l_shin',
    'llowerleg',
    'llowleg',
    'llleg',
    'ltibia',
    'lfibula',
    'lshin',
    'left_lower_leg',
    'leftlow_leg',
    'left_l_leg',
    'left_tibia',
    'left_fibula',
    'left_shin',
    'leftlowerleg',
    'leftlowleg',
    'leftlleg',
    'lefttibia',
    'leftfibula',
    'leftshin'
]
LEFT_FOOT_LIST = ['l_foot', 'lfoot', 'left_foot', 'leftfoot']
RIGHT_SHOULDER_LIST = [
    'r_shoulder',
    'r_clavicle',
    'r_collar',
    'r_scapula',
    'rshoulder',
    'rclavicle',
    'rcollar',
    'rscapula',
    'right_shoulder',
    'right_clavicle',
    'right_collar',
    'right_scapula',
    'rightshoulder',
    'rightclavicle',
    'rightcollar',
    'rightscapula'
]
RIGHT_UP_ARM_LIST = [
    'r_upper_arm',
    'r_up_arm',
    'r_u_arm',
    'r_humerus',
    'r_arm',
    'rupperarm',
    'ruparm',
    'ruarm',
    'rhumerus',
    'rarm',
    'right_upper_arm',
    'right_up_arm',
    'right_u_arm',
    'right_humerus',
    'right_arm',
    'rightupperarm',
    'rightuparm',
    'rightuarm',
    'righthumerus',
    'rightarm'
]
RIGHT_LOW_ARM_LIST = [
    'r_lower_arm',
    'r_low_arm',
    'r_l_arm',
    'r_ulna',
    'r_radius',
    'r_fore_arm',
    'rlowerarm',
    'rlowarm',
    'rlarm',
    'rulna',
    'rradius',
    'rforearm',
    'right_lower_arm',
    'right_low_arm',
    'right_l_arm',
    'right_ulna',
    'right_radius',
    'right_fore_arm',
    'rightlowerarm',
    'rightlowarm',
    'rightlarm',
    'rightulna',
    'rightradius',
    'rightforearm'
]
RIGHT_HAND_LIST = ['r_hand', 'rhand', 'right_hand', 'righthand']
RIGHT_UP_LEG_LIST = [
    'r_upper_leg',
    'r_up_leg',
    'r_u_leg',
    'r_femur',
    'r_thigh',
    'rupperleg',
    'rupleg',
    'ruleg',
    'rfemur',
    'rthigh',
    'right_upper_leg',
    'right_up_leg',
    'right_u_leg',
    'right_femur',
    'right_thigh',
    'rightupperleg',
    'rightupleg',
    'rightuleg',
    'rightfemur',
    'rightthigh'
]
RIGHT_LOW_LEG_LIST = [
    'r_lower_leg',
    'r_low_leg',
    'r_l_leg',
    'r_tibia',
    'r_fibula',
    'r_shin',
    'rlowerleg',
    'rlowleg',
    'rlleg',
    'rtibia',
    'rfibula',
    'rshin',
    'right_lower_leg',
    'rightlow_leg',
    'right_l_leg',
    'right_tibia',
    'right_fibula',
    'right_shin',
    'rightlowerleg',
    'rightlowleg',
    'rightlleg',
    'righttibia',
    'rightfibula',
    'rightshin'
]
RIGHT_FOOT_LIST = ['r_foot', 'rfoot', 'right_foot', 'rightfoot']
DRAW_CHILDREN = True


### Classes ###
class Logger(threading.Thread):
    def __init__(self, function, args=[]):
        threading.Thread.__init__(self)
        self.function = function
        self.args = args
        self.keep_logging = True
        self.log_lock = threading.Lock()
    
    def __stupidWXCall(self):
        """Does absoultely nothing."""
        pass
    
    def run(self):
        """Starts the threaded object."""
        
        wx.CallAfter(self.__stupidWXCall)
        self.function(*self.args)
        
        self.log_lock.acquire()
        self.keep_logging = False
        self.log_lock.release()


class KeyframeStruct(object):
    __slots__ = ('end_frame_data', 'end_frame_num', 'start_frame_data', 'start_frame_num')
    
    def __init__(self):
        self.start_frame_data = None
        self.start_frame_num = None
        self.end_frame_data = None
        self.end_frame_num = None
    
    def __repr__(self):
        return "Data:%s, %s" % tuple(self.start_frame_data)
    
    def __str__(self):
        return self.__repr__()


### Recording Classes ###
class RecordSession(object): # A storage class
    
    """ A class that stores the recorded motion capture data.
        
        Attributes:
            bone_frame_counter: A dictionary containing the frame number of a
                bone.
            capture_rate: A float that denotes the rate the data is captured.
            dups: A dictionary containing the number of duplicated data for a
                bone.
            first_timestamp: A dictionary containing the first timestamp of a
                sensor.
            frame_data: A list of dictionaries containing a keyframe index for a
                given bone.
                For example:
                    frame_data[FrameNum][BoneName] = KeyframeIdx
            frame_data_lock: An instance of threading Lock.
            interp_method: A flag indicating what interpolation method to use.
            keyframe_data: A dictionary containing a list of keyframes.
                For example:
                    keyframe_data[BoneName] = [KeyframeStruct, ...]
            name: A string that has the name of the session.
            recorded_bone_list: A dictionary containing BoneState objects of
                what Bone objects were recorded.
            root_bone_list: A list of Bone objects that are at the root of the
                skeleton.
    """
    SLERP = 1
    SQUAD = 2
    def __init__(self, name, capture_rate, ped_track=False, log_win=None):
        """ Initializes the RecordSession class.
            
            Args:
                capture_rate: A float that denotes the rate the data is
                    captured.
        """
        self.name = name
        self.capture_rate = capture_rate
        # Using the two structures below, a frame may be resolved by getting the
        # current frame from frame_data, using the stored index to get the
        # proper keyframe from each bone's keyframe database, and resolving the
        # final frame value based on interpolation method
        self.frame_data = []
        self.keyframe_data = {}
        
        self.frame_data_lock = threading.Lock()
        self.recorded_bone_list = {}
        self.root_bone_list = []
        self.first_timestamp = {}
        self.bone_frame_counter = {}
        self.interp_method = RecordSession.SLERP
        self.dups = {}
        self.is_ped_track = ped_track
        self.log_window = log_win
    
    def getTopFrame(self):
        top_frame = {}
        self.frame_data_lock.acquire()
        if len(self.frame_data) > 1:
            for b in self.keyframe_data.keys():
                key_data = self.keyframe_data[b][self.frame_data[-2][b]]
                top_frame[b] = key_data.start_frame_data
        else:
            for b in self.keyframe_data.keys():
                if b not in self.frame_data[-1]:
                    top_frame[b] = [Quaternion(), Vector3()]
                else:
                    key_data = self.keyframe_data[b][self.frame_data[-1][b]]
                    top_frame[b] = key_data.start_frame_data
        self.frame_data_lock.release()
        return top_frame
    
    def recordFrame(self, root, b_list, total_frames):
        """ Gets data from the Bone objects and stores it in a frame.
            
            Args:
                b_list: A list containing what Bone objects are being recorded.
        """
        synched_data = {}
        
        for node in base_ng.global_input_nodes:
            is_output = False
            for output_port in node.output_ports:
                if output_port.connection is not None:
                    is_output = True
                    break
            if is_output:
                if node.device is not None:
                    device = node.device
                    serial_num = device.serial_number
                    first_frame_timestamp = None
                    prev_frame_timestamp = None
                    prev_timestamp = None
                    prev_orient = None
                    frame = 0
                    synched_data[serial_num] = []
                    for data in device.stream_data:
                        timestamp, tmp_orient = data
                        tmp_orient = list(tmp_orient)
                        
                        if first_frame_timestamp is None:
                            quat = Quaternion(tmp_orient)
                            first_frame_timestamp = timestamp
                            prev_frame_timestamp = timestamp
                            
                            synched_data[serial_num].append([prev_frame_timestamp, quat])
                            frame += 1
                        else:
                            diff_timestamp = (timestamp - prev_frame_timestamp) * 0.000001
                            if diff_timestamp >= self.capture_rate:
                                if frame > total_frames:
                                    break
                                frames_passed = int(round(diff_timestamp / self.capture_rate))
                                if frames_passed <= 1:
                                    cur_quat = Quaternion(tmp_orient)
                                    
                                    prev_quat = Quaternion(prev_orient)
                                    prev_diff_timestamp = (prev_timestamp - prev_frame_timestamp) * 0.000001
                                    
                                    interp_percentage = (self.capture_rate - prev_diff_timestamp) / (diff_timestamp - prev_diff_timestamp)
                                    
                                    prev_frame_timestamp = ((timestamp - prev_timestamp) * interp_percentage) + prev_timestamp
                                    
                                    if(self.interp_method == RecordSession.SLERP):
                                        if interp_percentage > 1.0:
                                            interp_percentage = 1.0
                                        elif interp_percentage < 0.0:
                                            interp_percentage = 0.0
                                        interp_orient = prev_quat.slerp(cur_quat, interp_percentage)
                                        quat = interp_orient
                                    else:
                                        if interp_percentage < 0.5:
                                            quat = prev_quat
                                        else:
                                            quat = cur_quat
                                    
                                    synched_data[serial_num].append([prev_frame_timestamp, quat])
                                    frame += 1
                                else:
                                    cur_quat = Quaternion(tmp_orient)
                                    
                                    prev_quat = Quaternion(prev_orient)
                                    for i in range(frames_passed):
                                        prev_diff_timestamp = (prev_timestamp - prev_frame_timestamp) * 0.000001
                                        
                                        interp_percentage = (self.capture_rate - prev_diff_timestamp) / (diff_timestamp - prev_diff_timestamp)
                                        
                                        prev_frame_timestamp = ((timestamp - prev_timestamp) * interp_percentage) + prev_timestamp
                                        
                                        if(self.interp_method == RecordSession.SLERP):
                                            if interp_percentage > 1.0:
                                                interp_percentage = 1.0
                                            elif interp_percentage < 0.0:
                                                interp_percentage = 0.0
                                            interp_orient = prev_quat.slerp(cur_quat, interp_percentage)
                                            quat = interp_orient
                                        else:
                                            if interp_percentage < 0.5:
                                                quat = prev_quat
                                            else:
                                                quat = cur_quat
                                        
                                        synched_data[serial_num].append([prev_frame_timestamp, quat])
                                        frame += 1
                                        
                                        prev_timestamp = prev_frame_timestamp
                                        prev_quat = quat.copy()
                                        
                                        diff_timestamp = (timestamp - prev_frame_timestamp) * 0.000001
                        
                        prev_timestamp = timestamp
                        prev_orient = tmp_orient
                    if len(synched_data[serial_num]) < total_frames:
                        print len(synched_data[serial_num])
                        for i in range(total_frames - len(synched_data[serial_num])):
                            new_data = []
                            for data in synched_data[serial_num][-1]:
                                if type(data) is Quaternion:
                                    new_data.append(data.copy())
                                else:
                                    new_data.append(data)
                            synched_data[serial_num].append(new_data)
        
        frame = 0
        while frame < total_frames:
            self.frame_data.append({})
            for input_node in base_ng.global_input_nodes:
                input_node.performOperation(synched_data)
            for static_node in base_ng.global_static_nodes:
                static_node.performOperation()
            
            for b in b_list:
                if b.vs_node is not None:
                    data = b.vs_node.input_ports[0].data
                    tmp_orient = Quaternion()
                    if data is not None:
                        data_type = b.vs_node.input_ports[0].data_type
                        timestamp = b.vs_node.input_ports[0].timestamp
                        
                        if data_type != "Q":
                            data = data.toQuaternion()
                        
                        tmp_orient = data.copy()
                    
                    if frame == 0:
                        self.keyframe_data[b.name] = []
                        key_data = KeyframeStruct()
                        key_data.start_frame_num = frame
                        key_data.start_frame_data = [tmp_orient]
                        self.keyframe_data[b.name].append(key_data)
                        
                        self.bone_frame_counter[b.name] = 1
                        key_idx = len(self.keyframe_data[b.name]) - 1
                        # Next we add the keyframe reference to this bone's
                        # latest frame.
                        self.frame_data[-1][b.name] = key_idx
                    else:
                        # We have new data that needs to be added. Finish the
                        # current keyframe.
                        self.keyframe_data[b.name][-1].end_frame_num = frame
                        self.keyframe_data[b.name][-1].end_frame_data = [tmp_orient]
                        
                        key_data = KeyframeStruct()
                        key_data.start_frame_num = frame
                        key_data.start_frame_data = [tmp_orient]
                        self.keyframe_data[b.name].append(key_data)
                    
                        self.bone_frame_counter[b.name] += 1
                        key_idx = len(self.keyframe_data[b.name]) - 1
                        # Next we add the keyframe reference to this bone's
                        # latest frame.
                        self.frame_data[-1][b.name] = key_idx
                else:
                    if frame == 0:
                        self.keyframe_data[b.name] = []
                        key_data = KeyframeStruct()
                        key_data.start_frame_num = frame
                        key_data.start_frame_data = [Quaternion()]
                        self.keyframe_data[b.name].append(key_data)
                        
                        self.bone_frame_counter[b.name] = 1
                        key_idx = len(self.keyframe_data[b.name]) - 1
                        self.frame_data[-1][b.name] = key_idx
                    
                    else:
                        self.keyframe_data[b.name][-1].end_frame_num = frame
                        self.keyframe_data[b.name][-1].end_frame_data = [Quaternion()]
                        key_data = KeyframeStruct()
                        key_data.start_frame_num = frame
                        key_data.start_frame_data = [Quaternion()]
                        self.keyframe_data[b.name].append(key_data)
                        
                        self.bone_frame_counter[b.name] += 1
                        key_idx = len(self.keyframe_data[b.name]) - 1
                        self.frame_data[-1][b.name] = key_idx
            frame += 1
            
            if self.log_window is not None:
                self.log_window.onLogData()
        
        for cur_frame in range(len(self.frame_data)):
            root.updateRecord(self, cur_frame)
    
    def recordSingleFrame(self, b_list):
        """ Gets data from the Bone objects and stores it in a frame.
            
            Args:
                b_list: A list containing what Bone objects are being recorded.
        """
        timestamp_units = 0.000001  # Second / Microsecond
        self.frame_data.append({})
        cur_frame = len(self.frame_data) - 1
        for b in b_list:
            if cur_frame == 0:
                tmp_orient = Quaternion()
            else:
                keyframe = self.getKeyframe(b.name, cur_frame - 1)
                tmp_orient = keyframe.start_frame_data[0]
            timestamp = 0
            frame = cur_frame
            # If the sensor is associated with a Virtual Sensor node, try to get
            # stream data out of it.
            if b.vs_node is not None:
                data = b.vs_node.input_ports[0].data
                if data is not None:
                    data_type = b.vs_node.input_ports[0].data_type
                    timestamp = b.vs_node.input_ports[0].timestamp
                    if data_type != "Q":
                        data = data.toQuaternion()
                    
                    tmp_orient = data.copy()
                    
                    if b.name not in self.bone_frame_counter:
                        self.bone_frame_counter[b.name] = 1
                    else:
                        self.bone_frame_counter[b.name] += 1
                    # Iniialize our frame time synchronization data for the
                    # first frame.
                    device = b.vs_node.getInputDevice(check_connect=False)
                    if device is not None:
                        id_hex = device.serial_number_hex
                        if id_hex not in self.first_timestamp:
                            self.first_timestamp[id_hex] = timestamp
                            frame = 0
                        else:
                            diff_timestamp = (timestamp - self.first_timestamp[id_hex])
                            frame = int(round((diff_timestamp * timestamp_units) / self.capture_rate))
            # Insert new data into the proper frame of animation.
            # Find out if we need to make a new keyframe struct for the bone.
            # If so, make it. If not, just overwrite the orient in the "start"
            # orient as it may be sightly more up-to-date data.
            self.frame_data_lock.acquire()
            if b.name not in self.keyframe_data:
                # We need to initialize this bone's frame storage structure.
                self.keyframe_data[b.name] = []
                key_data = KeyframeStruct()
                key_data.start_frame_num = 0
                key_data.start_frame_data = [tmp_orient, b.position]
                self.keyframe_data[b.name].append(key_data)
            
            elif frame > self.keyframe_data[b.name][-1].start_frame_num:
                # We have new data that needs to be added. Finish the current
                # keyframe.
                self.keyframe_data[b.name][-1].end_frame_num = frame
                self.keyframe_data[b.name][-1].end_frame_data = [tmp_orient, b.position]
                # Then add a new keyframe
                key_data = KeyframeStruct()
                key_data.start_frame_num = frame
                key_data.start_frame_data = [tmp_orient, b.position]
                self.keyframe_data[b.name].append(key_data)
            
            else:
                self.dups[b.name] += 1
            
            # We add a new sub-frame that references its keyframe range. First
            # we ensure that the correct keyframe range is being referenced.
            key_idx = len(self.keyframe_data[b.name]) - 1
            while(self.keyframe_data[b.name][key_idx].start_frame_num > cur_frame):
                key_idx -= 1
            # Next we add the keyframe reference to this bone's latest frame.
            self.frame_data[-1][b.name] = key_idx
            self.frame_data_lock.release()
            
            if self.log_window is not None:
                self.log_window.onLogData()
    
    def getKeyframe(self, bone_name, frame):
        return self.keyframe_data[bone_name][self.frame_data[frame][bone_name]]
    
    def createFromBVH(self, animation_data):
        for frame in range(len(animation_data)):
            bone_keyframes = animation_data[frame]
            self.frame_data.append({})
            for b_name in bone_keyframes:
                if b_name not in self.keyframe_data:
                    # We need to initialize this bone's frame storage structure
                    self.keyframe_data[b_name] = []
                # Add a new keyframe
                key_data = KeyframeStruct()
                key_data.start_frame_num = frame
                key_data.start_frame_data = bone_keyframes[b_name]
                self.keyframe_data[b_name].append(key_data)
                # Next we add the keyframe reference to this bone's latest frame
                self.frame_data[-1][b_name] = frame
    
    def createFromTSH(self, number_frames, skeletons):
        for frame in range(number_frames):
            self.frame_data.append({})
            for skel in skeletons:
                for bone in skel.bones:
                    if bone.name not in self.keyframe_data:
                        # We need to initialize this bone's frame storage
                        # structure
                        self.keyframe_data[bone.name] = []
                    # Add a new keyframe
                    key_data = KeyframeStruct()
                    key_data.start_frame_num = frame
                    key_data.start_frame_data = [bone.frames[frame].orient, bone.frames[frame].position]
                    self.keyframe_data[bone.name].append(key_data)
                    # Next we add the keyframe reference to this bone's latest
                    # frame
                    self.frame_data[-1][bone.name] = frame
    
    def interpolateData(self, bone_name, cur_frame):
        keyframe = self.getKeyframe(bone_name, cur_frame)
        if self.interp_method == RecordSession.SLERP:
            if keyframe.end_frame_num is not None:
                interp_percentage = (cur_frame - keyframe.start_frame_num) / (1.0 * (keyframe.end_frame_num - keyframe.start_frame_num))
                if (cur_frame < keyframe.start_frame_num):
                    print "########################################"
                    print "Start Frame:", keyframe.start_frame_num
                    print "Current frame:", cur_frame
                    print "End Frame:", keyframe.end_frame_num
                    print "Interpolation Percentage:", interp_percentage
                if interp_percentage > 1:
                    interp_percentage = 1
                elif interp_percentage < 0:
                    interp_percentage = 0
                interp_orient = keyframe.start_frame_data[0].slerp(keyframe.end_frame_data[0], interp_percentage)
                frame_diff = keyframe.end_frame_data[1] - keyframe.start_frame_data[1]
                interp_pos = keyframe.start_frame_data[1] + (frame_diff * interp_percentage)
                return [interp_orient, interp_pos]
            else:
                return keyframe.start_frame_data
        elif self.interp_method == RecordSession.SQUAD:
            if keyframe.end_frame_num is not None:
                prev_q = None
                cur_q = None
                next_q = None
                cur_s = None
                next_s = None
                if cur_frame == 0:
                    cur_s = keyframe.start_frame_data[0]
                else:
                    prev_keyframe = getKeyframe(bone_name, cur_frame - 1)
                    prev_q = prev_keyframe.start_frame_data[0]
                    cur_q = keyframe.start_frame_data[0]
                    next_q = keyframe.end_frame_data[0]
                    cur_s = cur_q * math.exp(-((math.log(-cur_q * next_q) + math.log(-cur_q * prev_q)) / 4.0))  ###### NOT CORRECT AT ALL ###########
                if cur_frame == len(self.frame_data) - 2:
                    next_keyframe = getKeyframe(bone_name, cur_frame + 1)
                    next_s = next_keyframe.start_frame_data[0]


class Recorder(threading.Thread): # Our threaded recording class
    
    """ A threading class that records data.
        
        Attributes:
            bone_list: A list containing what Bone objects are being recorded.
            capture_rate: A float that denotes the rate the data is captured.
            elapsed_time: A 
            keep_recording: A boolean that lets the Recorder know when to stop
                collecting data.
            record_lock: An instance of threading Lock.
            session: An instance of RecordSession.
            total_frames: An integer denoting what is the current total frames.
    """
    def __init__(self, capture_rate, root, b_list, ped_track, log_win):
        """ Initializes the Recorder class.
            
            Args:
                capture_rate: A float that denotes the rate the data is
                    captured.
                b_list: A list containing what Bone objects are being recorded.
        """
        threading.Thread.__init__(self)
        self.capture_rate = capture_rate
        self.session = RecordSession(str(datetime.datetime.today())[:-7].replace(' ', '_').replace(':', '.'), capture_rate, ped_track, log_win)
        self.keep_recording = True
        self.root = root
        self.bone_list = b_list
        self.total_frames = 0
        self.record_lock = threading.Lock()
        self._setupSession()
    
    def _setupSession(self):
        for bone in self.bone_list:
            record_bone = BoneState()
            record_bone.bone_length = bone.getLength()
            record_bone.pose_orient = bone.getPoseOrientation()
            if type(bone.parent) is SkelNode:
                record_bone.parent = None
            else:
                record_bone.parent = bone.parent.getName()
            record_bone.offset = bone.getOffset()
            
            if bone.vs_node is not None:
                record_bone.vs_name = bone.vs_node.name
            
            for child in bone.children:
                record_bone.children.append(child.getName())
            
            self.session.recorded_bone_list[bone.getName()] = record_bone
        
        for child in self.root.children:
            self.session.root_bone_list.append(child.getName())
    
    def __stupidWXCall(self):
        """Does absoultely nothing."""
        pass
    
    def run(self):
        """Starts the threaded object."""
        
        wx.CallAfter(self.__stupidWXCall)
        self.session.recordFrame(self.root, self.bone_list, self.total_frames)
        
        self.record_lock.acquire()
        self.keep_recording = False
        self.record_lock.release()


### Bone Classes ###
class BoneState(object): # Actually a struct
    
    """ A class that holds data from a Bone object for recording, loading, and
        saving.
        
        A class that is being used like a C++ struct.
        
        Attributes:
            bone_length: A float that denotes the length of the Bone object.
            children: A list of strings of the names of other Bone objects.
            offset: An instance of Vector3 that denotes the position of the Bone
                object.
            parent: A string that denotes the name of another Bone object.
            pose_orient: An instance of Matrix4 that denotes the initial
                orientation of the Bone object.
            sensor_pose: An instance of Euler that denotes the orientation of
                the sensor. Used for TSH Version 0.2 or earlier.
            vs_name: A string that denotes the name of a VirtualSensorNode
                object.
            vs_pose: An instance of Quaternion that denotes the initial
                orientation of the sensor. Used for TSH Version 0.2 or earlier.
    """
    
    __slots__ = ('bone_length', 'children', 'offset', 'parent', 'pose_orient', 'sensor_pose', 'vs_name', 'vs_pose')
    
    def __init__(self):
        self.bone_length = None
        self.children = []
        self.offset = None
        self.parent = None
        self.pose_orient = None
        self.sensor_pose = None     # Used for TSH Version 0.2 or earlier.
        self.vs_name = ""
        self.vs_pose = None         # Used for TSH Version 0.2 or earlier.


class SkelNode(object):
    
    """ An object that is used as a root for Skeleton objects.
        
        Attributes:
            children: A list of references to Bone objects.
            name: A string denoting a name for the object.
            parent: A reference to a SkelNode or Bone object.
    """
    
    __slots__ = ('children', 'name', 'parent')
    
    def __init__(self):
        self.children = []
        self.name = "None"
        self.parent = None
    
    def appendChild(self, child):
        """ Appends a Bone object to children list and makes self parent to Bone
            object.
            
            Args:
                child: A reference to a Bone object.
        """
        self.children.append(child)
        child.parent = self
    
    def performFunction(self, func, args):
        if hasattr(self, func):
            getattr(self, func)(*args)
        for child in self.children:
            child.performFunction(func, args)
    
    def getName(self):
        return self.name
    
    def getNode(self, node):
        """ A function that finds a Bone object in the skeleton tree
            recursively.
            
            Args:
                node: A string denoting the name of the Bone object to be found.
            
            Returns:
                Returns itself or a child.
        """
        if node == self.name:
            return self
        
        child_return = None
        for child in self.children:
            child_return = child.getNode(node)
            if child_return is not None:
                break
        return child_return
    
    def update(self, streaming=False, frame_data=None):
        """ Updates the object and its children.
            
            Args:
                streaming: A boolean that indicates if the Mocap Studio is
                    streaming data (default is False)
                frame_data: A map that holds frame data for the bones of the
                    Skeleton (default is None)
        """
        for child in self.children:
            child.update(streaming, frame_data)
    
    def updateRecord(self, session, cur_frame):
        """ Updates the object and its children for recording.
            
            Args:
                session: A RecordSession instance.
                cur_frame: An integer denoting the current frame.
        """
        for child in self.children:
            child.updateRecord(session, cur_frame)


class Skeleton(SkelNode):
    
    """ A SkelNode that is used to store Bone objects that make a skeleton.
        
        Attributes:
            call_lock: An instance of threading Lock.
            chest_bone: A reference to a Bone object, used for the Chest.
            children: A list of references to Bone objects.
            foot_bone_l: A reference to a Bone object, used for the Left Foot.
            foot_bone_r: A reference to a Bone object, used for the Right Foot.
            foot_down_l: A boolean that denotes the Left Foot is down or not.
            foot_down_r: A boolean that denotes the Right Foot is down or not.
            foot_epsilon: A float denoting the margin of error for the feet
                touching the ground.
            foot_pos_l: An instance of Vector3 denoting the previous Left Foot
                position.
            foot_pos_r: An instance of Vector3 denoting the previous Right Foot
                position.
            hand_bone_l: A reference to a Bone object, used for the Left Hand.
            hand_bone_r: A reference to a Bone object, used for the Right Hand.
            head_bone: A reference to a Bone object, used for the Head.
            hip_bone: A reference to a Bone object, used for the Hip.
            low_arm_bone_l: A reference to a Bone object, used for the Left
                Lower Arm.
            low_arm_bone_r: A reference to a Bone object, used for the Right
                Lower Arm.
            low_leg_bone_l: A reference to a Bone object, used for the Left
                Lower Leg.
            low_leg_bone_r: A reference to a Bone object, used for the Right
                Lower Leg.
            lowest_point: A float denoting the lowest point of the skeleton.
            mesh: A reference to a SkelMeshNode.
            name: A string denoting a name for the object.
            neck_bone: A reference to a Bone object, used for the Neck.
            orientation: An instance of Matrix4 denoting the initial
                orientation.
            parent: A reference to a SkelNode.
            position: An instance of Vector3 denoting the absoulte position.
            pose_position: An instance of Vector3 denoting the initial position.
            shoulder_bone_l: A reference to a Bone object, used for the Left
                Shoulder.
            shoulder_bone_r: A reference to a Bone object, used for the Right
                Shoulder.
            up_arm_bone_l: A reference to a Bone object, used for the Left Upper
                Arm.
            up_arm_bone_r: A reference to a Bone object, used for the Right
                Upper Arm.
            up_leg_bone_l: A reference to a Bone object, used for the Left Upper
                Leg.
            up_leg_bone_r: A reference to a Bone object, used for the Right
                Upper Leg.
    """
    
    __slots__ = (
        'call_lock',
        'chest_bone',
        'foot_bone_l',
        'foot_bone_r',
        'foot_down_l',
        'foot_down_r',
        'foot_epsilon',
        'foot_pos_l',
        'foot_pos_r',
        'hand_bone_l',
        'hand_bone_r',
        'head_bone',
        'hip_bone',
        'low_arm_bone_l',
        'low_arm_bone_r',
        'low_leg_bone_l',
        'low_leg_bone_r',
        'lowest_point',
        'mesh',
        'neck_bone',
        'pose_orientation',
        'position',
        'shoulder_bone_l',
        'shoulder_bone_r',
        'up_arm_bone_l',
        'up_arm_bone_r',
        'up_leg_bone_l',
        'up_leg_bone_r'
    )
    
    def __init__(self, name, orient=Matrix4(), pos=Vector3()):
        """ Initializes the Bone class.
            
            Args:
                name: A string denoting a name for the Skeleton object.
                orient: An instance of Matrix4 denoting the initial orientation
                    (default is Identity Matrix)
                pos: An instance of Vector3 denoting the absoulte position
                    (default is Origin)
        """
        SkelNode.__init__(self)
        self.call_lock = threading.Lock()
        self.chest_bone = None
        self.foot_bone_l = None
        self.foot_bone_r = None
        self.foot_down_l = True
        self.foot_down_r = True
        self.foot_epsilon = 0.1
        self.foot_pos_l = None
        self.foot_pos_r = None
        self.hand_bone_l = None
        self.hand_bone_r = None
        self.head_bone = None
        self.hip_bone = None
        self.low_arm_bone_l = None
        self.low_arm_bone_r = None
        self.low_leg_bone_l = None
        self.low_leg_bone_r = None
        self.lowest_point = float('inf')
        self.mesh = None
        self.name = name
        self.neck_bone = None
        self.pose_orientation = orient.copy()
        self.position = pos.copy()
        self.shoulder_bone_l = None
        self.shoulder_bone_r = None
        self.up_arm_bone_l = None
        self.up_arm_bone_r = None
        self.up_leg_bone_l = None
        self.up_leg_bone_r = None
    
    def __repr__(self):
        return "Skeleton name: " + self.name
    
    def __str__(self):
        return self.__repr__()
    
    def buildSkeleton(self, bone_name, height, bone_map, bone_list, canvas, properties, parent=None):
        # Create Bone
        length, pose, pos = bone_map[bone_name][:3]
        tmp_bone = None
        self.call_lock.acquire()
        if parent is None:
            pos *= height
            length *= height
            name, vs_node = properties[bone_name]
            i = 0
            while name in bone_list:
                name = name.rstrip('0123456789')
                name += str(i)
                i += 1
            tmp_bone = Bone(name, length, pos, pose, vs_node)
            bone_list[name] = tmp_bone
            canvas.addMesh(tmp_bone)
            
            tmp_bone.setAmbientColor()
            
            tmp_bone.setSkeletonOrient(self.pose_orientation)
            
            if bone_name == 'Hips':
                self.hip_bone = tmp_bone
            elif bone_name == 'Chest':
                self.chest_bone = tmp_bone
            elif bone_name == 'Neck':
                self.neck_bone = tmp_bone
            elif bone_name == 'Head':
                self.head_bone = tmp_bone
            elif bone_name == 'L_Shoulder':
                self.shoulder_bone_l = tmp_bone
            elif bone_name == 'L_Upper_Arm':
                self.up_arm_bone_l = tmp_bone
            elif bone_name == 'L_Lower_Arm':
                self.low_arm_bone_l = tmp_bone
            elif bone_name == 'L_Hand':
                self.hand_bone_l = tmp_bone
            elif bone_name == 'R_Shoulder':
                self.shoulder_bone_r = tmp_bone
            elif bone_name == 'R_Upper_Arm':
                self.up_arm_bone_r = tmp_bone
            elif bone_name == 'R_Lower_Arm':
                self.low_arm_bone_r = tmp_bone
            elif bone_name == 'R_Hand':
                self.hand_bone_r = tmp_bone
            elif bone_name == 'L_Upper_Leg':
                self.up_leg_bone_l = tmp_bone
            elif bone_name == 'L_Lower_Leg':
                self.low_leg_bone_l = tmp_bone
            elif bone_name == 'L_Foot':
                self.foot_bone_l = tmp_bone
            elif bone_name == 'R_Upper_Leg':
                self.up_leg_bone_r = tmp_bone
            elif bone_name == 'R_Lower_Leg':
                self.low_leg_bone_r = tmp_bone
            elif bone_name == 'R_Foot':
                self.foot_bone_r = tmp_bone
            
            # Append to skeleton
            self.appendChild(tmp_bone)
        else:
            if pos is None:
                pos = parent.pose_orientation * Vector3(UNIT_Y) * parent.length
                if bone_name == "L_Shoulder":
                    pos += Vector3(UNIT_X) * 0.02 * height
                    pos += Vector3(NEG_UNIT_Z) * 1.5
                    pose *= Euler([15, 0, 0], is_degrees=True).toMatrix4()
                if bone_name == "R_Shoulder":
                    pos += Vector3(NEG_UNIT_X) * 0.02 * height
                    pos += Vector3(NEG_UNIT_Z) * 1.5
                    pose *= Euler([15, 0, 0], is_degrees=True).toMatrix4()
            else:
                pos *= height
            if bone_name != "Head":
                length *= height
            name, vs_node = properties[bone_name]
            i = 0
            while name in bone_list:
                name = name.rstrip('0123456789')
                name += str(i)
                i += 1
            tmp_bone = Bone(name, length, pos, pose, vs_node)
            bone_list[name] = tmp_bone
            canvas.addMesh(tmp_bone)
            
            tmp_bone.setAmbientColor()
            
            if bone_name == 'Hips':
                self.hip_bone = tmp_bone
            elif bone_name == 'Chest':
                self.chest_bone = tmp_bone
            elif bone_name == 'Neck':
                self.neck_bone = tmp_bone
            elif bone_name == 'Head':
                self.head_bone = tmp_bone
            elif bone_name == 'L_Shoulder':
                self.shoulder_bone_l = tmp_bone
            elif bone_name == 'L_Upper_Arm':
                self.up_arm_bone_l = tmp_bone
            elif bone_name == 'L_Lower_Arm':
                self.low_arm_bone_l = tmp_bone
            elif bone_name == 'L_Hand':
                self.hand_bone_l = tmp_bone
            elif bone_name == 'R_Shoulder':
                self.shoulder_bone_r = tmp_bone
            elif bone_name == 'R_Upper_Arm':
                self.up_arm_bone_r = tmp_bone
            elif bone_name == 'R_Lower_Arm':
                self.low_arm_bone_r = tmp_bone
            elif bone_name == 'R_Hand':
                self.hand_bone_r = tmp_bone
            elif bone_name == 'L_Upper_Leg':
                self.up_leg_bone_l = tmp_bone
            elif bone_name == 'L_Lower_Leg':
                self.low_leg_bone_l = tmp_bone
            elif bone_name == 'L_Foot':
                self.foot_bone_l = tmp_bone
            elif bone_name == 'R_Upper_Leg':
                self.up_leg_bone_r = tmp_bone
            elif bone_name == 'R_Lower_Leg':
                self.low_leg_bone_r = tmp_bone
            elif bone_name == 'R_Foot':
                self.foot_bone_r = tmp_bone
            
            # Append to parent
            parent.appendChild(tmp_bone)
        self.call_lock.release()
        
        # Set children up
        if len(bone_map[bone_name]) > 3:
            for child in bone_map[bone_name][3]:
                self.buildSkeleton(child, height, bone_map[bone_name][3], bone_list, canvas, properties, tmp_bone)
    
    def buildSkeletonCopy(self, skel, bone_list, canvas, parent=None, parent_copy=None):
        # Create Bone
        tmp_bone = None
        if parent is None:
            for child in self.children:
                name = child.getName() + '_Copy'
                i = 0
                while name in bone_list:
                    name = name.rstrip('0123456789')
                    name += str(i)
                    i += 1
                length = child.getLength()
                pose = child.getPoseOrientation()
                pos = child.getOffset()
                
                tmp_bone = Bone(name, length, pos, pose)
                bone_list[name] = tmp_bone
                canvas.addMesh(tmp_bone)
                
                # Update ambient color
                tmp_bone.setAmbientColor()
                
                self.call_lock.acquire()
                
                tmp_bone.setSkeletonOrient(self.pose_orientation)
                
                if child == self.hip_bone:
                    skel.setHipBone(tmp_bone)
                elif child == self.chest_bone:
                    skel.setChestBone(tmp_bone)
                elif child == self.neck_bone:
                    skel.setNeckBone(tmp_bone)
                elif child == self.head_bone:
                    skel.setHeadBone(tmp_bone)
                elif child == self.shoulder_bone_l:
                    skel.setShoulderBoneLeft(tmp_bone)
                elif child == self.up_arm_bone_l:
                    skel.setUpperArmBoneLeft(tmp_bone)
                elif child == self.low_arm_bone_l:
                    skel.setLowerArmBoneLeft(tmp_bone)
                elif child == self.hand_bone_l:
                    skel.setHandBoneLeft(tmp_bone)
                elif child == self.shoulder_bone_r:
                    skel.setShoulderBoneRight(tmp_bone)
                elif child == self.up_arm_bone_r:
                    skel.setUpperArmBoneRight(tmp_bone)
                elif child == self.low_arm_bone_r:
                    skel.setLowerArmBoneRight(tmp_bone)
                elif child == self.hand_bone_r:
                    skel.setHandBoneRight(tmp_bone)
                elif child == self.up_leg_bone_l:
                    skel.setUpperLegBoneLeft(tmp_bone)
                elif child == self.low_leg_bone_l:
                    skel.setLowerLegBoneLeft(tmp_bone)
                elif child == self.foot_bone_l:
                    skel.setFootBoneLeft(tmp_bone)
                elif child == self.up_leg_bone_r:
                    skel.setUpperLegBoneRight(tmp_bone)
                elif child == self.low_leg_bone_r:
                    skel.setLowerLegBoneRight(tmp_bone)
                elif child == self.foot_bone_r:
                    skel.setFootBoneRight(tmp_bone)
                
                self.call_lock.release()
                
                self.buildSkeletonCopy(skel, bone_list, canvas, child, tmp_bone)
                
                # Append to skeleton
                skel.appendChild(tmp_bone)
        else:
            for child in parent.children:
                name = child.getName() + '_Copy'
                i = 0
                while name in bone_list:
                    name = name.rstrip('0123456789')
                    name += str(i)
                    i += 1
                length = child.getLength()
                pose = child.getPoseOrientation()
                pos = child.getOffset()
                
                tmp_bone = Bone(name, length, pos, pose)
                bone_list[name] = tmp_bone
                canvas.addMesh(tmp_bone)
                
                # Update ambient color
                tmp_bone.setAmbientColor()
                
                self.call_lock.acquire()
                
                tmp_bone.setSkeletonOrient(self.pose_orientation)
                
                if child == self.hip_bone:
                    skel.setHipBone(tmp_bone)
                elif child == self.chest_bone:
                    skel.setChestBone(tmp_bone)
                elif child == self.neck_bone:
                    skel.setNeckBone(tmp_bone)
                elif child == self.head_bone:
                    skel.setHeadBone(tmp_bone)
                elif child == self.shoulder_bone_l:
                    skel.setShoulderBoneLeft(tmp_bone)
                elif child == self.up_arm_bone_l:
                    skel.setUpperArmBoneLeft(tmp_bone)
                elif child == self.low_arm_bone_l:
                    skel.setLowerArmBoneLeft(tmp_bone)
                elif child == self.hand_bone_l:
                    skel.setHandBoneLeft(tmp_bone)
                elif child == self.shoulder_bone_r:
                    skel.setShoulderBoneRight(tmp_bone)
                elif child == self.up_arm_bone_r:
                    skel.setUpperArmBoneRight(tmp_bone)
                elif child == self.low_arm_bone_r:
                    skel.setLowerArmBoneRight(tmp_bone)
                elif child == self.hand_bone_r:
                    skel.setHandBoneRight(tmp_bone)
                elif child == self.up_leg_bone_l:
                    skel.setUpperLegBoneLeft(tmp_bone)
                elif child == self.low_leg_bone_l:
                    skel.setLowerLegBoneLeft(tmp_bone)
                elif child == self.foot_bone_l:
                    skel.setFootBoneLeft(tmp_bone)
                elif child == self.up_leg_bone_r:
                    skel.setUpperLegBoneRight(tmp_bone)
                elif child == self.low_leg_bone_r:
                    skel.setLowerLegBoneRight(tmp_bone)
                elif child == self.foot_bone_r:
                    skel.setFootBoneRight(tmp_bone)
                
                self.call_lock.release()
                
                self.buildSkeletonCopy(skel, bone_list, canvas, child, tmp_bone)
                
                # Append to parent
                parent_copy.appendChild(tmp_bone)
    
    def delete(self, canvas, bone_list):
        for child in reversed(self.children):
            child.delete(canvas, bone_list)
        canvas.delMesh(self.mesh)
        del self
    
    def getChestBone(self):
        self.call_lock.acquire()
        tmp_bone = self.chest_bone
        self.call_lock.release()
        return tmp_bone
    
    def getFootBoneLeft(self):
        self.call_lock.acquire()
        tmp_bone = self.foot_bone_l
        self.call_lock.release()
        return tmp_bone
    
    def getFootBoneRight(self):
        self.call_lock.acquire()
        tmp_bone = self.foot_bone_r
        self.call_lock.release()
        return tmp_bone
    
    def getFootPosLeft(self):
        self.call_lock.acquire()
        tmp_foot_pos = self.foot_pos_l
        self.call_lock.release()
        return tmp_foot_pos
    
    def getFootPosRight(self):
        self.call_lock.acquire()
        tmp_foot_pos = self.foot_pos_r
        self.call_lock.release()
        return tmp_foot_pos
    
    def getHandBoneLeft(self):
        self.call_lock.acquire()
        tmp_bone = self.hand_bone_l
        self.call_lock.release()
        return tmp_bone
    
    def getHandBoneRight(self):
        self.call_lock.acquire()
        tmp_bone = self.hand_bone_r
        self.call_lock.release()
        return tmp_bone
    
    def getHeadBone(self):
        self.call_lock.acquire()
        tmp_bone = self.head_bone
        self.call_lock.release()
        return tmp_bone
    
    def getHipBone(self):
        self.call_lock.acquire()
        tmp_bone = self.hip_bone
        self.call_lock.release()
        return tmp_bone
    
    def getLowerArmBoneLeft(self):
        self.call_lock.acquire()
        tmp_bone = self.low_arm_bone_l
        self.call_lock.release()
        return tmp_bone
    
    def getLowerArmBoneRight(self):
        self.call_lock.acquire()
        tmp_bone = self.low_arm_bone_r
        self.call_lock.release()
        return tmp_bone
    
    def getLowerLegBoneLeft(self):
        self.call_lock.acquire()
        tmp_bone = self.low_leg_bone_l
        self.call_lock.release()
        return tmp_bone
    
    def getLowerLegBoneRight(self):
        self.call_lock.acquire()
        tmp_bone = self.low_leg_bone_r
        self.call_lock.release()
        return tmp_bone
    
    def getName(self):
        self.call_lock.acquire()
        tmp_name = self.name
        self.call_lock.release()
        return tmp_name
    
    def getNeckBone(self):
        self.call_lock.acquire()
        tmp_bone = self.neck_bone
        self.call_lock.release()
        return tmp_bone
    
    def getPoseOrientation(self):
        self.call_lock.acquire()
        tmp_orient = self.pose_orientation
        self.call_lock.release()
        return tmp_orient
    
    def getPosition(self):
        self.call_lock.acquire()
        tmp_pos = self.position
        self.call_lock.release()
        return tmp_pos
    
    def getShoulderBoneLeft(self):
        self.call_lock.acquire()
        tmp_bone = self.shoulder_bone_l
        self.call_lock.release()
        return tmp_bone
    
    def getShoulderBoneRight(self):
        self.call_lock.acquire()
        tmp_bone = self.shoulder_bone_r
        self.call_lock.release()
        return tmp_bone
    
    def getSkeletonBoneList(self):
        bone_list = []
        for child in self.children:
            bone_list.append(child.getName())
            bone_list += child.returnChildren()
        return bone_list
    
    def getUpperArmBoneLeft(self):
        self.call_lock.acquire()
        tmp_bone = self.up_arm_bone_l
        self.call_lock.release()
        return tmp_bone
    
    def getUpperArmBoneRight(self):
        self.call_lock.acquire()
        tmp_bone = self.up_arm_bone_r
        self.call_lock.release()
        return tmp_bone
    
    def getUpperLegBoneLeft(self):
        self.call_lock.acquire()
        tmp_bone = self.up_leg_bone_l
        self.call_lock.release()
        return tmp_bone
    
    def getUpperLegBoneRight(self):
        self.call_lock.acquire()
        tmp_bone = self.up_leg_bone_r
        self.call_lock.release()
        return tmp_bone
    
    def lowestPointOffest(self):
        self.call_lock.acquire()
        if self.hip_bone is not None:
            self.lowest_point = self.hip_bone.findLowestPoint(self.lowest_point)
            self.hip_bone.translate(Vector3([0, -self.lowest_point, 0]))
        else:
            for child in self.children:
                self.lowest_point = child.findLowestPoint(self.lowest_point)
                child.translate(Vector3([0, -self.lowest_point, 0]))
        
        # Check foot bones
        if self.foot_bone_l is not None:
            self.foot_bone_l.call_lock.acquire()
            bone_pos = self.foot_bone_l.position
            self.foot_bone_l.call_lock.release()
            
            if bone_pos.y >= (self.lowest_point - self.foot_epsilon) and bone_pos.y <= (self.lowest_point + self.foot_epsilon):
                if not self.foot_down_l:
                    self.foot_pos_l = bone_pos.copy()
                self.foot_down_l = True
            else:
                self.foot_down_l = False
        
        if self.foot_bone_r is not None:
            self.foot_bone_r.call_lock.acquire()
            bone_pos = self.foot_bone_r.position
            self.foot_bone_r.call_lock.release()
            
            if bone_pos.y >= (self.lowest_point - self.foot_epsilon) and bone_pos.y <= (self.lowest_point + self.foot_epsilon):
                if not self.foot_down_r:
                    self.foot_pos_r = bone_pos.copy()
                self.foot_down_r = True
            else:
                self.foot_down_r = False
        self.call_lock.release()
    
    def pedTrack(self):
        if '-nl' in sys.argv:
            return
        self.call_lock.acquire()
        pos = Vector3()
        if not self.foot_down_l:
            self.foot_bone_r.call_lock.acquire()
            pos = self.foot_pos_r - self.foot_bone_r.position
            pos.y = 0.0
            self.foot_bone_r.call_lock.release()
        
        if not self.foot_down_r:
            self.foot_bone_l.call_lock.acquire()
            pos = self.foot_pos_l - self.foot_bone_l.position
            pos.y = 0.0
            self.foot_bone_l.call_lock.release()
        
        self.hip_bone.translate(pos)
        self.call_lock.release()
    
    def resetLowestPoint(self):
        self.call_lock.acquire()
        self.lowest_point = float('inf')
        self.call_lock.release()
    
    def resetPedTracking(self):
        self.resetLowestPoint()
        self.call_lock.acquire()
        hip_offset = self.position.copy()
        hip_offset.y = self.hip_bone.getOffset().y
        self.hip_bone.setOffset(hip_offset)
        self.foot_down_l = True
        self.foot_down_r = True
        self.call_lock.release()
        self.update()
        self.call_lock.acquire()
        self.foot_pos_l = self.foot_bone_l.getPosition()
        self.foot_pos_r = self.foot_bone_r.getPosition()
        self.call_lock.release()
    
    def resetToPoseOrientation(self):
        for child in self.children:
            child.call_lock.acquire()
            child.orientation = Matrix4()
            child.call_lock.release()
    
    def setAmbientColor(self, color=None):
        if color is None:
            self.mesh.mat_col_amb = (0.2, 0.2, 0.2, 1.0)
        else:
            self.mesh.mat_col_amb = color
        for child in self.children:
            child.performFunction('setAmbientColor', [color])
    
    def setChestBone(self, bone):
        self.call_lock.acquire()
        self.chest_bone = bone
        self.call_lock.release()
    
    def setFootBoneLeft(self, bone):
        self.call_lock.acquire()
        self.foot_bone_l = bone
        self.call_lock.release()
    
    def setFootBoneRight(self, bone):
        self.call_lock.acquire()
        self.foot_bone_r = bone
        self.call_lock.release()
    
    def setFootPosLeft(self, pos):
        self.call_lock.acquire()
        self.foot_pos_l = pos.copy()
        self.call_lock.release()
    
    def setFootPosRight(self, pos):
        self.call_lock.acquire()
        self.foot_pos_r = pos.copy()
        self.call_lock.release()
    
    def setHandBoneLeft(self, bone):
        self.call_lock.acquire()
        self.hand_bone_l = bone
        self.call_lock.release()
    
    def setHandBoneRight(self, bone):
        self.call_lock.acquire()
        self.hand_bone_r = bone
        self.call_lock.release()
    
    def setHeadBone(self, bone):
        self.call_lock.acquire()
        self.head_bone = bone
        self.call_lock.release()
    
    def setHipBone(self, bone):
        self.call_lock.acquire()
        self.hip_bone = bone
        self.call_lock.release()
    
    def setLowerArmBoneLeft(self, bone):
        self.call_lock.acquire()
        self.low_arm_bone_l = bone
        self.call_lock.release()
    
    def setLowerArmBoneRight(self, bone):
        self.call_lock.acquire()
        self.low_arm_bone_r = bone
        self.call_lock.release()
    
    def setLowerLegBoneLeft(self, bone):
        self.call_lock.acquire()
        self.low_leg_bone_l = bone
        self.call_lock.release()
    
    def setLowerLegBoneRight(self, bone):
        self.call_lock.acquire()
        self.low_leg_bone_r = bone
        self.call_lock.release()
    
    def setName(self, name):
        self.call_lock.acquire()
        self.name = name
        self.call_lock.release()
    
    def setNeckBone(self, bone):
        self.call_lock.acquire()
        self.neck_bone = bone
        self.call_lock.release()
    
    def setPoseOrientation(self, orient):
        if orient is None:
            return
        self.call_lock.acquire()
        self.pose_orientation = orient.copy()
        self.call_lock.release()
        for child in self.children:
            child.performFunction('setSkeletonOrient', [orient])
    
    def setPosition(self, pos):
        if pos is None:
            return
        self.call_lock.acquire()
        self.position = pos.copy()
        self.call_lock.release()
    
    def setShoulderBoneLeft(self, bone):
        self.call_lock.acquire()
        self.shoulder_bone_l = bone
        self.call_lock.release()
    
    def setShoulderBoneRight(self, bone):
        self.call_lock.acquire()
        self.shoulder_bone_r = bone
        self.call_lock.release()
    
    def setSkeletonBone(self, bone):
        bone_name_lower = bone.getName().lower()
        if bone_name_lower in HIP_LIST:
            self.setHipBone(bone)
        elif bone_name_lower in CHEST_LIST:
            self.setChestBone(bone)
        elif bone_name_lower in NECK_LIST:
            self.setNeckBone(bone)
        elif bone_name_lower in HEAD_LIST:
            self.setHeadBone(bone)
        elif bone_name_lower in LEFT_SHOULDER_LIST:
            self.setShoulderBoneLeft(bone)
        elif bone_name_lower in LEFT_UP_ARM_LIST:
            self.setUpperArmBoneLeft(bone)
        elif bone_name_lower in LEFT_LOW_ARM_LIST:
            self.setLowerArmBoneLeft(bone)
        elif bone_name_lower in LEFT_HAND_LIST:
            self.setHandBoneLeft(bone)
        elif bone_name_lower in RIGHT_SHOULDER_LIST:
            self.setShoulderBoneRight(bone)
        elif bone_name_lower in RIGHT_UP_ARM_LIST:
            self.setUpperArmBoneRight(bone)
        elif bone_name_lower in RIGHT_LOW_ARM_LIST:
            self.setLowerArmBoneRight(bone)
        elif bone_name_lower in RIGHT_HAND_LIST:
            self.setHandBoneRight(bone)
        elif bone_name_lower in LEFT_UP_LEG_LIST:
            self.setUpperLegBoneLeft(bone)
        elif bone_name_lower in LEFT_LOW_LEG_LIST:
            self.setLowerLegBoneLeft(bone)
        elif bone_name_lower in LEFT_FOOT_LIST:
            self.setFootBoneLeft(bone)
        elif bone_name_lower in RIGHT_UP_LEG_LIST:
            self.setUpperLegBoneRight(bone)
        elif bone_name_lower in RIGHT_LOW_LEG_LIST:
            self.setLowerLegBoneRight(bone)
        elif bone_name_lower in RIGHT_FOOT_LIST:
            self.setFootBoneRight(bone)
    
    def setUpperArmBoneLeft(self, bone):
        self.call_lock.acquire()
        self.up_arm_bone_l = bone
        self.call_lock.release()
    
    def setUpperArmBoneRight(self, bone):
        self.call_lock.acquire()
        self.up_arm_bone_r = bone
        self.call_lock.release()
    
    def setUpperLegBoneLeft(self, bone):
        self.call_lock.acquire()
        self.up_leg_bone_l = bone
        self.call_lock.release()
    
    def setUpperLegBoneRight(self, bone):
        self.call_lock.acquire()
        self.up_leg_bone_r = bone
        self.call_lock.release()
    
    def update(self, streaming=False, frame_data=None):
        """ Updates the object and its children.
            
            Args:
                streaming: A boolean that indicates if the Mocap Studio is
                    streaming data (default is False)
                frame_data: A map that holds frame data for the bones of the
                    Skeleton (default is None)
        """
        self.call_lock.acquire()
        # Update Skeleton Mesh's position
        self.mesh.position = self.position.asArray()
        
        # Update bones
        for child in self.children:
            child.update(streaming, frame_data)
        self.call_lock.release()
        if '-nl' in sys.argv:
            return
        if streaming and frame_data is None:
            self.lowestPointOffest()
    
    def updateRecord(self, session, cur_frame):
        """ Updates the object and its children for recording.
            
            Args:
                session: A RecordSession instance.
                cur_frame: An integer denoting the current frame.
        """
        self.resetLowestPoint()
        self.call_lock.acquire()
        for child in self.children:
            child.updateRecord(session, cur_frame)
        if cur_frame == 0:
            if self.foot_bone_l:
                self.foot_pos_l = self.foot_bone_l.getPosition()
            if self.foot_bone_r:
                self.foot_pos_r = self.foot_bone_r.getPosition()
        self.call_lock.release()
        self.lowestPointOffest()
        if session.is_ped_track:
            self.pedTrack()


class Bone(SkelNode):
    
    """ A SkelNode that is used to create a bone for a skeleton.
        
        Attributes:
            call_lock: An instance of threading Lock.
            length: A float that denotes the length of the object.
            mesh: An instance of BoneMeshNode.
            mesh_ambient: A tuple denoting the ambient color of the
                BoneMeshNode.
            name: A string denoting the name of the Bone.
            offset: An instance of Vector3 denoting the offset from parent's
                position.
            orientation: An instance of Matrix4 denoting the current
                orientation.
            pose_orientation: An instance of Matrix4 denoting the initial
                orientation.
            position: An instance of Vector3 denoting the absoulte position.
            vs_node: An instance of VirtualSensorNode.
    """
    
    NO_VS_NODE = (0.0, 0.0, 0.6, 1.0)
    VS_NODE = (0.2, 0.2, 0.2, 1.0)
    __slots__ = (
        'call_lock',
        'length',
        'mesh',
        'mesh_ambient',
        'name',
        'offset',
        'orientation',
        'pose_orientation',
        'position',
        'skel_orient',
        'vs_node'
    )
    
    def __init__(self, name, length=5, pos=None, p_orient=None, vs_node=None):
        """ Initializes the Bone class.
            
            Args:
                name: A string denoting a name for the object.
                length: A float that denotes the length of the object
                    (default is 5)
                pos: An instance of Vector3 denoting the absoulte position
                    (default is None)
                p_orient: An instance of Matrix4 denoting the initial
                    orientation (default is None)
                vs_node: An instance of VirtualSensorNode (default is None)
        """
        SkelNode.__init__(self)
        self.call_lock = threading.Lock()
        self.length = length
        self.mesh = None
        if vs_node is None:
            self.mesh_ambient = Bone.NO_VS_NODE
        else:
            self.mesh_ambient = Bone.VS_NODE
        self.name = name
        if pos is not None:
            self.offset = Vector3(pos.asArray())
        else:
            self.offset = Vector3()
        self.orientation = Matrix4()
        if p_orient is not None:
            self.pose_orientation = p_orient
        else:
            self.pose_orientation = Matrix4()
        self.position = self.offset.copy()
        self.skel_orient = Matrix4()
        self.vs_node = vs_node
    
    def __repr__(self):
        return "Bone name: " + self.name
    
    def __str__(self):
        return self.__repr__()
    
    def addVSNode(self, vs_node):
        if vs_node is not None:
            self.vs_node = vs_node
            self.mesh_ambient = Bone.VS_NODE
    
    def delete(self, canvas, bone_list):
        for child in reversed(self.children):
            child.delete(canvas, bone_list)
        canvas.delMesh(self.mesh)
        self.delVSNode()
        del bone_list[self.name]
        del self
    
    def delVSNode(self):
        self.vs_node = None
        self.setOrientation(Matrix4())
        self.mesh_ambient = Bone.NO_VS_NODE
    
    def findLowestPoint(self, lowest_point):
        # Update My Position
        self.call_lock.acquire()
        if type(self.parent) is Bone:
            self.position = self.parent.position + (self.parent.orientation * self.offset)
        
        if self.position.y < lowest_point:
            lowest_point = self.position.y
        
        # # Get My Tail Position
        # orient = self.orientation
        # tail_len = Vector3([0, self.length, 0])
        # tail_pos = bone_pos + (orient * tail_len)
        
        # if tail_pos.y < lowest_point:
            # lowest_point = tail_pos.y
        
        for child in self.children:
            lowest_point = child.findLowestPoint(lowest_point)
        self.call_lock.release()
        return lowest_point
    
    def getAmbientColor(self):
        return self.mesh.mat_col_amb[:]
    
    def getLength(self):
        self.call_lock.acquire()
        tmp_len = self.length
        self.call_lock.release()
        return tmp_len
    
    def getName(self):
        self.call_lock.acquire()
        tmp_name = self.name
        self.call_lock.release()
        return tmp_name
    
    def getOffset(self):
        self.call_lock.acquire()
        tmp_pos = self.offset.copy()
        self.call_lock.release()
        return tmp_pos
    
    def getOrientation(self):
        self.call_lock.acquire()
        tmp_orient = self.orientation.copy()
        self.call_lock.release()
        return tmp_orient
    
    def getPoseOrientation(self):
        self.call_lock.acquire()
        tmp_orient = self.pose_orientation.copy()
        self.call_lock.release()
        return tmp_orient
    
    def getPosition(self):
        self.call_lock.acquire()
        tmp_pos = self.position.copy()
        self.call_lock.release()
        return tmp_pos
    
    def returnChildren(self):
        child_list = []
        for child in self.children:
            child_list.append(child.getName())
            child_list += child.returnChildren()
        return child_list
    
    def setAmbientColor(self, color=None):
        if color is None:
            self.mesh.mat_col_amb = self.mesh_ambient[:]
        else:
            self.mesh.mat_col_amb = color[:]
    
    def setLength(self, length):
        self.call_lock.acquire()
        self.length = length
        self.mesh.length = length
        self.call_lock.release()
    
    def setName(self, name):
        self.call_lock.acquire()
        self.name = name
        self.call_lock.release()
    
    def setOffset(self, pos):
        if pos is None:
            return
        self.call_lock.acquire()
        self.offset = pos.copy()
        self.call_lock.release()
    
    def setOrientation(self, orient):
        if orient is None:
            return
        self.call_lock.acquire()
        self.orientation = orient.copy()
        self.call_lock.release()
    
    def setPoseOrientation(self, pose_orient):
        if pose_orient is None:
            return
        self.call_lock.acquire()
        self.pose_orientation = pose_orient.copy()
        self.call_lock.release()
    
    def setPosition(self, pos):
        if pos is None:
            return
        self.call_lock.acquire()
        self.position = pos.copy()
        self.call_lock.release()
    
    def setSkeletonOrient(self, orient):
        if orient is None:
            return
        self.call_lock.acquire()
        self.skel_orient = orient.copy()
        self.call_lock.release()
    
    def translate(self, vector):
        self.call_lock.acquire()
        self.offset += vector
        # Set My Position
        if type(self.parent) is Bone:
            self.position = self.parent.position + (self.parent.orientation * self.skel_orient * self.offset)
        elif type(self.parent) is Skeleton:
            self.position = self.parent.position + (self.skel_orient * self.offset)
        else:
            self.position = self.skel_orient * self.offset
        self.call_lock.release()
    
    def update(self, streaming=False, frame_data=None):
        """ Updates the object and its children.
            
            Args:
                streaming: A boolean that indicates if the Mocap Studio is
                    streaming data (default is False)
                frame_data: A map that holds frame data for the bones of the
                    Skeleton (default is None)
        """
        self.call_lock.acquire()
        # Update own variables
        if self.vs_node is not None and streaming:
            # Update orientation based on virtal sensor data
            data = self.vs_node.input_ports[0].data
            data_type = self.vs_node.input_ports[0].data_type
            if data is not None:
                if data_type != 'Q':
                    data = data.toQuaternion()
                
                tared_orient = data.copy()
                
                self.orientation = tared_orient.toMatrix4()
            else:
                # print 'No orientation!'
                pass
        
        elif frame_data is not None:
            frame = frame_data[self.name]
            self.orientation = frame[0].toMatrix4()
            if type(self.parent) is not Bone:
                self.position = frame[1]
        
        self._updatePosition(frame_data)
        
        # Update Mesh
        # Update Bone Mesh's orientation/position
        self._updateMesh()
        
        for child in self.children:
            child.update(streaming, frame_data)
        self.call_lock.release()
    
    def _updateMesh(self):
        # Update Bone Mesh's orientation/position
        self.mesh.orientation = (self.orientation * self.skel_orient * self.pose_orientation).asColArray()
        self.mesh.position = self.position.asArray()
        
        if DRAW_CHILDREN:
            if type(self.parent) is Bone:
                tmp_vec = self.position - self.parent.position
                tmp_len = tmp_vec.length()
                # Compute average direction vector
                x_vec = Vector3(UNIT_X)
                y_vec = tmp_vec.normalizeCopy()
                z_vec = Vector3(UNIT_Z)
                # Compute orthogonal vectors
                if abs(y_vec._vec_array[0]) > abs(y_vec._vec_array[2]):
                    x_vec = y_vec.cross(z_vec).normalizeCopy()
                    z_vec = x_vec.cross(y_vec).normalizeCopy()
                else:
                    z_vec = x_vec.cross(y_vec).normalizeCopy()
                    x_vec = y_vec.cross(z_vec).normalizeCopy()
                # Build matrix
                x1, x2, x3 = x_vec.asArray()
                y1, y2, y3 = y_vec.asArray()
                z1, z2, z3 = z_vec.asArray()
                tmp_mat = [
                    x1, x2, x3, 0.0,
                    y1, y2, y3, 0.0,
                    z1, z2, z3, 0.0,
                    0.0, 0.0, 0.0, 1.0
                ]
                par_pos = self.parent.position.asArray()
                if len(self.mesh.children) > 0:
                    for child in self.mesh.children:
                        child.height = tmp_len
                        child.position = par_pos
                        child.orientation = tmp_mat
                else:
                    self.mesh.appendChild(gl_sg.GluCylinderNode(0.1, tmp_len, 8, 8, par_pos, tmp_mat))
    
    def _updatePosition(self, frame_data=None):
        # Update Position
        if type(self.parent) is Bone:
            self.position = self.parent.position + (self.parent.orientation * self.skel_orient * self.offset)
        elif type(self.parent) is Skeleton and frame_data is None:
            self.position = self.parent.position + (self.skel_orient * self.offset)
        elif frame_data is None:
            self.position = self.skel_orient * self.offset
    
    def updateRecord(self, session, cur_frame):
        """ Updates the object and its children for recording.
            
            Args:
                session: A RecordSession instance.
                cur_frame: An integer denoting the current frame.
        """
        self.call_lock.acquire()
        
        keyframe = session.getKeyframe(self.name, cur_frame)
        tmp_orient = keyframe.start_frame_data[0].toMatrix4()
        
        # Update Orientation
        self.orientation = tmp_orient
        
        # Update Position
        if cur_frame > 0:
            self._updatePosition()
            prev_keyframe = session.getKeyframe(self.name, cur_frame - 1)
            prev_keyframe.end_frame_data.append(self.position)
        else:
            self.offset = session.recorded_bone_list[self.name].offset.copy()
            self._updatePosition()
        
        keyframe.start_frame_data.append(self.position)
        
        for child in self.children:
            child.updateRecord(session, cur_frame)
        self.call_lock.release()


### Helper Functions ###
def findRoot(selected_list):
    """ Finds the most top level Bone object in a given list.
        
        Args:
            selected_list: A list of references to Bone objects.
        
        Returns:
            A reference to the top level Bone object.
    """
    bone = selected_list[0]
    par = bone.parent
    if par in selected_list:
        selected_list.remove(par)
        selected_list.insert(0, par)
        return findRoot(selected_list)
    return bone


def copyBone(bone, selected_list, name_list, parent=None):
    """ Makes copies of Bone objects in a given list.
        
        Args:
            bone: A reference to a Bone object. The current Bone the be copied.
            selected_list: A list of references to Bone objects.
            name_list: A list of strings of the names of the Bone objects being
                copied.
            parent: A reference to a Bone object (default is None)
        
        Returns:
            A list of the copied Bone objects.
    """
    tmp_list = []
    count = 0
    
    # Get the name and pose of the bone being copied
    bone.setAmbientColor()
    name = bone.getName() + "_Copy"
    pose_orient = bone.getPoseOrientation()
    length = bone.getLength()
    offset = bone.getOffset()
    
    i = 0
    while name in name_list:
        name = name.rstrip('0123456789')
        name += str(i)
        i += 1
    
    copy = Bone(name, length, offset, pose_orient)
    if parent is not None:
        parent.appendChild(copy)
    tmp_list.append(copy)
    selected_list.remove(bone)
    for child in bone.children:
        if child in selected_list:
            tmp_list += copyBone(child, selected_list, name_list, copy)
    return tmp_list


def calculateJointVaule(par_bone, child_bone, joint):
    orient0 = par_bone.vs_node.input_ports[0].data
    timestamp0 = par_bone.vs_node.input_ports[0].timestamp
    
    orient1 = child_bone.vs_node.input_ports[0].data
    timestamp1 = child_bone.vs_node.input_ports[0].timestamp
    
    if timestamp0 == -1:
        timestamp = timestamp1 / 1000000.0
    else:
        timestamp = timestamp0 / 1000000.0
    
    if joint < 11:
        forward0 = orient0 * Vector3(UNIT_Z)
        up0 = orient0 * Vector3(UNIT_Y)
        right0 = orient0 * Vector3(UNIT_X)
        
        forward1 = orient1 * Vector3(UNIT_Z)
        up1 = orient1 * Vector3(UNIT_Y)
        right1 = orient1 * Vector3(UNIT_X)
        
        ## Project child's forward and up vectors to the parent's right plane
        projected_up1 = up1 - right0 * (up1.dot(right0))
        projected_up1.normalize()
        projected_forward1 = forward1 - right0 * (forward1.dot(right0))
        projected_forward1.normalize()
        
        ## Calculate a vector perpendicular to the projected up and forward vectors and the up and forward vectors of the parent
        up_cross_axis = projected_up1.cross(up0)
        up_cross_axis.normalize()
        forward_cross_axis = projected_forward1.cross(forward0)
        forward_cross_axis.normalize()
        
        axis = None
        x_axis_rot = 0
        up_cross_dot = up_cross_axis.dot(right0)
        forward_cross_dot = forward_cross_axis.dot(right0)
        if((up_cross_dot < 1.1 and up_cross_dot > 0.9) or (up_cross_dot > -1.1 and up_cross_dot < -0.9)):
            x_axis_rot = math.acos(max(min(projected_up1.dot(up0), 1.0), -1.0))
            axis = up_cross_axis
        else: #if((forward_cross_dot < 1.1 and forward_cross_dot > 0.9) or (forward_cross_dot > -1.1 and forward_cross_dot < -0.9)):
            x_axis_rot = math.acos(max(min(projected_forward1.dot(forward0), 1.0), -1.0))
            axis = forward_cross_axis
        
        ## Set the sign of x_axis_rot using the axis calculated and the right vector of the parent
        x_axis_rot = math.copysign(x_axis_rot, axis.dot(right0))
        
        ## Project child's forward and right vectors to the parent's up plane
        projected_forward1 = forward1 - up0 * (forward1.dot(up0))
        projected_forward1.normalize()
        projected_right1 = right1 - up0 * (right1.dot(up0))
        projected_right1.normalize()
        
        ## Calculate a vector perpendicular to the projected forward and right vectors and the forward and right vectors of the parent
        forward_cross_axis = projected_forward1.cross(forward0)
        forward_cross_axis.normalize()
        right_cross_axis = projected_right1.cross(right0)
        right_cross_axis.normalize()
        
        axis = None
        y_axis_rot = 0
        forward_cross_dot = forward_cross_axis.dot(up0)
        right_cross_dot = right_cross_axis.dot(up0)
        if((forward_cross_dot < 1.1 and forward_cross_dot > 0.9) or (forward_cross_dot > -1.1 and forward_cross_dot < -0.9)):
            y_axis_rot = math.acos(max(min(projected_forward1.dot(forward0), 1.0), -1.0))
            axis = forward_cross_axis
        else: #if((right_cross_dot < 1.1 and right_cross_dot > 0.9) or (right_cross_dot > -1.1 and right_cross_dot < -0.9)):
            y_axis_rot = math.acos(max(min(projected_right1.dot(right0), 1.0), -1.0))
            axis = right_cross_axis
        
        ## Set the sign of y_angle using the axis calculated and the up vector of the parent
        y_axis_rot = math.copysign(y_axis_rot, axis.dot(up0))
        
        ## Project child's up and right vectors to the parent's forward plane
        projected_right1 = right1 - forward0 * (right1.dot(forward0))
        projected_right1.normalize()
        projected_up1 = up1 - forward0 * (up1.dot(forward0))
        projected_up1.normalize()
        
        ## Calculate a vector perpendicular to the projected right and up vectors and the right and up vectors of the parent
        right_cross_axis = projected_right1.cross(right0)
        right_cross_axis.normalize()
        up_cross_axis = projected_up1.cross(up0)
        up_cross_axis.normalize()
        
        axis = None
        z_axis_rot = 0
        right_cross_dot = right_cross_axis.dot(forward0)
        up_cross_dot = up_cross_axis.dot(forward0)
        if((right_cross_dot < 1.1 and right_cross_dot > 0.9) or (right_cross_dot > -1.1 and right_cross_dot < -0.9)):
            z_axis_rot = math.acos(max(min(projected_right1.dot(right0), 1.0), -1.0))
            axis = right_cross_axis
        else: #if((up_cross_dot < 1.1 and up_cross_dot > 0.9) or (up_cross_dot > -1.1 and up_cross_dot < -0.9)):
            z_axis_rot = math.acos(max(min(projected_up1.dot(up0), 1.0), -1.0))
            axis = up_cross_axis
        
        ## Set the sign of z_angle using the axis calculated and the forward vector of the parent
        z_axis_rot = math.copysign(z_axis_rot, axis.dot(forward0))
        
        return (timestamp, (math.degrees(x_axis_rot), math.degrees(y_axis_rot), math.degrees(z_axis_rot)))
    
    else:
        orientation_offest =  -orient0 * orient1
        if joint == 11:
            return (timestamp, orientation_offest)
        else:
            return (timestamp, orientation_offest.toMatrix3())

