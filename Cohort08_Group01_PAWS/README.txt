
kivy_pawsdashboard.py

-Kivy User Interface displaying graphs for data collected by various sensors installed in PAWS.
-Toggle between Auto and Green Thumb Mode
-Export sensor data from firebase

Instructions
-Ensure garden file is placed under C:\Users\user\AppData\Local\Programs\Python\Python36-32\Lib\site-packages\kivy
-Insert token file path in kivy_pawsdashboard.py
-Insert url of Firebase json database download into kivy_pawsdashboard.py
-Insert file path of model.pkl into kivy_pawsdashboard.py
-Ensure png files are in the same path as kivy_pawsdashboard.py
-Ensure prerequisite modules are installed on the RPi (firebase_admin, numpy, scipy, scikit-learn, kivy)



pi_pawssensors.py

-functions that collect data from the following sensors and motor:
    		1. Light Dependent Resistor
    		2. Moisture Sensor - Hygrometer
    		3. Temperature Sensor
    		4. Servo Motor
-enables data collection at regular intervals
-state machine to collect data to build linear regression model

Instructions
-Run file on RPi
-Ensure RPi is connected to the internet
-Ensure prerequisite modules are installed on the RPi (firebase_admin)
-Ensure token file is in the same path as pi_pawssensors.py



python_pawsbot.py

-retrieve analytical data
-remotely toggle between Auto and Green Thumb Mode
-retrieve next estimated watering time

Instructions
-Ensure prerequisite modules are installed on the RPi (firebase_admin, telepot)
-Ensure token file is in the same path as python_pawsbot.py
