import os
from pathlib import Path
from .utils import find_tool, run_subprocess
import subprocess

class VideoProcessor:
    def __init__(self):
        self.ffmpeg_bin = find_tool("ffmpeg")
        self.ffprobe_bin = find_tool("ffprobe")

    def is_supported(self, file_path: str) -> bool:
        ext = Path(file_path).suffix.lower()
        return ext in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.webm', '.ts', '.m2ts', '.m4v', '.flv', '.vob', '.mpg', '.mpeg']

    def process(self, file_path: str, preset: str, overwrite: bool, suffix: str, target_dir: str = None, crf_override: str = "", fps_override: str = "", res_override: str = "") -> tuple[bool, str, str]:
        if not self.is_supported(file_path):
            return False, "Unsupported video extension", ""

        if not self.ffmpeg_bin:
            return False, "ffmpeg not found in PATH", ""

        p = Path(file_path)
        out_ext = ".mkv"  # MKV recommended to preserve subtitles

        base_dir = Path(target_dir) if target_dir else p.parent
        if target_dir and not base_dir.exists():
            base_dir.mkdir(parents=True, exist_ok=True)

        if overwrite and not target_dir:
            out_path = p.with_suffix(out_ext)
            # if the original was already mkv, we must write to a temp file first
            temp_path = out_path.with_name(f"{out_path.stem}.tmp{out_ext}")
        else:
            out_path = base_dir / f"{p.stem}{suffix}{out_ext}"
            temp_path = out_path

        # Avoid accidental overwrite if not explicitly permitted
        if out_path.exists() and not overwrite and out_path != p:
            idx = 1
            while out_path.exists():
                out_path = base_dir / f"{p.stem}{suffix}_{idx}{out_ext}"
                idx += 1
            temp_path = out_path

        # FFprobe check for audio streams
        has_audio = self._has_audio_stream(file_path)

        audio_opts = ["-c:a", "copy"] if has_audio else ["-an"]

        if preset == "Main AV1":
            vf_opts = []
            crf = crf_override if crf_override else "28"
            av1_preset = "6"
            av1_params = "tune=0:keyint=10s:enable-overlays=1:scd=1"
        elif preset == "Course AV1":
            vf_opts = ["-vf", "scale=w=min(1920\\,iw):h=min(1080\\,ih):force_original_aspect_ratio=decrease:flags=lanczos,scale=trunc(iw/2)*2:trunc(ih/2)*2,fps=fps=24"]
            crf = crf_override if crf_override else "30"
            av1_preset = "5"
            av1_params = "tune=0:keyint=5s:enable-overlays=1:scd=1:film-grain=0:film-grain-denoise=0"
        else:
            return False, f"Unknown preset: {preset}", ""

        # Apply overrides
        if fps_override:
            if not vf_opts:
                vf_opts = ["-vf", f"fps=fps={fps_override}"]
            else:
                vf_opts[1] = vf_opts[1] + f",fps=fps={fps_override}"
                
        if res_override:
            res_val = res_override.lower().replace('p', '')
            if res_val.isdigit():
                scale_str = f"scale=w=min(-2\\,iw):h=min({res_val}\\,ih):force_original_aspect_ratio=decrease:flags=lanczos,scale=trunc(iw/2)*2:trunc(ih/2)*2"
                if not vf_opts:
                    vf_opts = ["-vf", scale_str]
                else:
                    vf_opts[1] = scale_str + "," + vf_opts[1]

        cmd = [
            self.ffmpeg_bin, "-y", "-nostdin", "-i", str(p),
            "-map", "0:V", "-map", "0:s?", "-map", "0:t?"
        ]
        if has_audio:
            cmd.extend(["-map", "0:a?"])
            
        cmd.extend(vf_opts)
        cmd.extend([
            "-pix_fmt", "yuv420p10le",
            "-c:v", "libsvtav1", "-crf", crf, "-preset", av1_preset,
            "-svtav1-params", av1_params
        ])
        cmd.extend(audio_opts)
        cmd.extend([
            "-c:s", "copy",
            "-c:t", "copy",
            "-map_metadata", "0",
            "-map_chapters", "0",
            "-f", "matroska", str(temp_path)
        ])

        success, msg = run_subprocess(cmd)

        if success:
            if overwrite and p.exists():
                # Remove original if different name, or overwrite in place
                try:
                    if p != out_path:
                        p.unlink()
                except Exception as e:
                    msg += f" (Warning: could not delete original: {e})"
            
            # Move temp to final
            if temp_path != out_path:
                if out_path.exists():
                    out_path.unlink()
                temp_path.rename(out_path)

            return True, msg, str(out_path)
        else:
            if temp_path.exists():
                temp_path.unlink()
            return False, msg, ""

    def process_sequence(self, sequence_dict: dict, overwrite: bool, suffix: str, target_dir: str = None, crf_override: str = "", fps_override: str = "", res_override: str = "") -> tuple[bool, str, str]:
        if not self.ffmpeg_bin:
            return False, "ffmpeg not found in PATH", ""

        start_num = sequence_dict['start_number']
        ffmpeg_pattern = sequence_dict['ffmpeg_pattern']
        base_name = sequence_dict['base_name']
        files = sequence_dict['files']
        
        if not files:
            return False, "Empty sequence", ""

        p = files[0]
        out_ext = ".webm" # WebM with VP9 supports alpha best

        base_dir = Path(target_dir) if target_dir else p.parent
        if target_dir and not base_dir.exists():
            base_dir.mkdir(parents=True, exist_ok=True)

        out_path = base_dir / f"{base_name}{suffix}{out_ext}"
        
        if out_path.exists() and not overwrite:
            idx = 1
            while out_path.exists():
                out_path = base_dir / f"{base_name}{suffix}_{idx}{out_ext}"
                idx += 1
        
        temp_path = out_path.with_name(f"{out_path.stem}.tmp{out_ext}")

        crf = crf_override if crf_override else "30"
        fps = fps_override if fps_override else "30"

        cmd = [
            self.ffmpeg_bin, "-y", "-nostdin",
            "-start_number", str(start_num),
            "-framerate", fps,
            "-i", ffmpeg_pattern,
            "-c:v", "libvpx-vp9",
            "-pix_fmt", "yuva420p",
            "-lossless", "0",
            "-crf", crf,
            "-b:v", "0",
            "-row-mt", "1"
        ]
        
        vf_opts = []
        if res_override:
            res_val = res_override.lower().replace('p', '')
            if res_val.isdigit():
                vf_opts = ["-vf", f"scale=w=min(-2\\,iw):h=min({res_val}\\,ih):force_original_aspect_ratio=decrease:flags=lanczos"]
                
        cmd.extend(vf_opts)
        cmd.append(str(temp_path))

        success, msg = run_subprocess(cmd)

        if success:
            if overwrite:
                for f in files:
                    try:
                        if f.exists():
                            f.unlink()
                    except Exception as e:
                        msg += f" (Warning: could not delete original {f.name}: {e})"
            
            if temp_path != out_path:
                if out_path.exists():
                    out_path.unlink()
                temp_path.rename(out_path)

            return True, msg, str(out_path)
        else:
            if temp_path.exists():
                temp_path.unlink()
            return False, msg, ""

    def _has_audio_stream(self, file_path: str) -> bool:
        if not self.ffprobe_bin:
            return True # Fallback to trying to copy audio
        cmd = [
            self.ffprobe_bin, "-v", "error", "-select_streams", "a",
            "-show_entries", "stream=index", "-of", "csv=p=0", str(file_path)
        ]
        # Use run_subprocess for timeout and cancellation safety
        success, out = run_subprocess(cmd, timeout=30)
        if success:
            return len(out.strip()) > 0
        return True
