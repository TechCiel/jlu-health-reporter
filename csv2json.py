#!/usr/bin/env python3
import sys, csv, json

data = csv.reader(open(sys.argv[1]+'.csv', 'r'))
headers = next(data)
tasks = []

for line in data:
	line = dict(zip(headers, line))
	if line['username'] == '': continue
	task = {}
	task['username'] = line['username']
	task['password'] = line['password']
	task['fields'] = {}
	for k, v in line.items():
		if k not in ['username', 'password', 'extra']:
			task['fields'][k] = v
	exec(line['extra'])
	tasks.append(task)

conf = json.load(open(sys.argv[1]+'.json', 'r'))
conf['tasks'] = tasks
json.dump(conf, open(sys.argv[1]+'.json', 'w'), indent='\t')
