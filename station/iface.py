from tkinter import *
from tkinter import ttk
from device import DeviceInfo, AudioStream, AudioData, AudioStation
from consumer import HttpSender, FileSaver, QueueConsumer
from threading import Thread


class Choice:
    HTTP = 'HTTP'
    FILE = 'FILE'
    QUEUE = 'QUEUE'


class Application(Tk):
    def __init__(self):
        super().__init__()
        self.thread = None
        self.station = None
        self.exporter = None
        self.title("Audio Stream Configuration")
        self.geometry('960x480')
        # self.maxsize(640, 480)
        self.__iface_init()

    def __iface_init(self):

        dev_button = Button(self, text="Get Mics", command=self.get_items)
        dev_button.grid(row=1, column=0, padx=5, pady=5)

        self.dev_box = Listbox(selectmode=EXTENDED)
        self.dev_box.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=E+W)
        self.dev_selected_box = Listbox(selectmode=EXTENDED)
        self.dev_selected_box.bind('<<ListboxSelect>>', self.listbox_modified)
        self.dev_selected_box.grid(row=2, column=3, columnspan=2, padx=5, pady=5, sticky=W)

        l_button = Button(self, text=">>>",
                          command=lambda i=self.dev_box, j=self.dev_selected_box: self.box_items_replace(i, j))
        l_button.grid(row=2, column=2, padx=5, pady=5, sticky=N)
        r_button = Button(self, text="<<<",
                          command=lambda i=self.dev_selected_box, j=self.dev_box: self.box_items_replace(i, j))
        r_button.grid(row=2, column=2, padx=5, pady=5, sticky=S)

        self.combobox = ttk.Combobox(values=['HTTP', 'FILE', 'QUEUE'], state="readonly")
        self.combobox.bind('<<ComboboxSelected>>', self.combobox_modified)
        self.combobox.grid(row=2, column=5, padx=5, pady=5, sticky=N+W)

        self.action_button = Button(self, text="Choose", command=self.get_choice, state=DISABLED)
        self.action_button.grid(row=2, column=5)

        self.choice_label = Label(self, text="")
        self.choice_entry = Entry(self)
        self.text = Text(width=60, height=10)

        self.start_button = Button(self, text="Start", command=self.start_streams, state=DISABLED)
        self.start_button.grid(row=5, column=2)
        self.stop_button = Button(self, text="Stop", command=self.stop_stream, state=DISABLED)
        self.stop_button.grid(row=5, column=3)

    def combobox_modified(self, event):
        self.choice_label.grid_remove()
        self.choice_entry.grid_remove()
        self.text.grid_remove()
        self.action_button.config(state=NORMAL)

    def listbox_modified(self, event):
        list_box_len = len(self.dev_selected_box.get(0, END))
        if list_box_len > 0 and self.combobox.get():
            self.start_button.config(state=NORMAL)
        else:
            self.start_button.config(state=DISABLED)

    def get_choice(self):
        choice = self.combobox.get()
        if choice == Choice.HTTP:
            self.choice_label.config(text="Server URL:")
            self.choice_label.grid(row=2, column=5, padx=5, pady=5, sticky=S+W)
            self.choice_entry.grid(row=2, column=6, padx=5, pady=5, sticky=S+W)
        elif choice == Choice.FILE:
            self.choice_label.config(text="Filename:")
            self.choice_label.grid(row=2, column=5, padx=5, pady=5, sticky=S+W)
            self.choice_entry.grid(row=2, column=6, padx=5, pady=5, sticky=S+W)
        elif choice == Choice.QUEUE:
            self.text.grid(row=4, column=1, padx=5, pady=5, sticky=N+W)
        else:
            print('CHOOSE')
        return choice

    def get_items(self):
        dev_info = DeviceInfo()
        devs = dev_info.get_mic_devices()
        formatted_devs = [f"{x['index']}: {x['name']}" for x in devs]
        for i in formatted_devs:
            self.dev_box.insert(END, i)

    def box_items_replace(self, first, second):
        select = first.curselection()
        for i in select:
            second.insert(END, first.get(i))
        select = list(select)
        select.reverse()
        for i in select:
            first.delete(i)

    def start_streams(self):

        mics = self.dev_selected_box.get(0, END)
        list_audio_streams = []
        for el in mics:
            ind, name, *other = el.split(":")
            a = AudioStream(int(ind), 1, 44100)
            list_audio_streams.append(a)

        choice = self.get_choice()
        param = self.choice_entry.get()

        audio_data = AudioData()
        self.station = AudioStation(audio_data, list_audio_streams)

        if choice == Choice.HTTP:
            url = param if param else '192.168.0.1'
            self.exporter = HttpSender(audio_data, url)
        elif choice == Choice.FILE:
            filename = param if param else 'data.txt'
            self.exporter = FileSaver(audio_data, filename)
        elif choice == Choice.QUEUE:
            self.exporter = QueueConsumer(audio_data)
            self.thread = Thread(target=self.__print_buffer, daemon=True)
            self.thread.start()

        self.stop_button.config(state=NORMAL)
        self.start_button.config(state=DISABLED)
        self.station.start()

    def stop_stream(self):
        self.station.stop()
        self.stop_button.config(state=DISABLED)
        self.start_button.config(state=NORMAL)

    def __print_buffer(self):
        while True:
            msg = self.exporter.deque.get()
            self.text.insert(1.0, str(msg) + '\n')


if __name__ == "__main__":
    app = Application()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print('Exit')
