'''
pytddmon re-engineered.

pytddmon v2 only has these states:
GREEN  (all tests pass)
RED    (one or more tests fail)

The machine can be illustrated like this:


  +--(test run failure)------------+
  |                                V
GREEN                             RED
  ^                                |
  +-------(test run success)-------+


We can see there are essentially only two signals:

'test_run_failed' - plus some details like number of tests, error log etc.
'test_run_success' - plus number of tests

The implementation of this state machine is trivial! But it is the heart
of pytddmon and we might call it something like PytddmonBehaviour since
it is the most central/visible feature of the whole app.

So where is all the "meat" of this app...? It's in the threads/active objects
that publish those signals.

The test running active object has two states, DORMANT and TESTING.

In the DORMANT state, it is waiting for a 'file_change' signal.

On that signal, it switches to TESTING, a state which spawns a worker thread
to run all tests. This thread publishes the 'test_run_failed' or
'test_run_success' signals.

So when does the TestRunner switch back to DORMANT? A simple answer is
'when it hears any of the test_run' signals. In fact, one option would be
to simplify the design so that the test_run_* signals is compacted to only one:
'test_run_finished' with the parameters specifying the result of the run.
This means the TestRunner only listens for two signals: 'file_change' and
'test_run_finished'.

What happens if the 'file_change' signal is published in the middle of a test
run..? Well one approach would be to ignore it, which would have the consequence
that the UI might show an incorrect test result. Not desireable.

Another approach would be to set some bool state 'rerun', which is checked
on the signal 'test_run_finished'. If True, the test runner machine will
NOT go back to dormant, but instead trigger another test run immediately.

This has the consequence that the UI will eventually show the correct result.

Even better would be if he test running thread would be aborted on file_change
signal, and instantly re-started. This has the negative consequence that
it's hard to stop running threads/processes cleanly. A way around this would
be to break up the test run in small chunks instead of a large mega operation,
so as to be able to "breethe" and check some 'abort' state. (is it actually
a state machine itself that thread...? or rather, a part of the test runner
machine?)

Travelling further down in this system, we wonder where the 'file_change'
signal comes from. But before that let's think of the big picture:
how do signals arrive at state machine? What does it mean to publish
a signal/event?

The main method of the app might look something like this:

  pytddmon = PytddmonBehaviour()
  testrunner = TestRunner()
  .... # any other state machines we need
  machine_runner = MachineRunner()
  machine_runner.add_machine(pytddmon)
  machine_runner.add_machine(testrunner)
  publish = machine_runner.publish
  file_change_detection_thread = FileChangeMonitorThread(publish)
  file_change_detection_thread.start()
  while True:
  	machine_runner.tick()
  	time.sleep(0.1)  # This basically controls the granularity of the whole app!
  	# Note the machines are all running on the main thread;
  	# not in parallell. Very deterministic and simple.

Notice how the thread gets hold of the publish method, so as to be able
to publish signals into the system.

All other objects are state machines, and will 'live' by the happenings
in tick(). In the very simplest of implementations for MachineRunner, tick()
dispatches every incoming signal given to publish since last run of tick()
to every known machine to handle by itself. No subscription is necessary!

If we wanted a UI in this app, we could make the 'main loop' happen in the
idle callback, so that all machine could potentially get hold of and update
the UI as necessary, e.g. by being given a reference to "their" widget
when constructed.

The MachineRunner is so simple it may look something like this:

class MachineRunner(object):

	def add_machine(self, machine):
		self.signal_queue = Queue.Queue()  # good for concurrent/threade op!
		self.machines.append(machine)

	def tick(self):
		while self.signal_queue.has_items():
			sig = self.signal_queue.pop()
			for m in self.machines:
				m.dispatch(sig)

	def publish(signal):
		self.signal_queue.push(signal)

Of course, from here it's possible to extend ad infinituum:

- let machines subscribe to the signals they're interested in (optimization)
- make it possible to add/remove machines in runtime (flexibility)
- state transitions e.g. by have machine.state method (code reduction)
- add conventional entry/exit signals states (code reduction)
- run machines concurrently instead of in single thread (optimization)
- hierarchical state machines (possible already but the oracle 'dispatch'
  doesn't help very much)
- ...

'''
