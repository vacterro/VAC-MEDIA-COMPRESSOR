import json
import os
from pathlib import Path

DEFAULT_THEMES = {
    "Vintage 95": {
        "background": "#C0C0C0",
        "surface": "#C0C0C0",
        "surfaceRaised": "#FFFFFF",
        "surfaceAlt": "#E6E6E6",
        "borderSubtle": "#808080",
        "borderStrong": "#404040",
        "borderHighlight": "#FFFFFF",
        "textPrimary": "#000000",
        "textSecondary": "#202020",
        "textMuted": "#666666",
        "accentTurquoise": "#008080",
        "accentTurquoiseDim": "#006666",
        "accentTealDeep": "#004C4C",
        "blackBrown": "#1A1208",
        "success": "#008000",
        "warning": "#808000",
        "danger": "#800000",
        "bg_header": "#008080",  # Turquoise for selected text bg
    }
}

class ThemeManager:
    def __init__(self, config_path="theme_config.json"):
        self.config_path = config_path
        self.themes = DEFAULT_THEMES.copy()
        
        self.config = {
            "active_theme": "Vintage 95",
            "is_custom": False,
            "font_size": 14,
            "custom_palette": self.themes["Vintage 95"].copy()
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
        if self.config.get("is_custom", False):
            return self.config.get("custom_palette", self.themes["Vintage 95"])
        name = self.config.get("active_theme", "Vintage 95")
        return self.themes.get(name, self.themes["Vintage 95"])

    def set_active_theme(self, name: str):
        if name in self.themes:
            self.config["active_theme"] = name
            self.save_config()

    def get_active_theme_name(self) -> str:
        return self.config.get("active_theme", "Vintage 95")

    def update_custom_color(self, key: str, hex_color: str):
        self.config["custom_palette"][key] = hex_color
        self.themes["Custom"] = self.config["custom_palette"]
        self.save_config()

    def get_font_family(self) -> str:
        return self.config.get("font_family", "MS Sans Serif")

    def set_font_family(self, font: str):
        self.config["font_family"] = font
        self.save_config()

    def get_font_size(self) -> int:
        return self.config.get("font_size", 14)

    def set_font_size(self, size: int):
        self.config["font_size"] = size
        self.save_config()
