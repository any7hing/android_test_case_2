from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.common.mobileby import MobileBy
import pyfiglet
import frida
from time import sleep
import json

print(pyfiglet.figlet_format('script started',width=180))

capabilities = {
        'platformName': 'Android',
        'deviceName': 'Google_Pixel',
    }
url = 'http://localhost:4723/wd/hub'
driver = webdriver.Remote(url, capabilities)
driver.implicitly_wait(3)

# Подключение к устройству и запуск приложения
device = frida.get_usb_device()
digit1_btn = driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value='Inware')
digit1_btn.click()

session = device.attach("Inware")

# хукаем метод TextView.setText и отправляем данные в код
script_code = """
Java.perform(function() {
    var TextView = Java.use("android.widget.TextView");
    TextView.setText.overload('java.lang.CharSequence').implementation = function(text) {
        var data = text.toString();
        send(data);
        return this.setText(text);
        };
    });
"""


script = session.create_script(script_code)
imports = ""


def on_message(message, _data):
    #функция получает данные из приложения
    global imports
    if message["type"] == "send":
        imports+=f"|{message['payload']}"


script.on("message", on_message)
#запускаем скрипт
script.load()
#Собираем данные с вкладки "Device"
digit1_btn = driver.find_element(by=MobileBy.ANDROID_UIAUTOMATOR, value='new UiSelector().textContains("Device")')
digit1_btn.click()
for _ in range(3):
    driver.swipe(800, 1300, 800, 300, 400)
driver.press_keycode(4)

res = {}
imports = imports[1:].split('|')
try: # метод немного костыльный т.к. приложение формирует подзаголовки не с помошью setText
    res = {imports[0]:{'Basics': {imports[i]:imports[i+1] for i in range(1,len(imports[1:9]),2)},
                       'Display': {imports[i]:imports[i+1] for i in range(9, 26 ,2)},
                       'Features': {imports[i]:imports[i+1] for i in range(27, 34 ,2)},
                       'Identifiers': {imports[i]:imports[i+1] for i in range(35, 38 ,2)}}
            }
except(IndexError):
    print('Ошибка при сборе данных, попробуйте снова')
    
sleep(1)
imports = ""
#Собираем данные с вкладки "System"
digit1_btn = driver.find_element(by=MobileBy.ANDROID_UIAUTOMATOR, value='new UiSelector().textContains("System")')
digit1_btn.click()

for _ in range(3):
    driver.swipe(800, 1300, 800, 300, 400)
driver.press_keycode(4)

imports = imports[1:].split('|')
try:
    res[imports[0]] = {'OS': {imports[i]:imports[i+1] for i in range(1, 38 ,2)},
                       'Extra': {imports[i]:imports[i+1] for i in range(39, 48 ,2)}
                       } 
    res[imports[0]]['Extra'].pop('Up Time', None)
except(IndexError):
    print('Ошибка при сборе данных, попробуйте снова')
    
sleep(1)
imports = ""
#Собираем данные с вкладки "Media"
for _ in range(2):
    driver.swipe(800, 1300, 800, 300, 400)
digit1_btn = driver.find_element(by=MobileBy.ANDROID_UIAUTOMATOR, value='new UiSelector().textContains("Media")')
digit1_btn.click()
sleep(1)

imports = imports[1:].split('|')
if len(imports) < 10: # Раздела "Widevine CDM" нет на эмуляторе, только на устройствах
    try:
        res[imports[0]] = {'ClearKey CDM': {imports[i]:imports[i+1] for i in range(2, 5 ,2)}}
    except(IndexError):
        print('Ошибка при сборе данных, попробуйте снова')
else: 
    try:
        res[imports[0]] = {'Widevine CDM': {imports[i]:imports[i+1] for i in range(2, 9 ,2)},
                           'ClearKey CDM': {imports[i]:imports[i+1] for i in range(10, 13 ,2)}
                           }
    except(IndexError):
        print('Ошибка при сборе данных, попробуйте снова')
    
driver.press_keycode(4)
driver.swipe(545, 140, 540, 1700, 400)
driver.press_keycode(4)

# Завершаем скрипт
session.detach()

with open('data.json', 'w') as outfile:
    json.dump(res, outfile, indent=4)

print(pyfiglet.figlet_format('script finished, file saved', width=200))