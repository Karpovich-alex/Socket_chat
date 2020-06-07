import sys
import time


class ProgressBar:
    # todo: Time
    def __init__(self, name, total_tasks):
        self._name = name
        self._total_t = total_tasks
        self._interest_for_one_point = total_tasks // 10
        self.file = sys.stderr
        self(0)

    def __call__(self, cur_task: int):
        if cur_task == self._total_t - 1:
            print('\b' * self._len_msg + ' ' * self._len_msg, end='\r', flush=True, file=self.file)
            print('Complete', file=self.file)
        else:
            cur_int = (cur_task / self._total_t) * 100
            cur_l = '*' * (cur_task // self._interest_for_one_point)
            print('\r', end='', file=self.file)
            self._len_msg = len(f'{self._name} |{cur_l:_<10}| {cur_int:.1f}%')
            print(f'{self._name} |{cur_l:_<10}| {cur_int:.1f}%', end='', file=self.file)

    def end(self, text='Complete'):
        print('\b' * self._len_msg + ' ' * self._len_msg, end='\r', flush=True, file=self.file)
        print(text, file=self.file)


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
