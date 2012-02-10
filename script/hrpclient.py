#!/opt/grx/share/hrpsys/jython/hrpsyspy
import socket

import rtm
import waitInput
import bodyinfo
import OpenHRP
from OpenHRP.RobotHardwareServicePackage import SwitchStatus

def init(hostname=None):
    print "creating components"
    rtcList = createComps(hostname)

    print "connecting components"
    connectComps()

    print "activating components"
    activateComps(rtcList)

    print "initialized successfully"


def activateComps(rtcList):
    rtm.serializeComponents(rtcList)
    for r in rtcList:
        r.start()

def initRTC(module, name):
    ms.load(module)
    return ms.create(module, name)

def setJointAnglesDeg(pose, tm, wait=True):
    seq_svc.setJointAngles(bodyinfo.makeCommandPose(pose), tm)
    if wait:
        seq_svc.waitInterpolation()

def goInitial(tm=bodyinfo.timeToInitialPose):
    waitInputConfirm("!! Robot Motion Warning !! \n Push [OK] to Initial Postion ")
    setJointAnglesDeg(bodyinfo.initialPose, tm)

def initial(tm=bodyinfo.timeToInitialPose):
    setJointAnglesDeg(bodyinfo.initialPose, tm)


def goActual():
    sh_svc.goActual()

def son():
    goActual()
    if rh_svc != None:
        rh_svc.servo("all", SwitchStatus.SWITCH_ON)

def soff():
    if rh_svc != None:
        rh_svc.servo("all", SwitchStatus.SWITCH_OFF)

def loadPattern(basename, tm=3.0):
    seq_svc.loadPattern(basename, tm)

def testPattern():
    waitInputConfirm("!! Robot Motion Warning !! \n Push [OK] to execute "+bodyinfo.testPatternName)
    setJointAnglesDeg(bodyinfo.halfsitPose, bodyinfo.timeToHalfsitPose)
    goInitial(2)
    waitInputConfirm("finished")

def sit(tm=bodyinfo.timeToSitPose):
		setJointAnglesDeg(bodyinfo.sitPose, tm)
    
def halfSit(tm=bodyinfo.timeToHalfsitPose):
    setJointAnglesDeg(bodyinfo.halfsitPose, tm)

def createComps(hostname=socket.gethostname()):
    global ms, rh, rh_svc, seq, seq_svc, sh, sh_svc, servo
    ms = rtm.findRTCmanager(hostname)

    rh = rtm.findRTC("RobotHardware0")
    rh_svc = None
    if rh != None:
        rh_svc = OpenHRP.RobotHardwareServiceHelper.narrow(rh.service("service0"))
        servo = rh
    else:
        rh = rtm.findRTC(bodyinfo.modelName+"Controller(Robot)0")
        servo = rtm.findRTC("PDservo0")
    seq = initRTC("SequencePlayer", "seq")
    sh  = initRTC("StateHolder", "StateHolder0")
    seq_svc = OpenHRP.SequencePlayerServiceHelper.narrow(seq.service("service0"))
    sh_svc = OpenHRP.StateHolderServiceHelper.narrow(sh.service("service0"))
    return [rh, seq, sh]

def connectComps():
    rtm.connectPorts(rh.port("q"),          sh.port("currentQIn"))
    rtm.connectPorts(sh.port("qOut"),       seq.port("qInit"))
    rtm.connectPorts(sh.port("basePosOut"), seq.port("basePosInit"))
    rtm.connectPorts(sh.port("baseRpyOut"), seq.port("baseRpyInit"))
    rtm.connectPorts(seq.port("qRef"),      sh.port("qIn"))
    rtm.connectPorts(seq.port("baseRpy"),   sh.port("baseRpyIn"))
    if servo != None:
        rtm.connectPorts(sh.port("qOut"), servo.port("qRef"))
    else:
        rtm.connectPorts(sh.port("qOut"), rh.port("qIn"))



