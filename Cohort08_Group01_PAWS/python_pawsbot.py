# -------------------------
# PAWS TELEGRAM BOT
# @audreypotbot
# Built by Cohort 8 Group 1 for Digital World 1D Project April 2018
# -------------------------

import telepot
from telepot.loop import MessageLoop
import time

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("telepotplant-firebase-adminsdk-volhf-7becc138ca.json")
firebase_admin.initialize_app(cred, {
                              'databaseURL' : 'https://telepotplant.firebaseio.com'
                              		})

root = db.reference()
settings = root.child('settings')
temperature = root.child('temperature')
moisture = root.child('moisture')
light = root.child('light')

bot = telepot.Bot('551909737:AAHpdE4Cf-ANwhXIudWWWw4vycfAO2LiOYo')
bot.setWebhook()

url = "https://telepotplant.firebaseio.com"
token = "9AE0mIbmEP7on9h2xVDTaYv3Q63YHtwU4sOK78eq"

def returnHello(chat_id):
	bot.sendMessage(chat_id, 'Hi! I\'m Audrey the plant! 🌱')
	settings.update({'greenthumbMode': True})

def activateGreenThumb(chat_id):
	get_settings = settings.get()
	if get_settings['greenthumbMode'] == True:
		bot.sendMessage(chat_id, 'I am already in Green Thumb Mode!')
	else:
		bot.sendMessage(chat_id, 'Green Thumb Mode Activated! 💪')
		settings.update({'greenthumbMode': True})

def activateAutoMode(chat_id):
	get_settings = settings.get()
	if get_settings['greenthumbMode'] == True:
		bot.sendMessage(chat_id, 'Auto Mode Activated! 🙌')
		settings.update({'greenthumbMode': False})
	else:
		bot.sendMessage(chat_id, 'I am already in Auto Mode!')

def getTemperature(chat_id):
	snapshot = temperature.child('raw').order_by_key().limit_to_last(1).get()
	for key,v in snapshot.items():
		temp = v['temp']
		tstamp = v['time']

	ans = 'It\'s ' + str(round(temp,1)) + ' degrees out there.'
	if temp > 30:
		ans += ' That\'s pretty hot! 🔥'
	elif temp < 20:
		ans += ' It\'s a bit cold here 😷'
	ans += '\n\nLast reading: ' + time.strftime('%d/%m/%Y %H:%M', time.localtime(tstamp))
	bot.sendMessage(chat_id, ans)

def getMoisture(chat_id):
	snapshot = moisture.child('raw').order_by_key().limit_to_last(1).get()
	for key,v in snapshot.items():
		moist = v['moisture']
		tstamp = v['time']
	if moist == 1:
		ans = 'I\'m well watered 🤤'
	elif moist == 0:
		ans = 'I\'m pretty dry 😣'
	ans += '\n\nLast reading: ' + time.strftime('%d/%m/%Y %H:%M', time.localtime(tstamp))
	bot.sendMessage(chat_id, ans)

def getLight(chat_id):
	snapshot = light.child('raw').order_by_key().limit_to_last(1).get()
	for key,v in snapshot.items():
		brightness = v['light']
		tstamp = v['time']
	if brightness <= 15:
		ans = 'I\'m getting enough sunshine! 😎'
	elif brightness > 15:
		ans = 'I\'m not getting enough sunlight 😥'

	ans += '\n\nLast reading: ' + time.strftime('%d/%m/%Y %H:%M', time.localtime(tstamp))
	bot.sendMessage(chat_id, ans)

def nextWater(chat_id):
	snapshot = temperature.child('analytics').get()
	secondsToNextTime = temperature.child('predicted').get()
	lastTime = snapshot[1]
	nextTime = lastTime + secondsToNextTime
	timestamp = time.strftime('%d/%m %H:%M', time.localtime(nextTime))
	now = time.time()
	timeLeft = int((nextTime - now)/60)
	if timeLeft > 60:
		timeNext = str(int(timeLeft/60)) + " hours!"
	else:
		timeNext = str(timeLeft) + " minutes!"
	get_settings = settings.get()
	if get_settings['greenthumbMode'] == False:
		ans = "Next watering in "
	else:
		ans = "Water me in "
	ans += timeNext + " At " + timestamp + "!"
	bot.sendMessage(chat_id, ans)

def returnHelp(chat_id):
	ans = '''
Hi! I\'m Audrey the plant! 🌱

Here are some of the things I can do!
/greenthumb - Activate Green Thumb Mode
/auto - Activate Auto Watering Mode
/temperature - Get temperature reading
/moisture - Get moisture reading
/light - Get light reading
/nextwater - When next to water the plant

*What is Green Thumb Mode?*
Green Thumb mode helps plant owners build good habits of plant care by prompting them whenever the plant needs watering or other forms of care.

------------------------------
I am a project made for 10.009 1D Project
by Abi, Benedict, Ivan, Wesson, Yu Lian.
'''
	bot.sendMessage(chat_id, ans, parse_mode= 'Markdown')

command = {
	"/greenthumb": activateGreenThumb,
	"/auto": activateAutoMode,
	"/start": returnHello,
	"/temperature": getTemperature,
	"/moisture": getMoisture,
	"/light": getLight,
	"/nextwater": nextWater,
	"/help": returnHelp,
	"help": returnHelp,
}


def handle(msg):
	content_type, chat_type, chat_id = telepot.glance(msg)
	content = msg['text']

	if content_type == 'text':

		if content in command.keys():
			command[content](chat_id)

		if content[0] != '/':
			bot.sendMessage(chat_id, '🌱')


MessageLoop(bot, handle).run_as_thread()
print('Audrey is listening...')

while 1:
	time.sleep(10)
