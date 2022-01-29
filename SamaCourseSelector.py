# Copyright (c) 2021 Mahan Akbari.
# This file is part of Sama Course Selector
# (see https://github.com/Mahan-AK/sama-selector).
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import time
import datetime
import requests
from os import path
from selenium import webdriver
from optparse import OptionParser


parser = OptionParser(usage="python %prog -c path_to_config_file -t starting_time")
parser.add_option('-c', action="store", dest="config_file")
parser.add_option('-t', action="store", dest="action_time")

opts, args = parser.parse_args()

if not opts.config_file:
    print("You must specify the config file.")
    parser.print_usage()
    exit()

config_file = opts.config_file
action_time = opts.action_time

print("Loading config info!... ", end='')

config = {}

with open(config_file, 'r') as f:
    line = f.readline()
    
    while line:
        if line.startswith('#') or line.strip() == '':
            line = f.readline()
            continue
            
        arg = line.split('=')[0].strip()
        val = line.split('=')[1].strip()
        
        if arg != 'std_sel':
            config.update({arg:val})
        else:
            config.update({'std_sel':[]})
            line = f.readline()

            while line.strip() != ']':
                if line.startswith('#') or line.strip() == '':
                    line = f.readline()
                    continue
                    
                config['std_sel'].append(line.strip().split())
                line = f.readline()
                
        line = f.readline()
            
config['host'] = config['host'].strip('/')

print("Done")

driver = webdriver.Firefox(executable_path="./geckodriver")
driver.get(f"{config['host']}/samaweb/Login.aspx")

if action_time != "now":
    t = datetime.datetime.today()
    hour = int(action_time.split(':')[0])
    minute = int(action_time.split(':')[1])
    target_time = datetime.datetime(t.year, t.month, t.day, hour, minute)

    if datetime.datetime.now() >= target_time: action_time = "now"

print("Logging in...")

driver.find_element_by_xpath('//*[@id="UserCode"]').send_keys(config['std_num'])
if config['passwd']:
    driver.find_element_by_xpath('//*[@id="KeyCode"]').send_keys(config['passwd'])
    if action_time == "now": driver.find_element_by_xpath('//*[@id="input"]').click()
else:
    print("You have not provided a password!")
    print("Please fill the password field.")
    if action_time == "now": print("Press enter when done...")

if action_time != "now":
    print(f"Waiting until {action_time}...")
    
    t = datetime.datetime.today()
    hour = int(action_time.split(':')[0])
    minute = int(action_time.split(':')[1])
    target_time = datetime.datetime(t.year, t.month, t.day, hour, minute)
    
    while True:
        if datetime.datetime.now() < target_time - datetime.timedelta(minutes=2):
            print(f"{int((target_time - datetime.datetime.now()).total_seconds() // 60)+1} minutes until action...", end='\r')
            time.sleep(60)
        elif datetime.datetime.now() < target_time:
            print(f"{int((target_time - datetime.datetime.now()).total_seconds())} seconds until action...", end='\r')
            time.sleep(1)
        else:
            time.sleep(10)
            print('\x1b[2K' + "Time's up! Starting selection procedure...")            
            driver.find_element_by_xpath('//*[@id="input"]').click()
            break

print("Getting cookies... ", end='')

while True:
    if driver.get_cookie('ASP.NET_SessionId') and driver.get_cookie('.ASPXAUTH'):
        print("Done")
        driver.execute_script("window.stop();")
        break

# print(f"Current Cookies: {[c['name'] for c in driver.get_cookies()]}")

print("Submitting selection request...")

header_str = f"""Content-Length: 155
Cache-Control: max-age=0
Sec-Ch-Ua: " Not A;Brand";v="99", "Chromium";v="92"
Sec-Ch-Ua-Mobile: ?0
Upgrade-Insecure-Requests: 1
Origin: {config['host']}
Content-Type: application/x-www-form-urlencoded
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: navigate
Sec-Fetch-User: ?1
Sec-Fetch-Dest: document
Referer: {config['host']}/samaweb/StuUnitSelection.asp
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9
Connection: close"""

url = f"{config['host']}/samaweb/StuUnitSelection.asp"
headers = {h.split(': ')[0]:h.split(': ')[1] for h in header_str.split('\n')}
cookies = {c['name']:c['value'] for c in driver.get_cookies()}

codes = '%3B'.join([x[0] for x in config['std_sel']])
groups = '%3B'.join([x[1] for x in config['std_sel']])

data = f"insView=4&LessonRegisterStatus=0&strLessonSelections={codes}&strGroupSelections={groups}&strSelectSelections=&StNo={config['std_num']}&TermCode={config['term']}".encode()

res = requests.post(url, headers=headers, cookies=cookies, data=data)

if res.status_code == 200: print("Selection seems to be successfull!")

res_file = f"{config['std_num']}.html"
with open(res_file, 'wb') as f:
    f.write(res.content)

driver.get(f"file://{path.abspath(res_file)}")