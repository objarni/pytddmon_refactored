# pytddmon_refactored
An attempt to refactor pytddmon into a more unit-testable and extensible architecture
based on Finite State Machines / message queues


Problems with current design
============================

The current pytddmon source is basically a "hack"; it began with any unit tests at all,
written in a night of inspiration (and perspiration).

It used pygame for the graphical user interface, and os.system() calls to run tests
using nosetests.

To display the result - number of passed and total count of unit tests - it parsed the
stdout of nosetests and updated the UI.

Years later it has moved from pygame to Tkinter, and uses subprocess + multiprocess
pooling to run unit test removing the need to parse the output. A lot of functionality
has moved to small classes that are unit tested, and it now features some command line
options, e.g. the ability to run in 'test mode' for integration level automatic tests
(the systests suite).

Even if the design is a whole lot better than the hack it used to be, it is still entangled
on the top-level of the "system"; e.g. the UI class "knows" a lot about the internals of the
Pytddmon class.

A new design
============

A moder loosely coupled design is basing as many components as possible of pytddmon on
_finite state machines_, running (logically) independent of each other, and just publishing
and/or listening to events happening in the system.

The function of pytddmon lends itself to be described by such devices quite naturally:

    - The TestRunner would be a state machine that is responsible for running tests.
    - The ChangeDetector would be a state machine that is responsible for detecting file changes.
    - The Lamp would be a state machine responsible for updating the UI depending on
      test results (and possibly tests being run too, a feature not present in current
      pytddmon.)
      
With this architecture, the whole of pytddmon would be setting up these machines, choosing
an appropriate UI object (Tk/Gtk/Console), and then making the whole thing 'tick' by
publishing events.


Open questions
==============

1. How does the ChangeDetector detect files...? What makes it scan for file changes? In
traditional pytddmon, this was a timeout triggering a scan every half a second. The
equivalent in this redesign would be a thread publishing a 'heartbeat' event with same
interval, or a mechanism that is intrinsic to the choice of GUI tech (preferably not).
An even better approach would be to listen to operating system level notifications.

2. How do devices publish events? For testability, the publish method should be easily
mockable.

3. What's an event? Is it a better name than signal, or message?

