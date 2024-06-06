import locale
import pyaudio
import json
import numpy as np


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

    def open_stream(self, is_input: bool = True):
        self.stream = self._pa.open(format=self.format,
                                    channels=self.channels,
                                    rate=self.rate,
                                    input=is_input,
                                    frames_per_buffer=self.chunk,
                                    input_device_index=self.mic_index)

    def read_data(self, exception_on_overflow: bool = False, dtype=np.int16):
        return np.frombuffer(self.stream.read(self.chunk, exception_on_overflow=exception_on_overflow), dtype=dtype)

    def close_stream(self):
        self.stream.stop_stream()
        self.stream.close()


if __name__ == "__main__":
    devs = DeviceInfo()
    data = devs.get_all_audio_devices()
    for i in data:
        print(i)
