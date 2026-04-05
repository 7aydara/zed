import threading
import queue
import time
import json
import tkinter as tk
import customtkinter as ctk
import sounddevice as sd
import numpy as np
import keyboard
from PIL import Image

# Import Zed components
import config
import brain
import rag
import listener

class FloatingAgent(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Appearance
        ctk.set_appearance_mode("Dark")
        
        # Window settings
        self.overrideredirect(True) # Frameless
        self.attributes("-topmost", True) # Always on top
        
        self.configure(fg_color="#18181A")
        
        # Position variables
        self._drag_start_x = 0
        self._drag_start_y = 0
        
        # State
        self.expanded = False
        self.history_file = config.VAULT_PATH / ".zed_history.json"
        self.chat_history = []
        
        # Audio state
        self.recording = False
        self.audio_data = []
        self.audio_stream = None
        self.current_zed_response = ""
        
        # Size Configuration
        self.collapsed_width = 60
        self.collapsed_height = 60
        self.expanded_width = 350
        self.expanded_height = 500
        
        self.geometry(f"{self.collapsed_width}x{self.collapsed_height}+100+100")
        
        # Audio / Listener events
        self.wake_event = threading.Event()
        self.text_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.continuous_event = threading.Event()
        
        self.build_collapsed_ui()
        self.build_expanded_ui()
        
        # Start RAG sync
        rag.start_background_sync(interval=60)
        
        self.response_queue = queue.Queue()
        
        self.load_history()
        
        # Start listener loop
        from listener import listener_loop
        threading.Thread(target=listener_loop, args=(self.wake_event, self.text_queue, self.stop_event, self.continuous_event), daemon=True).start()
        
        # Start in collapsed state
        self.show_collapsed(animate=False)
        self.after(100, self.process_queue)
        self.after(200, self.poll_listener)
        
        # Register global hotkey
        try:
            keyboard.add_hotkey('ctrl+alt+d', self.trigger_global_voice)
        except Exception as e:
            print("Failed to register global hotkey:", e)

    def trigger_global_voice(self):
        self.after(0, self._handle_global_voice_trigger)
        
    def _handle_global_voice_trigger(self):
        if not self.expanded:
            self.show_expanded(animate=False)
        self.toggle_record()

    def poll_listener(self):
        # 1. Check for wake word
        if self.wake_event.is_set():
            self.wake_event.clear()
            if not self.expanded:
                self.show_expanded(animate=True)
            self.continuous_event.set()
            self.mic_btn.configure(fg_color="#D03B3B", hover_color="#B02A2A", text="⏹")
            self.entry.configure(placeholder_text="Listening...", border_color="#D03B3B")
            self.entry.delete(0, "end")
            import audio
            audio.play_beep()

        # 2. Check for transcribed text chunks
        try:
            while True:
                msg = self.text_queue.get_nowait()
                if msg:
                    # User stopped speaking
                    self.continuous_event.clear()
                    self.mic_btn.configure(fg_color="#D4AF37", hover_color="#B5952F", text="🎤")
                    self.entry.configure(placeholder_text="Zed is thinking...", border_color="#D4AF37")
                    
                    lower_msg = msg.lower().strip()
                    if "bye zed" in lower_msg or lower_msg == "bye":
                        self.current_zed_response = "Goodbye!"
                        self.speak_response(continuous=False) # Say bye then collapse
                        continue
                        
                    self.send_message_direct(msg)
                else:
                    # Keep listening or return to standard
                    if not self.continuous_event.is_set():
                        self.mic_btn.configure(fg_color="#D4AF37", text="🎤")
                        self.entry.configure(placeholder_text="Wait for wake word...")
        except queue.Empty:
            pass

        self.after(200, self.poll_listener)

    def build_collapsed_ui(self):
        import os
        self.collapsed_frame = ctk.CTkFrame(self, width=self.collapsed_width, height=self.collapsed_height, corner_radius=15, fg_color="#18181A", border_width=1, border_color="#333333")
        self.collapsed_frame.pack_propagate(False)
        
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "icon.png")
            icon_img = Image.open(icon_path).resize((50, 50), Image.LANCZOS)
            self.logo_image = ctk.CTkImage(light_image=icon_img, dark_image=icon_img, size=(50, 50))
            self.z_btn = ctk.CTkButton(self.collapsed_frame, text="", image=self.logo_image, width=60, height=60, 
                                       corner_radius=15, fg_color="transparent", hover_color="#28282B",
                                       command=self.toggle_expand)
        except Exception as e:
            print("Failed to load icon:", e)
            self.z_btn = ctk.CTkButton(self.collapsed_frame, text="⚡", width=60, height=60, 
                                       corner_radius=15, font=("Inter", 30, "bold"), text_color="#D4AF37",
                                       fg_color="#18181A", hover_color="#28282B",
                                       command=self.toggle_expand)
                                       
        self.z_btn.pack(expand=True, fill="both")
        
        # Bind drag events
        self.z_btn.bind("<ButtonPress-1>", self.on_drag_start)
        self.z_btn.bind("<B1-Motion>", self.on_drag_motion)
        
        # Bind right click to exit
        self.z_btn.bind("<Button-3>", lambda e: self.destroy())

    def build_expanded_ui(self):
        # Dark stylish background 
        self.expanded_frame = ctk.CTkFrame(self, width=self.expanded_width, height=self.expanded_height, corner_radius=20, border_width=1, border_color="#333333", fg_color="#18181A")
        self.expanded_frame.pack_propagate(False)
        
        # Header
        self.header_frame = ctk.CTkFrame(self.expanded_frame, height=45, corner_radius=0, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=15, pady=(15, 5))
        self.header_frame.pack_propagate(False)
        
        self.title_lbl = ctk.CTkLabel(self.header_frame, text="ZED", font=("Inter", 18, "bold"), text_color="#FFFFFF")
        self.title_lbl.pack(side="left")
        
        self.min_btn = ctk.CTkButton(self.header_frame, text="—", width=30, height=30, 
                                     command=self.toggle_expand, fg_color="transparent", 
                                     text_color="#FFFFFF", hover_color="#28282B")
        self.min_btn.pack(side="right")
        
        # Header Drag
        self.title_lbl.bind("<ButtonPress-1>", self.on_drag_start)
        self.title_lbl.bind("<B1-Motion>", self.on_drag_motion)
        self.header_frame.bind("<ButtonPress-1>", self.on_drag_start)
        self.header_frame.bind("<B1-Motion>", self.on_drag_motion)
        
        # Chat Display
        self.chat_display = ctk.CTkTextbox(self.expanded_frame, wrap="word", state="disabled", font=("Inter", 14), 
                                           fg_color="#1F1F22", text_color="#EAEAEA", border_width=1, border_color="#333333")
        self.chat_display.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Input Area
        self.input_frame = ctk.CTkFrame(self.expanded_frame, height=50, fg_color="transparent")
        self.input_frame.pack(fill="x", padx=15, pady=(0, 15))
        self.input_frame.pack_propagate(False)
        
        # Elegant gold accent for buttons
        self.mic_btn = ctk.CTkButton(self.input_frame, text="🎤", width=40, height=40, corner_radius=20, 
                                     fg_color="#D4AF37", text_color="#FFFFFF", hover_color="#B5952F", command=self.toggle_record)
        self.mic_btn.pack(side="left", padx=(0, 10))

        self.entry = ctk.CTkEntry(self.input_frame, placeholder_text="Ask Zed...", font=("Inter", 14), height=40,
                                  fg_color="#18181A", border_color="#D4AF37", border_width=1, text_color="#EAEAEA")
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self.send_message())
        
        self.speak_btn = ctk.CTkButton(self.input_frame, text="🔊", width=40, height=40, corner_radius=20, 
                                       fg_color="#1F1F22", text_color="#D4AF37", hover_color="#28282B", command=self.speak_response)
        self.speak_btn.pack(side="right")

    # ── History ─────────────────────────────────────────────────────────

    def load_history(self):
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.chat_history = json.load(f)
                self.chat_display.configure(state="normal")
                for msg in self.chat_history[-50:]:  # Load only last 50 directly directly
                    if msg.get('sender') == 'You':
                        self.chat_display.insert("end", f"You: {msg.get('text')}\n\n")
                    else:
                        self.chat_display.insert("end", f"Zed: {msg.get('text')}\n\n")
                self.chat_display.configure(state="disabled")
                self.chat_display.see("end")
            except Exception as e:
                print(f"Could not load history: {e}")

    def save_history(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.chat_history[-100:], f, ensure_ascii=False) # Keep latest 100 in file
        except Exception as e:
            print(f"Could not save history: {e}")

    # ── Audio Push-to-Talk ───────────────────────────────────────────────

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(status)
        self.audio_data.append(indata.copy())

    def toggle_record(self):
        if not self.expanded:
            self.show_expanded(animate=True)
            
        if not self.continuous_event.is_set():
            self.continuous_event.set()
            self.mic_btn.configure(fg_color="#D03B3B", hover_color="#B02A2A", text="⏹") # Red square
            self.entry.configure(placeholder_text="Listening...", border_color="#D03B3B")
            import audio
            audio.play_beep()
        else:
            self.continuous_event.clear()
            self.mic_btn.configure(fg_color="#D4AF37", hover_color="#B5952F", text="🎤")
            self.entry.configure(placeholder_text="Transcribing...", border_color="#D4AF37")

    def transcribe_thread(self, audio_np):
        try:
            model = listener._get_whisper()
            segments, _ = model.transcribe(audio_np, beam_size=5)
            text = " ".join([s.text for s in segments]).strip()
            self.response_queue.put({"type": "transcribed", "content": text})
        except Exception as e:
            self.response_queue.put({"type": "transcribed", "content": f"[Error: {e}]"})

    # ── Animation & State ────────────────────────────────────────────────────────

    def speak_response(self, continuous=False):
        if self.current_zed_response:
            def _tts_thread():
                import audio
                audio.speak(self.current_zed_response)
                # After speaking, if continuous mode, start listening again
                if continuous and "bye" not in self.current_zed_response.lower() and "goodbye" not in self.current_zed_response.lower():
                    self.continuous_event.set()
                    self.after(0, lambda: self.mic_btn.configure(fg_color="#D03B3B", hover_color="#B02A2A", text="⏹"))
                    self.after(0, lambda: self.entry.configure(placeholder_text="Listening...", border_color="#D03B3B"))
                elif not continuous or "bye" in self.current_zed_response.lower() or "goodbye" in self.current_zed_response.lower():
                    self.continuous_event.clear()
                    self.after(0, lambda: self.show_collapsed(animate=True))

            threading.Thread(target=_tts_thread, daemon=True).start()

    def show_collapsed(self, animate=True):
        self.expanded = False
        self.expanded_frame.pack_forget()
        self.collapsed_frame.pack(fill="both", expand=True)
        if animate:
            self.animate_size(self.winfo_width(), self.winfo_height(), self.collapsed_width, self.collapsed_height)
        else:
            self.geometry(f"{self.collapsed_width}x{self.collapsed_height}")

    def show_expanded(self, animate=True):
        self.expanded = True
        self.collapsed_frame.pack_forget()
        self.expanded_frame.pack(fill="both", expand=True)
        if animate:
            self.animate_size(self.winfo_width(), self.winfo_height(), self.expanded_width, self.expanded_height)
        else:
            self.geometry(f"{self.expanded_width}x{self.expanded_height}")
        self.entry.focus()

    def animate_size(self, cur_w, cur_h, target_w, target_h):
        # Very brief micro-animation loop 
        steps = 5
        step_w = (target_w - cur_w) / steps
        step_h = (target_h - cur_h) / steps
        
        def step(count):
            if count < steps:
                new_w = int(cur_w + step_w * (count + 1))
                new_h = int(cur_h + step_h * (count + 1))
                self.geometry(f"{new_w}x{new_h}")
                self.after(5, lambda: step(count + 1))
            else:
                self.geometry(f"{target_w}x{target_h}")
        step(0)

    def toggle_expand(self):
        if self.expanded:
            self.show_collapsed()
        else:
            self.show_expanded()

    def on_drag_start(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def on_drag_motion(self, event):
        x = self.winfo_x() - self._drag_start_x + event.x
        y = self.winfo_y() - self._drag_start_y + event.y
        self.geometry(f"+{x}+{y}")

    # ── Chat Logistics ────────────────────────────────────────────────────────

    def add_to_chat(self, text, sender="Zed", newline=True):
        self.chat_display.configure(state="normal")
        if sender == "You":
            self.chat_display.insert("end", f"You: {text}\n\n")
            self.chat_history.append({"sender": "You", "text": text})
            self.save_history()
        elif sender == "Zed_Start":
            self.chat_display.insert("end", f"Zed: ")
            self.current_zed_response = ""
        elif sender == "Zed_Chunk":
            self.chat_display.insert("end", f"{text}")
            self.current_zed_response += text
        elif sender == "Zed_End":
            if newline:
                self.chat_display.insert("end", "\n\n")
            self.chat_history.append({"sender": "Zed", "text": self.current_zed_response.strip()})
            self.save_history()
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def send_message(self):
        user_text = self.entry.get().strip()
        if not user_text:
            return
        self.entry.delete(0, "end")
        self.send_message_direct(user_text)
        
    def send_message_direct(self, user_text):
        self.add_to_chat(user_text, sender="You")
        self.add_to_chat("", sender="Zed_Start")
        
        # Start thread to generate response
        threading.Thread(target=self.generate_response_thread, args=(user_text,), daemon=True).start()

    def generate_response_thread(self, text):
        try:
            for chunk in brain.think(text):
                self.response_queue.put({"type": "chunk", "content": chunk + " "})
            self.response_queue.put({"type": "done"})
        except Exception as e:
            self.response_queue.put({"type": "chunk", "content": f"\n[Error: {str(e)}] "})
            self.response_queue.put({"type": "done"})

    def process_queue(self):
        while not self.response_queue.empty():
            msg = self.response_queue.get()
            if msg["type"] == "chunk":
                self.add_to_chat(msg["content"], sender="Zed_Chunk")
            elif msg["type"] == "done":
                self.add_to_chat("", sender="Zed_End")
                # Auto-speak if generated
                self.speak_response(continuous=True)
            elif msg["type"] == "transcribed":
                text = msg["content"]
                self.entry.configure(placeholder_text="Ask Zed...")
                if text:
                    self.entry.insert(0, text)
                    self.send_message() # Auto send when transcribed
                
        self.after(50, self.process_queue)

if __name__ == "__main__":
    app = FloatingAgent()
    app.mainloop()
