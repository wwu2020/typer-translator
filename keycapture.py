import keyboard
import requests
from datetime import datetime
import platform as _platform

# A smarter man could figure out how to pass the channel into here and publish directly
class Keycapture:  
    # this is from keyboard.get_typed_strings but ignores ctrl modifier
    def capture_sentence(self, events, allow_backspace=True):
        backspace_name = 'delete' if _platform.system() == 'Darwin' else 'backspace'

        shift_pressed = False
        capslock_pressed = False
        ctrl_pressed = False
        string = ''
        for event in events:
            name = event.name

            # Space is the only key that we _parse_hotkey to the spelled out name
            # because of legibility. Now we have to undo that.
            if event.name == 'space':
                name = ' '
            
            if 'ctrl' in event.name:
                ctrl_pressed = event.event_type == 'down'

            if 'shift' in event.name:
                shift_pressed = event.event_type == 'down'
            elif event.name == 'caps lock' and event.event_type == 'down':
                capslock_pressed = not capslock_pressed
            elif allow_backspace and event.name == backspace_name and event.event_type == 'down':
                string = string[:-1]
            elif event.event_type == 'down':
                if len(name) == 1:
                    if shift_pressed ^ capslock_pressed:
                        name = name.upper()
                    string = string if ctrl_pressed else string + name
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
            
            data = {
                "text": msg,
                "time": current_time,
                "translator": "nobody",
                "translated": msg + " sus"
            }
            try:
                requests.post('http://localhost:5000/publish', json=data)
            except:
                pass

    def start_capture(self, whitelist):
        # while True:
        #     event = keyboard.read_event()
        #     if event.event_type == keyboard.KEY_DOWN:
        #         self.send_sentence(event.name)
        #         #print(event.name)
        while True:
            self.send_sentence(self.capture_sentence(keyboard.record(until='enter')))

    def __init__(self):
        pass