"""
progress bar to show the progress of a process with known number of steps
"""


class ProgressBar(object):
    """
    progress bar to show the progress of a process with known number of steps
    """
    def __init__(self, total, prefix='Progress:', suffix='Complete', decimals=1, bar_length=50):
        """
        Creates a progress bar object
        After creation, call `show_current` to show the initial state of the `ProgressBar`
        Then, call `advance` to move the bar to the next point
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            bar_length  - Optional  : character length of bar (Int)
        """
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.decimals = decimals
        self.bar_length = bar_length
        self.current_iteration = 0
        self.is_finished = False

    def advance(self, note=""):
        """
        Advances the `ProgressBar` by a single step, if available
        """
        if self.is_finished:
            return
        self.current_iteration = self.current_iteration + 1
        self.show_current(note)

    def show_current(self, note=""):
        """
        Show the progress bar
        """
        str_format = "{0:." + str(self.decimals) + "f}"
        percents = str_format.format(100 * (self.current_iteration / float(self.total)))
        filled_length = int(round(self.bar_length * self.current_iteration / float(self.total)))
        bar = '█' * filled_length + '-' * (self.bar_length - filled_length)

        print('\r%s |%s| %s%s %s %s' % (self.prefix, bar, percents, '%', self.suffix, note), end='\r')

        if self.current_iteration == self.total:
            self.is_finished = True
            print()
