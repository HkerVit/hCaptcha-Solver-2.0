from selenium.webdriver.chrome.options import Options
from PyDictionary import PyDictionary
from colorama import Fore, init
from selenium import webdriver
import numpy as np
import cvlib as cv
import requests
import json
import time
import cv2


init(convert=True)

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
                image = requests.get(url)
                nparr = np.frombuffer(image.content, np.uint8)
                im = cv2.imdecode(nparr, flags=1)
                objects = cv.detect_common_objects(im, confidence=0.5, nms_thresh=1, enable_gpu=False)[1]
                if obj.lower() in objects:
                    print(f'{Fore.GREEN}[{Fore.WHITE}INFO{Fore.GREEN}] {Fore.CYAN}{taskkey}.jpg is a {obj}')
                    self.builder['answers'][taskkey] = 'true'
                    return
                print(f'{Fore.GREEN}[{Fore.WHITE}INFO{Fore.GREEN}] {Fore.CYAN}{taskkey}.jpg is not a {obj}')
                self.builder['answers'][taskkey] = 'false'
                break
            except Exception as e:
                print(f"{Fore.RED}[{Fore.WHITE}ERROR{Fore.RED}] Unexpected error: {Fore.WHITE}{e}")

    def handle_images(self):
        payload = self.get_payload()
        print(f"{Fore.GREEN}[{Fore.WHITE}INFO{Fore.GREEN}]{Fore.CYAN} Received payload")
        key = payload['key']
        obj = payload['requester_question']['en'].split(' ')[-1].replace("motorbus", "bus")

        self.builder['job_mode'] = 'image_label_binary'
        self.builder['answers'] = {}
        self.builder['serverdomain'] = self.host
        self.builder['sitekey'] = self.sitekey
        self.builder['motionData'] = '{"st":' + str(int(round(time.time() * 1000))) +',"dct":' + str(int(round(time.time() * 1000))) +',"mm": []}'
        self.builder['n'] = self.get_n(self.c['req'])
        self.builder['c'] = json.dumps(self.c).replace("'", '"')
        print(f'{Fore.GREEN}[{Fore.WHITE}INFO{Fore.GREEN}] {Fore.CYAN}{str(len(payload["tasklist"]))} images retrieved...')
        for task in payload['tasklist']:
            taskkey = task['task_key']
            url = task['datapoint_uri']
            self.is_correct(obj, url, taskkey)
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

        if r.json()['pass']:
            print(f"{Fore.GREEN}[{Fore.WHITE}PASSED{Fore.GREEN}] {Fore.CYAN}hCaptcha has been solved...")
            print(f"{Fore.GREEN}[{Fore.WHITE}KEY{Fore.GREEN}] {Fore.CYAN}UUID:\n{Fore.LIGHTBLACK_EX}" + r.json()['generated_pass_UUID'])
            endtime = time.time()
            print(f"{Fore.GREEN}[{Fore.WHITE}INFO{Fore.GREEN}] {Fore.CYAN}Time taken: {str(round(endtime - self.starttime))}s")
        else:
            print(f"{Fore.RED}[{Fore.WHITE}FAIL{Fore.RED}] Retrying...")
            self.handle_images()

if __name__ == "__main__":
    Run = hCaptcha()
    Run.handle_images()
