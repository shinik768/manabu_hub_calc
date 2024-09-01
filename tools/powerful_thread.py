import threading
import ctypes
import time

# カスタムスレッドクラス
# 引用元：https://qiita.com/76r6qo698/items/a0d3bdac3425dda6056a
class powerful_thread(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        threading.Thread.__init__(self, group=group, target=target, name=name)
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        self._target(*self.args, **self.kwargs)

    def get_id(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id
    
    # 強制終了させる関数
    def raise_exception(self):
        thread_id = self.get_id()
        resu = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), ctypes.py_object(SystemExit))
        if resu > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), 0)
            print('Failure in raising exception')

# 開始するスレッドで実行する関数
def sample_func(a, b, c, hoge1=None, hoge2=None, hoge3=None):
    try:
        for _ in range(5):
            print((a, b, c, hoge1, hoge2, hoge3))
            time.sleep(1)
    finally:
        print('ended')

def main():
    # 開始するスレッドを定義
    x = powerful_thread(name='Thread A', target=sample_func, args=(1, 2, 3), kwargs={'hoge1': 'hogehoge1', 'hoge2': 'hogehoge2', 'hoge3': 'hogehoge3'})
    # スレッド開始
    x.start()

    # スレッドが10秒以内に終了するか確認
    start_time = time.time()
    while x.is_alive():
        elapsed_time = time.time() - start_time
        if elapsed_time > 10:
            print("Time limit exceeded, terminating the thread.")
            x.raise_exception()
            break
        time.sleep(0.1)  # 100msのスリープでCPU使用率を抑える

    # スレッドの終了を待機
    x.join()
    print("Main function completed.")