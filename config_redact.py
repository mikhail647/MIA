import sys

import wx.adv
import PySimpleGUI as sg
import yaml
import os
import windowsapps
import speech_recognition as sr

RECOGNIZER = sr.Recognizer()
RECOGNIZER.pause_threshold = 0.5

config = "mia-1-2-0/bin/config.yaml"
with open(config, encoding="utf-8") as f:
    read_data = yaml.safe_load(f)

def listen():
    try:
        with sr.Microphone() as microphone:
            RECOGNIZER.adjust_for_ambient_noise(
                source=microphone,
                duration=0.5
            )
            audio = RECOGNIZER.listen(source=microphone)
            query = RECOGNIZER.recognize_google(
                audio_data=audio,
                language='ru-RU'
            ).lower()
            print(query)
            return query
    except sr.UnknownValueError:
        print(" ")
        listen()


def writer(name, cmd_world):
    if name in read_data['mia_cmd_open']:
        read_data['mia_cmd_open'][name]['cmd_worlds'] = [cmd_world]
        read_data['mia_cmd_open'][name]['name'] = name
    else:
        writedict = {
            'cmd_worlds': [cmd_world],
            'name': name,
            'patch': "null",
            'process_name': "null"
        }
        read_data['mia_cmd_open'][name] = writedict


def is_ascii(s):
    return all(ord(c) < 128 for c in s)

def confredact():
    list_apps_nosort = sorted(list(windowsapps.get_apps().keys()))
    list_apps = [element for element in list_apps_nosort if is_ascii(element)]

    sg.theme('Dark')
    tab1layout = [[sg.T('Конфигурация')],
                  [sg.T('Выбор приложения')],
                  [sg.Combo(list_apps, key='selection')],
                  # тут список и кнопка. KEY это есть "тег" элемента, к которому обращаются ивенты и валью
                  [sg.T('распознаное слово')],
                  [sg.InputText(key='namechange'), sg.B('Распознать', key='runrespond')],
                  [sg.B('Сохранить', key='savename')],
                  ]

    tab2layout = [[sg.T('тут много текста')]]
    layout = [[sg.TabGroup([[sg.Tab('Конфиг', tab1layout)], [sg.Tab('Помощь', tab2layout)]])]]

    window = sg.Window('Config Changes', layout)
    while True:
        event, values = window.read()
        if event == 'runrespond':
            # если прожата кнопка, то он берет и вставляет выбранный в списке текст в поля для ввода,
            # думаю под вставку из ямль-я не сложно переделать будет
            window['namechange'].update("Скажитее название приложения, оно появится здесь")
            window['namechange'].update(str(listen()))
        if event == 'savename':  # сохраняет вписанное имя (пока только выводит в консоль)
            writer(values['selection'], values['namechange'])
            with open('config.yaml', 'w', encoding="utf-8") as f: yaml.dump(read_data, f, allow_unicode=True)
            window['namechange'].update("Имя успешно сохранено")

        if event == sg.WIN_CLOSED:
            break
class MyTaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame):
        super().__init__()
        self.frame = frame

        # Загружаем изображение для иконки
        icon = wx.Icon("mia-1-2-0/bin/mia.ico", wx.BITMAP_TYPE_ICO)

        self.SetIcon(icon, "Tooltip for tray icon")
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.adv.EVT_TASKBAR_RIGHT_DOWN, self.on_right_down)

    def on_left_down(self, event):
        confredact()

    def on_right_down(self, event):
        # При нажатии на правую кнопку мыши
        self.ShowContextMenu()

    def ShowContextMenu(self):
        # Создаем контекстное меню
        menu = wx.Menu()
        # Добавляем пункт "Закрыть"
        close_item = menu.Append(-1, "Закрыть")
        self.Bind(wx.EVT_MENU, self.OnClose, close_item)
        # Отображаем меню
        self.PopupMenu(menu)
        menu.Destroy()

    def OnClose(self, event):
        # При нажатии на пункт "Закрыть"
        wx.GetApp().ExitMainLoop()
        sys.exit()


def icon():
    app = wx.App()
    frame = wx.Frame(None)
    task_bar_icon = MyTaskBarIcon(frame)
    app.MainLoop()

icon()