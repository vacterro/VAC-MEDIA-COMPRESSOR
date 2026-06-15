import os
from pathlib import Path
import shutil
from .utils import find_tool, run_subprocess

class ImageProcessor:
    SUPPORTED_EXTS = frozenset({'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.avif', '.tga', '.dds', '.jfif', '.heic', '.hdr', '.exr', '.tiff', '.tif', '.ico'})

    def __init__(self):
        self.magick_bin = find_tool("magick")
        self.jpegoptim_bin = find_tool("jpegoptim")
        self.oxipng_bin = find_tool("oxipng")
        
    def is_supported(self, file_path: str) -> bool:
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_EXTS

    def process(self, file_path: str, preset: str, overwrite: bool, suffix: str, target_dir: str = None, out_format: str = "Keep Original Extension", skip_existing: bool = False, img_quality: int = 85) -> tuple[bool, str, str]:
        """
        Returns (success, message, final_output_path)
        """
        if not self.is_supported(file_path):
            return False, "Unsupported file extension", ""

        p = Path(file_path)
        # Determine output path
        out_ext = p.suffix
        if out_format not in ["Keep Original Extension", "Keep Original"] and out_format.strip():
            fmt_upper = out_format.upper()
            if "WEBP" in fmt_upper:
                out_ext = ".webp"
            elif "JPG" in fmt_upper or "JPEG" in fmt_upper:
                out_ext = ".jpg"
            elif "PNG" in fmt_upper:
                out_ext = ".png"
            elif "AVIF" in fmt_upper:
                out_ext = ".avif"
            else:
                # Fallback if just the extension was passed
                out_ext = out_format if out_format.startswith('.') else f".{out_format.lower()}"

        base_dir = Path(target_dir) if target_dir else p.parent
        if target_dir and not base_dir.exists():
            base_dir.mkdir(parents=True, exist_ok=True)

        if overwrite and not target_dir:
            out_path = p.with_suffix(out_ext)
        else:
            out_path = base_dir / f"{p.stem}{suffix}{out_ext}"

        # If skip_existing is checked and the target exists, we just skip it entirely
        if skip_existing and out_path.exists() and out_path != p:
            return True, "Skipped (already exists)", str(out_path)

        # If it's not overwriting and file exists, abort to prevent accidental overwrites
        if out_path.exists() and not overwrite and out_path != p:
            # We can auto-rename or just return error. Let's append an index.
            idx = 1
            while out_path.exists():
                out_path = base_dir / f"{p.stem}{suffix}_{idx}{out_ext}"
                idx += 1

        success = False
        msg = ""

        if preset == "Lossless":
            # If changing format, we must use magick, not the format-specific optimizers
            if out_ext.lower() != p.suffix.lower():
                success, msg = self._process_magick(p, out_path, quality=100)
            else:
                success, msg = self._process_lossless(p, out_path, overwrite)
        elif preset == "Custom":
            success, msg = self._process_magick(p, out_path, quality=img_quality)
        elif preset == "Web":
            success, msg = self._process_magick(p, out_path, quality=80)
        elif preset == "Quality > Size":
            success, msg = self._process_magick(p, out_path, quality=92)
        elif preset == "Size > Quality":
            success, msg = self._process_magick(p, out_path, quality=60)
        else:
            return False, f"Unknown preset: {preset}", ""

        # If overwrite is true and the extension changed, we delete the original.
        if success and overwrite and p != out_path and p.exists():
            try:
                p.unlink()
            except Exception as e:
                msg += f" (Warning: could not delete original: {e})"

        if success and not out_path.exists():
            return False, f"Processed, but output file {out_path.name} was not found", ""

        return success, msg, str(out_path)

    def _process_lossless(self, p: Path, out_path: Path, overwrite: bool) -> tuple[bool, str]:
        ext = p.suffix.lower()
        if ext in ['.jpg', '.jpeg', '.jfif'] and self.jpegoptim_bin:
            target = out_path
            if target != p:
                try:
                    shutil.copy2(p, target)
                except Exception as e:
                    return False, f"Failed to copy for processing: {e}"
            cmd = [self.jpegoptim_bin, "--preserve", str(target)]
            return run_subprocess(cmd)
        elif ext == '.png' and self.oxipng_bin:
            target = out_path
            if target != p:
                try:
                    shutil.copy2(p, target)
                except Exception as e:
                    return False, f"Failed to copy for processing: {e}"
            cmd = [self.oxipng_bin, "-o4", "--preserve", str(target)]
            return run_subprocess(cmd)
        elif self.magick_bin:
            # Fallback to magick lossless
            cmd = [self.magick_bin, str(p), "-quality", "100", str(out_path)]
            return run_subprocess(cmd)
        else:
            return False, "No suitable tool found for Lossless compression (need jpegoptim, oxipng, or magick)"

    def _process_magick(self, p: Path, out_path: Path, quality: int) -> tuple[bool, str]:
        if not self.magick_bin:
            return False, "ImageMagick (magick) not found in PATH"
        
        cmd = [self.magick_bin, str(p), "-auto-orient", "-quality", str(quality), str(out_path)]
        return run_subprocess(cmd)
