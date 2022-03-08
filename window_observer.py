# https://mhammond.github.io/pywin32/modules.html
import win32gui, win32process
import psutil
import requests

import sys
import time
import ctypes
import ctypes.wintypes

# https://stackoverflow.com/questions/4407631/is-there-windows-system-event-on-active-window-changed
# https://stackoverflow.com/questions/15849564/how-to-use-winapi-setwineventhook-in-python

WINEVENT_OUTOFCONTEXT = 0
WINEVENT_SKIPOWNTHREAD = 1
WINEVENT_SKIPOWNPROCESS = 2
WINEVENT_INCONTEXT = 4

# https://docs.microsoft.com/en-us/windows/win32/winauto/event-constants
EVENT_OBJECT_NAMECHANGE = 0x800C
EVENT_SYSTEM_FOREGROUND = 0x0003

WinEventProcType = ctypes.WINFUNCTYPE(
    None, 
    ctypes.wintypes.HANDLE,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.HWND,
    ctypes.wintypes.LONG,
    ctypes.wintypes.LONG,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.DWORD
)

class WindowObserver:
    def __init__(self, port):
        self.port = port

        self.locked_window_name = ''

        self.current_window_name = ''
        self.current_pid = 0
        self.current_process_name = ''

        self.foreground_handle = 0

        self.open_windows = []
        self.open_window_processes = []

        self.user32 = ctypes.windll.user32
        self.ole32 = ctypes.windll.ole32

        self.ole32.CoInitialize(0)

        self.WinEventProc = WinEventProcType(self.observer_callback)
        self.user32.SetWinEventHook.restype = ctypes.wintypes.HANDLE

        # we'll need to see what window we're on
        if self.user32.SetWinEventHook(EVENT_SYSTEM_FOREGROUND, EVENT_SYSTEM_FOREGROUND, 0, self.WinEventProc, 0, 0, WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS) == 0:
            print('SetWinEventHook failed for EVENT_SYSTEM_FOREGROUND')
            sys.exit(1)    

        # Within a window, we switch tabs or something
        if self.user32.SetWinEventHook(EVENT_OBJECT_NAMECHANGE, EVENT_OBJECT_NAMECHANGE, 0, self.WinEventProc, 0, 0, WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS) == 0:
            print('SetWinEventHook failed for EVENT_SYSTEM_FOREGROUND')
            sys.exit(1)    
         
    
    def get_current_process(self):
        return self.current_process_name
    
    def get_current_window(self):
        return self.locked_window_name
        
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

    def observer_callback(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        self.current_window_name = win32gui.GetWindowText(hwnd) 
        (tid, self.current_pid) = win32process.GetWindowThreadProcessId(hwnd) # (thread id, process id)
        # different windows/tabs will have the same pid/tid, so unfortunately we have to stick with window titles

        # there will be many windows with titles changing, we want the foreground one (e.g. switching tabs in browser/discord)
        if event == EVENT_SYSTEM_FOREGROUND:
            self.foreground_handle = hwnd

        if self.current_window_name != self.locked_window_name and hwnd == self.foreground_handle:
            if self.current_pid > 0:
                try:
                    self.current_process_name = psutil.Process(self.current_pid).name()

                    self.locked_window_name = self.current_window_name

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
        
    # compared to self.observe in previous commits, we save like 10% cpu if we're event driven
    def observe_event_based(self):
        msg = ctypes.wintypes.MSG()
        while self.user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
            self.user32.TranslateMessageW(msg)
            self.user32.DispatchMessageW(msg)