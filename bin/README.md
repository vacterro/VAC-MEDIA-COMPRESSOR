# Dependencies Directory

To make this application completely portable (so it works immediately after cloning without modifying system environment variables), place your `.exe` binaries inside this folder.

The application automatically checks this `bin` directory first before falling back to your system `PATH`.

## Required Binaries
- `ffmpeg.exe` and `ffprobe.exe` (For video/audio processing)
- `magick.exe` (ImageMagick v7+ for image processing)

## Optional Binaries
- `texconv.exe` (For direct DDS/TGA conversions)
- `oxipng.exe` (For aggressive lossless PNG optimization)
- `jpegoptim.exe` (For lossless JPG optimization)
