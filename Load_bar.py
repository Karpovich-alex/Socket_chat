import sys
import time
import math


class ProgressBarOrganiser:
    def __init__(self, length=10):
        self._length = length
        self._progres_bars = []
        self._max_name = 0
        self._max_act = 0

    def new_bar(self, name: str, total_tasks: int, action: str = ' ', p: bool = False):
        bar = ProgressBar(name, total_tasks, self._length, p)
        if self._max_name < len(name):
            self._max_name = len(name)
        if self._max_act < len(action):
            self._max_act = len(action)
        self._progres_bars.append((action, bar))
        return bar

    def __bool__(self):
        return len(self._progres_bars) > 0

    def get_progress(self):
        msg = "\n".join(map(lambda x: f"{x[0] :<{self._max_act}} : {x[1].name :<{self._max_name}} {x[1].get_load()}",
                            self._progres_bars))
        for bar in self._progres_bars:
            if bar[1].complete:
                self._progres_bars.remove(bar)
        return msg or 'No loads'

    def __repr__(self):
        return self.get_progress()


class ProgressBar:
    # todo: Time
    def __init__(self, name: str, total_tasks: int, length: int = 10, p=False):
        self.name = name
        self._p = p
        self._length: int = length
        self._total_t = total_tasks
        self._interest_for_one_point = math.ceil(total_tasks / length)
        self.file = sys.stdout
        self.complete = False
        self._msg = ""
        self(0)

    def __call__(self, cur_task: int):
        if cur_task >= self._total_t - 1:
            self.end()
        else:
            cur_int = (cur_task / self._total_t) * 100
            cur_l = '*' * math.ceil(cur_task / self._interest_for_one_point)
            # print('\r', end='', file=self.file)
            self._len_msg = len(f'{self.name} |{cur_l:_<{self._length + 2}}| {cur_int:.1f}%')
            self._msg = f'|{cur_l:_<{self._length + 2}}| {cur_int:.1f}%'
            if self._p:
                print(self._msg, end='', file=self.file)

    def __repr__(self):
        return self._msg

    def end(self, text='Complete'):
        self._msg = text
        self.complete = True
        if self._p:
            print(self._msg, end='\r', flush=True, file=self.file)

    def get_load(self):
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
