import os
import subprocess
import fitz  # This is PyMuPDF!
from music21 import converter, chord
import ollama

# --- CONFIGURATION ---
input_pdf = "test_song.pdf" 
temp_image = "temp_page_1.png"
output_xml = "temp_page_1.musicxml" # Oemer will name its output this

# ==========================================
# STAGE 0: THE BRIDGE (PDF -> High-Res Image)
# ==========================================
print("-" * 30)
print(f"STAGE 0: Converting '{input_pdf}' to an image...")

try:
    # Open the PDF and grab the very first page (Page 0)
    doc = fitz.open(input_pdf)
    page = doc.load_page(0)
    
    # THE FIX: Use a scaling matrix instead of a blind DPI setting
    # '2' means 2x zoom (which is usually a perfect ~150-200 DPI for standard PDFs)
    zoom = 1
    mat = fitz.Matrix(zoom, zoom)
    
    pix = page.get_pixmap(matrix=mat)
    pix.save(temp_image)
    print(f"Success! Created '{temp_image}' for the scanner.")
except Exception as e:
    print(f"\n[ERROR] Failed to read PDF. Make sure '{input_pdf}' exists!")
    print(f"Details: {e}")
    exit()

# ==========================================
# STAGE 1: THE VISION LAYER (Image -> MusicXML)
# ==========================================
print("-" * 30)
print(f"STAGE 1: Scanning '{temp_image}' with Oemer...")
print("Please wait. (Using CPU, you can ignore any red CUDA warnings...)")

try:
    subprocess.run(["oemer", temp_image], check=True)
    print("Scan Complete! MusicXML file generated.")
except Exception as e:
    print(f"\n[ERROR] The scanner failed.")
    exit()

# ==========================================
# STAGE 2: THE LOGIC LAYER (MusicXML -> Chords)
# ==========================================
print("-" * 30)
print(f"STAGE 2: Analyzing chords from '{output_xml}'...")

try:
    s = converter.parse(output_xml)
    b_chords = s.chordify()
    first_measure_chords = []

    for c in b_chords.recurse().getElementsByClass(chord.Chord)[:10]:
        name = c.pitchedCommonName
        if name not in first_measure_chords:
            first_measure_chords.append(name)

    chord_list = ", ".join(first_measure_chords)
    print(f"Detected Chords: {chord_list}")
except Exception as e:
    print(f"\n[ERROR] Could not analyze the XML file. Oemer might have produced an empty scan.")
    exit()

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

# Optional: Clean up the temporary image so your folder stays tidy
if os.path.exists(temp_image):
    os.remove(temp_image)