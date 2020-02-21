#!/usr/bin/env python3
USERS = [('zhaoyy2119', 'PASSWORD')]
# USERNAME and USERPASS are deprecated now for multi-user support
USERNAME = 'zhaoyy2119'
USERPASS = 'PASSWORD'
INTERVAL = 86400 
MAX_RETRY = 30
RETRY_INTERVAL = 20
TRANSACTION = 'JLDX_BK_XNYQSB' # 'JLDX_YJS_XNYQSB'git
DEBUG = 0#+1

import re
from sys import argv
import json
from time import time, sleep
import urllib3
import requests
import logging
from logging import debug, info, warning, error, critical

logging.basicConfig(level=logging.INFO-10*DEBUG, format='%(asctime)s %(levelname)s %(message)s')
warning('Started.')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
if USERS is None: USERS = [(USERNAME, USERPASS)]

while True: # main loop
	for USERNAME, USERPASS in USERS:
		for tries in range(0, MAX_RETRY):
			try:
				info('User: '+USERNAME)
				info('Authenticating...')
				s = requests.Session()
				s.headers.update({'Referer':'https://ehall.jlu.edu.cn/'})
				s.verify = False
				
				r = s.get('https://ehall.jlu.edu.cn/jlu_portal/login')
				pid = re.search('(?<=name="pid" value=")[a-z0-9]{8}', r.text)[0]
				debug('PID: '+pid)

				postPayload = {'username':USERNAME,'password':USERPASS,'pid':pid}
				r = s.post('https://ehall.jlu.edu.cn/sso/login',data=postPayload)

				info('Requesting form...')
				r = s.get('https://ehall.jlu.edu.cn/infoplus/form/'+TRANSACTION+'/start')
				csrfToken = re.search('(?<=csrfToken" content=").{32}',r.text)[0]
				debug('CSRF: '+csrfToken)

				postPayload = {'idc':TRANSACTION,'csrfToken':csrfToken}
				r = s.post('https://ehall.jlu.edu.cn/infoplus/interface/start',data=postPayload)
				sid = re.search('(?<=form/)\\d*(?=/render)',r.text)[0]
				debug('Step ID: '+sid)

				postPayload = {'stepId':sid,'csrfToken':csrfToken}
				r = s.post('https://ehall.jlu.edu.cn/infoplus/interface/render',data=postPayload)
				data = json.loads(r.content)['entities'][0]
				payload_1 = data['data']
				payload_1['fieldCNS'] = True
				payload_1 = json.dumps(payload_1)
				debug('DATA: '+payload_1)
				payload_2 = ','.join(data['fields'].keys())
				debug('FIELDS: '+payload_2)

				info('Submitting form...')
				postPayload = {
					'actionId':1,
					'formData':payload_1,
					'nextUsers':'{}',
					'stepId':sid,
					'timestamp':int(time()),
					'boundFields':payload_2,
					'csrfToken':csrfToken
				}
				r = s.post('https://ehall.jlu.edu.cn/infoplus/interface/doAction',data=postPayload)
				debug(r.text)

				if json.loads(r.content)['ecode'] != 'SUCCEED' :
					raise Exception('The server returned a non-successful status.')
				
				info('Success!')
				break

			except Exception as e:
				warning(e)
				if tries+1 == MAX_RETRY :
					error('Failed too many times! Skipping...')
					break
				error('Unknown error occured, retrying...')
				sleep(RETRY_INTERVAL)

	if len(argv) > 1 and argv[1] == '--once' :
		info('Exiting...')
		exit()

	info('Waiting for next run...')
	sleep(INTERVAL)
