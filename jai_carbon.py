# jai_carbon.py
def handle_carbon_command(command: str, session) -> str:
    """Simple carbon footprint handler"""
    cmd = command.lower()
    
    if "driving" in cmd or "car" in cmd:
        return "Driving a car for 100 km produces approximately 20-25 kg of CO2 (depending on the car type)."
    elif "flight" in cmd or "flying" in cmd:
        return "A flight from New York to London produces around 1,000 kg of CO2 per passenger."
    elif "beef" in cmd:
        return "Eating beef has a much higher carbon footprint than vegetables (about 60 kg CO2 per kg of beef)."
    else:
        return "I can help estimate carbon footprints for activities like driving, flying, or diet. Try asking something specific!"
