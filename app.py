import os
import subprocess
import fitz  # PyMuPDF
from music21 import converter, chord, roman
import ollama
import streamlit as st
import base64
import streamlit.components.v1 as components
import cv2   # The Computer Vision library!

# --- PAGE SETUP ---
st.set_page_config(page_title="AI Piano Tutor", page_icon="🎹", layout="centered", initial_sidebar_state="collapsed")

st.title("🎹 AI Piano Tutor (Pro Vision)")
st.write("Scan your sheet music, slice it into practice sections, and listen to the playback before your AI lesson!")

# ==========================================
# UI: FILE UPLOAD
# ==========================================
uploaded_file = st.file_uploader("Upload Sheet Music (PDF)", type=["pdf"])

if uploaded_file is not None:
    input_pdf = "temp_uploaded.pdf"
    output_xml = "temp_page_1.musicxml"
    
    with open(input_pdf, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    if 'scan_complete' not in st.session_state:
        st.session_state.scan_complete = False

    # ==========================================
    # STAGE 1: SCANNING (Run Once)
    # ==========================================
    if not st.session_state.scan_complete:
        if st.button("🔍 Scan Full Sheet Music", type="primary", use_container_width=True):
            
            # 1. Convert the PDF and Clean with OpenCV
            with st.spinner("Converting PDF & Cleaning Image for AI..."):
                temp_image = "temp_page_1.png"
                doc = fitz.open(input_pdf)
                page = doc.load_page(0)
                mat = fitz.Matrix(1, 1)
                pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
                pix.save(temp_image)

                # --- OPENCV IMAGE CLEANING ---
                # 1. Read the image back into memory
                img = cv2.imread(temp_image, cv2.IMREAD_GRAYSCALE)
                
                # 2. Apply Otsu's Thresholding (Separates pure black ink from white paper)
                _, clean_binary_img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                # 3. Save the perfectly crisp image for Oemer to scan
                cv2.imwrite(temp_image, clean_binary_img)
                # ----------------------------------

            # 2. Set up the Live Progress UI
            st.write("### 🤖 AI Vision Scanner Running")
            progress_bar = st.progress(0)
            status_text = st.empty() # An empty box we can update with text
            
            # The known stages of Oemer based on your logs
            oemer_stages = [
                "Extracting staffline and symbols",
                "Extracting layers of different symbols",
                "Dewarping",
                "Extracting stafflines",
                "Extracting noteheads",
                "Analyzing notehead bboxes",
                "Instanitiating notes",
                "Grouping noteheads",
                "Extracting symbols",
                "Extracting rhythm types",
                "Building MusicXML document"
            ]
            total_stages = len(oemer_stages)
            current_stage_idx = 0

            # 3. Run Oemer and "Listen" to its output in real-time
            status_text.info("Waking up AI Vision Models...")
            
            process = subprocess.Popen(
                ["oemer", temp_image],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Capture all output (including the red CUDA warnings)
                text=True,
                bufsize=1
            )

            # Read the terminal output line by line as it generates
            for line in process.stdout:
                # Check if the terminal printed one of our known stages
                for idx, stage in enumerate(oemer_stages):
                    if stage in line and idx >= current_stage_idx:
                        current_stage_idx = idx
                        # Calculate the percentage (e.g. stage 5 of 11 = ~45%)
                        progress_pct = int(((current_stage_idx + 1) / total_stages) * 100)
                        
                        # Update the Streamlit UI
                        progress_bar.progress(progress_pct)
                        status_text.info(f"**Step {current_stage_idx + 1}/{total_stages}:** {stage}...")
                        break

            # Wait for it to officially close
            process.wait()
            
            if process.returncode == 0:
                progress_bar.progress(100)
                status_text.success("Vision Scan Complete!")
                st.session_state.scan_complete = True
                st.rerun()
            else:
                st.error("The Oemer scanner failed. Check your terminal for details.")
                
    # ==========================================
    # STAGE 2: SLICING & DEEP ANALYSIS & AUDIO
    # ==========================================
    if st.session_state.scan_complete:
        st.success("Scan Complete! 🎵")
        st.divider()
        
        st.subheader("✂️ Slice Your Practice Section")
        st.write("Select how many chords you want to practice in this chunk:")
        
        # Slicer: Let the user pick how many chords to analyze
        chord_range = st.slider("Select Chord Range", min_value=1, max_value=20, value=(1, 8))
        
        with st.spinner("Processing your slice and analyzing music theory..."):
            # Load the XML
            s = converter.parse(output_xml)
            b_chords = s.chordify()
            
            # Extract only the chords in the user's selected slice
            all_chords = list(b_chords.recurse().getElementsByClass(chord.Chord))
            start_idx = chord_range[0] - 1
            end_idx = chord_range[1]
            sliced_chords = all_chords[start_idx:end_idx]
            
            # --- NEW DEEP ANALYSIS ---
            # 1. Have Music21 automatically detect the Key of the song
            detected_key = s.analyze('key')
            
            # 2. Extract chords AND their Roman Numeral function relative to the key
            unique_chords_data = []
            unique_chord_names = [] # Kept for the visual UI
            
            for c in sliced_chords:
                name = c.pitchedCommonName
                if name not in unique_chord_names:
                    unique_chord_names.append(name)
                    # Calculate the Roman Numeral (e.g., "V", "I", "vi")
                    try:
                        rn = roman.romanNumeralFromChord(c, detected_key)
                        unique_chords_data.append(f"{name} ({rn.figure})")
                    except:
                        # Fallback if it's a weird chord it can't analyze
                        unique_chords_data.append(name)
            
            # The visual display for the user (just the names)
            detected_chords_str = ", ".join(unique_chord_names)
            
            # The ultra-detailed string we will feed secretly to the AI
            st.session_state.deep_ai_context = f"Key: {detected_key}. Chords and Functions: {', '.join(unique_chords_data)}"

            # Generate MIDI file for playback
            midi_path = "temp_playback.mid"
            s.write('midi', fp=midi_path) 
            
            # Convert MIDI to Base64 so the browser can play it
            with open(midi_path, "rb") as f:
                b64_midi = base64.b64encode(f.read()).decode()

        # --- VISUALS: Display Chords nicely ---
        st.markdown(f"### 🎼 Main Chords (Detected Key: **{detected_key}**)")
        cols = st.columns(len(unique_chord_names) if len(unique_chord_names) > 0 else 1)
        for i, chord_name in enumerate(unique_chord_names):
            with cols[i % len(cols)]:
                st.info(f"**{chord_name}**")

        # --- AUDIO: The Web MIDI Player ---
        st.markdown("### 🎧 Listen & Visualize")
        # CHANGED: 'type="piano-roll"' is now 'type="waterfall"'
        # CHANGED: Added a darker background to make the glowing keys pop!
        midi_html = f"""
        <script src="https://cdn.jsdelivr.net/combine/npm/tone@14.7.58,npm/@magenta/music@1.23.1/es6/core.js,npm/html-midi-player@1.5.0"></script>
        <midi-player src="data:audio/midi;base64,{b64_midi}" sound-font visualizer="#myVisualizer" style="width: 100%;"></midi-player>
        <midi-visualizer type="waterfall" id="myVisualizer" src="data:audio/midi;base64,{b64_midi}" style="width: 100%; height: 350px; background: #1e1e1e; border-radius: 10px;"></midi-visualizer>
        """
        components.html(midi_html, height=400)

        # ==========================================
        # STAGE 3: AI TUTOR INTERCEPT
        # ==========================================
        st.divider()
        st.subheader("🧠 Final Sanity Check")
        final_chords = st.text_input("Verify or edit the chords before asking the AI:", value=detected_chords_str)
        
        if st.button("🎓 Get Piano Lesson for this Slice", type="primary"):
            with st.spinner("Consulting Llama 3.1..."):
                # UPGRADED MODEL
                model_to_use = 'llama3.1:8b'
                
                response = ollama.chat(model=model_to_use, messages=[
                    {
                        'role': 'system', 
                        'content': 'You are a patient, expert piano teacher. Your goal is to simplify complex music theory. '
                                   'Keep tips short, practical, and encouraging for someone who finds sheet music intimidating.'
                    },
                    {
                        'role': 'user', 
                        # UPGRADED PROMPT INJECTING THE DEEP CONTEXT
                        'content': f"I am practicing a specific slice of a song. "
                                   f"The deep analysis of this section is: {st.session_state.deep_ai_context}. "
                                   f"The user has verified these chords: {final_chords}. "
                                   f"CRITICAL INSTRUCTION: Do NOT spell out the individual notes. "
                                   f"Please explain the harmonic function of this progression based on the Key and Roman numerals, "
                                   f"and give me ONE short, encouraging physical tip on how to smoothly transition between them. "
                                   f"Keep your entire answer under 4 sentences."
                    },
                ])
                
                st.success("Lesson Generated!")
                st.markdown(f"### Professor's Breakdown\n\n> {response['message']['content']}")