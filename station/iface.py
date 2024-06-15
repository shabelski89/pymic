from tkinter import *
from tkinter import ttk
from threading import Thread
from tkinter.messagebox import showwarning
try:
    from .device import DeviceInfo, AudioStream, AudioData, AudioStation
    from .consumer import HttpSender, FileSaver, QueueConsumer
except ImportError:
    from device import DeviceInfo, AudioStream, AudioData, AudioStation
    from consumer import HttpSender, FileSaver, QueueConsumer


CHOICES = {'HTTP': 'IP-address', 'FILE': 'Filename', 'QUEUE': None}


class Application(Tk):
    def __init__(self):
        super().__init__()
        self.thread = None
        self.station = None
        self.exporter = None
        self.title("Audio Stream Configuration")
        self.geometry('640x480')
        self.running = False
        self.__iface_init()

    def __iface_init(self):

        self.frame_one = Frame(self, borderwidth=1)
        self.frame_two = Frame(self, borderwidth=1)
        self.frame_three = Frame(self, borderwidth=1)
        self.frame_four = Frame(self, borderwidth=1)
        self.frame_five = Frame(self, borderwidth=1)

        self.frame_one.pack()
        self.frame_two.pack(fill=X)
        self.frame_three.pack()
        self.frame_four.pack()
        self.frame_five.pack(fill=X)

        dev_button = Button(self.frame_one, text="Get Mics", command=self.get_items)
        dev_button.pack()

        self.dev_box = Listbox(self.frame_two, selectmode=EXTENDED)
        self.dev_box.pack(side=LEFT, padx=5, pady=5, expand=1, anchor=W, fill=X)
        self.dev_selected_box = Listbox(self.frame_two, selectmode=EXTENDED)
        self.dev_selected_box.bind('<<ListboxSelect>>', self.listbox_modified)
        self.dev_selected_box.pack(side=RIGHT, padx=5, pady=5, expand=1, anchor=E, fill=X)

        self.l_button = Button(self.frame_two, text=">>>", command=lambda: self.box_items_replace(1))
        self.l_button.pack(side=TOP, padx=5, pady=5)
        self.r_button = Button(self.frame_two, text="<<<", command=lambda: self.box_items_replace(2))
        self.r_button.pack(side=BOTTOM, padx=5, pady=5)

        combobox_values = [x for x in CHOICES]
        self.combobox = ttk.Combobox(self.frame_three, values=combobox_values, state=DISABLED)
        self.combobox.current(0)
        self.combobox.bind('<<ComboboxSelected>>', self.combobox_modified)
        self.combobox.pack(side=LEFT, padx=5, pady=5, anchor=E)

        self.combobox_rate = ttk.Combobox(self.frame_three, values=['44100', '48000'], state=DISABLED)
        self.combobox_rate.current(0)
        self.combobox_rate.pack(side=LEFT, padx=5, pady=5, anchor=E)

        self.choice_entry = Entry(self.frame_three)
        self.choice_entry.bind("<KeyRelease>", self.check_choice_entry)
        self.choice_entry.pack(side=RIGHT, padx=5, pady=5)
        self.choice_entry.config(state=DISABLED)
        self.choice_label = Label(self.frame_three, text=CHOICES[combobox_values[0]])
        self.choice_label.pack(side=RIGHT, padx=5, pady=5)
        self.text = Text(self.frame_five, width=60, height=10)
        self.text.pack(side=TOP, padx=5, pady=5)

        self.stop_button = Button(self.frame_four, text="Stop", command=self.stop_stream, state=DISABLED)
        self.stop_button.pack(side=RIGHT, padx=5, pady=5)
        self.start_button = Button(self.frame_four, text="Start", command=self.start_streams, state=DISABLED)
        self.start_button.pack(side=RIGHT, padx=5, pady=5)

    def box_items_replace(self, button_id):
        if button_id == 1:
            first = self.dev_box
            second = self.dev_selected_box
        else:
            first = self.dev_selected_box
            second = self.dev_box

        select = first.curselection()
        for i in select:
            second.insert(END, first.get(i))
        select = list(select)
        select.reverse()
        for i in select:
            first.delete(i)
        self.check_listbox()

    def check_listbox(self):
        len_selected_box = len(self.dev_selected_box.get(0, END))
        if len_selected_box > 0:
            self.combobox.config(state=NORMAL)
            self.combobox_rate.config(state=NORMAL)
            self.get_choice()
        else:
            self.combobox.config(state=DISABLED)
            self.combobox_rate.config(state=DISABLED)

    def combobox_modified(self, event):
        self.get_choice()

    def check_choice_entry(self, event):
        self.start_button.config(state=NORMAL)

    def listbox_modified(self, event):
        list_box_len = len(self.dev_selected_box.get(0, END))
        if list_box_len > 0 and self.combobox.get():
            self.start_button.config(state=NORMAL)
        else:
            self.start_button.config(state=DISABLED)

    def get_choice(self):
        choice = self.combobox.get()
        if choice == 'HTTP':
            self.choice_entry.config(state=NORMAL)
            self.choice_label.config(text=CHOICES[choice])
        elif choice == 'FILE':
            self.choice_entry.config(state=NORMAL)
            self.choice_label.config(text=CHOICES[choice])
        elif choice == 'QUEUE':
            self.choice_label.config(text="")
            self.choice_entry.config(state=DISABLED)
            self.start_button.config(state=NORMAL)
        return choice

    def get_items(self):
        if len(self.dev_box.get(0, END)) > 0:
            self.dev_box.delete(0, END)

        dev_info = DeviceInfo()
        devs = dev_info.get_mic_devices()
        formatted_devs = [f"{x['index']}: {x['name']}" for x in devs]
        for i in formatted_devs:
            self.dev_box.insert(END, i)

    def start_streams(self):
        if self.running:
            self.stop_stream()

        mics = self.dev_selected_box.get(0, END)
        list_audio_streams = []
        for el in mics:
            ind, name, *other = el.split(":")
            a = AudioStream(int(ind), 1, int(self.combobox_rate.get()))
            list_audio_streams.append(a)

        choice = self.get_choice()
        param = self.choice_entry.get()

        audio_data = AudioData()
        self.station = AudioStation(audio_data, list_audio_streams)

        if choice in ['HTTP', 'FILE'] and not self.choice_entry.get():
            showwarning(title="Предупреждение", message=f"Пустое поле - {CHOICES.get('HTTP')}")
            return

        if choice == 'HTTP':
            self.exporter = HttpSender(audio_data, param)
        elif choice == 'FILE':
            self.exporter = FileSaver(audio_data, param)
        elif choice == 'QUEUE':
            self.exporter = QueueConsumer(audio_data)
            self.thread = Thread(target=self.__print_buffer, name='QUEUE')
            self.running = True
            self.thread.start()

        self.stop_button.config(state=NORMAL)
        self.start_button.config(state=DISABLED)
        self.station.start()
        self.running = True

    def stop_stream(self):
        self.station.stop()
        self.stop_button.config(state=DISABLED)
        self.start_button.config(state=NORMAL)
        self.running = False

        if self.thread:
            self.thread = None

            with self.exporter.deque.mutex:
                self.exporter.deque.queue.clear()

    def __print_buffer(self):
        while self.running:
            msg = self.exporter.deque.get()
            self.text.insert(1.0, str(msg) + '\n')


if __name__ == "__main__":
    app = Application()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print('Exit')
