import locale
import pyaudio
import json
import numpy as np
import time
from typing import List
from threading import Thread
from .observer import Subject, Observer


class AudioData(Subject):
    def __init__(self):
        self._observers = []
        self._signal = None
        self._timestamp = None
        self._mic_index = None

    def register_observer(self, observer: Observer):
        self._observers.append(observer)

    def remove_observer(self, observer: Observer):
        if observer in self._observers:
            self._observers.remove(observer)

    def notify_observers(self):
        for observer in self._observers:
            observer.update(self._signal, self._timestamp, self._mic_index)

    def data_changed(self):
        self.notify_observers()

    def set_data(self, signal: int, timestamp: int, mic_index: int):
        self._signal = signal
        self._timestamp = timestamp
        self._mic_index = mic_index
        self.data_changed()


class DeviceInfo:
    def __init__(self):
        self._pa = pyaudio.PyAudio()

    def get_all_audio_devices(self):
        region, coding = locale.getlocale()
        return [
            json.loads(json.dumps(self._pa.get_device_info_by_index(i), ensure_ascii=False).encode(coding))
            for i in range(self._pa.get_device_count())
        ]

    def get_mic_devices(self):
        return [dev for dev in self.get_all_audio_devices() if dev["maxInputChannels"] > 0 and dev["hostApi"] == 0]

    def get_mic_info_by_index(self, ind: int):
        all_dev = self.get_all_audio_devices()
        for dev in all_dev:
            if dev.get('index') == ind:
                return dev
        return None

    def __repr__(self):
        return "\n".join(self.get_all_audio_devices())


class AudioStream:
    def __init__(self, mic_index: int, channels: int, rate: int, pa_format: int = pyaudio.paInt16, chunk: int = 1024):
        self.mic_index = mic_index
        self.format = pa_format
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.stream = None
        self._pa = pyaudio.PyAudio()
        self._sp = SignalProcessor()

    def _open_stream(self, is_input: bool = True):
        self.stream = self._pa.open(format=self.format,
                                    channels=self.channels,
                                    rate=self.rate,
                                    input=is_input,
                                    frames_per_buffer=self.chunk,
                                    input_device_index=self.mic_index)

    def read_data(self, exception_on_overflow: bool = False, dtype=np.int16):
        self._open_stream()
        data = {}
        try:
            data = np.frombuffer(self.stream.read(self.chunk, exception_on_overflow=exception_on_overflow), dtype=dtype)
        except IOError as e:
            print(f"Error reading from {self.mic_index}: {e}")
        return data

    def get_decibel_data(self) -> tuple:
        db = self._sp.calculate_decibels(self.read_data())
        ts = time.time()
        ind = self.mic_index
        return db, ts, ind

    def close_stream(self):
        self.stream.stop_stream()
        self.stream.close()


class SignalProcessor:
    @staticmethod
    def calculate_decibels(audio_data: np.ndarray):
        try:
            rms = np.sqrt(np.abs(np.mean(np.square(audio_data))))
            decibels = 20 * np.log10(rms)
        except Exception as E:
            print(E)
            decibels = 0
        return decibels


class AudioStation(Thread):
    def __init__(self, audio_data: AudioData, streams: List[AudioStream]):
        super().__init__(target=self.run)
        self.audio_data = audio_data
        self.streams = streams
        self.is_running = False

    def run(self):
        print("Start...")

        try:
            self.is_running = True
            while self.is_running:
                for stream in self.streams:
                    db, ts, ind = stream.get_decibel_data()
                    self.audio_data.set_data(db, ts, ind)
                time.sleep(1)

        except KeyboardInterrupt:
            print("Terminating...")
            for stream in self.streams:
                stream.close_stream()

    def stop(self):
        if self.is_running:
            self.is_running = False

            try:
                Thread.join(self)
            except RuntimeError:
                pass

            for stream in self.streams:
                stream.close_stream()

            print("Exit...")
        else:
            print("Nothing to stop...")


if __name__ == "__main__":
    devs = DeviceInfo()
    test_data = devs.get_mic_devices()
    for i in test_data:
        print(i)

    print(devs.get_mic_info_by_index(1))
