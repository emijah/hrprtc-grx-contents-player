import os
import time
import thread
import threading

class SoundManager:
  def __init__(self):
    self.playList = []
    self.timeList = []
    self.isPlaying = False

  def playListFunc(self):
    if self.isPlaying:
      return
    self.isPlaying = True
    startTime = time.time()
    for i in range(len(self.playList)):
      playFile  = self.playList[i]
      timeLine = self.timeList[i]
      timeToStart = timeLine - (time.time() - startTime)
      if timeToStart > 0.01:
          time.sleep(timeToStart)
      diff = (time.time() - startTime) - timeLine
      print 'timeline(diff.)[s] = %7.2f(%7.2f) : play '%(timeLine, diff) + playFile
      os.system("aplay -q " + playFile)
    self.playList = []
    self.timeList = []
    self.isPlaying = False

  def play(self, filename = None, sync = False):
    if filename != None: 
      self.playList.append(filename)
    if not self.isPlaying:
      thread.start_new_thread(self.playListFunc, ())
    if sync:
      self.sync()

  def append(self, filename, timeLine = 0.0):
    if self.isPlaying == False:
      self.playList.append(filename)
      self.timeList.append(timeLine)
  
  def stop(self):
    os.system("killall -9 aplay") 

  def clear(self):
    self.playList = []

  def sync(self):
    while len(self.playList) > 0:
      time.sleep(0.010)

  def mute():
    os.system("amixer -c 0 set PCM off")

  def setVolume(val = 100):
    os.system("amixer -c 0 set PCM on %3d" %val)

if __name__ == '__main__':
  sound1="/home/fujii/export/sHrpsys/robot/TAIZO2/demo/speech/B06.wav"
  sm = SoundManager()
  sm.play(sound1)
  sm.play(sound1)
  time.sleep(1)
  sm.stop()
  sm.clear()
  sm.play(sound1)
  sm.sync()
