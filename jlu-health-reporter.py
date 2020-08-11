#!/usr/bin/env python3
CONFIG = 'config.json'
MAX_RETRY = 30
RETRY_INTERVAL = 10
DEBUG = 0+1

import re
import json
from time import time, sleep
import urllib3
import requests
import logging
from logging import debug, info, warning, error, critical

logging.basicConfig(level=logging.INFO-10*DEBUG, format='%(asctime)s %(levelname)s %(message)s')
warning('Started.')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
config = json.load(open(CONFIG))

for user in config['users']:
	info('Processing '+user['username']+'...')
	for tries in range(MAX_RETRY):
		try:
			info('Authenticating...')
			s = requests.Session()
			s.headers.update({'Referer':'https://ehall.jlu.edu.cn/'})
			s.verify = False
			
			r = s.get('https://ehall.jlu.edu.cn/jlu_portal/login')
			pid = re.search('(?<=name="pid" value=")[a-z0-9]{8}', r.text)[0]
			debug('PID: '+pid)

			postPayload = {'username':user['username'],'password':user['password'],'pid':pid}
			r = s.post('https://ehall.jlu.edu.cn/sso/login',data=postPayload)

			info('Requesting form...')
			r = s.get('https://ehall.jlu.edu.cn/infoplus/form/'+config['transaction']+'/start')
			csrfToken = re.search('(?<=csrfToken" content=").{32}',r.text)[0]
			debug('CSRF: '+csrfToken)

			postPayload = {'idc':config['transaction'],'csrfToken':csrfToken}
			r = s.post('https://ehall.jlu.edu.cn/infoplus/interface/start',data=postPayload)
			sid = re.search('(?<=form/)\\d*(?=/render)',r.text)[0]
			debug('Step ID: '+sid)

			postPayload = {'stepId':sid,'csrfToken':csrfToken}
			r = s.post('https://ehall.jlu.edu.cn/infoplus/interface/render',data=postPayload)
			data = json.loads(r.content)['entities'][0]
			payload_1 = data['data']
			for u, v in config['fields'].items(): payload_1[u] = v
			for u, v in user['fields'].items(): payload_1[u] = v
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
			error(e)
			error('Unknown error occured!')
			sleep(RETRY_INTERVAL)

info('Exiting...')
exit()
