#!/usr/bin/env python3
"""
gen_tracks_json.py - Scan a directory for media files and generate tracks JSON.

Usage:
    python gen_tracks_json.py [directory] [options]

Options:
    --dir DIR          Directory to scan (default: current directory)
    --name NAME        Default wallet/name value (default: "1234567890.web3")
    --ext EXT          File extensions to include, comma-separated (default: mp4,mp3)
    --out FILE         Output file (default: stdout)
    --lang LANG        Only include specific language(s), comma-separated (e.g. de,es)
    --prefix PREFIX    Filename prefix filter (default: "tracks")

Example:
    python gen_tracks_json.py --dir ./1234567890.web3 --name "1234567890.web3" --out tracks.json
"""

import os
import re
import json
import argparse
from collections import defaultdict

# Language code -> full name mapping
LANG_NAMES = {
    "en": "English", "es": "Spanish", "ru": "Russian", "de": "German",
    "fr": "French", "it": "Italian", "zh": "Chinese", "ar": "Arabic",
    "ja": "Japanese", "pl": "Polish", "uk": "Ukrainian", "tr": "Turkish",
    "kz": "Kazakh", "ro": "Romanian", "hy": "Armenian", "az": "Azerbaijani",
    "he": "Hebrew", "fa": "Farsi", "pt": "Portuguese", "nl": "Dutch",
    "sv": "Swedish", "no": "Norwegian", "fi": "Finnish", "da": "Danish",
    "cs": "Czech", "sk": "Slovak", "hu": "Hungarian", "bg": "Bulgarian",
    "hr": "Croatian", "sr": "Serbian", "sl": "Slovenian", "el": "Greek",
    "th": "Thai", "vi": "Vietnamese", "ko": "Korean", "id": "Indonesian",
    "ms": "Malay", "hi": "Hindi",
}

# Standard empty language stubs (matching original JSON format)
STANDARD_EMPTY_LANGS = ["ar", "az", "fa", "he", "hy", "ja", "kz", "pl", "ro", "tr", "uk", "zh"]

def parse_filename(filename, extensions):
    """
    Parse filename like: tracks-de-1-Clean_Release-Alt.mp4
    Returns dict with lang, index, title, is_alt, or None if no match.
    Pattern: {prefix}-{lang}-{index}-{title}[-Alt].{ext}
    """
    base, ext = os.path.splitext(filename)
    if ext.lstrip('.').lower() not in extensions:
        return None

    # Match: anything-LANG-NUM-Title_Words[-Alt]
    pattern = r'^(.+?)-([a-z]{2,3})-(\d+)-(.+?)(-Alt)?$'
    m = re.match(pattern, base, re.IGNORECASE)
    if not m:
        return None

    prefix, lang, index, raw_title, alt_suffix = m.groups()
    lang = lang.lower()
    is_alt = alt_suffix is not None

    # Convert underscores to spaces, preserve hyphens in titles (e.g. Pear-Shaped)
    title = raw_title.replace('_', ' ')

    return {
        "prefix": prefix,
        "lang": lang,
        "index": int(index),
        "title": title,
        "is_alt": is_alt,
        "filename": filename,
        "ext": ext.lstrip('.').lower(),
    }

def sort_langs(langs):
    """Sort languages with 'en' always first, then alphabetically."""
    others = sorted(l for l in langs if l != "en")
    return (["en"] if "en" in langs else []) + others

def build_json(directory, name, extensions, lang_filter=None, prefix_filter=None):
    """Scan directory and build the tracks JSON structure."""

    try:
        all_files = sorted(os.listdir(directory))
    except FileNotFoundError:
        print(f"Error: Directory '{directory}' not found.")
        exit(1)

    found_langs = set()
    lang_tracks = defaultdict(list)

    for filename in all_files:
        parsed = parse_filename(filename, extensions)
        if not parsed:
            continue

        if prefix_filter and not parsed["prefix"].lower().startswith(prefix_filter.lower()):
            continue

        lang = parsed["lang"]

        if lang_filter and lang not in lang_filter:
            continue

        found_langs.add(lang)
        lang_tracks[lang].append(parsed)

    result = {}

    # Add found languages: English first, then alphabetical
    for lang in sort_langs(found_langs):
        tracks = sorted(lang_tracks[lang], key=lambda x: (x["index"], x["is_alt"]))
        entries = []
        for i, t in enumerate(tracks, start=1):
            title_display = t["title"]
            if t["is_alt"]:
                title_display += " Alt"
            # title_display += f" - {LANG_NAMES.get(lang, lang.upper())}"

            entries.append({
                "i": i,
                "t": title_display,
                "f": t["filename"],
                "l": 'lyrics-' + t["filename"][7:].replace("wav", "md").replace("mp3", "md").replace("mp4", "md"),
                "a": 1 if t["is_alt"] else 0,
                "n": name,
            })

        result[lang] = entries

    # Add empty stubs for standard langs not found, in alphabetical order
    for lang in sorted(STANDARD_EMPTY_LANGS):
        if lang not in result:
            result[lang] = []

    return result

def main():
    parser = argparse.ArgumentParser(
        description="Scan media files and generate tracks JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("directory", nargs="?", default=".",
                        help="Directory to scan (default: current directory)")
    parser.add_argument("--dir", dest="dir_override",
                        help="Directory to scan (overrides positional argument)")
    parser.add_argument("--name", default="1234567890.web3",
                        help='Default n value (default: "1234567890.web3")')
    parser.add_argument("--ext", default="mp4,mp3",
                        help="File extensions to include, comma-separated (default: mp4,mp3)")
    parser.add_argument("--out", default=None,
                        help="Output file (default: stdout)")
    parser.add_argument("--lang", default=None,
                        help="Only include specific languages, comma-separated (e.g. de,es)")
    parser.add_argument("--prefix", default=None,
                        help="Filename prefix filter (e.g. 'tracks')")

    args = parser.parse_args()

    directory = args.dir_override or args.directory
    extensions = {e.strip().lower().lstrip('.') for e in args.ext.split(',')}
    lang_filter = {l.strip().lower() for l in args.lang.split(',')} if args.lang else None

    result = build_json(
        directory=directory,
        name=args.name,
        extensions=extensions,
        lang_filter=lang_filter,
        prefix_filter=args.prefix,
    )

    output = json.dumps(result, indent=4, ensure_ascii=False)

    if args.out:
        with open(args.out, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"✓ Written to {args.out}")
        for lang, tracks in result.items():
            if tracks:
                print(f"  [{lang}] {len(tracks)} tracks")
    else:
        print(output)

if __name__ == "__main__":
    main()