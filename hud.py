import tkinter as tk
import random
import time

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class JAIHUD(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("J.A.I. Spatial HUD Interface - v3.0")
        self.geometry("850x640")
        self.configure(bg="#050b14")
        
        # Header Title
        title_label = tk.Label(
            self, 
            text="J.A.I. // SPATIAL HUD SYSTEM v3.0", 
            font=("Courier", 18, "bold"), 
            fg="#00f3ff", 
            bg="#050b14"
        )
        title_label.pack(pady=15)
        
        # Status Frame
        status_frame = tk.Frame(self, bg="#0a192f", highlightbackground="#00f3ff", highlightthickness=1)
        status_frame.pack(fill="x", padx=40, pady=5)
        
        self.status_label = tk.Label(
            status_frame, 
            text="STATUS: INTERACTIVE CONTROL BUS ACTIVE // WAITING FOR INPUT", 
            font=("Courier", 10, "bold"), 
            fg="#00ff66", 
            bg="#0a192f"
        )
        self.status_label.pack(padx=20, pady=12)
        
        # Telemetry Frame (MUST be defined here first!)
        telemetry_frame = tk.Frame(self, bg="#050b14")
        telemetry_frame.pack(fill="both", expand=True, padx=40, pady=10)
        
        self.cpu_label = tk.Label(
            telemetry_frame, 
            text="CPU LOAD: INITIALIZING...", 
            font=("Courier", 11), 
            fg="#00f3ff", 
            bg="#050b14", 
            anchor="w"
        )
        self.cpu_label.pack(fill="x", pady=4)
        
        self.ram_label = tk.Label(
            telemetry_frame, 
            text="MEMORY ALLOCATION: INITIALIZING...", 
            font=("Courier", 11), 
            fg="#00f3ff", 
            bg="#050b14", 
            anchor="w"
        )
        self.ram_label.pack(fill="x", pady=4)
        
        self.net_label = tk.Label(
            telemetry_frame, 
            text="DISPLAY MAT PROJECTION: MAPPED (1920x1080 @ 60Hz)", 
            font=("Courier", 11), 
            fg="#00f3ff", 
            bg="#050b14", 
            anchor="w"
        )
        self.net_label.pack(fill="x", pady=4)

        # Audio Waveform Visualizer Canvas
        tk.Label(telemetry_frame, text="AUDIO / VOICE INPUT SPECTRUM:", font=("Courier", 9, "bold"), fg="#8892b0", bg="#050b14", anchor="w").pack(fill="x", pady=(10, 2))
        
        self.canvas = tk.Canvas(telemetry_frame, height=70, bg="#02070f", highlightthickness=1, highlightbackground="#00f3ff")
        self.canvas.pack(fill="x", pady=5)

        # Action Buttons Frame (Correctly placed inside __init__)
        button_frame = tk.Frame(telemetry_frame, bg="#050b14")
        button_frame.pack(fill="x", pady=15)
        
        btn_1 = tk.Button(button_frame, text="[ LAUNCH JAI CORE ]", bg="#0a192f", fg="#00f3ff", font=("Courier", 10, "bold"), relief="solid", bd=1, padx=10, pady=5)
        btn_1.pack(side="left", padx=5)
        
        btn_2 = tk.Button(button_frame, text="[ TOGGLE HOLO-MAT ]", bg="#0a192f", fg="#00ff66", font=("Courier", 10, "bold"), relief="solid", bd=1, padx=10, pady=5)
        btn_2.pack(side="left", padx=5)
        
        btn_3 = tk.Button(button_frame, text="[ SYSTEM DIAGNOSTIC ]", bg="#0a192f", fg="#ff0055", font=("Courier", 10, "bold"), relief="solid", bd=1, padx=10, pady=5)
        btn_3.pack(side="left", padx=5)
        
        # Footer
        footer_label = tk.Label(
            self, 
            text="[HALF-LIFE HACKATHON // WEEK 4 ENTRY 3: INTERACTIVE HUD BUTTONS]", 
            font=("Courier", 9), 
            fg="#8892b0", 
            bg="#050b14"
        )
        footer_label.pack(side="bottom", pady=10)
        
        # Start loops
        self.update_telemetry()
        self.animate_waveform()

    # Bind F11 for Fullscreen Holographic Mode toggle
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.end_fullscreen)
        self.is_fullscreen = False

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)
        self.status_label.config(text=f"STATUS: HOLOGRAPHIC PROJECTION MODE // FULLSCREEN: {self.is_fullscreen}")

    def end_fullscreen(self, event=None):
        self.is_fullscreen = False
        self.attributes("-fullscreen", False)
        self.status_label.config(text="STATUS: HOLOGRAPHIC PROJECTION MODE // WINDOWED")

    def update_telemetry(self):
        if PSUTIL_AVAILABLE:
            try:
                cpu = psutil.cpu_percent()
                ram = psutil.virtual_memory()
                ram_used = round(ram.used / (1024**3), 1)
                ram_total = round(ram.total / (1024**3), 1)
                ram_pct = ram.percent
                self.cpu_label.config(text=f"CPU LOAD: {cpu}%")
                self.ram_label.config(text=f"MEMORY ALLOCATION: {ram_used} / {ram_total} GB ({ram_pct}%)")
            except Exception:
                cpu = round(random.uniform(15.0, 35.0), 1)
                self.cpu_label.config(text=f"CPU LOAD: {cpu}%")
                self.ram_label.config(text=f"MEMORY ALLOCATION: 4.8 / 16.0 GB (30%)")
        else:
            cpu = round(random.uniform(15.0, 35.0), 1)
            self.cpu_label.config(text=f"CPU LOAD: {cpu}%")
            self.ram_label.config(text=f"MEMORY ALLOCATION: 4.8 / 16.0 GB (30%) (Simulated)")
            
        self.after(1000, self.update_telemetry)

    def animate_waveform(self):
        self.canvas.delete("all")
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width > 1:
            bars = 32
            bar_width = width / bars
            for i in range(bars):
                h = random.randint(10, height - 10)
                x0 = i * bar_width + 2
                y0 = (height - h) / 2
                x1 = (i + 1) * bar_width - 2
                y1 = y0 + h
                color = "#00f3ff" if i % 2 == 0 else "#00ff66"
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
                
        self.after(150, self.animate_waveform)

if __name__ == "__main__":
    app = JAIHUD()
    app.mainloop()
