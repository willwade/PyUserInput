#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
from Quartz import *
from AppKit import NSEvent
from .base import PyKeyboardMeta, PyKeyboardEventMeta
# The following makes this more keyboard layout independent
import mac_keycode

# Taken from events.h
# /System/Library/Frameworks/Carbon.framework/Versions/A/Frameworks/HIToolbox.framework/Versions/A/Headers/Events.h

key_aliases = {
    '=': 0x18, # NB: These are variable and shouldn't really be here.. 
    '-': 0x1b,
    ']': 0x1e,
    '[': 0x21,
    '\'': 0x27,
    ';': 0x29,
    '\\': 0x2a,
    ',': 0x2b,
    '/': 0x2c,
    '.': 0x2f,
    '`': 0x32,
    ' ': 0x31,
    '\r': 0x24,
    '\t': 0x30,
    '\n': 0x24,
    'return' : 0x24, # the following are fixed keys # http://stackoverflow.com/a/16125341/1123094
    'tab' : 0x30,
    'space' : 0x31,
    'delete' : 0x33,
    'escape' : 0x35,
    'command' : 0x37,
    'shift' : 0x38,
    'capslock' : 0x39,
    'option' : 0x3A,
    'alternate' : 0x3A,
    'control' : 0x3B,
    'rightshift' : 0x3C,
    'rightoption' : 0x3D,
    'rightcontrol' : 0x3E,
    'function' : 0x3F,
    'home': 0x73,
    'multiply':0x43,
    'add':0x45,
    'subtract':0x4e,
    'divide':0x4b,
    'pagedown': 0x79,
    'forwarddelete': 0x75,
    'pagedown' : 0x79,
    'help' : 0x72,
    'home' : 0x73,
    'pageup' : 0x74,
    'forwarddelete' : 0x75,
    'F18' : 0x4F,
    'F19' : 0x50,
    'F20' : 0x5A,
    'F5' : 0x60,
    'F6' : 0x61,
    'F7' : 0x62,
    'F3' : 0x63,
    'F8' : 0x64,
    'F9' : 0x65,
    'F11' : 0x67,
    'F13' : 0x69,
    'F16' : 0x6A,
    'F14' : 0x6B,
    'F10' : 0x6D,
    'F12' : 0x6F,
    'F15' : 0x71,
    'function' : 0x3F,
    'F17' : 0x40
}

# Taken from ev_keymap.h
# http://www.opensource.apple.com/source/IOHIDFamily/IOHIDFamily-86.1/IOHIDSystem/IOKit/hidsystem/ev_keymap.h
special_key_translate_table = {
    'KEYTYPE_SOUND_UP': 0,
    'KEYTYPE_SOUND_DOWN': 1,
    'KEYTYPE_BRIGHTNESS_UP': 2,
    'KEYTYPE_BRIGHTNESS_DOWN': 3,
    'KEYTYPE_CAPS_LOCK': 4,
    'KEYTYPE_HELP': 5,
    'POWER_KEY': 6,
    'KEYTYPE_MUTE': 7,
    'UP_ARROW_KEY': 8,
    'DOWN_ARROW_KEY': 9,
    'KEYTYPE_NUM_LOCK': 10,
    'KEYTYPE_CONTRAST_UP': 11,
    'KEYTYPE_CONTRAST_DOWN': 12,
    'KEYTYPE_LAUNCH_PANEL': 13,
    'KEYTYPE_EJECT': 14,
    'KEYTYPE_VIDMIRROR': 15,
    'KEYTYPE_PLAY': 16,
    'KEYTYPE_NEXT': 17,
    'KEYTYPE_PREVIOUS': 18,
    'KEYTYPE_FAST': 19,
    'KEYTYPE_REWIND': 20,
    'KEYTYPE_ILLUMINATION_UP': 21,
    'KEYTYPE_ILLUMINATION_DOWN': 22,
    'KEYTYPE_ILLUMINATION_TOGGLE': 23
}

