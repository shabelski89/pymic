import json
import requests
from queue import Queue
try:
    from .observer import Observer, Export
    from .device import AudioData
except ImportError:
    from observer import Observer, Export
    from device import AudioData


class QueueConsumer(Observer, Export):
    def __init__(self, audio_data: AudioData):
        self.audio_data = audio_data
        self.audio_data.register_observer(self)
        self._signal = None
        self._timestamp = None
        self._mic_index = None
        self.deque = Queue(maxsize=1000)

    def update(self, signal, ts, ind):
        self._signal = signal
        self._timestamp = ts
        self._mic_index = ind
        self.send()

    def send(self):
        self.deque.put([self._signal, self._timestamp, self._mic_index])


class StdOut(Observer, Export):
    def __init__(self, audio_data: AudioData):
        self.audio_data = audio_data
        self.audio_data.register_observer(self)
        self._signal = None
        self._timestamp = None
        self._mic_index = None

    def update(self, signal, ts, ind):
        self._signal = signal
        self._timestamp = ts
        self._mic_index = ind
        self.send()

    def send(self):
        print(f"CurrentData: signal - {self._signal}, ts - {self._timestamp}, ind - {self._mic_index}")


class HttpSender(Observer, Export):
    def __init__(self, audio_data: AudioData, server_url: str):
        self.audio_data = audio_data
        self.server_url = server_url
        self.audio_data.register_observer(self)
        self._signal = None
        self._timestamp = None
        self._mic_index = None
        self.headers = {'Content-Type': 'application/json'}

    def update(self, signal, ts, ind):
        self._signal = signal
        self._timestamp = ts
        self._mic_index = ind
        self.send()

    def send(self):
        decibel_data = {
            "signal_strength_db": self._signal,
            "time": self._timestamp,
            "mic_index": self._mic_index
        }

        json_data = json.dumps(decibel_data)

        try:
            response = requests.post(self.server_url, data=json_data, headers=self.headers)
            response.raise_for_status()
            print(f"Data sent successfully: {json_data}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending data: {e}")


class FileSaver(Observer, Export):
    def __init__(self, audio_data: AudioData, filename: str):
        self.audio_data = audio_data
        self.filename = filename
        self.audio_data.register_observer(self)
        self._signal = None
        self._timestamp = None
        self._mic_index = None

    def update(self, signal, ts, ind):
        self._signal = signal
        self._timestamp = ts
        self._mic_index = ind
        self.send()

    def send(self):
        decibel_data = {
            "signal_strength_db": self._signal,
            "time": self._timestamp,
            "mic_index": self._mic_index
        }

        json_data = json.dumps(decibel_data)

        with open(self.filename, 'a', encoding='utf-8') as file:
            file.write(json_data + '\n')


if __name__ == "__main__":
    from device import AudioStream, AudioStation
    a = AudioStream(1, 1, 44100)
    b = AudioStream(2, 1, 44100)
    list_audio_streams = [a, b]
    ad = AudioData()
    ast = AudioStation(ad, list_audio_streams)
    ast.start()
    ds = StdOut(audio_data=ad)
    fs = FileSaver(audio_data=ad, filename='data')
    ast.stop()
