from genericpath import exists
from flask import Flask, request, send_from_directory, g, jsonify
from gevent import config
config.set('resolver', 'block') #explained below
from gevent.pywsgi import WSGIServer
import flask_sse
import threading, signal
import json
import sqlite3
import configparser
import sys, os

import wx.adv
import wx
import webbrowser

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

TRAY_TOOLTIP = 'Typer Translator' 
TRAY_ICON = resource_path('./client/public/favicon.png')

from window_observer import WindowObserver
from key_capture import KeyCapture

DATABASE = './typer-translator-database.db'
PORT = 35465

app = Flask(__name__)
# https://github.com/singingwolfboy/flask-sse/issues/7
channel = flask_sse.Channel()

def init_config():
    if not exists("./config.ini"):
        config['default'] = {}
        default = config['default']
        default['provider'] = "deepl"
        # default['from_lang'] = "EN"
        default['to_lang'] = "ja"

        config['deepl'] = {}
        deepl = config['deepl']
        deepl['secret_access_key'] = 'null'
        deepl['pro'] = 'False'

        config['microsoft'] = {}
        msft = config['microsoft']
        msft['secret_access_key'] = 'null'

        config['mymemory'] = {}
        mmem = config['mymemory']
        mmem['email'] = 'null'

        config['libre'] = {}
        libre = config['libre']
        libre['secret_access_key'] = 'null'
        libre['base_url'] = 'http://localhost:5000'

        with open('./config.ini', 'w') as configfile:
            config.write(configfile)
    else:
        config.read('./config.ini')

whitelist = []
config = configparser.ConfigParser()
init_config()
wobserver = WindowObserver(PORT)
klogger = KeyCapture(whitelist, PORT, wobserver, config)

#server = WSGIServer(("", PORT), app) 
obthread = threading.Thread(target=wobserver.observe_event_based, daemon=True)
klthread = threading.Thread(target=klogger.start_capture, daemon=True)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def query_db(query, args=(), one=False):
    with app.app_context():
        cur = get_db().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv

def edit_db(query, args=()):
    with app.app_context():
        cur = get_db().execute(query, args)
        lrid = cur.lastrowid
        cur.close()
        get_db().commit()
        return lrid

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/programs')
def programs():
    return jsonify({"processes": wobserver.get_all_open_window_processes(), "windows": wobserver.get_all_open_window_names()})

@app.route('/currentprogram')
def currentprogram():
    return jsonify({"process": wobserver.get_current_process(), "window": wobserver.get_current_window()})

@app.route('/whitelist', methods=['POST', 'GET'])
def getwhitelist():
    if request.method == 'POST':
        #print("whitelist rule: " + request.json["action"] + " " + request.json["program"])
        action = request.json["action"]
        if action == "add":
            whitelist.append(request.json["program"])
            edit_db("INSERT INTO whitelist (process) VALUES (?)", [request.json["program"]])
        elif action == "remove":
            whitelist.remove(request.json["program"])
            edit_db("DELETE FROM whitelist WHERE process = ?", [request.json["program"]])
        return "OK"
    return jsonify(whitelist)

@app.route('/savedphrases', methods=['POST', 'GET'])
def getsavedphrases():
    if request.method == 'POST':
        action = request.json["action"]
        if action == "add":
            lrid = edit_db("INSERT INTO saved (phrase, tl_phrase) VALUES (?, ?)", [request.json["phrase"], request.json["tl_phrase"]])
            return jsonify({"id": lrid, "phrase": request.json["phrase"], "tl_phrase": request.json["tl_phrase"]})
        elif action == "remove":
            edit_db("DELETE FROM saved WHERE id = ?", [request.json["id"]])
            return "OK"
    
    savedphrases = []
    for phrase in query_db('SELECT * from saved'):
        savedphrases.append({"id": phrase["id"], "phrase": phrase["phrase"], "tl_phrase": phrase["tl_phrase"]})
    return jsonify(savedphrases)

@app.route('/subscribe')
def subscribe():
    return channel.subscribe()

@app.route('/publish', methods=['POST'])
def publish():
    channel.publish(json.dumps(request.json))
    return "OK"

@app.route('/enable', methods=['POST', 'GET'])
def enable():
    if request.method == 'POST':
        klogger.enable(request.json["enable"])
        return "OK"
    return jsonify({"status": klogger.get_enable_status()})

# Path for our main Svelte page
@app.route("/")
def base():
    return send_from_directory('client/public', 'index.html')

# Path for all the static files (compiled JS/CSS, etc.)
@app.route("/<path:path>")
def home(path):
    return send_from_directory('client/public', path)

# @app.route("/shutdown")
# def shutdown():
#     print("Shutdown request")
#     server.stop()
#     return "Goodbye, remember to hit any key"

# for when you run in a terminal
def ctrlc_handler(signum, frame):
    wobserver.cleanup()
    #server.stop()

def populate_whitelist():
    for entry in query_db('SELECT * FROM whitelist'):
        whitelist.append(entry["process"])

def reload_config():
    init_config()
    klogger.reload_config(config)

def open_config():
    os.startfile('config.ini')

'''
Now for headless application
'''

def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.Append(item)
    return item

class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame):
        self.frame = frame
        super(TaskBarIcon, self).__init__()
        self.set_icon(TRAY_ICON)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        create_menu_item(menu, 'Open Config', self.on_open_config)
        create_menu_item(menu, 'Reload Config', self.on_reload_config)
        menu.AppendSeparator()
        create_menu_item(menu, '2 Letter ISO codes', self.on_iso_codes)
        menu.AppendSeparator()
        create_menu_item(menu, 'Exit', self.on_exit)
        return menu

    def set_icon(self, path):
        icon = wx.Icon(path)
        self.SetIcon(icon, TRAY_TOOLTIP)

    def on_left_down(self, event):      
        webbrowser.open('http://localhost:' + str(PORT))
    
    def on_open_config(self, event):
        open_config()

    def on_reload_config(self, event):
        reload_config()
    
    def on_iso_codes(self, event):
        webbrowser.open("https://www.sitepoint.com/iso-2-letter-language-codes/")

    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        self.frame.Close()

class wxApp(wx.App):
    def OnInit(self):
        frame=wx.Frame(None)
        self.SetTopWindow(frame)
        TaskBarIcon(frame)
        return True

# https://github.com/gevent/gevent/issues/1427
# How to run wsgi server in threads, relevant to the 'block' dns resolver at top
def run_server():
    def run_wsgi():
        server = WSGIServer(("", PORT), app) 
        server.serve_forever()
    t = threading.Thread(target=run_wsgi, daemon=True)
    t.start()

def main():
    init_db()
    populate_whitelist()   

    klthread.start()
    obthread.start()

    # for production
    run_server()
    wxA = wxApp(False)
    wxA.MainLoop()

    # for debug in terminal

    signal.signal(signal.SIGINT, ctrlc_handler)
    # server.serve_forever()
    ctrlc_handler(0, 0)
    print("Goodbye")

if __name__ == "__main__":
	main()