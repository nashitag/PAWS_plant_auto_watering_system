from __future__ import division
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder
from kivy.uix.image import Image
from kivy.core.window import Window
from threading import Thread
from kivy.network.urlrequest import UrlRequest
from kivy.garden import MeshLinePlot
from kivy.properties import NumericProperty
from kivy.properties import StringProperty
from kivy.clock import Clock
from firebase_admin import credentials
from firebase_admin import db
from sklearn import linear_model
import pickle
import numpy as np
import firebase_admin
import os
import zipfile
import time


'''gain access to firebase database'''
cred = credentials.Certificate(r"INSERT FIREBASE JSON FILEPATH HERE")  # Insert the filepath where the firebase json file is located at
firebase_admin.initialize_app(cred, {'databaseURL': 'https://telepotplant.firebaseio.com'})
roots = db.reference()
settings = roots.child('settings')
temperature = roots.child('temperature')
moisture = roots.child('moisture')
light = roots.child('light')

'''Url to download from and the name of the file in the drive'''
ZIP_URL = 'https://telepotplant.firebaseio.com/.json?print=pretty&format=export&download=telepotplant-export.json&auth=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1MjQwNDM0MDYsImV4cCI6MTUyNDA0NzAwNiwidiI6MCwiYWRtaW4iOnRydWV9.kPPLCT1pqbbW0W6FM230OFAQJgFz1Mp-yQyNL8z6Gqs'
# Insert url that allows for download of the json file of the database in firebase. If download is unsuccessful, it means that the link has expired. Login to Firebase to retrieve a new link.
ZIP_FILENAME = 'telepotplant-export.json'


def get_data():
    '''get data from firebase continuously'''
    global moisture1
    global temp1
    global light1
    global timing

    moisture1 = [0]
    temp1 = [0]
    light1 = [0]


    while True:
        '''Constantly updates plant data in the graph to the most recent value'''
        light_data = light.child('raw').order_by_key().get()
        light1 = [(-1*light_data[i]['light']+180) for i in light_data][-160:]

        moisture_data = moisture.child('raw').order_by_key().get()
        moisture1 = [moisture_data[i]['moisture'] for i in moisture_data][-160:]

        temperature_data = temperature.child('raw').order_by_key().get()
        temp1 = [temperature_data[i]['temp'] for i in temperature_data][-160:]


