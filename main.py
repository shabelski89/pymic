from station.iface import Application


if __name__ == "__main__":
    app = Application()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print('Exit')
