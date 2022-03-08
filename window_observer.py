# https://mhammond.github.io/pywin32/modules.html
import win32gui, win32process
import psutil
import requests

class WindowObserver:
    def __init__(self, port):
        self.port = port

        self.last_window_name = ''

        self.current_window_name = ''
        self.current_pid = 0
        self.current_process_name = ''

        self.open_windows = []
        self.open_window_processes = []
    
    def get_current_process(self):
        return self.current_process_name
    
    def get_current_window(self):
        return self.current_window_name
        
    def get_all_open_window_processes(self):
        self.open_window_processes = []

        def winEnumHandler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                (tid, pid) = win32process.GetWindowThreadProcessId(hwnd) # (thread id, process id)
                process = psutil.Process(pid)
                if process.name() not in self.open_window_processes: self.open_window_processes.append(process.name())
        
        win32gui.EnumWindows(winEnumHandler, None)
        self.open_window_processes.sort()
        #print(self.open_window_processes)
        return self.open_window_processes

    def get_all_open_window_names(self):
        self.open_windows = []
        def winEnumHandler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title not in self.open_windows and title != '': self.open_windows.append(title)
        
        win32gui.EnumWindows(winEnumHandler, None)
        self.open_windows.sort()

        return self.open_windows

    # while this is cool, the user's really only going to be typing into windows that are open
    # def get_all_user_processes(self, bind_to_open_windows=True):
    #     user_name = win32api.GetUserNameEx(win32api.NameSamCompatible)
    #     processes = []
    #     for proc in psutil.process_iter():
    #         try:
    #             if proc.username() == user_name:
    #                 if proc.name() not in processes:
    #                     processes.append(proc.name())
    #         except:
    #             pass
    #     processes.sort()
    #     print(processes)      
    
    def observe(self):
        while True:
            window = win32gui.GetForegroundWindow() 
            self.current_window_name = win32gui.GetWindowText(window) 
            (tid, self.current_pid) = win32process.GetWindowThreadProcessId(window) # (thread id, process id)
            # different windows/tabs will have the same pid/tid, so unfortunately we have to stick with window titles

            if self.current_window_name != self.last_window_name:
                if self.current_pid > 0:
                    try:
                        self.current_process_name = psutil.Process(self.current_pid).name()

                        self.last_window_name = self.current_window_name

                        data = {
                            "type": "program",
                            "window_name": self.current_window_name,
                            "process_name": self.current_process_name
                        }

                        try:
                            requests.post('http://localhost:' + str(self.port) + '/publish', json=data)
                        except:
                            pass
                    except: # When we alt tab/task switch, we get a weird PID
                        pass