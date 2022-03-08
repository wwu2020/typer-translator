import keyboard
import requests
from datetime import datetime
import time
import platform as _platform

from translator import Translator

invisible_keys = {
    'left',
    'up',
    'down',
    'right',
    'esc',
    'tab',
    'scroll lock',
    'print screen',
    'insert',
    'pause',
    'caps lock',
    'num lock',
}

# A smarter man could figure out how to pass the channel into here and publish directly
class KeyCapture:  
    def __init__(self, whitelist, port, wobserver, config):
        self.whitelist = whitelist
        self.port = port
        self.wobserver = wobserver
        self.config = config
        self.enabled = True

        self.translator = Translator(config)

        '''
        program_sentence is a map that stores a list of key events per program
        this is important because a user could switch between applications without finishing sentences in one
        especially important if we're going to be whitelisting reading keystrokes in certain applications
        '''
        self.program_sentence = dict()

    def enable(self, status):
        self.enabled = status
        if not self.enabled:
            self.program_sentence = dict()

    def reload_config(self, config):
        self.program_sentence = dict()
        self.translator = Translator(config)
    
    def get_enable_status(self):
        return self.enabled

    # this is from keyboard.get_typed_strings but ignores ctrl and windows key modifiers
    '''
        Things it won't understand:
            autocompletion, like completing an emoji (message was not sent), if your client allows it, try if tab works
            copy paste
            ctrl+a and then backspace
            moving cursor around with arrow keys or mouse
            try to finish your sentence before alt tabbing to different applications
    '''
    def capture_sentence(self, events, allow_backspace=True):
        backspace_name = 'delete' if _platform.system() == 'Darwin' else 'backspace'

        shift_pressed = False
        capslock_pressed = False
        ctrl_pressed = False
        windows_pressed = False
        ctrl_a_state = False
        string = ''
        for count, event in enumerate(events):
            name = event.name

            # Space is the only key that we _parse_hotkey to the spelled out name
            # because of legibility. Now we have to undo that.
            if event.name == 'space':
                name = ' '
            #print(count, event, string)
            # handling ctrl a situations
            if 'a' in event.name.lower() and ctrl_pressed and not ctrl_a_state and event.event_type == 'down':
                ctrl_a_state = True     
            elif event.name in ['shift', 'ctrl', 'windows']:
                if 'ctrl' in event.name: ctrl_pressed = event.event_type == 'down' 
                if 'shift' in event.name: shift_pressed = event.event_type == 'down'
                if 'windows' in event.name: windows_pressed = event.event_type == 'down'
            elif event.name == 'caps lock' and event.event_type == 'down':
                capslock_pressed = not capslock_pressed
            elif allow_backspace and event.name == backspace_name and event.event_type == 'down':
                if ctrl_a_state:
                    string = ''
                    ctrl_a_state = False
                elif not ctrl_pressed:
                    string = string[:-1]
                else: # support for ctrl backspace which deletes last word
                    idx = string.rfind(' ')
                    if idx != -1:
                        string = string[:idx]
                    else:
                        string = ''  
            elif event.event_type == 'down':
                if ctrl_a_state:
                    if event.name not in set.union(keyboard.all_modifiers, invisible_keys) or event.name == 'space':
                        string = name
                    ctrl_a_state = False
                elif len(name) == 1:
                    if shift_pressed ^ capslock_pressed:
                        name = name.upper()
                    string = string if ctrl_pressed or windows_pressed else string + name
                else:
                    yield string
                    string = ''
        yield string

    def send_sentence(self, gen):
        for msg in gen:
            if msg.isspace() or msg == '':
                continue
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")

            translated = self.translator.translate(msg)
            data = {
                "type": "phrase",
                "phrase": msg,
                "time": int(time.time()),
                "timestring": current_time,
                "tl_phrase": translated
            }
            try:
                print("f: " + msg)
                #requests.post('http://localhost:' + str(self.port) + '/publish', json=data)
            except:
                pass

    '''
    If window is in whitelist, log per window
    else if whole process in whitelist, even if window is whitelisted log to process

    For example you don't want to log your bank account in firefox, only twitter.com
    but you should log all of discord
    '''
    def start_capture(self):
        while True:
            event = keyboard.read_event()
            d = self.program_sentence
            w = self.wobserver.get_current_window()
            p = self.wobserver.get_current_process()

            if self.enabled:
                if w in self.whitelist:
                    if w not in d:
                        d[w] = []
                
                    if event.name == 'enter':
                        self.send_sentence(self.capture_sentence(d[w]))
                        d[w] = []
                    else:
                        d[w].append(event) 
                elif p in self.whitelist:
                    if p not in d:
                        d[p] = []
                
                    if event.name == 'enter':
                        self.send_sentence(self.capture_sentence(d[p]))
                        d[p] = []
                    else:
                        d[p].append(event) 
                

            

            # self.send_sentence(self.capture_sentence(keyboard.record(until='enter')))