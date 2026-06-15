import json
import os
from pathlib import Path

DEFAULT_THEMES = {
    "Synthwave": {
        "bg_base": "#121212",
        "bg_surface": "#1E1E1E",
        "bg_surface_hover": "#2C2C2C",
        "bg_header": "#1A1A1A",
        "bg_log": "#0F0F0F",
        "text_main": "#FFFFFF",
        "text_muted": "#A0A0A0",
        "border": "#333333",
        "primary": "#BB86FC",
        "primary_hover": "#D0A9FF",
        "primary_pressed": "#9C4DFF",
        "primary_button": "#3700B3",
        "primary_button_hover": "#6200EE",
        "secondary": "#03DAC6",
        "secondary_hover": "#018786",
        "danger": "#CF6679",
        "danger_hover": "#B00020"
    },
    "Ocean Blue": {
        "bg_base": "#0B132B",
        "bg_surface": "#1C2541",
        "bg_surface_hover": "#3A506B",
        "bg_header": "#121A33",
        "bg_log": "#060A17",
        "text_main": "#F0F8FF",
        "text_muted": "#9BA8B5",
        "border": "#3A506B",
        "primary": "#5BC0BE",
        "primary_hover": "#78D3D1",
        "primary_pressed": "#3A9B99",
        "primary_button": "#1A659E",
        "primary_button_hover": "#2881C3",
        "secondary": "#FFB703",
        "secondary_hover": "#FB8500",
        "danger": "#FF4D4D",
        "danger_hover": "#D32F2F"
    },
    "Dracula": {
        "bg_base": "#282A36",
        "bg_surface": "#44475A",
        "bg_surface_hover": "#6272A4",
        "bg_header": "#21222C",
        "bg_log": "#1E1F29",
        "text_main": "#F8F8F2",
        "text_muted": "#6272A4",
        "border": "#44475A",
        "primary": "#FF79C6",
        "primary_hover": "#FF92D0",
        "primary_pressed": "#FF5EB8",
        "primary_button": "#BD93F9",
        "primary_button_hover": "#D0A9FF",
        "secondary": "#50FA7B",
        "secondary_hover": "#3EDB69",
        "danger": "#FF5555",
        "danger_hover": "#FF3333"
    },
    "Charcoal Dark": {
        "bg_base": "#1E1E1E",
        "bg_surface": "#252526",
        "bg_surface_hover": "#2D2D30",
        "bg_header": "#1A1A1A",
        "bg_log": "#181818",
        "text_main": "#D4D4D4",
        "text_muted": "#858585",
        "border": "#3E3E42",
        "primary": "#007ACC",
        "primary_hover": "#1C97EA",
        "primary_pressed": "#005A9E",
        "primary_button": "#0E639C",
        "primary_button_hover": "#1177BB",
        "secondary": "#4EC9B0",
        "secondary_hover": "#42A892",
        "danger": "#F14C4C",
        "danger_hover": "#D13A3A"
    },
    "Midnight Violet": {
        "bg_base": "#0E0914",
        "bg_surface": "#16111D",
        "bg_surface_hover": "#221A2D",
        "bg_header": "#0B0710",
        "bg_log": "#09060D",
        "text_main": "#E2D9EE",
        "text_muted": "#8A7D9D",
        "border": "#2C223C",
        "primary": "#B271FF",
        "primary_hover": "#C996FF",
        "primary_pressed": "#8833FF",
        "primary_button": "#5E2C99",
        "primary_button_hover": "#7D3DCC",
        "secondary": "#F92AAD",
        "secondary_hover": "#D71891",
        "danger": "#FF2A55",
        "danger_hover": "#D6183D"
    },
    "Obsidian Green": {
        "bg_base": "#080C0A",
        "bg_surface": "#0C1310",
        "bg_surface_hover": "#15201A",
        "bg_header": "#050807",
        "bg_log": "#030504",
        "text_main": "#D1E8DB",
        "text_muted": "#698F7A",
        "border": "#1A2822",
        "primary": "#00FF66",
        "primary_hover": "#4DFF94",
        "primary_pressed": "#00CC52",
        "primary_button": "#008033",
        "primary_button_hover": "#00B347",
        "secondary": "#00E5FF",
        "secondary_hover": "#00B8CC",
        "danger": "#FF3333",
        "danger_hover": "#CC0000"
    },
    "Eye Care Gold": {
        "bg_base": "#1a1814",
        "bg_surface": "#26221c",
        "bg_surface_hover": "#332d25",
        "bg_header": "#14120e",
        "bg_log": "#14120e",
        "text_main": "#e6d5b8",
        "text_muted": "#a69b86",
        "border": "#40392f",
        "primary": "#d4af37",
        "primary_hover": "#ebd373",
        "primary_pressed": "#ad8c26",
        "primary_button": "#8c721f",
        "primary_button_hover": "#ad8c26",
        "secondary": "#a16b47",
        "secondary_hover": "#c28760",
        "danger": "#a34141",
        "danger_hover": "#c45656"
    }
}

class ThemeManager:
    def __init__(self, config_path="theme_config.json"):
        self.config_path = config_path
        self.themes = DEFAULT_THEMES.copy()
        
        self.config = {
            "active_theme": "Eye Care Gold",
            "font_family": "",
            "font_size": 14,
            "custom_palette": self.themes["Eye Care Gold"].copy()
        }
        self.load_config()

    def load_config(self):
        if Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    self.config.update(data)
            except Exception:
                pass

        self.themes["Custom"] = self.config["custom_palette"]

    def save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get_palette(self) -> dict:
        name = self.config.get("active_theme", "Synthwave")
        return self.themes.get(name, self.themes["Synthwave"])

    def set_active_theme(self, name: str):
        if name in self.themes:
            self.config["active_theme"] = name
            self.save_config()

    def get_active_theme_name(self) -> str:
        return self.config.get("active_theme", "Synthwave")

    def update_custom_color(self, key: str, hex_color: str):
        self.config["custom_palette"][key] = hex_color
        self.themes["Custom"] = self.config["custom_palette"]
        self.save_config()

    def get_font_family(self) -> str:
        return self.config.get("font_family", "")

    def set_font_family(self, font: str):
        self.config["font_family"] = font
        self.save_config()

    def get_font_size(self) -> int:
        return self.config.get("font_size", 14)

    def set_font_size(self, size: int):
        self.config["font_size"] = size
        self.save_config()
