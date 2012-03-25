

import sys
import curses

class ProgressBar(object):
    '''A simple progress bar for the terminal.'''

    template = '%(message)s[%(progress)s%(empty)s] %(persetage).1f%%\n'

    def __init__(self, total, message='', width=40):
        self.total = float(total)
        self.width = width
        self.message = message
        self.lines = None

        curses.setupterm()

    def update(self, progress):
        '''Update progress and the display.'''

        # Clear the previous progress bar
        if not self.lines is None:
            sys.stdout.write( self.lines * curses.tigetstr('cuu1'))

        progress = min(progress, self.total)
        percent = progress/self.total * 100.0
        size = int(progress/self.total * self.width)

        bar = self.template % {
                'message': self.message,
                'progress': '#'*size,
                'empty': ' '*(self.width-size),
                'persetage': percent 
                }

        sys.stdout.write(bar)
        sys.stdout.flush()

        self.lines = len(bar.splitlines())


if __name__ == '__main__':
    import random
    import time

    progressbar = ProgressBar(10, message='Testing\n', width=10)
    progress = 0
    while progress < 10:
        progress += random.random()
        #progress = min(10, progress)
        progressbar.update(progress)
        time.sleep(0.5)


