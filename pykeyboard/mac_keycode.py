#!/usr/bin/env python
# PyKeycode : https://github.com/abarnert/pykeycode
# With thanks to abarnet 
# http://stackoverflow.com/questions/1918841/how-to-convert-ascii-character-to-cgkeycode */

import ctypes
import ctypes.util
import CoreFoundation
import Foundation
import objc

try:
    unichr
except NameError:
    unichr = chr

carbon_path = ctypes.util.find_library('Carbon')
carbon = ctypes.cdll.LoadLibrary(carbon_path)
    
# We could rely on the fact that kTISPropertyUnicodeKeyLayoutData has
# been the string @"TISPropertyUnicodeKeyLayoutData" since even the
# Classic Mac days. Or we could load it from the framework. 
# Unfortunately, the framework doesn't have PyObjC wrappers, and there's
# no easy way to force PyObjC to wrap a CF/ObjC object that it doesn't
# know about. So:
_objc = ctypes.PyDLL(objc._objc.__file__)
_objc.PyObjCObject_New.restype = ctypes.py_object
_objc.PyObjCObject_New.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
def objcify(ptr):
    return _objc.PyObjCObject_New(ptr, 0, 1)
kTISPropertyUnicodeKeyLayoutData_p = ctypes.c_void_p.in_dll(
    carbon, 'kTISPropertyUnicodeKeyLayoutData')
kTISPropertyUnicodeKeyLayoutData = objcify(kTISPropertyUnicodeKeyLayoutData_p)

carbon.TISCopyCurrentKeyboardInputSource.argtypes = []
carbon.TISCopyCurrentKeyboardInputSource.restype = ctypes.c_void_p
carbon.TISGetInputSourceProperty.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
carbon.TISGetInputSourceProperty.restype = ctypes.c_void_p
carbon.LMGetKbdType.argtypes = []
carbon.LMGetKbdType.restype = ctypes.c_uint32
OptionBits = ctypes.c_uint32
UniCharCount = ctypes.c_uint8
UniChar = ctypes.c_uint16
UniChar4 = UniChar * 4
carbon.UCKeyTranslate.argtypes = [ctypes.c_void_p, # keyLayoutPtr
                                  ctypes.c_uint16, # virtualKeyCode
                                  ctypes.c_uint16, # keyAction
                                  ctypes.c_uint32, # modifierKeyState
                                  ctypes.c_uint32, # keyboardType
                                  OptionBits,      # keyTranslateOptions
                                  ctypes.POINTER(ctypes.c_uint32), # deadKeyState
                                  UniCharCount,    # maxStringLength
                                  ctypes.POINTER(UniCharCount), # actualStringLength
                                  UniChar4]
carbon.UCKeyTranslate.restype = ctypes.c_uint32 # OSStatus
kUCKeyActionDisplay = 3
kUCKeyTranslateNoDeadKeysBit = 0

kTISPropertyUnicodeKeyLayoutData = ctypes.c_void_p.in_dll(
    carbon, 'kTISPropertyUnicodeKeyLayoutData')

def createStringForKey(keycode, modifiers=0):
    keyboard_p = carbon.TISCopyCurrentKeyboardInputSource()
    keyboard = objcify(keyboard_p)
    layout_p = carbon.TISGetInputSourceProperty(keyboard_p, 
                                                kTISPropertyUnicodeKeyLayoutData)
    layout = objcify(layout_p)
    layoutbytes = layout.bytes()
    keysdown = ctypes.c_uint32()
    length = UniCharCount()
    chars = UniChar4()
    retval = carbon.UCKeyTranslate(layoutbytes.tobytes(),
                                   keycode,
                                   kUCKeyActionDisplay,
                                   modifiers,
                                   carbon.LMGetKbdType(),
                                   kUCKeyTranslateNoDeadKeysBit,
                                   ctypes.byref(keysdown),
                                   4,
                                   ctypes.byref(length),
                                   chars)
    s = u''.join(unichr(chars[i]) for i in range(length.value))
    CoreFoundation.CFRelease(keyboard)
    return s

codedict = {createStringForKey(code, modifiers): (code, modifiers)
            for code in range(128) for modifiers in (10, 8, 2, 0)}

# Aliases
aliases = {
    u'space': u' ',
    u'tab': u'\t',
    # ...
}
for alias, c in aliases.items():
    codedict[alias] = codedict[c]

# The following is fixed
specials = {
    u'return' : (0x24, 0),
    u'delete' : (0x33, 0),
    u'escape' : (0x35, 0),
    u'command' : (0x37, 0),
    u'shift' : (0x38, 0),
    u'capslock' : (0x39, 0),
    u'option' : (0x3A, 0),
    u'alternate' : (0x3A, 0),
    u'control' : (0x3B, 0),
    u'rightshift' : (0x3C, 0),
    u'rightoption' : (0x3D, 0),
    u'rightcontrol' : (0x3E, 0),
    u'function' : (0x3F, 0),
    u'home': (0x73, 0),
    u'pagedown': (0x79, 0),
    u'forwarddelete': (0x75, 0),
    u'pagedown' : (0x79, 0),
    u'help' : (0x72, 0),
    u'home' : (0x73, 0),
    u'pageup' : (0x74, 0),
    u'forwarddelete' : (0x75, 0),
    u'F18' : (0x4F, 0),
    u'F19' : (0x50, 0),
    u'F20' : (0x5A, 0),
    u'F5' : (0x60, 0),
    u'F6' : (0x61, 0),
    u'F7' : (0x62, 0),
    u'F3' : (0x63, 0),
    u'F8' : (0x64, 0),
    u'F9' : (0x65, 0),
    u'F11' : (0x67, 0),
    u'F13' : (0x69, 0),
    u'F16' : (0x6A, 0),
    u'F14' : (0x6B, 0),
    u'F10' : (0x6D, 0),
    u'F12' : (0x6F, 0),
    u'F15' : (0x71, 0),
    u'function' : (0x3F, 0),
    u'F17' : (0x40, 0)
}
codedict.update(specials)


def keyCodeForChar(c):
    return codedict[c]
    
def printcode(keycode):
    print(u"{}: {!r} Shift{!r} Option{!r} Command{!r}".format(
        keycode,
        createStringForKey(keycode, 0),
        createStringForKey(keycode, 2),
        createStringForKey(keycode, 8),
        createStringForKey(keycode, 10)))

if __name__ == '__main__':
    import sys
    for arg in sys.argv[1:]:
        try:
            arg = arg.decode(sys.stdin.encoding)
        except AttributeError:
            pass
        try:
            keycode = int(arg)
        except ValueError:
            print(u"{!r} ('{}'): keycode {}, mod {}".format(
                arg, arg, *keyCodeForChar(arg)))
        else:
            printcode(keycode)
    if len(sys.argv) < 2:
        for keycode in range(128):
            printcode(keycode)