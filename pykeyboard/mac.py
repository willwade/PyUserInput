#Copyright 2013 Paul Barton
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time
import Quartz
from AppKit import NSEvent
from .base import PyKeyboardMeta, PyKeyboardEventMeta
# Needs to be merged at some point...
import mac_keycode

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

independent_from_layout_keys = {
    'return' : 0x24,
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
}

class PyKeyboard(PyKeyboardMeta):

    def __init__(self):
      self.shift_key = 'shift'
      self.modifier_table = {'Shift':False,'Command':False,'Control':False,'Alternate':False}
        
    def press_key(self, key):
        # Press the modifier
        if key.title() in self.modifier_table: self.modifier_table.update({key.title():True})
        # NB: we also need to actually press the modifier so this gets passed to normal_key
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

    def type_string(self,char_string, interval=0):
        for ch in char_string:
            self.tap_key(ch)
            time.sleep(interval)
        
    def special_key_assignment(self):
        self.volume_mute_key = 'KEYTYPE_MUTE'
        self.volume_down_key = 'KEYTYPE_SOUND_DOWN'
        self.volume_up_key = 'KEYTYPE_SOUND_UP'
        self.media_play_pause_key = 'KEYTYPE_PLAY'

        # Doesn't work :(
        # self.media_next_track_key = 'KEYTYPE_NEXT'
        # self.media_prev_track_key = 'KEYTYPE_PREVIOUS'

    def _handle_key(self, key):
        if key.lower() in independent_from_layout_keys:
            key_code = independent_from_layout_keys[key.lower()]
            yield (key_code, 0)

        # VK_ is a raw keycode. 
        elif key[0:3]=='VK_':
            key_code = int(key[3:])
            yield (key_code, 0)

        else:
            # NB: this could then provide a different modifier
            for key_code, modifier in self.lookup_keycode_value(key):
                # Update this.. # hmm. how does this get set back again after a key press
                self.update_modifier_table(modifier)
                if key_code == None:
                    raise RuntimeError("Key {} not implemented.".format(key))
                yield (key_code, modifier)


    def _press_normal_key(self, key, down):
        try:
            for key_code, modifier in self._handle_key(key):
                # For sticky keys
                event = Quartz.CGEventCreateKeyboardEvent(None, key_code, down)
                mkeyStr = ''
                # Caps, and the two unknown mod keys are not KCGEventMask keys. Not sure what do 
                for mkey in self.modifier_table:
                    if self.modifier_table[mkey]:
                        if len(mkeyStr)>1: mkeyStr = mkeyStr+' ^ '
                        mkeyStr = mkeyStr+'Quartz.kCGEventFlagMask'+mkey   
                if len(mkeyStr)>1:
                    eval('Quartz.CGEventSetFlags(event, '+mkeyStr+')')
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
                # I don't get this line: 
                if key.title() in self.modifier_table:
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

        Quartz.CGEventPost(0, ev.Quartz.CGEvent())


    def update_modifier_table(self,n):
        """ Pass a modifier Bit and it will return which keys are set 1: Cntrol 2: Shift 4: Caps-lock 8: Option """
        modar = mac_keycode.mods(n)
        for mod in modar:
            if mod in self.modifier_table and modar[mod] is True:
                self.modifier_table[mod] = True
        return True        
        
    def lookup_character_value(self, keycode, modifier=0):
        """ Helper method to lookup a character value from a keycode """
        return mac_keycode.CharForKeyCode(keycode, modifier)
    
    def lookup_keycode_value(self, character):
        """ Helper method to lookup a keycode from a character """
        return [(int(key_code), int(modifier)) for key_code, modifier in mac_keycode.KeyCodeForChar(character)]
    
    def is_char_shifted(self, character):
        """ Returns True if the key character is uppercase or shifted."""
        return any(modifier == 2 for key_code, modifier in mac_keycode.KeyCodeForChar(character))

class PyKeyboardEvent(PyKeyboardEventMeta):
    def run(self):
        tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionDefault,
            Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown) |
            Quartz.CGEventMaskBit(Quartz.kCGEventKeyUp),
            self.handler,
            None)

        loopsource = Quartz.CFMachPortCreateRunLoopSource(None, tap, 0)
        loop = Quartz.CFRunLoopGetCurrent()
        Quartz.CFRunLoopAddSource(loop, loopsource, Quartz.kCFRunLoopDefaultMode)
        Quartz.CGEventTapEnable(tap, True)

        while self.state:
            Quartz.CFRunLoopRunInMode(Quartz.kCFRunLoopDefaultMode, 5, False)

    def handler(self, proxy, type, event, refcon):
        key = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
        if type == Quartz.kCGEventKeyDown:
            self.key_press(key)
        elif type == Quartz.kCGEventKeyUp:
            self.key_release(key)

        if self.capture:
            Quartz.CGEventSetType(event, Quartz.kCGEventNull)

        return event
