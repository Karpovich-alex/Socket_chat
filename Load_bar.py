import sys
import time
import math


class ProgressBarOrganiser:
    def __init__(self, length=10):
        assert length > 0
        self._length = length
        self._progress_bars = []
        self._max_name = 0
        self._max_act = 0

    def new_bar(self, name: str, total_tasks: int, action: str = ' ', printable: bool = False,
                complete_text: str = 'Complete'):
        assert total_tasks > 0
        bar = ProgressBar(name, total_tasks, self._length, p=printable, complete_text=complete_text)
        if self._max_name < len(name):
            self._max_name = len(name)
        if self._max_act < len(action):
            self._max_act = len(action)
        self._progress_bars.append((action, bar))
        return bar

    def __bool__(self):
        return len(self._progress_bars) > 0

    def get_progress(self):
        msg = "\n".join(map(lambda x: f"{x[0] :<{self._max_act}} : {x[1].name :<{self._max_name}} {x[1].current_load}",
                            self._progress_bars))
        for bar in self._progress_bars:
            if bar[1].complete:
                self._progress_bars.remove(bar)
        return msg or 'No loads'

    def __repr__(self):
        return self.get_progress()


class ProgressBar:
    # todo: Time
    def __init__(self, name: str, total_tasks: int, length: int = 10, p=False, complete_text: str = 'Complete', fill_char='*', empty_char='='):
        assert total_tasks > 0
        assert length > 0
        self.name = name
        self._p = p
        self._length: int = length
        self._total_t = total_tasks
        self._interest_for_one_point = round(total_tasks / length)
        self.file = sys.stderr
        self.complete = False
        self._complete_text = complete_text
        self._msg = ""
        self._time_start = time.time()
        self._current_task = 0
        self._fill_char=fill_char
        self._empty_char=empty_char
        # create "zero" progress bar
        self(0)

    def __call__(self, cur_task: int):
        if cur_task >= self._total_t:
            self.end()
        else:
            self._current_task = cur_task
            cur_int = (self._current_task / self._total_t) * 100
            cur_l = self._fill_char * round(self._current_task / self._interest_for_one_point)  # math.ceil
            self._msg = f"|{cur_l:{self._empty_char}<{self._length}}| {cur_int:.1f}% [{time.strftime('%M:%S', time.gmtime(self.time_left))}]"
            self._len_msg = len(self._msg)
            if self._p:
                print(f"\r {self.name} {self._msg}", end='\r', file=self.file)
                self._len_msg = len(f"\r {self.name} {self._msg}")

    def __repr__(self):
        return self._msg

    @property
    def time_left(self):
        if self._current_task:
            cur_avg_time = round((time.time() - self._time_start) / self._current_task, 2)
        else:
            cur_avg_time = 1
        avg_time_left = (self._total_t - self._current_task) * cur_avg_time
        return avg_time_left

    def end(self):
        self._msg = self._complete_text
        self.complete = True
        if self._p:
            print('\r'+self._msg+' '*self._len_msg, flush=True, file=self.file)

    @property
    def current_load(self):
        return self._msg


if __name__ == '__main__':
    def print_load(total_tasks, cur_task):
        interest_for_one_point = total_tasks // 10
        file = sys.stderr
        if cur_task % interest_for_one_point == 0:
            current_int = (cur_task / total_tasks) * 100
            cur_load = '*' * (cur_task // interest_for_one_point)
            print(f'|{cur_load:_<12}| {current_int:.1f}%', end='', file=file)
            # sys.stderr.flush()
            print('\r', end='', file=file)


    n = 'NAME'
    lp = 11
    pb = ProgressBar('loader', lp)

    # bar=FillingCirclesBar(n, max=lp)
    for i in range(lp):
        time.sleep(0.1)
        pb(i)
        # print(i)
        # bar.next()
    # bar.finish()
    # print(f'[{n:_>10}]')
    # c_l='*'*5
    # c_i=2
    # print(f'|{c_l:_<10}| {c_i:.1f}%')
    # for i in range(lp):
    #     print_load(lp, i)
