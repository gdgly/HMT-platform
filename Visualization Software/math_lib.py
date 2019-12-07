#!/usr/bin/env python2.7

""" A linear algebra math library.

    This is a math library that can convert between multiple different
    orientation methods and perform simple math opperations and conversions
    between them.
"""


import math
import random
import time


### Static Globals ###
UNIT_X = [1, 0, 0]
UNIT_Y = [0, 1, 0]
UNIT_Z = [0, 0, 1]
NEG_UNIT_X = [-1, 0, 0]
NEG_UNIT_Y = [0, -1, 0]
NEG_UNIT_Z = [0, 0, -1]
MATRIX3_IDENTITY = [
    1.0, 0.0, 0.0,
    0.0, 1.0, 0.0,
    0.0, 0.0, 1.0
]
MATRIX3_90_X = [
    1, 0, 0,
    0, 0, -1,
    0, 1, 0
]
MATRIX3_90_Y = [
    0, 0, 1,
    0, 1, 0,
    -1, 0, 0
]
MATRIX3_90_Z = [
    0, -1, 0,
    1, 0, 0,
    0, 0, 1
]
MATRIX3_NEG_90_X = [
    1, 0, 0,
    0, 0, 1,
    0, -1, 0
]
MATRIX3_NEG_90_Y = [
    0, 0, -1,
    0, 1, 0,
    1, 0, 0
]
MATRIX3_NEG_90_Z = [
    0, 1, 0,
    -1, 0, 0,
    0, 0, 1
]
MATRIX3_180_X = [
    1, 0, 0,
    0, -1, 0,
    0, 0, -1
]
MATRIX3_180_Y = [
    -1, 0, 0,
    0, 1, 0,
    0, 0, -1
]
MATRIX3_180_Z = [
    -1, 0, 0,
    0, -1, 0,
    0, 0, 1
]
MATRIX4_IDENTITY = [
    1.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 1.0
]
MATRIX4_90_X = [
    1, 0, 0, 0,
    0, 0, -1, 0,
    0, 1, 0, 0,
    0, 0, 0, 1
]
MATRIX4_90_Y = [
    0, 0, 1, 0,
    0, 1, 0, 0,
    -1, 0, 0, 0,
    0, 0, 0, 1
]
MATRIX4_90_Z = [
    0, -1, 0, 0,
    1, 0, 0, 0,
    0, 0, 1, 0,
    0, 0, 0, 1
]
MATRIX4_NEG_90_X = [
    1, 0, 0, 0,
    0, 0, 1, 0,
    0, -1, 0, 0,
    0, 0, 0, 1
]
MATRIX4_NEG_90_Y = [
    0, 0, -1, 0,
    0, 1, 0, 0,
    1, 0, 0, 0,
    0, 0, 0, 1
]
MATRIX4_NEG_90_Z = [
    0, 1, 0, 0,
    -1, 0, 0, 0,
    0, 0, 1, 0,
    0, 0, 0, 1
]
MATRIX4_180_X = [
    1, 0, 0, 0,
    0, -1, 0, 0,
    0, 0, -1, 0,
    0, 0, 0, 1
]
MATRIX4_180_Y = [
    -1, 0, 0, 0,
    0, 1, 0, 0,
    0, 0, -1, 0,
    0, 0, 0, 1
]
MATRIX4_180_Z = [
    -1, 0, 0, 0,
    0, -1, 0, 0,
    0, 0, 1, 0,
    0, 0, 0, 1
]

_MAT_TO_EULER_MAP = {}


### Classes ###
class Vector3(object):
    
    """ Vector3 object that opperates like most other Vector3 classes.
        
        A Vector3 can be a point or a direction depending on usage.
        
        Vector3s are [X, Y, Z].
        
        Attributes:
            _vec_array: A list of floats denoting a position in the world.
            x: A property instance that gets/sets its vaule from/to _vec_array.
            y: A property instance that gets/sets its vaule from/to _vec_array.
            z: A property instance that gets/sets its vaule from/to _vec_array.
    """
    
    __slots__ = ('_vec_array', 'x', 'y', 'z')
    
    def __init__(self, vals=[0.0, 0.0, 0.0]):
        """ Creates a Vector3 object.
            
            Args:
                vals: A list of floats [X, Y, Z] to init the Vector3.
        """
        if len(vals) != 3:
            raise AttributeError("VECTOR3: Passed in list does not have 3 values, it has %d" % len(vals))
        self._vec_array = [(v * 1.0) for v in vals]
        self.x = self._vec_array[0]
        self.y = self._vec_array[1]
        self.z = self._vec_array[2]
    
    def __repr__(self):
        return "[%0.4f, %0.4f, %0.4f]" % tuple(self._vec_array)
    
    def __str__(self):
        return self.__repr__()
    
    def __add__(self, other):
        if type(other) is Vector3:
            x0, y0, z0 = self._vec_array
            x1, y1, z1 = other._vec_array
            return Vector3([x0 + x1, y0 + y1, z0 + z1])
        raise TypeError("VECTOR3: Can only add two Vector3s together")
    
    def __sub__(self, other):
        # Assumes self is on the left
        if type(other) is Vector3:
            x0, y0, z0 = self._vec_array
            x1, y1, z1 = other._vec_array
            return Vector3([x0 - x1, y0 - y1, z0 - z1])
        raise TypeError("VECTOR3: Can only subtract two Vector3s together")
    
    def __mul__(self, other):
        other_type = type(other)
        if other_type is int or other_type is float:
            x, y, z = self._vec_array
            return Vector3([x * other, y * other, z * other])
        elif other_type is Vector3:
            x0, y0, z0 = self._vec_array
            x1, y1, z1 = other._vec_array
            return Vector3([x0 * x1, y0 * y1, z0 * z1])
        raise TypeError("VECTOR3: Can only multiply with a scalar or Vector3")
    
    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __neg__(self):
        x, y, z = self._vec_array
        return Vector3([-x, -y, -z])
    
    def __getitem__(self, idx):
        return self._vec_array[idx]
    
    def __setitem__(self, idx, val):
        self._vec_array[idx] = val * 1.0
    
    def __eq__(self, other):
        if type(other) is Vector3:
            return self._vec_array == other._vec_array
        raise TypeError("VECTOR3: Can only compare with other Vector3s")
    
    def __getX(self):
        return self._vec_array[0]
    
    def __setX(self, val):
        self._vec_array[0] = val * 1.0
    
    def __getY(self):
        return self._vec_array[1]
    
    def __setY(self, val):
        self._vec_array[1] = val * 1.0
    
    def __getZ(self):
        return self._vec_array[2]
    
    def __setZ(self, val):
        self._vec_array[2] = val * 1.0
    
    def cross(self, other):
        # Assumes self is on the left
        if type(other) is Vector3:
            x0, y0, z0 = self._vec_array
            x1, y1, z1 = other._vec_array
            return Vector3([
                y0 * z1 - z0 * y1,
                z0 * x1 - x0 * z1,
                x0 * y1 - y0 * x1
            ])
        raise TypeError("VECTOR3: Can only cross two Vector3s")
    
    def dot(self, other):
        # Assumes self is on the left
        if type(other) is Vector3:
            x0, y0, z0 = self._vec_array
            x1, y1, z1 = other._vec_array
            return x0 * x1 + y0 * y1 + z0 * z1
        raise TypeError("VECTOR3: Can only dot two Vector3s")
    
    def copy(self):
        return Vector3(self._vec_array)
    
    def normalize(self):
        length = self.length()
        if length > 0:
            self._vec_array[0] /= length
            self._vec_array[1] /= length
            self._vec_array[2] /= length
    
    def normalizeCopy(self):
        tmp_vec = Vector3(self._vec_array)
        tmp_vec.normalize()
        return tmp_vec
    
    def length(self):
        return (self.dot(self)) ** 0.5
    
    def asArray(self):
        return self._vec_array[:]
    
    x = property(__getX, __setX, None, "x property")
    y = property(__getY, __setY, None, "y property")
    z = property(__getZ, __setZ, None, "z property")


