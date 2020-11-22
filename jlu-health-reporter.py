#!/usr/bin/env python3
import os, sys, re, json, random, logging as log, threading, urllib3, requests
from time import time, sleep
DEBUG = 0#+1
CONFIG = sys.argv[1] if len(sys.argv)>1 else 'config.json' # take cli arg or default
CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG) # relative to file
# times to retry a failed task
RETRIES = 500
# network timeout & retry interval
TIMEOUT = 10
# time between worker thread start
INTERVAL = 2
# random delay to lower the load of ehall
RAND_DELAY = 30*60

def runTask(task):
	for _ in range(RETRIES):
		try:
			s = requests.Session()
			s.headers.update({'Referer': 'https://ehall.jlu.edu.cn/'})
			s.verify = False
			
			log.info('Authenticating...')
			r = s.get('https://ehall.jlu.edu.cn/jlu_portal/login', timeout=TIMEOUT)
			pid = re.search('(?<=name="pid" value=")[a-z0-9]{8}', r.text)[0]
			log.debug(f"PID: {pid}")
			postPayload = {'username': task['username'], 'password': task['password'], 'pid': pid}
			r = s.post('https://ehall.jlu.edu.cn/sso/login', data=postPayload, timeout=TIMEOUT)

			log.info('Requesting form...')
			r = s.get(f"https://ehall.jlu.edu.cn/infoplus/form/{task['transaction']}/start", timeout=TIMEOUT)
			csrfToken = re.search('(?<=csrfToken" content=").{32}', r.text)[0]
			log.debug(f"CSRF: {csrfToken}")
			postPayload = {'idc': task['transaction'], 'csrfToken': csrfToken}
			r = s.post('https://ehall.jlu.edu.cn/infoplus/interface/start', data=postPayload, timeout=TIMEOUT)
			sid = re.search('(?<=form/)\\d*(?=/render)', r.text)[0]
			log.debug(f"Step ID: {sid}")
			postPayload = {'stepId': sid, 'csrfToken': csrfToken}
			r = s.post('https://ehall.jlu.edu.cn/infoplus/interface/render', data=postPayload, timeout=TIMEOUT)
			data = json.loads(r.content)['entities'][0]

			log.info('Submitting form...')
			for k, v in task['fields'].items():
				if eval(task['conditions'].get(k, 'True')):
					data['data'][k] = v
			postPayload = {
				'actionId': 1,
				'formData': json.dumps(data['data']),
				'nextUsers': '{}',
				'stepId': sid,
				'timestamp': int(time()),
				'boundFields': ','.join(data['fields'].keys()),
				'csrfToken': csrfToken
			}
			log.debug(f"Payload: {postPayload}")
			r = s.post('https://ehall.jlu.edu.cn/infoplus/interface/doAction', data=postPayload, timeout=TIMEOUT)
			log.debug(f"Result: {r.text}")
			if json.loads(r.content)['ecode'] != 'SUCCEED' :
				raise Exception('The server returned a non-successful status.')
			log.info('Success!')
			return
		except Exception as e:
			log.error(e)
			sleep(TIMEOUT)
	log.error('Failed too many times, exiting...')

log.basicConfig(
	level=log.INFO-10*DEBUG,
	format='%(asctime)s %(threadName)s:%(levelname)s %(message)s'
)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
log.warning('Started.')
try:
	log.info('Press Control-C to skip random delay...')
	sleep(random.random()*RAND_DELAY)
except KeyboardInterrupt:
	pass

log.info(f'Reading config from {CONFIG}')
config = json.load(open(CONFIG))
for task in config.get('tasks', config.get('users', [{}])):
	for k in ['username', 'password', 'transaction']:
		task.setdefault(k, config.get(k))
	for k in ['fields', 'conditions']:
		task[k] = {**config.get(k, {}), **task.get(k, {})}
	if task['transaction']:
		threading.Thread(
			target=runTask,
			name=f"{task['transaction']}:{task['username']}",
			args=(task,)
		).start()
	sleep(INTERVAL)
