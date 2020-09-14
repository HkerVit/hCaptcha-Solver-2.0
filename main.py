from selenium.webdriver.chrome.options import Options
from PyDictionary import PyDictionary
from selenium import webdriver
import threading
import requests
import json
import time

HEADERS = {
    'authority': 'hcaptcha.com',
    'accept': 'application/json',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://assets.hcaptcha.com',
    'sec-fetch-site': 'same-site',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'accept-language': 'en-US,en;q=0.9'
}

class hCaptcha(object):
    def __init__(self):
        self.sitekey = 'eaaffc67-ea9f-4844-9740-9eefd238c7dc'
        self.host = 'caspers.app'
        self.builder = {}
        self.c = {}
        self.starttime = time.time()

    def get_n(self, req):
        
        options = Options()
        options.headless = True
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = webdriver.Chrome(options=options)

        with open("result.js", "r") as f:
            return driver.execute_script(f.read() + f"return hsw('{req}');")

    def get_req(self):
        r = requests.get(f'https://hcaptcha.com/checksiteconfig?host={self.host}&sitekey={self.sitekey}&sc=1&swa=1')
        self.c = r.json()['c']
        return r.json()['c']['req']

    def get_payload(self):
        req = self.get_req()
        n = self.get_n(req)

        data = {
            'sitekey': self.sitekey,
            'host': self.host,
            'hl': 'en',
            'motionData': '{}',
            'n': n,
            'c': '{"type":"hsw","req":"' + req + '"}'
        }

        r = requests.post('https://hcaptcha.com/getcaptcha', headers=HEADERS, data=data)

        return r.json()
    
    def is_correct(self, obj, url, taskkey):
        while True:
            try:
                identifier = requests.post('https://www.imageidentify.com/objects/user-26a7681f-4b48-4f71-8f9f-93030898d70d/prd/urlapi', data={'image': url})
                if obj == "motorbus": obj = "bus"
                syns = PyDictionary().synonym(obj)
                for syn in syns:
                    if syn in json.dumps(identifier.json()['identify']):
                        self.builder['answers'][taskkey] = 'true'
                        return
                
                self.builder['answers'][taskkey] = 'false'
                break
            except Exception as e:
                print(identifier.text)

    def handle_images(self):
        payload = self.get_payload()
        key = payload['key']
        obj = payload['requester_question']['en'].split(' ')[-1]

        self.builder['job_mode'] = 'image_label_binary'
        self.builder['answers'] = {}
        self.builder['serverdomain'] = self.host
        self.builder['sitekey'] = self.sitekey
        self.builder['motionData'] = '{"st":' + str(int(round(time.time() * 1000))) +',"dct":' + str(int(round(time.time() * 1000))) +',"mm": []}'
        self.builder['n'] = self.get_n(self.c['req'])
        self.builder['c'] = json.dumps(self.c).replace("'", '"')

        for task in payload['tasklist']:
            taskkey = task['task_key']
            url = task['datapoint_uri']
            threading.Thread(target=self.is_correct, args=(obj, url, taskkey, )).start()
        
        while True:
            if threading.active_count() == 1:
                break
            time.sleep(0.5)
        self.submit(key)

    def submit(self, key):
        r = requests.post(
            f'https://hcaptcha.com/checkcaptcha/{key}', 
            headers = {
                'authority': 'hcaptcha.com',
                'accept': '*/*',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
                'content-type': 'application/json',
                'origin': 'https://assets.hcaptcha.com',
                'sec-fetch-site': 'same-site',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty',
                'accept-language': 'en-US,en;q=0.9'
            },
            data=json.dumps(self.builder)
        )

        if r.json()['pass'] == False:
            self.handle_images()
        else:
            print(json.dumps(r.json(), indent=4))
            endtime = time.time()
            print(endtime - self.starttime)

if __name__ == "__main__":
    Run = hCaptcha()
    Run.handle_images()