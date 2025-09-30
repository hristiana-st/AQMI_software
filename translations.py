import json
import os
import sys

if getattr(sys, "frozen", False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

json_path = os.path.join(base_path, "translations.json")

with open(json_path, "r", encoding="utf-8") as f:
    _translations = json.load(f)

_current_language = "pt"  

def set_language(lang):
    global _current_language
    _current_language = lang

def get_translation():
    global _translations, _current_language
    return _translations.get(_current_language, {})
