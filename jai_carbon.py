# jai_carbon.py
import os
import json
import requests
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CarbonInterface:
    """Carbon Interface API integration for JAI"""
    
    def __init__(self):
        self.api_key = os.environ.get("CARBON_INTERFACE_API_KEY")
        self.base_url = "https://www.carboninterface.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    def _make_request(self, endpoint: str, data: dict) -> dict:
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Carbon Interface API error: {e}")
            return {"error": str(e)}
    
    def estimate_electricity(self, kwh: float, country: str = "us", state: str = None) -> dict:
        """Estimate carbon from electricity usage"""
        payload = {
            "type": "electricity",
            "electricity_unit": "kwh",
            "electricity_value": kwh,
            "country": country
        }
        if state:
            payload["state"] = state
        return self._make_request("/estimates", payload)
    
    def estimate_flight(self, legs: list, passengers: int = 1) -> dict:
        """Estimate carbon from flights"""
        payload = {
            "type": "flight",
            "passengers": passengers,
            "legs": legs
        }
        return self._make_request("/estimates", payload)
    
    def estimate_vehicle(self, distance_km: float, vehicle_model_id: str) -> dict:
        """Estimate carbon from vehicle travel"""
        payload = {
            "type": "vehicle",
            "distance_unit": "km",
            "distance_value": distance_km,
            "vehicle_model_id": vehicle_model_id
        }
        return self._make_request("/estimates", payload)
    
    def estimate_shipping(self, weight_kg: float, distance_km: float, method: str = "truck") -> dict:
        """Estimate carbon from shipping"""
        payload = {
            "type": "shipping",
            "weight_unit": "kg",
            "weight_value": weight_kg,
            "distance_unit": "km",
            "distance_value": distance_km,
            "transport_method": method
        }
        return self._make_request("/estimates", payload)


# Global instance
carbon_client = CarbonInterface()