class Quaternion(object):
    
    """ Quaternion object that opperates like most other Quaternion classes.
        
        A Quaternion can be used for orientation for a object in the world.
        
        Quaternions are [X, Y, Z, W].
        
        Attributes:
            _quat_array: A list of floats denoting a rotation in the world.
            x: A property instance that gets/sets its vaule from/to _quat_array.
            y: A property instance that gets/sets its vaule from/to _quat_array.
            z: A property instance that gets/sets its vaule from/to _quat_array.
            w: A property instance that gets/sets its vaule from/to _quat_array.
    """
    
    __slots__ = ('_quat_array', 'w', 'x', 'y', 'z')
    
    def __init__(self, vals=[0.0, 0.0, 0.0, 1.0]):
        """ Creates Quaternion object.
            
            Args:
                vals: A list of floats [X, Y, Z, W] to init the Quaternion.
        """
        if len(vals) != 4:
            raise AttributeError("QUATERNION: Passed in list does not have 4 values, it has %d" % len(vals))
        self._quat_array = [(v * 1.0) for v in vals]
        self.x = self._quat_array[0]
        self.y = self._quat_array[1]
        self.z = self._quat_array[2]
        self.w = self._quat_array[3]
    
    def __repr__(self):
        return "[%0.4f, %0.4f, %0.4f, %0.4f]" % tuple(self._quat_array)
    
    def __str__(self):
        return self.__repr__()
    
    def __add__(self, other):
        if type(other) is Quaternion:
            x0, y0, z0, w0 = self._quat_array
            x1, y1, z1, w1 = other._quat_array
            return Quaternion([x0 + x1, y0 + y1, z0 + z1, w0 + w1])
        raise TypeError("QUATERNION: Can only add two Quaternions together")
    
    def __sub__(self, other):
        if type(other) is Quaternion:
            x0, y0, z0, w0 = self._quat_array
            x1, y1, z1, w1 = other._quat_array
            return Quaternion([x0 - x1, y0 - y1, z0 - z1, w0 - w1])
        raise TypeError("QUATERNION: Can only subtract two Quaternions together")
    
    def __mul__(self, other):
        other_type = type(other)
        if other_type is float or other_type is int:
            x, y, z, w = self._quat_array
            return Quaternion([x * other, y * other, z * other, w * other])
        elif other_type is Quaternion:
            x0, y0, z0, w0 = self._quat_array
            x1, y1, z1, w1 = other._quat_array
            x_cross = y0 * z1 - z0 * y1
            y_cross = z0 * x1 - x0 * z1
            z_cross = x0 * y1 - y0 * x1
            dot = x0 * x1 + y0 * y1 + z0 * z1
            w_new = w0 * w1 - dot
            x_new = x1 * w0 + x0 * w1 + x_cross
            y_new = y1 * w0 + y0 * w1 + y_cross
            z_new = z1 * w0 + z0 * w1 + z_cross
            return Quaternion([x_new, y_new, z_new, w_new])
        elif other_type is Vector3:
            x0, y0, z0, w = self._quat_array
            scale = (1 - max(min(w * w, 1.0), -1.0)) ** 0.5
            if scale > 0:
                x0 /= scale
                y0 /= scale
                z0 /= scale
            w = max(min(w, 1.0), -1.0)
            ang = math.acos(w) * 2.0
            x1, y1, z1 = other._vec_array
            tmp_cos = math.cos(ang)
            tmp_sin = math.sin(ang)
            x_cross = y0 * z1 - z0 * y1
            y_cross = z0 * x1 - x0 * z1
            z_cross = x0 * y1 - y0 * x1
            dot = x0 * x1 + y0 * y1 + z0 * z1
            x_new = x1 * tmp_cos + x_cross * tmp_sin + x0 * dot * (1 - tmp_cos)
            y_new = y1 * tmp_cos + y_cross * tmp_sin + y0 * dot * (1 - tmp_cos)
            z_new = z1 * tmp_cos + z_cross * tmp_sin + z0 * dot * (1 - tmp_cos)
            return Vector3([x_new, y_new, z_new])
        raise TypeError("QUATERNION: Can only multiply with a scalar or Quaternion (or with a Vector3 on the right)")
    
    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __neg__(self):
        """Is the conjugate of a Quaternion or inverse if a unit Quaternion."""
        x, y, z, w = self._quat_array
        return Quaternion([-x, -y, -z, w])
    
    def __getitem__(self, idx):
        return self._quat_array[idx]
    
    def __setitem__(self, idx, val):
        self._quat_array[idx] = val * 1.0
    
    def __eq__(self, other):
        if type(other) is Quaternion:
            return self._quat_array == other._quat_array
        raise TypeError("QUATERNION: Can only compare with other Quaternions")
    
    def __getX(self):
        return self._quat_array[0]
    
    def __setX(self, val):
        self._quat_array[0] = val * 1.0
    
    def __getY(self):
        return self._quat_array[1]
    
    def __setY(self, val):
        self._quat_array[1] = val * 1.0
    
    def __getZ(self):
        return self._quat_array[2]
    
    def __setZ(self, val):
        self._quat_array[2] = val * 1.0
    
    def __getW(self):
        return self._quat_array[3]
    
    def __setW(self, val):
        self._quat_array[3] = val * 1.0
    
    def __vecCross(self, other):
        # Assumes self is on the left
        if type(other) is Quaternion:
            x0, y0, z0, w0 = self._quat_array
            x1, y1, z1, w1 = other._quat_array
            return [y0 * z1 - z0 * y1, z0 * x1 - x0 * z1, x0 * y1 - y0 * x1]
        raise TypeError("QUATERNION: Can only vector cross two Quaternions")
    
    def dot(self, other):
        # Assumes self is on the left
        if type(other) is Quaternion:
            x0, y0, z0, w0 = self._quat_array
            x1, y1, z1, w1 = other._quat_array
            return x0 * x1 + y0 * y1 + z0 * z1 + w0 * w1
        raise TypeError("QUATERNION: Can only dot two Quaternions")
    
    def __vecDot(self, other):
        # Assumes self is on the left
        if type(other) is Quaternion:
            x0, y0, z0, w0 = self._quat_array
            x1, y1, z1, w1 = other._quat_array
            return x0 * x1 + y0 * y1 + z0 * z1
        raise TypeError("QUATERNION: Can only vector dot two Quaternions")
    
    def copy(self):
        return Quaternion(self._quat_array)
    
    def normalize(self):
        length = self.length()
        if length > 0.0:
            self._quat_array[0] /= length
            self._quat_array[1] /= length
            self._quat_array[2] /= length
            self._quat_array[3] /= length
    
    def normalizeCopy(self):
        tmp_quat = Quaternion(self._quat_array)
        tmp_quat.normalize()
        return tmp_quat
    
    def length(self):
        return (self.dot(self)) ** 0.5
    
    def slerp(self, other, interval):
        if type(other) is Quaternion:
            if interval >= 0.0 and interval <= 1.0:
                quat0 = self.normalizeCopy()
                quat1 = other.normalizeCopy()
                theta = quat0.dot(quat1)
                if theta < 0.0:
                    quat0 = (-1.0) * quat0
                    theta = -theta
                if (1.0 - theta) > 0.0001:
                    theta = math.acos(theta)
                    sin_theta = math.sin(theta)
                    sin0 = math.sin((1.0 - interval) * theta) / sin_theta
                    sin1 = math.sin(interval * theta) / sin_theta
                else:
                    sin0 = 1.0 - interval
                    sin1 = interval
                new_quat = (sin0 * quat0) + (sin1 * quat1)
                return new_quat
            
            raise ValueError("QUATERNION: The interval must be between 0 and 1")
        raise TypeError("QUATERNION: Can only slerp between two Quaternions")
    
    def toMatrix3(self):
        # http://gpwiki.org/index.php/OpenGL:Tutorials:Using_Quaternions_to_represent_rotation#How_to_convert_to.2Ffrom_quaternions
        # Remember, all matrix arrays are stored internaly in row major
        # [M[0][0], M[0][1], ...]
        x, y, z, w = self._quat_array
        xx = x * x
        yy = y * y
        zz = z * z
        ww = w * w
        xy = x * y * 2.0
        xz = x * z * 2.0
        yz = y * z * 2.0
        wx = w * x * 2.0
        wy = w * y * 2.0
        wz = w * z * 2.0
        # I manualy transpose the matrix before creating it to put the values
        # into row major
        return Matrix3([
            ww + xx - yy - zz, (xy - wz), (xz + wy),
            (xy + wz), ww - xx + yy - zz, (yz - wx),
            (xz - wy), (yz + wx), ww - xx - yy + zz
        ])
    
    def toMatrix4(self):
        # http://gpwiki.org/index.php/OpenGL:Tutorials:Using_Quaternions_to_represent_rotation#How_to_convert_to.2Ffrom_quaternions
        # Remember, all matrix arrays are stored internaly in row major
        # [M[0][0], M[0][1], ...]
        x, y, z, w = self._quat_array
        xx = x * x
        yy = y * y
        zz = z * z
        ww = w * w
        xy = x * y * 2.0
        xz = x * z * 2.0
        yz = y * z * 2.0
        wx = w * x * 2.0
        wy = w * y * 2.0
        wz = w * z * 2.0
        # I manualy transpose the matrix before creating it to put the values
        # into row major
        return Matrix4([
            ww + xx - yy - zz, (xy - wz), (xz + wy), 0.0,
            (xy + wz), ww - xx + yy - zz, (yz - wx), 0.0,
            (xz - wy), (yz + wx), ww - xx - yy + zz, 0.0,
            0.0, 0.0, 0.0, 1.0
        ])
    
    def toEuler(self, order="xyz"):
        # Enforce correct "order" format
        order = order.lower()
        if len(order) != 3:
            raise TypeError("EULER: Must pass in 3 axes for multiplication order")
        if order.count("x") != 1 or order.count("y") != 1 or order.count("z") != 1:
            raise TypeError("EULER: Must pass in only 1 'X', 1'Y', and 1 'Z' for multiplication order")
        return self.toMatrix3().toEuler(order)
    
    def toAxisAngle(self):
        x, y, z, w = self._quat_array
        scale = (1 - max(min(w * w, 1.0), -1.0)) ** 0.5
        if scale > 0:
            x /= scale
            y /= scale
            z /= scale
        w = max(min(w, 1.0), -1.0)
        ang = math.acos(w) * 2.0
        return AxisAngle([x, y, z, ang])
    
    def asArray(self):
        return self._quat_array[:]
    
    x = property(__getX, __setX, None, "x property")
    y = property(__getY, __setY, None, "y property")
    z = property(__getZ, __setZ, None, "z property")
    w = property(__getW, __setW, None, "w property")