class Logic(BoxLayout):
    current_timing = NumericProperty()
    countdown = StringProperty()
    moisture_picture = StringProperty()
    temp_picture = StringProperty()
    light_picture = StringProperty()

    def __init__(self, **kwargs):
        super(Logic, self).__init__()
        self.plot = MeshLinePlot(color=[0, 1, 0, 1])  # Plot a graph
        self.plot2 = MeshLinePlot(color=[1, 1, 0, 1])  # Plot a graph
        self.plot3 = MeshLinePlot(color=[0, 3, 10, 1])  # Plot a graph
        self.current_timing = self.machine()
        self.countdown = "Water me in: \n{}H:{}M:{}S".format(self.current_timing//3600,self.current_timing%3600//60,self.current_timing%3600%60)
        self.moisture_picture = 'moisture.png'
        self.temp_picture = 'temperature.png'
        self.light_picture = 'light.png'
        Clock.schedule_interval(self.picture_content, 3)  # Updates the plant status every 3 sec
        Clock.schedule_interval(self.timer, 1)  # Initiates a countdown timer

    def machine(self):
        '''Machine learning via Linear Regression to predict the time left before the next watering session'''
        modelpickle = r'INSERT FILEPATH OF MODEL.PKL HERE'  # Insert the filepath of model.pkl here
        with open(modelpickle, 'rb') as f:
            model = pickle.load(f)
        testX = temperature.child('analytics').get()[0]
        timing = int(model.predict(testX))
        return timing*60

        temperature.update({'predicted': timing*60})  # Updates the predicted timing to firebase

    def start(self):
        '''Starts updating the graph every 1 sec. Data retrieved via get_data.'''
        self.ids.graph.add_plot(self.plot)
        self.ids.graph2.add_plot(self.plot2)
        self.ids.graph3.add_plot(self.plot3)
        Clock.schedule_interval(self.get_value, 1)

    def stop(self):
        '''Stops updating the graph'''
        Clock.unschedule(self.get_value)

    def get_value(self, dt):
        '''Get data from firebase. Data points to be displayed on the graph'''
        self.plot.points = [(0.625*i, j) for i, j in enumerate(temp1)]
        self.plot2.points = [(0.625*i, j) for i, j in enumerate(light1)]
        self.plot3.points = [(0.625*i, j) for i, j in enumerate(moisture1)]

    def switch_on(self, instance, value):
        '''Changes the state of greenthumbMode between on/off'''
        global a
        a = settings.child('greenthumbMode').get()
        if a is False:
            print("Switch On")
            settings.update({'greenthumbMode': True})
            print(True)
        else:
            print("Switch Off")
            settings.update({'greenthumbMode': False})
            print(False)

    def Bool(self):
        '''Display the initial state of greenthumbMode when app is launched'''
        return settings.child('greenthumbMode').get()

    def download_content(self):
        '''Download content via url'''
        self.ids["download_button"].disabled = True
        req = UrlRequest(ZIP_URL, on_progress=self.update_progress,
                         chunk_size=1024, on_success=self.unzip_content,
                         file_path=ZIP_FILENAME)

    def update_progress(self, request, current_size, total_size):
        '''Progress of the progress bar'''
        self.ids['download_progress_bar'].value = current_size / total_size

    def unzip_content(self, req, result):
        '''Unzips content'''
        Thread(target=self.unzip_thread).start()

    def unzip_thread(self):
        '''Unzips thread'''
        print("Unzipping file")
        fh = open(ZIP_FILENAME, 'rb')
        z = zipfile.ZipFile(fh)
        ZIP_EXTRACT_FOLDER = ZIP_FILENAME + '_extracted'
        if not os.path.exists(ZIP_EXTRACT_FOLDER):
            os.makedirs(ZIP_EXTRACT_FOLDER)
        z.extractall(ZIP_EXTRACT_FOLDER)
        fh.close()
        os.remove(ZIP_FILENAME)  # removes downloaded file if it is alreaday in the drive

        print("Done")

    def timer(self, interval):
        '''Counts countdown timer'''
        self.current_timing = self.current_timing-1
        self.countdown = "Water me in: \n{}H:{}M:{}S".format(self.current_timing//3600,self.current_timing%3600//60,self.current_timing%3600%60)

    def picture_content(self, interval):
        '''Display different pictures based on the plant status'''
        if temp1[-1] >= 35:
            self.temp_picture = 'hottemp.png'  # hot
        elif temp1[-1] >= 22:
            self.temp_picture = 'normaltemp.png'  # normal
        else:
            self.temp_picture = 'coldtemp.png'  # cold

        if light1[-1] >= 75:
            self.light_picture = 'sunon.png'  # bright
        else:
            self.light_picture = 'sunoff.png'  # dark

        if moisture1[-1] == 1:
            self.moisture_picture = 'wateron.png'  # wet
        else:
            self.moisture_picture = 'wateroff.png'  # dry


    def exitclk(self):
        '''Exits app'''
        App.get_running_app().stop()
        Window.close()


class Paws(App):
    def build(self):
        return Builder.load_string(
"""
Logic:
    BoxLayout:
        orientation: "vertical"
        BoxLayout:
            orientation:'horizontal'
            size_hint:[1,.4]
            Image:
                source: "logo.png"
                allow_stretch: False
                keep_ratio: True

            Image:
                source: root.temp_picture
                allow_stretch: False
                keep_ratio: True

            Image:
                source: root.light_picture
                allow_stretch: False
                keep_ratio: True

            Image:
                source: root.moisture_picture
                allow_stretch: False
                keep_ratio: True

        BoxLayout:
            BoxLayout:
                size_hint: [.4, 1]
                Graph:
                    id: graph
                    ymin:20
                    ymax:50
                    xlabel: "Time"
                    ylabel: "Temperature"

            BoxLayout:
                size_hint: [.4, 1]
                Graph:
                    ymin:-30
                    ymax:175
                    id: graph2
                    xlabel: "Time"
                    ylabel: "Light"

        BoxLayout:
            BoxLayout:
                size_hint: [.4, 1]
                Graph:
                    id: graph3
                    ymin:-1
                    ymax:2
                    xlabel: "Time"
                    ylabel: "Moisture"

                Label:
                    text:str(root.countdown)

        BoxLayout:
            size_hint: [1, .2]
            orientation: "horizontal"

            Button:
                text: "Start"
                bold: True
                on_press: root.start()

            Button:
                text: "Stop"
                bold: True
                on_press: root.stop()

            BoxLayout:
                orientation: 'vertical'
                Label:
                    text: 'GreenThumb Mode'

                Switch:
                    text: 'GreenThumb Mode'
                    id: switch_id
                    active: root.Bool()
                    on_active:
                        root.switch_on(self, self.active)

            BoxLayout:
                orientation: 'vertical'
                Button:
                    size_hint:[1,.8]
                    id: download_button
                    text: "Export"
                    on_press: root.download_content()

                ProgressBar:
                    size_hint: [1,.2]
                    id: download_progress_bar
                    max: 1
                    value: 0
            Button:
                size_hint: [1, 1]
                text: 'Exit'
                on_press:
                    root.exitclk()
                """)


if __name__ == "__main__":
    moisture1 = []
    temp1 = []
    light1 = []
    get_level_thread = Thread(target=get_data)
    get_level_thread.start()
    Paws().run()
