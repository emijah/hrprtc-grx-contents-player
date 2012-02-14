#!/opt/grx/share/hrpsys/jython/hrpsyspy
import os,sys
import time
import socket
import thread
import random
#import select
from select import cpython_compatible_select as select
import traceback
from org.yaml.snakeyaml import Yaml
import codecs

import hrpclient
import sound

interpret_flag = True
playRate_ = 1.0
AFTER_ACTION_INTERVAL = 1.0 # [s]

DEFAULT_SCENARIO_DIR = ''
DEFAULT_COMMANDLIST = DEFAULT_SCENARIO_DIR + 'commandList.yaml'
EXTRA_COMMANDLIST = DEFAULT_SCENARIO_DIR + 'extraCommandList.yaml'

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 11000

commandList_ ={}
actionBuffer_ = {}
systemCommandList_ = {
	'seat':    ['-', 					'send msg to seat : seat [STATE NAME]'],
	'goa':     ['hrpclient.goActual()',	'goActual'],
#	'temp':    ['hrpclient.temp()',		'check motor temp. see hrpsys output'],
#	'volt':    ['hrpclient.voltage()',	'check voltage . see hrpsys output'],
#	'read':    ['hrpclient.readData()',	'get status of the robot'],
	'son':     ['hrpclient.son()', 		'Servo On'],
	'soff':    ['hrpclient.soff()', 	'Servo Off'],
	'sit':     ['../motion/sit.pseq',	'move to sit pose'],
	'halfsit': ['hrpclient.halfSit()', 	'harf sit pose'],
	'norm':    ['setPlayRate(1.0)',		'play motion in 1/1'],
	'slow':    ['setPlayRate(0.5)',		'play motion in 1/2'],
	'sslow':   ['setPlayRate(0.25)',	'play motion in 1/4'],
	'load':    ['loadList()','Load command list'],
	'exit':    ['exit()',				'Exit'],
	'help':    ['help()', 				'Show this help'],
	'?':       ['help()', 				'Show this help'],
	'h':       ['help()', 				'Show this help'],
}

#日本語(UTF-8)出力設定
sys.stdout = codecs.getwriter('utf_8')(sys.stdout)

def exit():
	global interpret_flag
	interpret_flag = False

def setPlayRate(playRate):
	global playRate_
	if 0.1 <= playRate and playRate <= 1:
		playRate_ = playRate
		print 'play rate = ' + str(playRate_)
		loadList(doClean=True)

def help(commandList = commandList_):
	n = 0
	keys = commandList_.keySet()
	print "Demo Command Menu"
	print "-----------+-------------------------"
	for key in commandList_.keySet():
		val = commandList_.get(key)
		print "%-10s : %-s"%(key, val[1])
	print "-----------+-------------------------"
	for key in systemCommandList_:
		val = systemCommandList_[key]
		print "%-10s : %-s"%(key, val[1])
	print "-----------+-------------------------"

def loadList(fname = DEFAULT_COMMANDLIST,  backGround = False, doClean = False):
	fin = open(fname)
	comList = Yaml().load(fin)
	fin.close()
	if backGround:
		thread.start_new_thread(updateActionBuffer, (comList, doClean))
	else:
		updateActionBuffer(comList, doClean)
	return comList

def saveList(fname = DEFAULT_COMMANDLIST, comList = commandList_):
	fout = open(fname)
	Yaml().dump(comList, fout)
	fout.close()

def updateActionBuffer(comList = commandList_, doClean = False):
	global actionBuffer_
	if doClean:
		actionBuffer_.clear()
	for com in comList.entrySet():
	  val = com.getValue()
	  commandPath = DEFAULT_SCENARIO_DIR + val[0]
	  if actionBuffer_.has_key(commandPath):
	  	continue
	  if os.path.isfile(commandPath):
	  	print 'processing ... ' + commandPath
	  	actionBuffer_[commandPath] = makeActionList(commandPath, 0.0)

def makeActionList(fname, timeOffset = 0.0):
	global playRate_
	if actionBuffer_.has_key(fname):
		return actionBuffer_[fname]
	print 'load: ' + fname
	fin = open(fname)
	a = Yaml().load(fin.read())
	fin.close()
	type = a['type']
	name = a['name']
	refs = a['refs']

	actionList  = list()
	timeList = list()
	for ref in refs:
		timeLine = ref['time'] + timeOffset
		contents = ref['refer']
		if contents.__class__.__name__ == 'str': # play sound or refer another file
			aa = contents.find('#')
			if aa > 0:
			  cbuf = contents.split('#')
			  contents = cbuf[0].rstrip()
			if contents.endswith('.wav'):
				actionList.append(contents)
				timeList.append(timeLine)
			elif contents.endswith('.pseq'):
				al, tl = makeActionList(contents, timeLine)
				actionList += al
				timeList   += tl
			else:
				print 'unknown file format ( ' + contents + ' )'
		else: # execute motion
			vals = ' '.join(map(str, contents['values']))
			timeToTransition = contents['transition-time'] / playRate_
			actionList.append(vals + ' ' + str(timeToTransition))
			timeList.append(timeLine)

	return actionList,timeList

