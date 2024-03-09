import time
import random
import yaml
import os

import torch
import psutil

import sounddevice as sd
import speech_recognition as sr

from windowsapps import open_app
from omegaconf import OmegaConf
from fuzzywuzzy import fuzz
from enum import Enum
import subprocess

RECOGNIZER = sr.Recognizer()
RECOGNIZER.pause_threshold = 0.5

config = "mia-1-2-0/bin/config.yaml"
with open(config, encoding="utf-8") as f: read_data = yaml.safe_load(f)

# import model
torch.hub.download_url_to_file(
    'https://raw.githubusercontent.com/snakers4/silero-models/master/models.yml',
    'latest_silero_models.yml',
    progress=False
)
models = OmegaConf.load('latest_silero_models.yml')
sample_rate = 48_000
speaker = 'xenia'
put_accent = True
put_yo = True
device = torch.device('cpu')
text = " "
model, _ = torch.hub.load(
    repo_or_dir='snakers4/silero-models',
    model='silero_tts',
    language='ru',
    speaker='v3_1_ru'
)
model.to(device)


def va_speak(what: str):
    audio = model.apply_tts(text=what + "..",
                            speaker=speaker,
                            sample_rate=sample_rate,
                            put_accent=put_accent,
                            put_yo=put_yo)

    sd.play(audio, sample_rate * 1.05)
    time.sleep((len(audio) / sample_rate) + 0.5)
    sd.stop()


#######
class CmdAction(Enum):
    OPEN = 0
    CLOSE = 1
    SEARCH = 2


START_COMMANDS = {

    'запусти': CmdAction.OPEN,
    'включи': CmdAction.OPEN,
    'открой': CmdAction.OPEN,

    'закрой': CmdAction.CLOSE,
    'выключи': CmdAction.CLOSE,
    'останови': CmdAction.CLOSE,

    'скажи': CmdAction.SEARCH,
    'найди': CmdAction.SEARCH,
    'ответь': CmdAction.SEARCH

}


def search_cmd_start(text: str):
    text_split = text.split()
    actions = []
    Programs = []
    index = len(text_split) - 1

    while index != -1:

        for cmd_tag, cmd_move in START_COMMANDS.items():
            if fuzz.ratio(cmd_tag, text_split[index]) >= 70:
                Programs.append(text.split(text_split[index])[1][1:])
                text = text.split(text_split[index])[0][0:]
                actions.append(cmd_move)

        index = index - 1
    if Programs == []: search_inf(text)
    Programs.reverse()
    actions.reverse()
    programs_main(actions, Programs)


def search_programs(text):
    keys = []
    types = []

    for worlds_text in str(text).split():

        for key in read_data['mia_cmd_open']:

            for worlds_dict in read_data['mia_cmd_open'][key]['cmd_worlds']:

                if fuzz.ratio(worlds_text, worlds_dict) >= 65:
                    keys.append(key)

    return keys


def search_process(proc_search):
    global proc_name
    proc_name = proc_search
    for proc in psutil.process_iter():
        proc_name_in_loop = proc.name()
        try:
            proc_name_in_loop = proc.name()
        except psutil.NoSuchProcess:
            pass
        else:
            if proc_name_in_loop == proc_name:
                return proc.exe()


def programs_start(programs):
    for program in programs:
        try:
            open_app(read_data['mia_cmd_open'][program]["name"])
            va_speak(random.choice(read_data["mia_reactions"]["default"]))
        except:
            print("except")


def programs_close(programs):
    for program in programs:
        THRESHOLD = 80
        for proc in psutil.process_iter(['pid', 'name']):
            ratio = fuzz.partial_ratio(program, proc.info['name'])
            if ratio >= THRESHOLD:
                subprocess.run(['taskkill', "/F", "/PID", str(proc.info['pid'])])


def filter_letters_and_spaces(message):
    filtered_message = ''.join(c for c in message if c.isalpha() or c.isspace())
    return filtered_message


def search_inf(question):
    from openai import OpenAI
    api_key = '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'
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant, who answering only worlds."},
            {"role": "user", "content": question}
        ]
    )
    answer = str(str(list(response)[1][1]).split("content=", 1)[1:]).split("role=", 1)[0:][0]
    va_speak(filter_letters_and_spaces(answer))


def programs_main(Actions, Programs):
    index = 0
    Programs = search_programs(Programs)
    for action in Actions:

        if action == CmdAction.OPEN: programs_start(Programs)

        if action == CmdAction.CLOSE: programs_close(Programs)

        if action == CmdAction.SEARCH: search_inf(Programs[index])

        index = index + 1


def respond(voice: str):
    if voice == None: return None
    for world in ('миа', 'мия', 'mia'):
        if world in voice:
            search_cmd_start(voice.split(world, 1)[1][1:])


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
def close():
    os.kill(os.getpid())
