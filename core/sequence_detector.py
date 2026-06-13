import re
from pathlib import Path
from collections import defaultdict

def detect_sequences(paths: list[Path], min_sequence_length=10) -> tuple[list[dict], list[Path]]:
    """
    Scans a list of Paths and groups them into sequential image sequences.
    Returns:
        sequences: list of dicts with keys 'ffmpeg_pattern', 'start_number', 'files', 'base_name'
        unmatched: list of Paths that didn't form a valid sequence
    """
    # Regex to match trailing numbers before extension
    # e.g., "frame_001.png" -> prefix "frame_", number "001", ext ".png"
    pattern = re.compile(r'^(.*?)(\d+)(\.[^.]+)$')
    
    # Group by (directory, prefix, ext, number_length)
    groups = defaultdict(list)
    
    unmatched_paths = []
    
    for p in paths:
        if not p.is_file():
            continue
        match = pattern.match(p.name)
        if match:
            prefix, num_str, ext = match.groups()
            key = (str(p.parent), prefix, ext, len(num_str))
            groups[key].append((int(num_str), p))
        else:
            unmatched_paths.append(p)
            
    sequences = []
    
    for key, items in groups.items():
        # Items is a list of (number, Path)
        items.sort(key=lambda x: x[0])
        
        if len(items) >= min_sequence_length:
            parent_dir, prefix, ext, num_len = key
            start_num = items[0][0]
            
            ffmpeg_pattern = f"{prefix}%0{num_len}d{ext}"
            seq_path = Path(parent_dir) / ffmpeg_pattern
            
            # Clean up the base name (remove trailing underscore or dash)
            clean_prefix = prefix
            if clean_prefix.endswith('_') or clean_prefix.endswith('-'):
                clean_prefix = clean_prefix[:-1]
                
            sequences.append({
                'ffmpeg_pattern': str(seq_path),
                'start_number': start_num,
                'files': [p for _, p in items],
                'base_name': clean_prefix
            })
        else:
            # Not enough files to form a sequence, put them back
            for _, p in items:
                unmatched_paths.append(p)
                
    return sequences, unmatched_paths