def execCommand(com):
	global commandList_ ,systemCommandList_
	
	if com.strip() == '':
		return 

	if com.startswith('seat '):
		msg = com.split()[1]
		sendMsgToSeat(msg + '\n')
		return

	#if com.isdigit():
	#	com = int(com)
	
	if commandList_.containsKey(com):
		com = commandList_[com][0]

	elif systemCommandList_.has_key(com):
		com = systemCommandList_[com][0]

	if os.path.isfile(DEFAULT_SCENARIO_DIR + str(com)):
		execFile(DEFAULT_SCENARIO_DIR + str(com))
	else:
		try:
			#if com.endswith(")"):
			#	val =  eval(com)
			#	if val is not None: 
			#		print val
			#else:
			exec(com)
		except:
			traceback.print_exc(file=sys.stdout)

def execFile(fname):
	global actionBuffer_, sndManager
	print 'scene: ' + fname
	al, tl = makeActionList(fname)
	for action, timeLine in zip(al,tl):
		if action.endswith('.wav'):
			sndManager.append(action, timeLine)
	startTime = time.time()
	sndManager.play()
	for action, timeLine in zip(al,tl):
		if action.endswith('.wav'):
			continue
		timeToStart = timeLine - (time.time() - startTime)
		if timeToStart > 0.01:
			time.sleep(timeToStart)
		diff = (time.time() - startTime) - timeLine
		dat = action.split()
		alist = list()
		for i in range(22):
			alist.append(float(dat[i]))
		atm = float(dat[22])
		hrpclient.setJointAnglesDeg(alist, atm)
		print 'timeline(diff.)[s] = %7.2f(%7.2f) : play motion'%(timeLine, diff)
	sndManager.sync()

def SocketRecvLoop(host = DEFAULT_HOST, port = DEFAULT_PORT):
	global clientsock
	while interpret_flag:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind((host, port))
		s.listen(1)
		while True:
			print 'SocketRecvLoop: Waiting for connections...'
			clientsock, clientaddr = s.accept()
			print 'SocketRecvLoop: Accept the connection'
			rcvmsg = ''
			while True:
				time.sleep(1)
				r, w, x = select([clientsock,], [], [], 0.01)
				if len(r) != 0:
					rcvmsg = clientsock.recv(1024)
					print "skipping buffered input %s" % rcvmsg
				
				rcvmsg = clientsock.recv(1024)
				if len(rcvmsg) == 0:
					break
				rcvmsg = rcvmsg.rstrip('\n')
				rcvmsg = rcvmsg.rstrip('\r')
				print 'Recevied ->[%s]' %(rcvmsg)
				execCommand(rcvmsg)
			clientsock.close()

def sendMsgToSeat(msg, doShow = True):
	global clientsock
	if doShow:
		print msg
	clientsock.send(msg+'\n')

def main(argv = None):
	if argv == None: argv = sys.argv
	global sndManager, commandList_, systemCommandList_

	thread.start_new_thread(SocketRecvLoop, (DEFAULT_HOST, DEFAULT_PORT))

	sndManager = sound.SoundManager()

	if len(sys.argv) > 1:
		commandList_ = loadList(sys.argv[1], backGround = False)
	else:
		commandList_ = loadList(backGround = False)

	try:
	  hrpclient.init()
	except:
		traceback.print_exc(file=sys.stdout)
		print 'Init hrpclient error'

	help()	

	while interpret_flag:
		execCommand(raw_input('> '))

try:
    import readline
    import rlcompleter
    import atexit
    _historyPath = os.path.expanduser('~/.pyhistory')
    def _save_history(historyPath=_historyPath):
        readline.write_history_file(historyPath)
    if os.path.exists(_historyPath):
        readline.read_history_file(_historyPath)
    atexit.register(_save_history)
    del _historyPath, _save_history
except (ImportError, TypeError):
    pass
else:
    readline.parse_and_bind("tab: complete")
    print "else"

if __name__ == '__main__':
	sys.exit(main())