class Euler(object):
    
    """ Euler object that opperates like most other Vector3 classes.
        
        Eulers are always internally stored as radians.
        
        There are two ways to acsess the Euler array, asDegreeArray and
        asRadianArray.
        
        Eulers are [X, Y, Z].
        
        Attributes:
            _euler_array : A list of floats denoting a rotation in the world.
            x: A property instance that gets/sets its vaule from/to
                _euler_array.
            y: A property instance that gets/sets its vaule from/to
                _euler_array.
            z: A property instance that gets/sets its vaule from/to
                _euler_array.
    """
    
    __slots__ = ('_euler_array', 'x', 'y', 'z')
    
    def __init__(self, vals=[0.0, 0.0, 0.0], is_degrees=False):
        # Angles are stored as radians
        if len(vals) != 3:
            raise AttributeError("Euler: Passed in list does not have 3 values, it has %d" % len(vals))
        if is_degrees:
            self._euler_array = [math.radians((v * 1.0)) for v in vals]
        else:
            self._euler_array = [(v * 1.0) for v in vals]
        self.x = self._euler_array[0]
        self.y = self._euler_array[1]
        self.z = self._euler_array[2]
    
    def __repr__(self):
        return "[%0.4f, %0.4f, %0.4f]" % tuple(self._euler_array)
    
    def __str__(self):
        return self.__repr__()
    
    def __add__(self, other):
        if type(other) is Euler:
            x0, y0, z0 = self._euler_array
            x1, y1, z1 = other._euler_array
            return Euler([x0 + x1, y0 + y1, z0 + z1])
        raise TypeError("EULER: Can only add two Eulers together")
    
    def __sub__(self, other):
        if type(other) is Euler:
            x0, y0, z0 = self._euler_array
            x1, y1, z1 = other._euler_array
            return Euler([x0 - x1, y0 - y1, z0 - z1])
        raise TypeError("EULER: Can only subtract two Eulers together")
    
    def __mul__(self, other):
        other_type = type(other)
        if other_type is int or other_type is float:
            x, y, z = self._euler_array
            return Euler([x * other, y * other, z * other])
        raise TypeError("EULER: Can only multiply with a scalar")
    
    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __neg__(self):
        x, y, z = self._euler_array
        return Euler([-x, -y, -z])
    
    def __getitem__(self, idx):
        return self._euler_array[idx]
    
    def __setitem__(self, idx, val):
        self._euler_array[idx] = val * 1.0
    
    def __eq__(self, other):
        if type(other) is Euler:
            return self._euler_array == other._euler_array
        raise TypeError("EULER: Can only compare with other Eulers")
    
    def __getX(self):
        return self._euler_array[0]
    
    def __setX(self, val):
        self._euler_array[0] = val * 1.0
    
    def __getY(self):
        return self._euler_array[1]
    
    def __setY(self, val):
        self._euler_array[1] = val * 1.0
    
    def __getZ(self):
        return self._euler_array[2]
    
    def __setZ(self, val):
        self._euler_array[2] = val * 1.0
    
    def copy(self):
        return Euler(self._euler_array[:])
    
    def toMatrix3(self, order="xyz"):
        # Enforce correct "order" format
        order = order.lower()
        if len(order) != 3:
            raise TypeError("EULER: Must pass in 3 axes for multiplication order")
        if order.count("x") != 1 or order.count("y") != 1 or order.count("z") != 1:
            raise TypeError("EULER: Must pass in only 1 'X', 1'Y', and 1 'Z' for multiplication order")
        x, y, z = self._euler_array
        x_sin = math.sin(x)
        y_sin = math.sin(y)
        z_sin = math.sin(z)
        x_cos = math.cos(x)
        y_cos = math.cos(y)
        z_cos = math.cos(z)
        
        tmp_mat = Matrix3()
        x_mat = Matrix3([
            1.0, 0.0, 0.0,
            0.0, x_cos, -x_sin,
            0.0, x_sin, x_cos
        ])
        y_mat = Matrix3([
            y_cos, 0.0, y_sin,
            0.0, 1.0, 0.0,
            -y_sin, 0.0, y_cos
        ])
        z_mat = Matrix3([
            z_cos, -z_sin, 0.0,
            z_sin, z_cos, 0.0,
            0.0, 0.0, 1.0
        ])
        
        for axis in order:
            if axis == "x":
                tmp_mat = x_mat * tmp_mat
            elif axis == "y":
                tmp_mat = y_mat * tmp_mat
            else:
                tmp_mat = z_mat * tmp_mat
        
        return tmp_mat
    
    def toMatrix4(self, order="xyz"):
        # Enforce correct "order" format
        order = order.lower()
        if len(order) != 3:
            raise TypeError("EULER: Must pass in 3 axis for multiplication order")
        if order.count("x") != 1 or order.count("y") != 1 or order.count("z") != 1:
            raise TypeError("EULER: Must pass in only 1 'X', 1'Y', and 1 'Z' for multiplication order")
        x, y, z = self._euler_array
        x_sin = math.sin(x)
        y_sin = math.sin(y)
        z_sin = math.sin(z)
        x_cos = math.cos(x)
        y_cos = math.cos(y)
        z_cos = math.cos(z)
        
        tmp_mat = Matrix4()
        x_mat = Matrix4([
            1.0, 0.0, 0.0, 0.0,
            0.0, x_cos, -x_sin, 0.0,
            0.0, x_sin, x_cos, 0.0,
            0.0, 0.0, 0.0, 1.0
        ])
        y_mat = Matrix4([
            y_cos, 0.0, y_sin, 0.0,
            0.0, 1.0, 0.0, 0.0,
            -y_sin, 0.0, y_cos, 0.0,
            0.0, 0.0, 0.0, 1.0
        ])
        z_mat = Matrix4([
            z_cos, -z_sin, 0.0, 0.0,
            z_sin, z_cos, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0
        ])
        
        for axis in order:
            if axis == "x":
                tmp_mat = x_mat * tmp_mat
            elif axis == "y":
                tmp_mat = y_mat * tmp_mat
            else:
                tmp_mat = z_mat * tmp_mat
        
        return tmp_mat
    
    def toQuaternion(self, order="xyz"):
        # Enforce correct "order" format
        order = order.lower()
        if len(order) != 3:
            raise TypeError("EULER: Must pass in 3 axis for multiplication order")
        if order.count("x") != 1 or order.count("y") != 1 or order.count("z") != 1:
            raise TypeError("EULER: Must pass in only 1 'X', 1'Y', and 1 'Z' for multiplication order")
        x, y, z = self._euler_array
        x_sin = math.sin(x / 2.0)
        y_sin = math.sin(y / 2.0)
        z_sin = math.sin(z / 2.0)
        x_cos = math.cos(x / 2.0)
        y_cos = math.cos(y / 2.0)
        z_cos = math.cos(z / 2.0)
        
        tmp_quat = Quaternion()
        x_quat = Quaternion([x_sin, 0.0, 0.0, x_cos])
        y_quat = Quaternion([0.0, y_sin, 0.0, y_cos])
        z_quat = Quaternion([0.0, 0.0, z_sin, z_cos])
        
        for axis in order:
            if axis == "x":
                tmp_quat = x_quat * tmp_quat
            elif axis == "y":
                tmp_quat = y_quat * tmp_quat
            else:
                tmp_quat = z_quat * tmp_quat
        
        return tmp_quat.normalizeCopy()
    
    def toAxisAngle(self, order="xyz"):
        return self.toQuaternion(order).toAxisAngle()
    
    def asDegreeArray(self):
        tmp_array = [math.degrees(v) for v in self._euler_array]
        return tmp_array
    
    def asRadianArray(self):
        return self._euler_array[:]
    
    x = property(__getX, __setX, None, "x property")
    y = property(__getY, __setY, None, "y property")
    z = property(__getZ, __setZ, None, "z property")