class PyKeyboard(PyKeyboardMeta):

    def __init__(self):
      self.shift_key = 'shift'
      self.modifier_table = {'Shift':False,'Command':False,'Control':False,'Alternate':False}
        

    def press_key(self, key):
        if key.title() in self.modifier_table: 
            self.modifier_table.update({key.title():True})
            
        if key in special_key_translate_table:
            self._press_special_key(key, True)
        else:
            self._press_normal_key(key, True)

    def release_key(self, key):
        # remove the key
        if key.title() in self.modifier_table: self.modifier_table.update({key.title():False})
        
        if key in special_key_translate_table:
            self._press_special_key(key, False)
        else:
            self._press_normal_key(key, False)

    def special_key_assignment(self):
        self.volume_mute_key = 'KEYTYPE_MUTE'
        self.volume_down_key = 'KEYTYPE_SOUND_DOWN'
        self.volume_up_key = 'KEYTYPE_SOUND_UP'
        self.media_play_pause_key = 'KEYTYPE_PLAY'

        # Doesn't work :(
        # self.media_next_track_key = 'KEYTYPE_NEXT'
        # self.media_prev_track_key = 'KEYTYPE_PREVIOUS'

    def _press_normal_key(self, key, down):
        try:
            # VK_ is a raw keycode
            if key[0:3]=='VK_':
                key_code = int(key[3:])
            else:
                key_code = self.lookup_keycode_value(key.lower())
                if key_code == None:
                    raise RuntimeError("Key {} not implemented.".format(key))
            # certain flags are required for Mac for modifier keys. These are: 
            # kCGEventFlagMaskAlternate | kCGEventFlagMaskCommand |
            #   kCGEventFlagMaskControl | kCGEventFlagMaskShift
            event = CGEventCreateKeyboardEvent(None, key_code, down)
            mkeyStr = ''
            for mkey in self.modifier_table:
                if self.modifier_table[mkey]:
                    if len(mkeyStr)>1: mkeyStr = mkeyStr+' ^ '
                    mkeyStr = mkeyStr+'kCGEventFlagMask'+mkey                    
            if len(mkeyStr)>1:
                eval('CGEventSetFlags(event, '+mkeyStr+')')
            CGEventPost(kCGHIDEventTap, event)
            if key.lower() == "shift":
              time.sleep(.1)

        except KeyError:
            raise RuntimeError("Key {} not implemented.".format(key))

    def _press_special_key(self, key, down):
        """ Helper method for special keys. 

        Source: http://stackoverflow.com/questions/11045814/emulate-media-key-press-on-mac
        """
        key_code = special_key_translate_table[key]

        ev = NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
                NSSystemDefined, # type
                (0,0), # location
                0xa00 if down else 0xb00, # flags
                0, # timestamp
                0, # window
                0, # ctx
                8, # subtype
                (key_code << 16) | ((0xa if down else 0xb) << 8), # data1
                -1 # data2
            )

        CGEventPost(0, ev.CGEvent())
    

    def lookup_character_value(self, keycode):
        """ Helper method to lookup a character value from a keycode """
        return mac_keycode.createStringForKey(keycode)
    
    def lookup_keycode_value(self, character):
        """ Helper method to lookup a keycode from a character """
        if character.lower() in key_aliases:
            key_code = key_aliases[character.lower()]
        else:
            key_code = mac_keycode.keyCodeForChar(character)
        return key_code
    
class PyKeyboardEvent(PyKeyboardEventMeta):
    def run(self):
        tap = CGEventTapCreate(
            kCGSessionEventTap,
            kCGHeadInsertEventTap,
            kCGEventTapOptionDefault,
            CGEventMaskBit(kCGEventKeyDown) |
            CGEventMaskBit(kCGEventKeyUp),
            self.handler,
            None)

        loopsource = CFMachPortCreateRunLoopSource(None, tap, 0)
        loop = CFRunLoopGetCurrent()
        CFRunLoopAddSource(loop, loopsource, kCFRunLoopDefaultMode)
        CGEventTapEnable(tap, True)

        while self.state:
            CFRunLoopRunInMode(kCFRunLoopDefaultMode, 5, False)

    def handler(self, proxy, type, event, refcon):
        key = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
        if type == kCGEventKeyDown:
            self.key_press(key)
        elif type == kCGEventKeyUp:
            self.key_release(key)

        if self.capture:
            CGEventSetType(event, kCGEventNull)

        return event
