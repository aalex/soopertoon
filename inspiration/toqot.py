from PyQt4.QtCore import *
from PyQt4.QtGui import *
import liblo
import sys
from myLogger import *

OSC_SERVER_PORT = "1234"
SOOPERLOOPER_SERVER_PORT = 9951

class Emitter(QObject):
  def __init__(self, parent = None):
    super(Emitter, self).__init__(parent)

  def emitM(self, signal, arg1, arg2=None):
    self.emit(SIGNAL(signal), arg1, arg2)

class OscServer(liblo.ServerThread):
  def __init__(self, loop = "0"):
    liblo.ServerThread.__init__(self, OSC_SERVER_PORT)
    self.target = liblo.Address(SOOPERLOOPER_SERVER_PORT)
    self.emitter = Emitter()

  def initOsc(self, loop = 0):
    liblo.send(self.target, '/ping', 'osc.udp://localhost:%s' % OSC_SERVER_PORT, '/loopcount')
    liblo.send(self.target, '/sl/%s/get' % loop, 'state', 'osc.udp://localhost:%s' % OSC_SERVER_PORT, '/loopstate')
    liblo.send(self.target, '/sl/%s/get' % loop, 'wet', 'osc.udp://localhost:%s' % OSC_SERVER_PORT, '/loopvelocity')
    liblo.send(self.target, '/sl/%s/get' % loop, 'cycle_len', 'osc.udp://localhost:%s' % OSC_SERVER_PORT, '/cyclelen')
    liblo.send(self.target, '/sl/%s/get' % loop, 'loop_len', 'osc.udp://localhost:%s' % OSC_SERVER_PORT, '/looplen')
    liblo.send(self.target, '/sl/%s/register_auto_update' % loop, 'loop_pos', 100, 'osc.udp://localhost:%s' % OSC_SERVER_PORT, '/looppos')
    liblo.send(self.target, '/sl/%s/register_auto_update' % loop, 'wet', 100, 'osc.udp://localhost:%s' % OSC_SERVER_PORT, '/loopvelocity')
    liblo.send(self.target, '/sl/%s/register_auto_update' % loop, 'state', 100, 'osc.udp://localhost:%s' % OSC_SERVER_PORT, '/loopstate')
    liblo.send(self.target, '/sl/%s/register_auto_update' % loop, 'next_state', 100, 'osc.udp://localhost:%s' % OSC_SERVER_PORT, '/loopnextstate')
    liblo.send(self.target, '/sl/%s/register_auto_update' % loop, 'cycle_len', 100, 'osc.udp://localhost:%s' % OSC_SERVER_PORT, '/cyclelen')
    liblo.send(self.target, '/sl/%s/register_auto_update' % loop, 'loop_len', 100, 'osc.udp://localhost:%s' % OSC_SERVER_PORT, '/looplen')
    liblo.send(self.target, '/register_auto_update', 'selected_loop_num', 100, 'osc.udp://localhost:%s' % OSC_SERVER_PORT, '/selectedloopnum')

  def sendSelectedLoopNum(self, loopnum):
    liblo.send(self.target, '/set', 'selected_loop_num', float(loopnum))
    log("sent: /set/selected_loop_num %s" % str(loopnum))

  def sendHit(self, loopnum, command):
    liblo.send(self.target, '/sl/%s/hit' % str(loopnum), command)
    log("sent: /sl/%s/hit %s" % (str(loopnum), command))

  def sendLoopVelocity(self, loopnum, value):
    liblo.send(self.target, '/sl/%s/set' % str(loopnum), 'wet', value)
    log("sent: /sl/%s/set wet %f" % (str(loopnum), value))

  @liblo.make_method('/cyclelen', 'isf')
  def cyclelen_callback(self, path, args):
    loopnumber, cyclelen, cyclelength = args
    #log("received '%s' message with arguments: %d, %s, %f" % (path, loopnumber, cyclelen, cyclelength))
    self.emitter.emitM('cyclelen', loopnumber, cyclelength)

  @liblo.make_method('/looplen', 'isf')
  def looplen_callback(self, path, args):
    loopnumber, looplen, looplength = args
    #log("received '%s' message with arguments: %d, %s, %f" % (path, loopnumber, looplen, looplength))
    self.emitter.emitM('looplen', loopnumber, looplength)

  @liblo.make_method('/looppos', 'isf')
  def looppos_callback(self, path, args):
    loopnumber, looppos, position = args
    ##log("received '%s' message with arguments: %d, %s, %f" % (path, loopnumber, looppos, position))
    self.emitter.emitM('looppos', loopnumber, position)

  @liblo.make_method('/loopcount', 'ssi')
  def loopcount_callback(self, path, args):
    hosturl, version, loopcount = args
    #log("received '%s' message with arguments: %s, %s, %i" % (path, hosturl, version, loopcount))
    self.emitter.emitM('loopcount', loopcount)

  @liblo.make_method('/loopstate', 'isf')
  def loopstate_callback(self, path, args):
    loopnumber, state, value = args
    #log("received '%s' message with arguments: %s, %s, %f" % (path, loopnumber, state, value))
    self.emitter.emitM('loopstate', loopnumber, value)

  @liblo.make_method('/loopnextstate', 'isf')
  def loopnextstate_callback(self, path, args):
    loopnumber, state, value = args
    #log("received '%s' message with arguments: %s, %s, %f" % (path, loopnumber, state, value))
    self.emitter.emitM('loopnextstate', loopnumber, value)

  @liblo.make_method('/loopvelocity', 'isf')
  def loopvelocity_callback(self, path, args):
    loopnumber, control, value = args
    #log("received '%s' message with arguments: %s, %s, %f" % (path, loopnumber, control, value))
    self.emitter.emitM('loopvelocity', loopnumber, value)

  @liblo.make_method('/selectedloopnum', 'isf')
  def selectedloopnum_callback(self, path, args):
    loopnumber, control, value = args
    #log("received '%s' message with arguments: %i, %s, %f" % (path, loopnumber, control, value))
    self.emitter.emitM('selectedloopnum', value)

  @liblo.make_method(None, None)
  def fallback(self, path, args):
    a, b, c = args
    #log("received unknown message '%s' %s:(%s) %s:(%s) %s:(%s) " % (path, a, type(a), b, type(b), c, type(c)))
    self.emitter.emitM('unknown', args)

