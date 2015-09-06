#!/usr/bin/env python

# Standard
import Queue
import logging

# Related
import pygtk
pygtk.require('2.0')
import gtk
import gobject

logging.basicConfig(
    format='%(funcName)s: %(message)s',
    level=logging.DEBUG
)

class MachineRunner(object):

    def __init__(self):
        self.machines = []
        self.signal_queue = Queue.Queue()
        self.ticks = 0

    def add_machine(self, machine):
        logging.info("Adding machine %s.", machine.__class__.__name__)
        self.machines.append(machine)

    def rtc(self):
        self.ticks += 1
        # Always publish a tick signal. This means machines that
        # want to do some piecewise work every rtc step can hook
        # onto this signal and do their work
        self.publish('tick', self.ticks)
        # Count number of signals before processing.
        # This is to avoid 'infinite rtc step' if any machine
        # puslishes a signal to itself, which would mean the queue
        # would never end in a while loop.
        signals_to_process = len(self.signal_queue.queue)
        # logging.debug("Tick %d. %d signal(s) to process.",
        #               self.ticks, signals_to_process)
        for _ in range(signals_to_process):
            (sig, par) = self.signal_queue.get()
            # logging.debug('Dispatching signal ("%s", %s).', sig, par)
            for m in self.machines:
                logging.debug('%s -> %s [%r]',
                              sig,
                              m.__class__.__name__,
                              m.state.__name__)
                m.state(sig, par)

    def publish(self, sig, par=None):
        assert type(sig) == type('')
        logging.debug('Enqueueing signal ("%s", %s)',
                      sig, repr(par))
        self.signal_queue.put((sig, par))



class TestRunner(object):

    def __init__(self, publish):
        self.state = self.dormant
        self.publish = publish

    def dormant(self, sig, par):
        if sig == 'file_change':
            logging.debug('Got file change signal, transitioning to running.')
            self.state = self.running
            self.total = 10
            self.green = 0
            self.publish('test_run_started')

    def running(self, sig, par):
        if sig == 'tick':
            self.green += 1
            if self.green == self.total:
                logging.debug('All tests run. Publishing result and dormenting.')
                self.publish('test_run_finished', (self.green, self.total))
                self.state = self.dormant
            else:
                logging.debug("Running test %d of %d.", self.green,
                              self.total)



class Lamp(object):

    def __init__(self):
        self.state = self.green

    def green(self, sig, par):
        if sig == 'file_change':
            self.state = self.gray
        elif sig == 'test_run_finished':
            (green, total) = par
            if green < total:
                logging.debug("It's a failed test run; going red.")
                self.state = self.red
            else:
                logging.debug("It's a successful test run; staying green.")

    def gray(self, sig, par):
        if sig == 'test_run_finished':
            (green, total) = par
            if green < total:
                self.state = self.red
            else:
                self.state = self.green

    def red(self, sig, par):
        if sig == 'test_run_started':
            self.state = self.gray
        elif sig == 'test_run_finished':
            (green, total) = par
            if green == total:
                logging.debug("It's a successful test run; going green.")
                self.state = self.green
            else:
                logging.debug("It's a failed test run; staying red.")


class HelloWorld:

    def hello(self, widget, data=None):
        self.mr.publish('file_change')

    def delete_event(self, widget, event, data=None):
        # If you return FALSE in the "delete_event" signal handler,
        # GTK will emit the "destroy" signal. Returning TRUE means
        # you don't want the window to be destroyed.
        # This is useful for popping up 'are you sure you want to quit?'
        # type dialogs.
        print "delete event occurred"

        # Change FALSE to TRUE and the main window will not be destroyed
        # with a "delete_event".
        return False

    def destroy(self, widget, data=None):
        print "destroy signal occurred"
        gtk.main_quit()

    def __init__(self, mr):
        self.mr = mr

        # create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    
        # When the window is given the "delete_event" signal (this is given
        # by the window manager, usually by the "close" option, or on the
        # titlebar), we ask it to call the delete_event () function
        # as defined above. The data passed to the callback
        # function is NULL and is ignored in the callback function.
        self.window.connect("delete_event", self.delete_event)
    
        # Here we connect the "destroy" event to a signal handler.  
        # This event occurs when we call gtk_widget_destroy() on the window,
        # or if we return FALSE in the "delete_event" callback.
        self.window.connect("destroy", self.destroy)
    
        # Sets the border width of the window.
        self.window.set_border_width(10)
    
        # Creates a new button with the label "Hello World".
        self.button = gtk.Button("Hello World")
    
        # When the button receives the "clicked" signal, it will call the
        # function hello() passing it None as its argument.  The hello()
        # function is defined above.
        self.button.connect("clicked", self.hello, None)
    
        # This will cause the window to be destroyed by calling
        # gtk_widget_destroy(window) when "clicked".  Again, the destroy
        # signal could come from here, or the window manager.
        # self.button.connect_object("clicked", gtk.Widget.destroy, self.window)
    
        # This packs the button into the window (a GTK container).
        self.window.add(self.button)

        gobject.timeout_add(2000, self.rtc)
    
        # The final step is to display this newly created widget.
        self.button.show()
    
        # and the window
        self.window.show()

    def rtc(self):
        self.mr.rtc()
        return True

    def main(self):
        # All PyGTK applications must have a gtk.main(). Control ends here
        # and waits for an event to occur (like a key press or mouse event).
        gtk.main()

if __name__ == "__main__":
    print('Starting pytddmon reengineered...')

    mr = MachineRunner()
    mr.add_machine(TestRunner(mr.publish))
    mr.add_machine(Lamp())

    hello = HelloWorld(mr)
    hello.main()
