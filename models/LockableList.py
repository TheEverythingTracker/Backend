import threading


class LockableList:
    safe_list: []
    lock: threading.Lock

    def __init__(self):
        self.safe_list = []
        self.lock = threading.Lock()

    def __iter__(self):
        self.lock.acquire()
        self.curr_index = 0
        return self

    def __next__(self):
        if self.curr_index < len(self.safe_list):
            ret = self.safe_list[self.curr_index]
            self.curr_index += 1
            return ret
        else:
            self.lock.release()
            raise StopIteration

    def append(self, val):
        with self.lock:
            self.safe_list.append(val)

    def remove(self, val):
        with self.lock:
            self.safe_list.remove(val)
    def size(self):
        with self.lock:
            return len(self.safe_list)

    def __len__(self):
        with self.lock:
            return len(self.safe_list)
