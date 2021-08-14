#!/usr/bin/env python3
import os, sys, re, json, random, logging as log, threading, requests
from time import time, sleep
DEBUG = 0#+1
CONFIG = sys.argv[1] if len(sys.argv)>1 else 'config.json' # take cli arg or default
os.chdir(os.path.dirname(os.path.abspath(__file__)))
# random delay to lower the load of ehall
RAND_DELAY = 30*60
# time between worker thread start
TASK_INTERVAL = 2
# times to retry a failed task
RETRY_UNTIL = 5*60*60
RETRY_INTERVAL = 60
# network timeout
TIMEOUT = 10

def runTask(task):
	started = time()
	while started+RETRY_UNTIL > time():
		try:
			s = requests.Session()
			s.headers.update({'Referer': 'https://ehall.jlu.edu.cn/'})
			s.verify = 'ca.crt' # False
			
			log.info('Authenticating...')
			r = s.get('https://ehall.jlu.edu.cn/sso/login', timeout=TIMEOUT)
			pid = re.search('(?<=name="pid" value=")[a-z0-9]{8}', r.text)[0]
			log.debug(f"PID: {pid}")
			postPayload = {'username': task['username'], 'password': task['password'], 'pid': pid}
			r = s.post('https://ehall.jlu.edu.cn/sso/login', data=postPayload, allow_redirects=False, timeout=TIMEOUT)

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
			sleep(RETRY_INTERVAL)
	log.error('Stop retrying, task failed!')

log.basicConfig(
	level=log.INFO-10*DEBUG,
	format='%(asctime)s %(threadName)s:%(levelname)s %(message)s'
)
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
	sleep(TASK_INTERVAL)