class AxisAngle(object):
    """ AxisAngle object that opperates like most other AxisAngle classes.
        
        The angle is always internally stored as radians.
        
        There are two ways to access the AxisAngle array, asDegreeArray and
        asRadianArray.
        
        AxisAngles are [X, Y, Z, Angle].
        
        Attributes:
            _axis_array : A list of floats denoting a rotation in the world.
            x: A property instance that gets/sets its vaule from/to _axis_array.
            y: A property instance that gets/sets its vaule from/to _axis_array.
            z: A property instance that gets/sets its vaule from/to _axis_array.
            angle: A property instance that gets/sets its vaule from/to
                _axis_array.
    """
    
    __slots__ = ('_axis_array', 'angle', 'x', 'y', 'z')
    
    def __init__(self, vals=[1.0, 0.0, 0.0, 0.0], is_degrees=False):
        if len(vals) != 4:
            raise AttributeError("AXISANGLE: Passed in list does not have 4 values, has %d" % len(vals))
        self._axis_array = [(v * 1.0) for v in vals]
        if is_degrees:
            self._axis_array[-1] = math.radians(self._axis_array[-1])
        self.x = self._axis_array[0]
        self.y = self._axis_array[1]
        self.z = self._axis_array[2]
        self.angle = self._axis_array[3]
    
    def __repr__(self):
        return "Axis = [%0.4f, %0.4f, %0.4f], Angle = %0.4f" % tuple(self._axis_array)
    
    def __str__(self):
        return self.__repr__()
    
    def __mul__(self, other):
        other_type = type(other)
        if other_type is Vector3:
            x0, y0, z0, ang = self._axis_array
            x1, y1, z1 = other._vec_array
            tmp_cos = math.cos(ang)
            tmp_sin = math.sin(ang)
            x_cross = y0 * z1 - z0 * y1
            y_cross = z0 * x1 - x0 * z1
            z_cross = x0 * y1 - y0 * x1
            dot = x0 * x1 + y0 * y1 + z0 * z1
            x_new = x1 * tmp_cos + x_cross * tmp_sin + x0 * dot * (1 - tmp_cos)
            y_new = y1 * tmp_cos + y_cross * tmp_sin + y0 * dot * (1 - tmp_cos)
            z_new = z1 * tmp_cos + z_cross * tmp_sin + z0 * dot * (1 - tmp_cos)
            return Vector3([x_new, y_new, z_new])
        raise TypeError("AXISANGLE: Can only multiply with a Vector3 on the right")
    
    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __getitem__(self, idx):
        return self._axis_array[idx]
    
    def __setitem__(self, idx, val):
        self._axis_array[idx] = val * 1.0
    
    def __eq__(self, other):
        if type(other) is AxisAngle:
            return self._axis_array == other._axis_array
        raise TypeError("AXISANGLE: Can only compare with other AxisAngles")
    
    def __getX(self):
        return self._axis_array[0]
    
    def __setX(self, val):
        self._axis_array[0] = val * 1.0
    
    def __getY(self):
        return self._axis_array[1]
    
    def __setY(self, val):
        self._axis_array[1] = val * 1.0
    
    def __getZ(self):
        return self._axis_array[2]
    
    def __setZ(self, val):
        self._axis_array[2] = val * 1.0
    
    def __getAng(self):
        return self._axis_array[3]
    
    def __setAng(self, val):
        self._axis_array[3] = val * 1.0
    
    def __vecCross(self, other):
         # Assumes self is on the left
        if type(other) is AxisAngle:
            x0, y0, z0, ang0 = self._axis_array
            x1, y1, z1, ang1 = other._axis_array
            return [y0 * z1 - z0 * y1, z0 * x1 - x0 * z1, x0 * y1 - y0 * x1]
        elif type(other) is Vector3:
            x0, y0, z0, ang0 = self._axis_array
            x1, y1, z1 = other._vec_array
            return [y0 * z1 - z0 * y1, z0 * x1 - x0 * z1, x0 * y1 - y0 * x1]
        else:
            raise TypeError("AXISANGLE: Can only vector cross two AxisAngles or with a Vector3")
    
    def __vecDot(self, other):
        # Assumes self is on the left
        if type(other) is AxisAngle:
            x0, y0, z0, ang0 = self._axis_array
            x1, y1, z1, ang1 = other._axis_array
            return x0 * x1 + y0 * y1 + z0 * z1
        elif type(other) is Vector3:
            x0, y0, z0, ang0 = self._axis_array
            x1, y1, z1 = other._vec_array
            return x0 * x1 + y0 * y1 + z0 * z1
        else:
            raise TypeError("AXISANGLE: Can only vector dot two AxisAngles or with a Vector3")
    
    def __vecLength(self):
        return (self.__vecDot(self)) ** 0.5
    
    def copy(self):
        return AxisAngle(self._axis_array)
    
    def normalize(self):
        length = self.__vecLength()
        if length > 0.0:
            self._axis_array[0] /= length
            self._axis_array[1] /= length
            self._axis_array[2] /= length
    
    def normalizeCopy(self):
        tmp_axis = AxisAngle(self._axis_array)
        tmp_axis.normalize()
        return tmp_axis
    
    def toMatrix3(self):
        tmp_axis = self.normalizeCopy()
        x, y, z, ang = tmp_axis._axis_array
        c = math.cos(ang)
        s = math.sin(ang)
        t = 1.0 - c           # The tilde matrix
        
        xx = x * x
        xy = x * y
        xz = x * z
        yy = y * y
        yz = y * z
        zz = z * z
        
        tmp_mat = [
            t * xx + c, t * xy - z * s, t * xz + y * s,
            t * xy + z * s, t * yy + c, t * yz - x * s,
            t * xz - y * s, t * yz + x * s, t * zz + c
        ]
        
        return Matrix3(tmp_mat)
    
    def toMatrix4(self):
        tmp_axis = self.normalizeCopy()
        x, y, z, ang = tmp_axis._axis_array
        c = math.cos(ang)
        s = math.sin(ang)
        t = 1.0 - c           # The tilde matrix
        
        xx = x * x
        xy = x * y
        xz = x * z
        yy = y * y
        yz = y * z
        zz = z * z
        
        tmp_mat = [
            t * xx + c, t * xy - z * s, t * xz + y * s, 0.0,
            t * xy + z * s, t * yy + c, t * yz - x * s, 0.0,
            t * xz - y * s, t * yz + x * s, t * zz + c, 0.0,
            0.0, 0.0, 0.0, 1.0
        ]
        
        return Matrix4(tmp_mat)
    
    def toEuler(self, order='xyz'):
        return self.toMatrix3().toEuler(order)
    
    def toQuaternion(self):
        tmp_axis = self.normalizeCopy()
        x, y, z, ang = tmp_axis._axis_array
        tmp_quat = [0.0] * 4
        tmp_quat[0] = x * math.sin(ang / 2.0)
        tmp_quat[1] = y * math.sin(ang / 2.0)
        tmp_quat[2] = z * math.sin(ang / 2.0)
        tmp_quat[3] = math.cos(ang / 2.0)
        return Quaternion(tmp_quat).normalizeCopy()
    
    def asDegreeArray(self):
        tmp_angle = math.degrees(self._axis_array[-1])
        return self._axis_array[:-1] + [tmp_angle]
    
    def asRadianArray(self):
        return self._axis_array[:]
    
    x = property(__getX, __setX, None, "x property")
    y = property(__getY, __setY, None, "y property")
    z = property(__getZ, __setZ, None, "z property")
    angle = property(__getAng, __setAng, None, "angle property")


