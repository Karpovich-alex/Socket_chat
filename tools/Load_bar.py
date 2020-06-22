import sys
import time
import math


class IterSpeed:
    def __init__(self, **kwargs):
        for n, v in kwargs.items():
            self.__setattr__(n, v)

    def convert(self, current_task, current_time, *args, **kwargs):
        pass

    def __call__(self, current_task, current_time, *args, **kwargs):
        return f"{self.convert(current_task, current_time, args, kwargs)}"


class DefaultIterSpeed(IterSpeed):
    def convert(self, current_task, current_time, *args, **kwargs):
        return f"{current_task / current_time:.2f} iter/sec" if current_time != 0 else f'{0:.2f} iter/sec'


class DataTransportSpeed(IterSpeed):
    def __init__(self, data_type_in: str):
        self._data_types = ['bit', 'Kbit', 'Mbit', 'Gbit', 'Pbit']  # difference is 1000
        self._data_types_count = len(self._data_types)
        try:
            self._input_level = self._data_types.index(data_type_in)
        except:
            raise ValueError(f'not data type \n supported:{self._data_types}')
        super().__init__(data_type_in=data_type_in)

    def convert(self, current_task, current_time, *args, **kwargs):
        if current_time:
            transport_speed = round(current_task / current_time, 4) or 1
        else:
            transport_speed = 1
        t_speed_lvl = math.floor(math.log(transport_speed, 1000))
        if t_speed_lvl:
            t_speed_convert = transport_speed // (1000 ** t_speed_lvl)
        else:
            t_speed_convert = transport_speed
        if t_speed_lvl > self._data_types_count - 1:
            t_speed_convert *= 1000 ** (t_speed_lvl - self._data_types_count - 1)
            t_speed_lvl = self._data_types_count - 1
        return f"{t_speed_convert:.2f} {self._data_types[t_speed_lvl]}/sec"


class ProgressBar:
    bar_length = 10
    completed_text: str = 'Complete'
    printable: bool = False
    fill_char: str = '*'
    empty_char: str = '_'

    def __init__(self, name: str, total_tasks: int, length: int = bar_length, printable=printable,
                 completed_text: str = completed_text,
                 fill_char: str = fill_char, empty_char: str = empty_char, iter_speed=DefaultIterSpeed()):
        assert total_tasks > 0
        assert length > 0
        self.name = name
        self._p = printable
        self._length: int = length
        self._total_t = total_tasks
        self._interest_for_one_point = total_tasks / length
        if printable:
            self.file = sys.stderr
        self.complete = False
        self._completed_text = completed_text
        self._msg = ""
        self._time_start = time.time()
        self._current_task = 0
        self._fill_char = fill_char
        self._empty_char = empty_char
        self._iter_speed = iter_speed
        self._len_msg = 0

    def __call__(self, cur_task: int):
        if cur_task >= self._total_t:
            self.end()
        else:
            self._current_task = cur_task
            current_load = math.floor(self._current_task / self._interest_for_one_point)
            cur_free = self._length - current_load
            self._msg = "|{loadbar}| {procent}% [{time}] {speed}".format(
                loadbar=f"{self._fill_char * current_load}{self._empty_char * cur_free}",
                procent=f"{self.current_interest:.1f}",
                time=time.strftime('%H:%M:%S', time.gmtime(self.time_left)),
                speed=self._iter_speed(cur_task, self.current_time))
            self._len_msg = len(self._msg)
            if self._p:
                print(f"{self.name} {self._msg}", end='\r', file=self.file)
                self.file.flush()
                self._len_msg = len(f"\r {self.name} {self._msg}")

    def __repr__(self):
        return self._msg

    @property
    def current_interest(self):
        return (self._current_task / self._total_t) * 100

    @property
    def time_left(self):
        if self._current_task:
            cur_avg_time = self.current_time / self._current_task
        else:
            cur_avg_time = 1
        avg_time_left = (self._total_t - self._current_task) * cur_avg_time
        return avg_time_left

    @property
    def current_time(self):
        return time.time() - self._time_start

    def end(self):
        self._msg = self._completed_text
        self.complete = True
        if self._p:
            print('\r' + self._msg + ' ' * self._len_msg, flush=True, file=self.file)

    @property
    def get_load_bar(self):
        return self._msg


class ProgressBarOrganiser:
    def __init__(self, length=10, **kwargs):
        assert length > 0
        self._length = length
        self._progress_bars = []
        self._max_name = 0
        self._max_act = 0
        self._bar_settings = kwargs

    def new_bar(self, bar: ProgressBar, action: str = ' ') -> ProgressBar:
        name = bar.name
        bar.__setattr__('_length', self._length)
        if self._max_name < len(name):
            self._max_name = len(name)
        if self._max_act < len(action):
            self._max_act = len(action)
        self._progress_bars.append((action, bar))
        return bar

    def __bool__(self):
        return len(self._progress_bars) > 0

    def get_progress(self):
        msg = "\n".join(map(lambda x: f"{x[0] :<{self._max_act}} : {x[1].name :<{self._max_name}} {x[1].get_load_bar}",
                            self._progress_bars))
        for bar in self._progress_bars:
            if bar[1].complete:
                self._progress_bars.remove(bar)
        return msg or 'No loads'

    def __repr__(self):
        return self.get_progress()

    def __str__(self):
        return '\r' + repr(self)


if __name__ == '__main__':
    total_task = 10 ** 10
    import random

    loadbarORG = ProgressBarOrganiser(length=20)
    loadbar = loadbarORG.new_bar(ProgressBar('TEST bar', total_task, iter_speed=DataTransportSpeed('bit')), action='UP')
    loadbar_1 = loadbarORG.new_bar(ProgressBar('Second bar', total_task / 10), action='Down')
    print('start')
    d = 0
    while d < total_task:
        b = random.randint(1, 10 ** 7)
        loadbar(d)
        loadbar_1(d)
        print(loadbarORG)
        time.sleep(random.randint(1, 3))
        d += b
    pass
