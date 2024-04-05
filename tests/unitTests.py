import queue
import time
import unittest

from business.video_frame_producer import VideoFrameProducerThread
from config.constants import QUEUE_SIZE, PRODUCER_THREAD_SEEMS_DEAD_TIMEOUT


class TestTracker(unittest.TestCase):
    frame_queue = queue.Queue(QUEUE_SIZE)
    video_frame_producer = None

    def test_frame_producer(self):
        self.video_frame_producer = VideoFrameProducerThread(self._on_producer_finished)
        self.video_frame_producer.load(video_source="https://www.sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4")
        self.video_frame_producer.add_queue(self.frame_queue)
        self.video_frame_producer.start()

        counter = 0

        while self.video_frame_producer.is_running():
            try:
                self.frame_queue.get(True,PRODUCER_THREAD_SEEMS_DEAD_TIMEOUT)
                counter += 1
            except Exception as e:
                break
        counter += self.frame_queue.qsize()
        self.assertEqual(counter, 132, "Number of Frames not as expected")


    def _on_producer_finished(self, message):
        self.video_frame_producer.quit()

if __name__ == '__main__':
    unittest.main()