class Matrix3(object):
    
    """ Matrix3 object that opperates like most other Matrix3 classes.
        
        Matrix3 is stored in Row major:
            [1.0, 0.0, 0.0]
            [0.0, 1.0, 0.0]
            [0.0, 0.0, 1.0]
        
        Attributes:
            _mat_array : A list of floats denoting a rotation in the world.
    """
    
    __slots__ = ('_mat_array')
    
    def __init__(self, vals=MATRIX3_IDENTITY):
        if len(vals) != 9:
            raise AttributeError("MATRIX3: Passed in list does not have 9 values, has %d" % len(vals))
        self._mat_array = [(v * 1.0) for v in vals]
    
    def __repr__(self):
        return (
            "[%0.4f, %0.4f, %0.4f]\n"
            "[%0.4f, %0.4f, %0.4f]\n"
            "[%0.4f, %0.4f, %0.4f]"
        ) % tuple(self._mat_array)
    
    def __str__(self):
        return self.__repr__()
    
    def __add__(self, other):
        if type(other) is Matrix3:
            m0_00, m0_01, m0_02,\
            m0_10, m0_11, m0_12,\
            m0_20, m0_21, m0_22 = self._mat_array
            m1_00, m1_01, m1_02,\
            m1_10, m1_11, m1_12,\
            m1_20, m1_21, m1_22 = other._mat_array
            return Matrix3([
                m0_00 + m1_00, m0_01 + m1_01, m0_02 + m1_02,
                m0_10 + m1_10, m0_11 + m1_11, m0_12 + m1_12,
                m0_20 + m1_20, m0_21 + m1_21, m0_22 + m1_22
            ])
        raise TypeError("MATRIX3: Can only add two Matrix3s together")
    
    def __sub__(self,other):
        if type(other) is Matrix3:
            m0_00, m0_01, m0_02,\
            m0_10, m0_11, m0_12,\
            m0_20, m0_21, m0_22 = self._mat_array
            m1_00, m1_01, m1_02,\
            m1_10, m1_11, m1_12,\
            m1_20, m1_21, m1_22 = other._mat_array
            return Matrix3([
                m0_00 - m1_00, m0_01 - m1_01, m0_02 - m1_02,
                m0_10 - m1_10, m0_11 - m1_11, m0_12 - m1_12,
                m0_20 - m1_20, m0_21 - m1_21, m0_22 - m1_22
            ])
        raise TypeError("MATRIX3: Can only subtract two Matrix3s together")
    
    def __mul__(self,other):
        other_type = type(other)
        if other_type is Matrix3:
            m0_00, m0_01, m0_02,\
            m0_10, m0_11, m0_12,\
            m0_20, m0_21, m0_22 = self._mat_array
            m1_00, m1_01, m1_02,\
            m1_10, m1_11, m1_12,\
            m1_20, m1_21, m1_22 = other._mat_array
            new_mat = [
                m0_00 * m1_00 + m0_01 * m1_10 + m0_02 * m1_20,
                m0_00 * m1_01 + m0_01 * m1_11 + m0_02 * m1_21,
                m0_00 * m1_02 + m0_01 * m1_12 + m0_02 * m1_22,
                
                m0_10 * m1_00 + m0_11 * m1_10 + m0_12 * m1_20,
                m0_10 * m1_01 + m0_11 * m1_11 + m0_12 * m1_21,
                m0_10 * m1_02 + m0_11 * m1_12 + m0_12 * m1_22,
                
                m0_20 * m1_00 + m0_21 * m1_10 + m0_22 * m1_20,
                m0_20 * m1_01 + m0_21 * m1_11 + m0_22 * m1_21,
                m0_20 * m1_02 + m0_21 * m1_12 + m0_22 * m1_22
            ]
            return Matrix3(new_mat)
        
        elif other_type is Vector3:
            m00, m01, m02,\
            m10, m11, m12,\
            m20, m21, m22 = self._mat_array
            x, y, z = other._vec_array
            new_vec = [
                m00 * x + m01 * y + m02 * z,
                m10 * x + m11 * y + m12 * z,
                m20 * x + m21 * y + m22 * z
            ]
            return Vector3(new_vec)
        
        elif other_type is int or other_type is float:
            m00, m01, m02,\
            m10, m11, m12,\
            m20, m21, m22 = self._mat_array
            return Matrix3([
                m00 * other, m01 * other, m02 * other,
                m10 * other, m11 * other, m12 * other,
                m20 * other, m21 * other, m22 * other
            ])
        
        raise TypeError("MATRIX3: Can only multiply with a scalar or Matrix3 (or with a Vector3 on the right)")
    
    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __neg__(self):
        # This returns the inverse (transpose) of the matrix
        m00, m01, m02,\
        m10, m11, m12,\
        m20, m21, m22 = self._mat_array
        return Matrix3([
            m00, m10, m20,
            m01, m11, m21,
            m02, m12, m22
        ])
    
    def __getitem__(self, idx):
        idx *= 3
        if idx == 6:
            return self._mat_array[idx:]
        elif idx > 6:
            idx /= 3
            raise IndexError("Index %d is out of the range of 2" % idx)
        return self._mat_array[idx:(idx + 3)]
    
    def __eq__(self, other):
        if type(other) is Matrix3:
            return self._mat_array == other._mat_array
        raise TypeError("MATRIX3: Can only compare with other Matrix3s")
    
    def copy(self):
        return Matrix3(self._mat_array)
    
    def determinant(self):
        m00, m01, m02,\
        m10, m11, m12,\
        m20, m21, m22 = self._mat_array
        return ((m00 * m11 * m22) - (m00 * m12 * m21) - (m01 * m10 * m22) + (m01 * m12 * m20) + (m02 * m10 * m21) - (m02 * m11 * m20))
    
    def orthonormalize(self):
        m00, m01, m02,\
        m10, m11, m12,\
        m20, m21, m22 = self._mat_array
        a1 = Vector3([m00, m10, m20])
        a2 = Vector3([m01, m11, m21])
        a3 = Vector3([m02, m12, m22])
        # The Gram-Schmidt process
        v1 = a1
        v2 = a2 - (((a2.dot(v1)) / (v1.dot(v1))) * v1)
        v3 = a3 - (((a3.dot(v1)) / (v1.dot(v1))) * v1) - (((a3.dot(v2)) / (v2.dot(v2))) * v2)
        
        # Check if the Gram-Schmidt process worked and correct it when necessary
        e1 = v1.normalizeCopy()
        e2 = v2.normalizeCopy()
        e3 = v3.normalizeCopy()
        
        x0, y0, z0 = e1._vec_array
        x1, y1, z1 = e2._vec_array
        x2, y2, z2 = e3._vec_array
        
        e1_dot_e2 = e1.dot(e2)
        e1_dot_e3 = e1.dot(e3)
        e2_dot_e3 = e2.dot(e3)
        e1_length = e1.length()
        e2_length = e2.length()
        e3_length = e3.length()
        
        if e1_dot_e2 < 0.00001 and e1_length > 0 and e2_length > 0:
            if e2_dot_e3 < 0.00001 and e1._vec_array != e3._vec_array and e3_length > 0:
                self._mat_array = [x0, x1, x2, y0, y1, y2, z0, z1, z2]
            else:
                e3 = e1.cross(e2).normalizeCopy()
                x2, y2, z2 = e3._vec_array
                self._mat_array = [x0, x1, x2, y0, y1, y2, z0, z1, z2]
        elif e1_dot_e3 < 0.00001 and e1_length > 0 and e3_length > 0:
            e2 = e3.cross(e1).normalizeCopy()
            x1, y1, z1 = e2._vec_array
            self._mat_array = [x0, x1, x2, y0, y1, y2, z0, z1, z2]
        elif e2_dot_e3 < 0.00001 and e2_length > 0 and e3_length > 0:
            e1 = e2.cross(e3).normalizeCopy()
            x0, y0, z0 = e1._vec_array
            self._mat_array = [x0, x1, x2, y0, y1, y2, z0, z1, z2]
        else:
            raise TypeError("MATRIX3: Cannot orthonormalize matrix\n %s" % self)
        det = self.determinant()
        if det < 0:
            self._mat_array = [x0, x1, -x2, y0, y1, -y2, z0, z1, -z2]
        det = self.determinant()
        if det < 0.998 or det > 1.001:
            raise ValueError("MATRIX3: The determinant of matrix is not 1, so it is an invaild matrix")
    
    def orthonormalizeCopy(self):
        tmp_mat = Matrix3(self._mat_array)
        tmp_mat.orthonormalize()
        return tmp_mat
    
    def toMatrix4(self):
        m00, m01, m02,\
        m10, m11, m12,\
        m20, m21, m22 = self._mat_array
        return Matrix4([
            m00, m01, m02, 0.0,
            m10, m11, m12, 0.0,
            m20, m21, m22, 0.0,
            0.0, 0.0, 0.0, 1.0
        ])
    
    def toQuaternion(self):
        # http://www.euclideanspace.com/maths/geometry/rotations/conversions/matrixToQuaternion/index.htm
        # A Quaternion is [X, Y, Z, W]
        m00, m01, m02,\
        m10, m11, m12,\
        m20, m21, m22 = self._mat_array
        trace = m00 + m11 + m22
        if trace > 0:
            scale = ((trace + 1.0) ** 0.5) * 2.0
            w = 0.25 * scale
            x = (m21 - m12) / scale
            y = (m02 - m20) / scale
            z = (m10 - m01) / scale
        elif m00 > m11 and m00 > m22:
            scale = ((1.0 + m00 - m11 - m22) ** 0.5) * 2.0
            w = (m21 - m12) / scale
            x = 0.25 * scale
            y = (m01 + m10) / scale
            z = (m02 + m20) / scale
        elif m11 > m22:
            scale = ((1.0 + m11 - m00 - m22) ** 0.5) * 2.0
            w = (m02 - m20) / scale
            x = (m01 + m10) / scale
            y = 0.25 * scale
            z = (m12 + m21) / scale
        else:
            scale = ((1.0 + m22 - m00 - m11) ** 0.5) * 2.0
            w = (m10 - m01) / scale
            x = (m02 + m20) / scale
            y = (m12 + m21) / scale
            z = 0.25 * scale
        return Quaternion([x, y, z, w]).normalizeCopy()
    
    def toEuler(self, order='xyz'):
        # Angles are stored as radians
        order = order.lower()
        if len(order) != 3:
            raise TypeError("MATRIX3: Must pass in 3 axes for multiplication order")
        _euler_array = list(_MAT_TO_EULER_MAP[order](self))
        return Euler(_euler_array)
    
    def toAxisAngle(self):
        return self.toQuaternion().toAxisAngle()
    
    def asRowArray(self):
        return self._mat_array[:]
    
    def asColArray(self):
        return (-self)._mat_array[:]


