import time
import threading
from threading import Event
from datetime import datetime

class User:
    def __init__(
        self,
        user_id: int, 
        expiry_date: str
    ) -> None:
        self.user_id = user_id
        self.expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")
        self.stop_event = Event()
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def run(self) -> None:
        print('fdsfsdfsdfsddfsdfdsdfsdfsdf')
        while not self.stop_event.is_set():
            # print('User ID: Connected!')
            time.sleep(5)

    def disconnect(self) -> None:
        self.stop_event.set()
        self.thread.join()