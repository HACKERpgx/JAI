import tkinter as tk
import random

class JAIHUD(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("J.A.I. Spatial HUD Interface")
        self.geometry("850x520")
        self.configure(bg="#050b14")
        
        # Header Title
        title_label = tk.Label(
            self, 
            text="J.A.I. // SPATIAL HUD SYSTEM", 
            font=("Courier", 18, "bold"), 
            fg="#00f3ff", 
            bg="#050b14"
        )
        title_label.pack(pady=20)
        
        # Status Frame
        status_frame = tk.Frame(self, bg="#0a192f", highlightbackground="#00f3ff", highlightthickness=1)
        status_frame.pack(fill="x", padx=40, pady=10)
        
        self.status_label = tk.Label(
            status_frame, 
            text="STATUS: CORE ONLINE // READY FOR GESTURE & VOICE INPUT", 
            font=("Courier", 11), 
            fg="#00ff66", 
            bg="#0a192f"
        )
        self.status_label.pack(padx=20, pady=15)
        
        # Telemetry Frame
        telemetry_frame = tk.Frame(self, bg="#050b14")
        telemetry_frame.pack(fill="both", expand=True, padx=40, pady=10)
        
        self.cpu_label = tk.Label(
            telemetry_frame, 
            text="CPU LOAD: 14.2%", 
            font=("Courier", 11), 
            fg="#00f3ff", 
            bg="#050b14", 
            anchor="w"
        )
        self.cpu_label.pack(fill="x", pady=6)
        
        self.ram_label = tk.Label(
            telemetry_frame, 
            text="MEMORY ALLOCATION: 4.8 / 16.0 GB (30%)", 
            font=("Courier", 11), 
            fg="#00f3ff", 
            bg="#050b14", 
            anchor="w"
        )
        self.ram_label.pack(fill="x", pady=6)
        
        self.net_label = tk.Label(
            telemetry_frame, 
            text="LOCAL LINK: ACTIVE // MAPPING DISPLAY MAT OVERLAY", 
            font=("Courier", 11), 
            fg="#00f3ff", 
            bg="#050b14", 
            anchor="w"
        )
        self.net_label.pack(fill="x", pady=6)
        
        # Footer
        footer_label = tk.Label(
            self, 
            text="[HALF-LIFE HACKATHON // WEEK 4: DESIGN WITH DISPLAYS]", 
            font=("Courier", 9), 
            fg="#8892b0", 
            bg="#050b14"
        )
        footer_label.pack(side="bottom", pady=15)
        
        # Simulate live telemetry fluctuation
        self.update_telemetry()

    def update_telemetry(self):
        cpu_val = round(random.uniform(12.0, 28.5), 1)
        self.cpu_label.config(text=f"CPU LOAD: {cpu_val}%")
        self.after(1500, self.update_telemetry)

if __name__ == "__main__":
    app = JAIHUD()
    app.mainloop()
