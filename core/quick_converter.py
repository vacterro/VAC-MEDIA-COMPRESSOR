import os
from pathlib import Path
from .utils import find_tool, run_subprocess

class QuickConverter:
    IMAGE_EXTS = frozenset({'.png', '.jpg', '.jpeg', '.tga', '.dds', '.pic', '.webp', '.bmp', '.tif', '.tiff', '.gif'})
    VIDEO_EXTS = frozenset({'.mp4', '.mkv', '.avi', '.mov', '.m4v', '.webm', '.flv', '.wmv'})

    def __init__(self):
        self.texconv_bin = find_tool("texconv")
        self.ffmpeg_bin = find_tool("ffmpeg")
        self.magick_bin = find_tool("magick")

    def get_file_type(self, path: str) -> str:
        ext = Path(path).suffix.lower()
        if ext in self.IMAGE_EXTS:
            return "Image"
        elif ext in self.VIDEO_EXTS:
            return "Video"
        return "Unknown"

    def process_image(self, path: str, action: str, option: str, adjustments: dict = None) -> tuple[bool, str]:
        p = Path(path)
        if not p.exists():
            return False, "File not found"

        # Special Legacy / Texture Actions
        if action == "DDS -> PNG (texconv / Pillow)":
            return self._dds_to_png(p)
        elif action.startswith("PNG -> DDS"):
            return self._png_to_dds_advanced(p, action)
        elif action == "PIC -> TGA (8x Upscale Nearest)":
            return self._pic_to_tga_8x(p)
        elif action == "TGA -> PNG (Lossless)":
            return self._convert_via_pillow(p, ".png", "PNG")
        elif action == "PNG -> TGA (Lossless)":
            return self._convert_via_pillow(p, ".tga", "TGA")
        elif action.startswith("2x Upscale") or action.startswith("4x Upscale") or action.startswith("8x Upscale"):
            return self._upscale_image(p, action)

        # Standard Magick Actions
        if not self.magick_bin:
            return False, "ImageMagick ('magick' command) not found in PATH."

        dst_ext = p.suffix
        action_args = []
        out_suffix = ""

        if action == "Convert to JPG":
            dst_ext = ".jpg"
        elif action == "Convert to WEBP":
            dst_ext = ".webp"
        elif action == "Palette 512 colors":
            action_args = ["-colors", "512"]
            out_suffix = "_cq512"
        elif action == "Palette 2048 colors":
            action_args = ["-colors", "2048"]
            out_suffix = "_cq2048"
        elif action == "Lossy Compress":
            action_args = ["-quality", "80"]
            out_suffix = "_lossy"
        elif action == "Web Compress":
            dst_ext = ".webp"
            action_args = ["-quality", "80"]
            out_suffix = "_web"

        import re
        resize_match = re.search(r"Resize\s*(\d+)%", option, re.IGNORECASE)
        if resize_match:
            val = min(int(resize_match.group(1)), 1200)
            action_args.extend(["-resize", f"{val}%"])
            out_suffix += f"_per{val}"
            
        if adjustments:
            b = adjustments.get('brightness', 100)
            c = adjustments.get('contrast', 100)
            s = adjustments.get('saturation', 100)
            if b != 100 or c != 100 or s != 100:
                # -brightness-contrast takes values between -100 to 100, where 0 is no change.
                # our slider is 0 to 200, 100 is no change. So we subtract 100.
                b_magick = b - 100
                c_magick = c - 100
                action_args.extend(["-brightness-contrast", f"{b_magick}x{c_magick}"])
                
                # -modulate brightness,saturation,hue. Default is 100,100,100.
                # We already did brightness. Let's just do saturation. 100 means no change.
                if s != 100:
                    action_args.extend(["-modulate", f"100,{s},100"])
                    
                out_suffix += "_adj"

        dst_name = f"{p.stem}{out_suffix}{dst_ext}"
        dst = p.with_name(dst_name)

        cmd = [self.magick_bin, str(p)] + action_args + [str(dst)]
        success, msg = run_subprocess(cmd)
        if success and dst.exists():
            return True, f"Processed -> {dst.name}"
        return False, f"Failed: {msg}"

    def process_video(self, path: str, action: str, option: str, adjustments: dict = None) -> tuple[bool, str]:
        p = Path(path)
        if not p.exists():
            return False, "File not found"

        if not self.ffmpeg_bin:
            return False, "FFmpeg not found in PATH."

        dst_name = ""
        
        # Build base input args
        input_args = ["-y"]
        if adjustments:
            trim_start = adjustments.get('trim_start')
            if trim_start:
                input_args.extend(["-ss", trim_start])
                
        input_args.extend(["-i", str(p)])
        
        cmd = [self.ffmpeg_bin] + input_args

        if action == "Extract Audio (MP3)":
            dst_name = f"{p.stem}_audio.mp3"
            cmd.extend(["-vn", "-c:a", "libmp3lame", "-q:a", "2"])
        elif action == "Extract Audio (WAV)":
            dst_name = f"{p.stem}_audio.wav"
            cmd.extend(["-vn", "-c:a", "pcm_s16le"])
        elif action == "Remove Audio (Fast / Copy)":
            dst_name = f"{p.stem}_noaudio{p.suffix}"
            cmd.extend(["-c", "copy", "-an"])
        elif action == "Remove Audio (Slow / Compress)":
            dst_name = f"{p.stem}_noaudio_compressed{p.suffix}"
            cmd.extend(["-c:v", "libsvtav1", "-crf", "30", "-preset", "5", "-an"])
        elif action == "Extract Frames":
            dst_dir = p.parent / f"{p.stem}_frames"
            dst_dir.mkdir(exist_ok=True)
            dst_name = f"{p.stem}_frames/%04d.jpg"
            cmd.extend(["-q:v", "2"])
            dst = dst_dir / "%04d.jpg" # For return message context
        elif action == "Make GIF (High Quality)":
            dst_name = f"{p.stem}_hq.gif"
            cmd.extend(["-vf", "split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"])
        elif action == "Make GIF (Small)":
            dst_name = f"{p.stem}_small.gif"
            cmd.extend(["-vf", "fps=10,scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"])
        elif action == "Compress MKV (AV1)":
            dst_name = f"{p.stem}_compressed.mkv"
            cmd.extend(["-c:v", "libsvtav1", "-preset", "6", "-crf", "28", "-c:a", "copy"])
        elif action == "Compress MP4 (AV1)":
            dst_name = f"{p.stem}_compressed.mp4"
            cmd.extend(["-c:v", "libsvtav1", "-preset", "6", "-crf", "28", "-c:a", "copy"])
        elif action.startswith("Convert Format ("):
            # e.g. Convert Format (AVI)
            fmt = action.split("(")[1].strip(")")
            dst_name = f"{p.stem}_converted.{fmt.lower()}"
            cmd.extend(["-c", "copy"]) # Best effort copy, ffmpeg auto remuxes

        if action != "Extract Frames":
            if adjustments:
                trim_end = adjustments.get('trim_end')
                if trim_end:
                    cmd.extend(["-to", trim_end])
                    dst_name = dst_name.replace(".", "_trimmed.")
            dst = p.with_name(dst_name)
            cmd.append(str(dst))
        else:
            cmd.append(str(dst_dir / "%04d.jpg"))

        success, msg = run_subprocess(cmd)
        if success:
            return True, f"Processed action: {action}"
        return False, f"FFmpeg failed: {msg}"

    # --- Legacy Quick Actions ---
    def _dds_to_png(self, p: Path) -> tuple[bool, str]:
        dst = p.with_suffix(".png")
        if self.texconv_bin:
            cmd = [self.texconv_bin, "-ft", "png", "-y", "-o", str(p.parent), str(p)]
            success, _ = run_subprocess(cmd)
            if success and dst.exists(): return True, "Converted via texconv"
        try:
            from PIL import Image
            with Image.open(p) as img:
                if img.mode != "RGBA": img = img.convert("RGBA")
                img.save(dst, format="PNG")
            return True, "Converted via Pillow"
        except Exception as e:
            return False, f"Failed: {e}"

    def _png_to_dds_advanced(self, p: Path, action: str) -> tuple[bool, str]:
        if not self.texconv_bin: 
            return False, "texconv.exe required for DDS encoding"
        
        fmt = "BC7_UNORM"
        if "BC3" in action:
            fmt = "BC3_UNORM"
        elif "BC1" in action:
            fmt = "BC1_UNORM"
        elif "BC5" in action:
            fmt = "BC5_UNORM"
            
        cmd = [self.texconv_bin, "-ft", "dds", "-f", fmt, "-y", "-o", str(p.parent), str(p)]
        success, msg = run_subprocess(cmd)
        if success: return True, f"Converted to DDS ({fmt})"
        return False, f"texconv failed: {msg}"

    def _pic_to_tga_8x(self, p: Path) -> tuple[bool, str]:
        try:
            from PIL import Image
            with Image.open(p) as img:
                img = img.resize((img.width * 8, img.height * 8), resample=Image.Resampling.NEAREST)
                img.save(p.with_suffix(".tga"), format="TGA")
            return True, "Upscaled 8x (NEAREST) to TGA"
        except Exception as e:
            return False, f"Failed: {e}"
            
    def _convert_via_pillow(self, p: Path, ext: str, fmt: str) -> tuple[bool, str]:
        try:
            from PIL import Image
            with Image.open(p) as img:
                if fmt == "PNG" and img.mode not in ["RGB", "RGBA"]:
                    img = img.convert("RGBA")
                img.save(p.with_suffix(ext), format=fmt)
            return True, f"Converted to {fmt}"
        except Exception as e:
            return False, f"Failed: {e}"
            
    def _upscale_image(self, p: Path, action: str) -> tuple[bool, str]:
        try:
            from PIL import Image
            with Image.open(p) as img:
                scale = 2
                if "4x" in action: scale = 4
                if "8x" in action: scale = 8
                
                resample_method = Image.Resampling.LANCZOS
                if "Nearest" in action:
                    resample_method = Image.Resampling.NEAREST
                    
                img = img.resize((img.width * scale, img.height * scale), resample=resample_method)
                
                out_name = f"{p.stem}_{scale}x_upscale{p.suffix}"
                img.save(p.with_name(out_name))
            return True, f"Upscaled {scale}x successfully"
        except Exception as e:
            return False, f"Failed upscaling: {e}"
