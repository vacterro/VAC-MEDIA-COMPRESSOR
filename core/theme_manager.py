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
    }
}

class ThemeManager:
    def __init__(self, config_path="theme_config.json"):
        self.config_path = config_path
        self.themes = DEFAULT_THEMES.copy()
        
        self.config = {
            "active_theme": "Synthwave",
            "custom_palette": self.themes["Synthwave"].copy()
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
