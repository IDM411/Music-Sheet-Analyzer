import os
import subprocess
from music21 import converter, chord
import ollama

# --- CONFIGURATION ---
# Change this to the exact name of your PDF file!
input_pdf = "test_song.pdf" 
# Oemer will automatically create a file with this name:
output_xml = input_pdf.replace(".pdf", ".musicxml") 

# ==========================================
# STAGE 1: THE VISION LAYER (PDF -> MusicXML)
# ==========================================
print("-" * 30)
print(f"STAGE 1: Scanning '{input_pdf}' with AI Vision...")
print("Please wait. (This may take a few minutes on the first run as it downloads AI models...)")

try:
    # This runs Oemer just like if you typed 'oemer test_song.pdf' in the terminal
    subprocess.run(["oemer", input_pdf], check=True)
    print("Scan Complete! MusicXML file generated.")
except Exception as e:
    print(f"\n[ERROR] The scanner failed. Make sure your PDF name is correct and Oemer is installed.")
    print(f"Details: {e}")
    exit()

# ==========================================
# STAGE 2: THE LOGIC LAYER (MusicXML -> Chords)
# ==========================================
print("-" * 30)
print(f"STAGE 2: Analyzing chords from '{output_xml}'...")

s = converter.parse(output_xml)
b_chords = s.chordify()
first_measure_chords = []

for c in b_chords.recurse().getElementsByClass(chord.Chord)[:10]:
    name = c.pitchedCommonName
    if name not in first_measure_chords:
        first_measure_chords.append(name)

chord_list = ", ".join(first_measure_chords)
print(f"Detected Chords: {chord_list}")

# ==========================================
# STAGE 3: THE INTELLIGENCE LAYER (Chords -> AI Tutor)
# ==========================================
print("-" * 30)
print("STAGE 3: Consulting your Local Music Tutor...")

model_to_use = 'llamusic/llamusic:latest'

response = ollama.chat(model=model_to_use, messages=[
    {
        'role': 'system', 
        'content': 'You are a patient, expert piano teacher. Your goal is to simplify complex music theory. '
                   'Keep tips short, practical, and encouraging for someone who finds sheet music intimidating.'
    },
    {
        'role': 'user', 
        'content': f"I am learning a piece of music with these chords: {chord_list}. "
                   f"CRITICAL INSTRUCTION: Do NOT spell out the individual notes of these chords, as I already have them on my sheet music. "
                   f"Please explain the musical relationship between these chords, and give me ONE short, encouraging physical tip "
                   f"on how to smoothly transition between them on the piano. Keep your entire answer under 4 sentences."
    },
])

print("\n--- PROFESSOR'S BREAKDOWN ---")
print(response['message']['content'])