try:
  oscserver = OscServer()
except liblo.ServerError, err:
  log(str(err))
  sys.exit()

#server.start()
#raw_input("press enter to quit...\n")

"""test in ipython:


target = liblo.Address(9951)
liblo.send(target, '/sl/0/register_auto_update', 'loop_pos', 100, 'osc.udp://localhost:1234', '/looppos')
liblo.send(target, '/ping', 'osc.udp://localhost:1234', '/loopcount')
liblo.send(target, '/sl/0/get', 'state', 'osc.udp://localhost:1234', '/loopstate')
liblo.send(target, '/sl/0/register_auto_update', 'wet', 100, 'osc.udp://localhost:1234', '/loopvelocity')
liblo.send(target, '/sl/0/register_auto_update', 'state', 100, 'osc.udp://localhost:1234', '/loopstate')

##

import math

def updateVelocity(velocity):
  if velocity <= 0:
    myLoopVelocity.velocity = 0
  else:
    myLoopVelocity.velocity = (((6.0 * math.log(velocity)/math.log(2.)+198)/198.)**8) * 32
  myLoopVelocity.update()
  app.processEvents()

def updateCycleLen(cyclelen):
  myCycleTime.cyclelen = cyclelen
    
def updateLoopLen(looplen):
  myLoopCycles.looplen = int(looplen/myCycleTime.cyclelen)
    
def updateLoopPos(looppos):
  myCycleTime.cyclepos = (looppos - (int(looppos/myCycleTime.cyclelen) * myCycleTime.cyclelen))/myCycleTime.cyclelen*360
  myLoopCycles.currentloop = int(looppos/myCycleTime.cyclelen)
  myCycleTime.update()
  myLoopCycles.update()
  app.processEvents()

QObject.connect(oscserver.emitter, SIGNAL('loopvelocity'), updateVelocity)
QObject.connect(oscserver.emitter, SIGNAL('cyclelen'), updateCycleLen)
QObject.connect(oscserver.emitter, SIGNAL('looplen'), updateLoopLen)
QObject.connect(oscserver.emitter, SIGNAL('looppos'), updateLoopPos)

oscserver.start()
oscserver.initOsc()
"""
