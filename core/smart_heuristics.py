class SmartHeuristics:
    BATCH_IMAGE_SUGGESTIONS = {
        '.png': ('Quality > Size', 'Convert to WebP'),
        '.jpg': ('Web', 'Convert to WebP'),
        '.jpeg': ('Web', 'Convert to WebP'),
        '.bmp': ('Quality > Size', 'Convert to WebP'),
        '.tga': ('Quality > Size', 'Convert to WebP'),
        '.dds': ('Quality > Size', 'Convert to PNG'),
        '.gif': ('Web', 'Convert to WebP'),
        '.webp': ('Lossless', 'Keep Original Extension'),
        '.avif': ('Lossless', 'Keep Original Extension'),
    }

    BATCH_VIDEO_SUGGESTIONS = {
        '.mp4': ('Main AV1', '28', '', ''),
        '.mkv': ('Main AV1', '28', '', ''),
        '.mov': ('Main AV1', '28', '', ''),
        '.avi': ('Main AV1', '28', '', ''),
        '.wmv': ('Main AV1', '28', '', ''),
        '.webm': ('Main AV1', '30', '', ''),
        '.ts': ('Course AV1', '30', '24', '1080p'),
        '.flv': ('Course AV1', '30', '24', '1080p'),
        '.m2ts': ('Course AV1', '30', '24', '1080p'),
    }

    QUICK_CONVERTER_SUGGESTIONS = {
        '.png': ('Web Compress', 'Default'),
        '.jpg': ('Convert to WEBP', 'Default'),
        '.jpeg': ('Convert to WEBP', 'Default'),
        '.bmp': ('Convert to PNG', 'Default'),
        '.tga': ('Convert to PNG', 'Default'),
        '.dds': ('DDS -> PNG (texconv / Pillow)', 'Default'),
        '.mp4': ('Compress MP4 (AV1)', 'Default'),
        '.mkv': ('Compress MKV (AV1)', 'Default'),
        '.mov': ('Convert Format (MP4)', 'Default'),
        '.avi': ('Convert Format (MP4)', 'Default'),
        '.webm': ('Compress MP4 (AV1)', 'Default'),
        '.wmv': ('Convert Format (MP4)', 'Default'),
        '.wav': ('Extract Audio (MP3)', 'Default'),
    }

    @classmethod
    def get_batch_image_suggestion(cls, ext: str) -> tuple[str, str]:
        return cls.BATCH_IMAGE_SUGGESTIONS.get(ext.lower(), ('Lossless', 'Keep Original Extension'))

    @classmethod
    def get_batch_video_suggestion(cls, ext: str) -> tuple[str, str, str, str]:
        return cls.BATCH_VIDEO_SUGGESTIONS.get(ext.lower(), ('Main AV1', '28', '', ''))

    @classmethod
    def get_quick_suggestion(cls, ext: str, ftype: str) -> tuple[str, str]:
        suggestion = cls.QUICK_CONVERTER_SUGGESTIONS.get(ext.lower())
        if suggestion:
            return suggestion
        return ("Lossy Compress", "Default") if ftype == "Image" else ("Compress MKV (AV1)", "Default")
