🎵 Music Sheet Analyzer
A Python-based toolkit for digitizing, analyzing, and enhancing musical scores. This project uses music21 for processing and integrates with MuseScore Studio for high-fidelity notation rendering and playback.

🛠 Prerequisites
Ensure you have the following installed before running the analyzer:

Python 3.12+

Muse Hub: Used to manage the MuseScore installation and sound libraries.

MuseScore Studio: (Formerly MuseScore 4) The core engine for rendering scores.

Libraries:

Bash
pip install music21 python-dotenv
⚙️ Configuration (The "2026 Fix")
Because MuseScore 4 was rebranded to MuseScore Studio, the default paths in many Python libraries (like music21) are often broken. You must configure your environment settings in app.py to point to the new executable.

1. Locate your Executable
Find where MuseScore Studio.exe is installed. Common paths include:

C:\Program Files\MuseScore 4\bin\MuseScore Studio.exe

C:\Program Files\MuseScore Studio\bin\MuseScore Studio.exe

2. Update your code
Add this block to the top of your main script:

Python
from music21 import environment
import os

# Update this path to your actual .exe location
mscore_path = r'C:\Program Files\MuseScore 4\bin\MuseScore Studio.exe'

if os.path.exists(mscore_path):
    us = environment.UserSettings()
    us['musicxmlPath'] = mscore_path
    us['musescoreDirectPNGPath'] = mscore_path
else:
    print("⚠️ Warning: MuseScore Studio executable not found. Check your path!")
🚀 To-Do List (Roadmap)
Phase 1: Stability
[ ] Path Automation: Move the MuseScore path to a .env file to avoid hardcoding.

[ ] Error Handling: Add a "Check Installation" utility to help users debug path issues.

[ ] Streamline Conversions: Optimize PDF-to-MusicXML conversion speeds.

Phase 2: AI Enhancements
[ ] Integrate NoteVision OMR: Explore the new AI-powered score recognition engine for better PDF accuracy.

[ ] AI Vocals: Add support for Cantai (AI singing models) for choral playback.

[ ] Humanization Model: Implement an AI-driven rhythmic "humanizer" to make MIDI playback feel less robotic.

Phase 3: Analysis Features
[ ] Harmonic Detection: Build a module to auto-tag Roman Numeral analysis.

[ ] Visualization: Create a web-based dashboard using Streamlit to view score statistics.

❌ Troubleshooting
SubConverterException
If you see music21.exceptions21.SubConverterException: Cannot find a path to the 'mscore' file, it means your script is looking for the old MuseScore4.exe.
The Fix: Check the Configuration section above and ensure your path points specifically to the new MuseScore Studio.exe file.
