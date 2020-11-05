#!/usr/bin/env python3
CONFIG = 'config.json'
MAX_RETRY = 15
RETRY_INTERVAL = 10
DEBUG = 0#+1

import os 
import re
import json
from sys import argv
from time import time, sleep
import logging
from logging import debug, info, warning, error, critical
import urllib3
import requests

logging.basicConfig(level=logging.INFO-10*DEBUG, format='%(asctime)s %(levelname)s %(message)s')
warning('Started.')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

os.chdir(os.path.dirname(os.path.realpath(__file__)))
if len(argv) > 1: CONFIG = argv[1]
info(f"Reading config from {format(os.path.realpath(CONFIG))}")
config = json.load(open(CONFIG))
tasks = config.get('tasks', config.get('users', [{}]))
for task in tasks:
	for k in ['username', 'password', 'transaction']:
		task.setdefault(k, config.get(k))
	for k in ['fields', 'conditions']:
		task[k] = {**config.get(k, {}), **task.get(k, {})}

for task in tasks:
	info(f"Processing {task['transaction']}:{task['username']}...")
	for tries in range(MAX_RETRY):
		if not task['transaction']:
			warning('Transaction is empty! Skipping disabled task...')
			break
		try:
			info('Authenticating...')
			s = requests.Session()
			s.headers.update({'Referer':'https://ehall.jlu.edu.cn/'})
			s.verify = False
			
			r = s.get('https://ehall.jlu.edu.cn/jlu_portal/login')
			pid = re.search('(?<=name="pid" value=")[a-z0-9]{8}', r.text)[0]
			debug(f"PID: {pid}")

			postPayload = {'username':task['username'],'password':task['password'],'pid':pid}
			r = s.post('https://ehall.jlu.edu.cn/sso/login',data=postPayload)

			info('Requesting form...')
			r = s.get(f"https://ehall.jlu.edu.cn/infoplus/form/{task['transaction']}/start")
			csrfToken = re.search('(?<=csrfToken" content=").{32}',r.text)[0]
			debug(f"CSRF: {csrfToken}")

			postPayload = {'idc':task['transaction'],'csrfToken':csrfToken}
			r = s.post('https://ehall.jlu.edu.cn/infoplus/interface/start',data=postPayload)
			sid = re.search('(?<=form/)\\d*(?=/render)',r.text)[0]
			debug(f"Step ID: {sid}")

			postPayload = {'stepId':sid,'csrfToken':csrfToken}
			r = s.post('https://ehall.jlu.edu.cn/infoplus/interface/render',data=postPayload)
			data = json.loads(r.content)['entities'][0]

			info('Submitting form...')
			for k,v in task['fields'].items():
				if eval(task['conditions'].get(k,'True')):
					data['data'][k] = v
			postPayload = {
				'actionId':1,
				'formData':json.dumps(data['data']),
				'nextUsers':'{}',
				'stepId':sid,
				'timestamp':int(time()),
				'boundFields':','.join(data['fields'].keys()),
				'csrfToken':csrfToken
			}
			debug(f"Payload: {postPayload}")
			r = s.post('https://ehall.jlu.edu.cn/infoplus/interface/doAction',data=postPayload)
			debug(f"Result: {r.text}")

			if json.loads(r.content)['ecode'] != 'SUCCEED' :
				raise Exception('The server returned a non-successful status.')
			
			info('Success!')
			break

		except Exception as e:
			error(e)
			error('Unknown error occured!')
			sleep(RETRY_INTERVAL)

info('Exiting...')
exit()
