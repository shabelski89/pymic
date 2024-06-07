import json
import requests
from abc import ABC, abstractmethod
import sys, io


class Exporter(ABC):
    @abstractmethod
    def send(self, data: dict):
        raise NotImplementedError


class HttpSender(Exporter):
    HEADERS = {'Content-Type': 'application/json'}

    def __init__(self, server_url: str):
        self.server_url = server_url

    def send(self, data: dict, headers=None):
        json_data = json.dumps(data)

        if headers is None:
            headers = self.HEADERS
        try:
            response = requests.post(self.server_url, data=json_data, headers=headers)
            response.raise_for_status()
            print(f"Data sent successfully: {json_data}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending data: {e}")


class FileSaver(Exporter):
    def __init__(self, filename: str):
        self.filename = filename

    def send(self, data: dict):
        with open(self.filename, mode='a', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, default=str)


class StdOut(Exporter):
    def send(self, data: dict):
        print(data)
