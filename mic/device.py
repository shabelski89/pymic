import locale
import pyaudio
import json
import numpy as np
import time
from typing import List
from sender import Exporter


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

    def get_decibel_data(self) -> dict:
        decibel_data = {
            "signal_strength_db": self._sp.calculate_decibels(self.read_data()),
            "time": time.time(),
            "mic_index": self.mic_index
        }
        return decibel_data

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


class SignalConsumer:
    def __init__(self, streams: List[AudioStream], exporter: Exporter):
        self.streams = streams
        self.exporter = exporter
        self.is_running = True

    def run(self):
        try:
            while self.is_running:
                for stream in self.streams:
                    stream_data = stream.get_decibel_data()
                    self.exporter.send(stream_data)
        except KeyboardInterrupt:
            print("Terminating...")
            for stream in self.streams:
                stream.close_stream()

    def stop(self):
        time.sleep(2)
        self.is_running = False
        print("Exit...")


if __name__ == "__main__":
    devs = DeviceInfo()
    test_data = devs.get_mic_devices()
    for i in test_data:
        print(i)

    print(devs.get_mic_info_by_index(1))

    a = AudioStream(1, 1, 44100)
    list_audio_streams = [a]

    from sender import StdOut
    exporter = StdOut()
    s = SignalConsumer(list_audio_streams, exporter)
    s.run()
