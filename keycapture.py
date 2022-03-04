import keyboard
import requests

# A smarter man could figure out how to pass the channel into here and publish directly
class Keycapture:
    def send_keystroke(self, key):
        data = {
            "text": key,
            "translator": "nobody",
            "translated": key + " sus"
        }
        try:
            requests.post('http://localhost:5000/publish', json=data)
        except:
            pass

    def start_capture(self):
        while True:
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_DOWN:
                self.send_keystroke(event.name)
                #print(event.name)

    def __init__(self):
        pass