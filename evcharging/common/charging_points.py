"""
Static metadata for charging points used by driver dashboards.

In a full deployment this would come from an asset registry service.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ChargingPointMetadata:
    cp_id: str
    name: str
    address: str
    city: str
    latitude: float
    longitude: float
    connector_type: str
    power_kw: float
    amenities: List[str]


METADATA: Dict[str, ChargingPointMetadata] = {
    "CP-001": ChargingPointMetadata(
        cp_id="CP-001",
        name="Central Plaza A1",
        address="123 Main St",
        city="Metropolis",
        latitude=40.7128,
        longitude=-74.0060,
        connector_type="Type 2",
        power_kw=22.0,
        amenities=["Restrooms", "Coffee", "WiFi"],
    ),
    "CP-002": ChargingPointMetadata(
        cp_id="CP-002",
        name="Harbor Fast Charge",
        address="5 Harbor Ave",
        city="Metropolis",
        latitude=40.7000,
        longitude=-74.0100,
        connector_type="CCS",
        power_kw=150.0,
        amenities=["24/7", "Restrooms"],
    ),
    "CP-003": ChargingPointMetadata(
        cp_id="CP-003",
        name="Airport Lot C",
        address="Airport Rd",
        city="Metropolis",
        latitude=40.6890,
        longitude=-74.1745,
        connector_type="Type 2",
        power_kw=11.0,
        amenities=["Parking", "Security"],
    ),
}


def get_metadata(cp_id: str) -> Optional[ChargingPointMetadata]:
    """Return metadata for a charging point, if available."""
    return METADATA.get(cp_id)