class Matrix4(object):
    
    """ Matrix4 object that opperates like most other Matrix4 classes.
       
        Matrix4 is stored in Row major:
            [1.0, 0.0, 0.0, 0.0]
            [0.0, 1.0, 0.0, 0.0]
            [0.0, 0.0, 1.0, 0.0]
            [0.0, 0.0, 0.0, 1.0]
        
        Attributes:
            _mat_array : A list of floats denoting a transformation in the
                world.
    """
    
    __slots__ = ('_mat_array')
    
    def __init__(self, vals=MATRIX4_IDENTITY):
        if len(vals) != 16:
            raise AttributeError("MATRIX4: Passed in list does not have 16 values, has %d" % len(vals))
        self._mat_array = [(v * 1.0) for v in vals]
    
    def __repr__(self):
        return (
            "[%0.4f, %0.4f, %0.4f, %0.4f]\n"
            "[%0.4f, %0.4f, %0.4f, %0.4f]\n"
            "[%0.4f, %0.4f, %0.4f, %0.4f]\n"
            "[%0.4f, %0.4f, %0.4f, %0.4f]"
        ) % tuple(self._mat_array)
    
    def __str__(self):
        return self.__repr__()
    
    def __add__(self, other):
        if type(other) is Matrix4:
            m0_00, m0_01, m0_02, m0_03,\
            m0_10, m0_11, m0_12, m0_13,\
            m0_20, m0_21, m0_22, m0_23,\
            m0_30, m0_31, m0_32, m0_33 = self._mat_array
            m1_00, m1_01, m1_02, m1_03,\
            m1_10, m1_11, m1_12, m1_13,\
            m1_20, m1_21, m1_22, m1_23,\
            m1_30, m1_31, m1_32, m1_33 = other._mat_array
            return Matrix4([
                m0_00 + m1_00, m0_01 + m1_01, m0_02 + m1_02, m0_03 + m1_03,
                m0_10 + m1_10, m0_11 + m1_11, m0_12 + m1_12, m0_13 + m1_13,
                m0_20 + m1_20, m0_21 + m1_21, m0_22 + m1_22, m0_23 + m1_23,
                m0_30 + m1_30, m0_31 + m1_31, m0_32 + m1_32, m0_33 + m1_33
            ])
        raise TypeError("MATRIX4: Can only add two Matrix4s together")
    
    def __sub__(self, other):
        if type(other) is Matrix4:
            m0_00, m0_01, m0_02, m0_03,\
            m0_10, m0_11, m0_12, m0_13,\
            m0_20, m0_21, m0_22, m0_23,\
            m0_30, m0_31, m0_32, m0_33 = self._mat_array
            m1_00, m1_01, m1_02, m1_03,\
            m1_10, m1_11, m1_12, m1_13,\
            m1_20, m1_21, m1_22, m1_23,\
            m1_30, m1_31, m1_32, m1_33 = other._mat_array
            return Matrix4([
                m0_00 - m1_00, m0_01 - m1_01, m0_02 - m1_02, m0_03 - m1_03,
                m0_10 - m1_10, m0_11 - m1_11, m0_12 - m1_12, m0_13 - m1_13,
                m0_20 - m1_20, m0_21 - m1_21, m0_22 - m1_22, m0_23 - m1_23,
                m0_30 - m1_30, m0_31 - m1_31, m0_32 - m1_32, m0_33 - m1_33
            ])
        raise TypeError("MATRIX4: Can only subtract two Matrix4s together")
    
    def __mul__(self, other):
        # This assumes self is the matrix on the left
        other_type = type(other)
        if other_type is Matrix4:
            m0_00, m0_01, m0_02, m0_03,\
            m0_10, m0_11, m0_12, m0_13,\
            m0_20, m0_21, m0_22, m0_23,\
            m0_30, m0_31, m0_32, m0_33 = self._mat_array
            m1_00, m1_01, m1_02, m1_03,\
            m1_10, m1_11, m1_12, m1_13,\
            m1_20, m1_21, m1_22, m1_23,\
            m1_30, m1_31, m1_32, m1_33 = other._mat_array
            new_mat = [
                m0_00 * m1_00 + m0_01 * m1_10 + m0_02 * m1_20 + m0_03 * m1_30,
                m0_00 * m1_01 + m0_01 * m1_11 + m0_02 * m1_21 + m0_03 * m1_31,
                m0_00 * m1_02 + m0_01 * m1_12 + m0_02 * m1_22 + m0_03 * m1_32,
                m0_00 * m1_03 + m0_01 * m1_13 + m0_02 * m1_23 + m0_03 * m1_33,
                
                m0_10 * m1_00 + m0_11 * m1_10 + m0_12 * m1_20 + m0_13 * m1_30,
                m0_10 * m1_01 + m0_11 * m1_11 + m0_12 * m1_21 + m0_13 * m1_31,
                m0_10 * m1_02 + m0_11 * m1_12 + m0_12 * m1_22 + m0_13 * m1_32,
                m0_10 * m1_03 + m0_11 * m1_13 + m0_12 * m1_23 + m0_13 * m1_33,
                
                m0_20 * m1_00 + m0_21 * m1_10 + m0_22 * m1_20 + m0_23 * m1_30,
                m0_20 * m1_01 + m0_21 * m1_11 + m0_22 * m1_21 + m0_23 * m1_31,
                m0_20 * m1_02 + m0_21 * m1_12 + m0_22 * m1_22 + m0_23 * m1_32,
                m0_20 * m1_03 + m0_21 * m1_13 + m0_22 * m1_23 + m0_23 * m1_33,
                
                m0_30 * m1_00 + m0_31 * m1_10 + m0_32 * m1_20 + m0_33 * m1_30,
                m0_30 * m1_01 + m0_31 * m1_11 + m0_32 * m1_21 + m0_33 * m1_31,
                m0_30 * m1_02 + m0_31 * m1_12 + m0_32 * m1_22 + m0_33 * m1_32,
                m0_30 * m1_03 + m0_31 * m1_13 + m0_32 * m1_23 + m0_33 * m1_33
            ]
            return Matrix4(new_mat)
        
        elif other_type is Vector3:
            m00, m01, m02, m03,\
            m10, m11, m12, m13,\
            m20, m21, m22, m23,\
            m30, m31, m32, m33 = self._mat_array
            x, y, z = other._vec_array
            new_vec = [
                m00 * x + m01 * y + m02 * z,
                m10 * x + m11 * y + m12 * z,
                m20 * x + m21 * y + m22 * z
            ]
            return Vector3(new_vec)
        
        elif other_type is int or other_type is float:
            m00, m01, m02, m03,\
            m10, m11, m12, m13,\
            m20, m21, m22, m23,\
            m30, m31, m32, m33 = self._mat_array
            return Matrix4([
                m00 * other, m01 * other, m02 * other, m03 * other,
                m10 * other, m11 * other, m12 * other, m13 * other,
                m20 * other, m21 * other, m22 * other, m23 * other,
                m30 * other, m31 * other, m32 * other, m33 * other
            ])
        
        raise TypeError("MATRIX4: Can only multiply with a scalar or Matrix4 (or with a Vector3 on the right)")
    
    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __neg__(self):
        # This returns the inverse (transpose) of the matrix
        m00, m01, m02, m03,\
        m10, m11, m12, m13,\
        m20, m21, m22, m23,\
        m30, m31, m32, m33 = self._mat_array
        return Matrix4([
            m00, m10, m20, m30,
            m01, m11, m21, m31,
            m02, m12, m22, m32,
            m03, m13, m23, m33
        ])
    
    def __getitem__(self, idx):
        idx *= 4
        if idx == 12:
            return self._mat_array[idx:]
        elif idx > 12:
            idx /= 4
            raise IndexError("Index %d is out of the range of 3" % idx)
        return self._mat_array[idx:(idx + 4)]
    
    def __eq__(self, other):
        if type(other) is Matrix4:
            return self._mat_array == other._mat_array
        raise TypeError("MATRIX4: Can only compare with other Matrix4s")
    
    def copy(self):
        return Matrix4(self._mat_array)
    
    def determinant(self):
        m00, m01, m02, m03,\
        m10, m11, m12, m13,\
        m20, m21, m22, m23,\
        m30, m31, m32, m33 = self._mat_array
        return ((m00 * m11 * m22) - (m00 * m12 * m21) - (m01 * m10 * m22) + (m01 * m12 * m20) + (m02 * m10 * m21) - (m02 * m11 * m20))
    
    def orthonormalize(self):
        m00, m01, m02, m03,\
        m10, m11, m12, m13,\
        m20, m21, m22, m23,\
        m30, m31, m32, m33 = self._mat_array
        a1 = Vector3([m00, m10, m20])
        a2 = Vector3([m01, m11, m21])
        a3 = Vector3([m02, m12, m22])
        # The Gram-Schmidt process
        v1 = a1
        v2 = a2 - (((a2.dot(v1)) / (v1.dot(v1))) * v1)
        v3 = a3 - (((a3.dot(v1)) / (v1.dot(v1))) * v1) - (((a3.dot(v2)) / (v2.dot(v2))) * v2)
        
        # Check if the Gram-Schmidt process worked and correct it when necessary
        e1 = v1.normalizeCopy()
        e2 = v2.normalizeCopy()
        e3 = v3.normalizeCopy()
        
        x0, y0, z0 = e1._vec_array
        x1, y1, z1 = e2._vec_array
        x2, y2, z2 = e3._vec_array
        
        e1_dot_e2 = e1.dot(e2)
        e1_dot_e3 = e1.dot(e3)
        e2_dot_e3 = e2.dot(e3)
        e1_length = e1.length()
        e2_length = e2.length()
        e3_length = e3.length()
        
        if e1_dot_e2 < 0.00001 and e1_length > 0 and e2_length > 0:
            if e2_dot_e3 < 0.00001 and e1._vec_array != e3._vec_array and e3_length > 0:
                self._mat_array = [
                    x0, x1, x2, m03,
                    y0, y1, y2, m13,
                    z0, z1, z2, m23,
                    m30, m31, m32, m33
                ]
            else:
                e3 = e1.cross(e2).normalizeCopy()
                x2, y2, z2 = e3._vec_array
                self._mat_array = [
                    x0, x1, x2, m03,
                    y0, y1, y2, m13,
                    z0, z1, z2, m23,
                    m30, m31, m32, m33
                ]
        elif e1_dot_e3 < 0.00001 and e1_length > 0 and e3_length > 0:
            e2 = e3.cross(e1).normalizeCopy()
            x1, y1, z1 = e2._vec_array
            self._mat_array = [
                x0, x1, x2, m03,
                y0, y1, y2, m13,
                z0, z1, z2, m23,
                m30, m31, m32, m33
            ]
        elif e2_dot_e3 < 0.00001 and e2_length > 0 and e3_length > 0:
            e1 = e2.cross(e3).normalizeCopy()
            x0, y0, z0 = e1._vec_array
            self._mat_array = [
                x0, x1, x2, m03,
                y0, y1, y2, m13,
                z0, z1, z2, m23,
                m30, m31, m32, m33
            ]
        else:
            raise TypeError("MATRIX4: Cannot orthonormalize matrix\n %s" % self)
        det = self.determinant()
        if det < 0:
            self._mat_array = [
                x0, x1, -x2, m03,
                y0, y1, -y2, m13,
                z0, z1, -z2, m23,
                m30, m31, m32, m33
            ]
        det = self.determinant()
        if det < 0.998 or det > 1.001:
            raise ValueError("MATRIX4: The determinant of matrix is not 1, so it is an invaild matrix")
    
    def orthonormalizeCopy(self):
        tmp_mat = Matrix4(self._mat_array)
        tmp_mat.orthonormalize()
        return tmp_mat
    
    def toMatrix3(self):
        m00, m01, m02, m03,\
        m10, m11, m12, m13,\
        m20, m21, m22, m23,\
        m30, m31, m32, m33 = self._mat_array
        return Matrix3([
            m00, m01, m02,
            m10, m11, m12,
            m20, m21, m22
        ])
    
    def toQuaternion(self):
        # http://www.euclideanspace.com/maths/geometry/rotations/conversions/matrixToQuaternion/index.htm
        # A Quaternion is [X, Y, Z, W]
        m00, m01, m02, m03,\
        m10, m11, m12, m13,\
        m20, m21, m22, m23,\
        m30, m31, m32, m33 = self._mat_array
        trace = m00 + m11 + m22
        if trace > 0:
            scale = ((trace + 1.0) ** 0.5) * 2.0
            w = 0.25 * scale
            x = (m21 - m12) / scale
            y = (m02 - m20) / scale
            z = (m10 - m01) / scale
        elif m00 > m11 and m00 > m22:
            scale = ((1.0 + m00 - m11 - m22) ** 0.5) * 2.0
            w = (m21 - m12) / scale
            x = 0.25 * scale
            y = (m01 + m10) / scale
            z = (m02 + m20) / scale
        elif m11 > m22:
            scale = ((1.0 + m11 - m00 - m22) ** 0.5) * 2.0
            w = (m02 - m20) / scale
            x = (m01 + m10) / scale
            y = 0.25 * scale
            z = (m12 + m21) / scale
        else:
            scale = ((1.0 + m22 - m00 - m11) ** 0.5) * 2.0
            w = (m10 - m01) / scale
            x = (m02 + m20) / scale
            y = (m12 + m21) / scale
            z = 0.25 * scale
        return Quaternion([x, y, z, w]).normalizeCopy()
    
    def toEuler(self, order='xyz'):
        return self.toMatrix3().toEuler(order)
    
    def toAxisAngle(self):
        return self.toQuaternion().toAxisAngle()
    
    def asRowArray(self):
        return self._mat_array[:]
    
    def asColArray(self):
        return (-self)._mat_array[:]


