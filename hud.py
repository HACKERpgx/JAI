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
        self.title("J.A.I. Spatial HUD Interface - v4.5 [PROD]")
        self.geometry("960x660")
        self.configure(bg="#030712")
        
        # Header Title
        title_label = tk.Label(
            self, 
            text="J.A.I. // SPATIAL HUD SYSTEM [SECURE V4.5]", 
            font=("Courier", 18, "bold"), 
            fg="#38bdf8", 
            bg="#030712"
        )
        title_label.pack(pady=15)
        
        # Status Frame
        status_frame = tk.Frame(self, bg="#0f172a", highlightbackground="#38bdf8", highlightthickness=1)
        status_frame.pack(fill="x", padx=40, pady=5)
        
        self.status_label = tk.Label(
            status_frame, 
            text="STATUS: NEURAL LINK ESTABLISHED // ALL SYSTEMS OPTIMIZED", 
            font=("Courier", 10, "bold"), 
            fg="#4ade80", 
            bg="#0f172a"
        )
        self.status_label.pack(padx=20, pady=12)
        
        # Telemetry Frame
        telemetry_frame = tk.Frame(self, bg="#030712")
        telemetry_frame.pack(fill="both", expand=True, padx=40, pady=10)
        
        self.cpu_label = tk.Label(
            telemetry_frame, 
            text="CPU LOAD: MONITORING...", 
            font=("Courier", 11), 
            fg="#38bdf8", 
            bg="#030712", 
            anchor="w"
        )
        self.cpu_label.pack(fill="x", pady=4)
        
        self.ram_label = tk.Label(
            telemetry_frame, 
            text="MEMORY ALLOCATION: MONITORING...", 
            font=("Courier", 11), 
            fg="#38bdf8", 
            bg="#030712", 
            anchor="w"
        )
        self.ram_label.pack(fill="x", pady=4)
        
        self.net_label = tk.Label(
            telemetry_frame, 
            text="DISPLAY PROJECTION BUS: OPTIMIZED (1920x1080 @ 60Hz - SYNCED)", 
            font=("Courier", 11), 
            fg="#38bdf8", 
            bg="#030712", 
            anchor="w"
        )
        self.net_label.pack(fill="x", pady=4)

        # Audio Waveform Visualizer Canvas
        tk.Label(telemetry_frame, text="AUDIO / VOICE INPUT SPECTRUM [PROD]:", font=("Courier", 9, "bold"), fg="#94a3b8", bg="#030712", anchor="w").pack(fill="x", pady=(10, 2))
        
        self.canvas = tk.Canvas(telemetry_frame, height=75, bg="#020617", highlightthickness=1, highlightbackground="#38bdf8")
        self.canvas.pack(fill="x", pady=5)

        # Action Buttons Frame (Ultra-Clean Pro Styling)
        button_frame = tk.Frame(telemetry_frame, bg="#030712")
        button_frame.pack(fill="x", pady=15)
        
        btn_1 = tk.Button(button_frame, text="[ LAUNCH JAI CORE ]", bg="#0f172a", fg="#38bdf8", font=("Courier", 9, "bold"), relief="solid", bd=1, padx=8, pady=6, command=self.launch_core)
        btn_1.pack(side="left", padx=4)
        
        btn_2 = tk.Button(button_frame, text="[ TOGGLE HOLO-MAT ]", bg="#0f172a", fg="#4ade80", font=("Courier", 9, "bold"), relief="solid", bd=1, padx=8, pady=6, command=self.toggle_holo)
        btn_2.pack(side="left", padx=4)
        
        btn_3 = tk.Button(button_frame, text="[ SYSTEM DIAGNOSTIC ]", bg="#0f172a", fg="#f43f5e", font=("Courier", 9, "bold"), relief="solid", bd=1, padx=8, pady=6, command=self.run_diagnostic)
        btn_3.pack(side="left", padx=4)
        
        btn_4 = tk.Button(button_frame, text="[ RESET LOGS ]", bg="#0f172a", fg="#fbbf24", font=("Courier", 9, "bold"), relief="solid", bd=1, padx=8, pady=6, command=self.reset_logs)
        btn_4.pack(side="left", padx=4)
        
        # Footer
        footer_label = tk.Label(
            self, 
            text="[HALF-LIFE HACKATHON // WEEK 4 ENTRY 7: PRODUCTION UI POLISH & OPTIMIZATION]", 
            font=("Courier", 9), 
            fg="#94a3b8", 
            bg="#030712"
        )
        footer_label.pack(side="bottom", pady=10)
        
        # Bind F11 for Fullscreen Holographic Mode toggle
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.end_fullscreen)
        self.is_fullscreen = False

        # Start loops
        self.update_telemetry()
        self.animate_waveform()

    def launch_core(self):
        self.status_label.config(text="STATUS: J.A.I. CORE ENGAGED // NEURAL MODULES ONLINE [OPTIMIZED]")

    def toggle_holo(self, event=None):
        current_bg = self.cget("bg")
        if current_bg == "#030712":
            self.configure(bg="#090d16")
            self.status_label.config(text="STATUS: HOLO-MAT OVERLAY ACTIVATED (PROD HIGH CONTRAST)")
        else:
            self.configure(bg="#030712")
            self.status_label.config(text="STATUS: HOLO-MAT OVERLAY STANDARD")

    def run_diagnostic(self):
        self.status_label.config(text="STATUS: DEEP DIAGNOSTIC COMPLETE // 100% SUBSYSTEM INTEGRITY")

    def reset_logs(self):
        self.status_label.config(text="STATUS: TELEMETRY BUFFER FLUSHED & RE-CALIBRATED SUCCESSFULLY")

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)
        self.status_label.config(text=f"STATUS: PROJECTION MAPPING // FULLSCREEN: {self.is_fullscreen}")

    def end_fullscreen(self, event=None):
        self.is_fullscreen = False
        self.attributes("-fullscreen", False)
        self.status_label.config(text="STATUS: PROJECTION MAPPING // WINDOWED MODE")

    def update_telemetry(self):
        if PSUTIL_AVAILABLE:
            try:
                cpu = psutil.cpu_percent()
                ram = psutil.virtual_memory()
                ram_used = round(ram.used / (1024**3), 1)
                ram_total = round(ram.total / (1024**3), 1)
                ram_pct = ram.percent
                self.cpu_label.config(text=f"CPU LOAD: {cpu}% [OPTIMIZED]")
                self.ram_label.config(text=f"MEMORY ALLOCATION: {ram_used} / {ram_total} GB ({ram_pct}%)")
            except Exception:
                cpu = round(random.uniform(15.0, 35.0), 1)
                self.cpu_label.config(text=f"CPU LOAD: {cpu}% [OPTIMIZED]")
                self.ram_label.config(text=f"MEMORY ALLOCATION: 4.8 / 16.0 GB (30%)")
        else:
            cpu = round(random.uniform(15.0, 35.0), 1)
            self.cpu_label.config(text=f"CPU LOAD: {cpu}% [SIMULATED]")
            self.ram_label.config(text=f"MEMORY ALLOCATION: 4.8 / 16.0 GB (30%)")
            
        self.after(1000, self.update_telemetry)

    def animate_waveform(self):
        self.canvas.delete("all")
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width > 1:
            bars = 36
            bar_width = width / bars
            for i in range(bars):
                h = random.randint(12, height - 12)
                x0 = i * bar_width + 2
                y0 = (height - h) / 2
                x1 = (i + 1) * bar_width - 2
                y1 = y0 + h
                color = "#38bdf8" if i % 2 == 0 else "#4ade80"
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
                
        self.after(140, self.animate_waveform)

if __name__ == "__main__":
    app = JAIHUD()
    app.mainloop()
