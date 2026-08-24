"""The standing harbour scene used to regression-test the whole pipeline.

Four vessels sit far enough apart that association is unambiguous:
  - `skiff`  — 8 m fishing boat, no AIS. Legally exempt: must never alert.
  - `dark`   — 120 m vessel, no AIS. The real dark vessel: must alert, but only
               after it persists.
  - `111`    — an AIS track with no vessel in view: an AIS ghost (raised only because
               a camera covers where it claims to be).
  - `clean`  — a 90 m vessel that matches its own AIS (`222`): must stay silent.
"""

from nereus.enums import SensorType, VesselClass
from nereus.models.ais_message import AisMessage
from nereus.models.camera import Camera
from nereus.models.detection import Detection


def _detection(det_id, lat, lon, length_m, confidence, vessel_class, ts):
    return Detection(
        timestamp=ts,
        det_id=det_id,
        camera_id="cam-1",
        lat=lat,
        lon=lon,
        vessel_class=vessel_class,
        length_m=length_m,
        heading=90.0,
        confidence=confidence,
        sensor=SensorType.EO,
    )


def _ais(mmsi, lat, lon, length_m, ts):
    return AisMessage(
        timestamp=ts,
        mmsi=mmsi,
        lat=lat,
        lon=lon,
        sog=0.0,
        cog=90.0,
        ship_type=70,
        length_m=length_m,
    )


def harbour_camera():
    """One camera whose range circle covers the whole harbour scene."""
    return [Camera(camera_id="cam-1", lat=31.815, lon=34.615, range_m=3000.0)]


def harbour_frame(ts):
    detections = [
        _detection("skiff", 31.800, 34.600, 8.0, 0.92, VesselClass.FISHING, ts),
        _detection("dark", 31.810, 34.610, 120.0, 0.90, VesselClass.CARGO, ts),
        _detection("clean", 31.830, 34.630, 90.0, 0.88, VesselClass.CARGO, ts),
    ]
    ais_messages = [
        _ais(111111111, 31.820, 34.620, 80.0, ts),
        _ais(222222222, 31.830, 34.630, 90.0, ts),
    ]
    return detections, ais_messages, ts