### Convenient Functions ###
# psi is X-Axis Angle, theta is Y-Axis Angle, phi is Z-Axis Angle
# From http://www.gregslabaugh.name/publications/euler.pdf
def _xyzMatToEuler(mat3):
    m00, m01, m02,\
    m10, m11, m12,\
    m20, m21, m22 = mat3._mat_array
    if m20 >= 0.998:
        theta = -math.pi / 2.0
        psi = math.atan2(-m01, -m02)
        phi = 0.0
    
    elif m20 <= -0.998:
        theta = math.pi / 2.0
        psi = math.atan2(m01, m02)
        phi = 0.0
    
    else:
        theta = math.asin(-m20)
        psi = math.atan2((m21 / math.cos(theta)), (m22 / math.cos(theta)))
        phi = math.atan2((m10 / math.cos(theta)), (m00 / math.cos(theta)))
    
    return (psi, theta, phi)


def _xzyMatToEuler(mat3):
    m00, m01, m02,\
    m10, m11, m12,\
    m20, m21, m22 = mat3._mat_array
    if m10 >= 0.998:
        phi = math.pi / 2.0
        psi = math.atan2(m02, m22)
        theta = 0.0
    
    elif m10 <= -0.998:
        phi = -math.pi / 2.0
        psi = math.atan2(-m02, m22)
        theta = 0.0
    
    else:
        phi = math.asin(m10)
        psi = math.atan2((-m12 / math.cos(phi)), (m11 / math.cos(phi)))
        theta = math.atan2((-m20 / math.cos(phi)), (m00 / math.cos(phi)))
    
    return (psi, theta, phi)


def _yxzMatToEuler(mat3):
    m00, m01, m02,\
    m10, m11, m12,\
    m20, m21, m22 = mat3._mat_array
    if m21 >= 0.998:
        psi = math.pi / 2.0
        theta = math.atan2(m10, m00)
        phi = 0.0
    
    elif m21 <= -0.998:
        psi = -math.pi / 2.0
        theta = math.atan2(m10, m00)
        phi = 0.0
    
    else:
        psi = math.asin(m21)
        phi = math.atan2((-m01 / math.cos(psi)), (m11 / math.cos(psi)))
        theta = math.atan2((-m20 / math.cos(psi)), (m22 / math.cos(psi)))
    
    return (psi, theta, phi)


def _yzxMatToEuler(mat3):
    m00, m01, m02,\
    m10, m11, m12,\
    m20, m21, m22 = mat3._mat_array
    if m01 >= 0.998:
        phi = -math.pi / 2.0
        theta = math.atan2(m20, m22)
        psi = 0.0
    
    elif m01 <= -0.998:
        phi = math.pi / 2.0
        theta = math.atan2(-m20, m22)
        psi = 0.0
    
    else:
        phi = math.asin(-m01)
        psi = math.atan2((m21 / math.cos(phi)), (m11 / math.cos(phi)))
        theta = math.atan2((m02 / math.cos(phi)), (m00 / math.cos(phi)))
    
    return (psi, theta, phi)


def _zxyMatToEuler(mat3):
    m00, m01, m02,\
    m10, m11, m12,\
    m20, m21, m22 = mat3._mat_array
    if m12 >= 0.998:
        psi = -math.pi / 2.0
        phi = math.atan2(m20, m21)
        theta = 0.0
    
    elif m12 <= -0.998:
        psi = math.pi / 2.0
        phi = math.atan2(-m20, m21)
        theta = 0.0
    
    else:
        psi = math.asin(-m12)
        phi = math.atan2((m10 / math.cos(psi)), (m11 / math.cos(psi)))
        theta = math.atan2((m02 / math.cos(psi)), (m22 / math.cos(psi)))
    
    return (psi, theta, phi)


def _zyxMatToEuler(mat3):
    m00, m01, m02,\
    m10, m11, m12,\
    m20, m21, m22 = mat3._mat_array
    if m02 >= 0.998:
        theta = math.pi / 2.0
        phi = math.atan2(m10, m11)
        psi = 0.0
    
    elif m02 <= -0.998:
        theta = -math.pi / 2.0
        phi = math.atan2(m10, m11)
        psi = 0.0
    
    else:
        theta = math.asin(m02)
        psi = math.atan2((-m12 / math.cos(theta)), (m22 / math.cos(theta)))
        phi = math.atan2((-m01 / math.cos(theta)), (m00 / math.cos(theta)))
    
    return (psi, theta, phi)


# Can't set before functions is defined, so global gets set here
_MAT_TO_EULER_MAP = {
    'xyz' : _xyzMatToEuler,
    'xzy' : _xzyMatToEuler,
    'yxz' : _yxzMatToEuler,
    'yzx' : _yzxMatToEuler,
    'zxy' : _zxyMatToEuler,
    'zyx' : _zyxMatToEuler
}
