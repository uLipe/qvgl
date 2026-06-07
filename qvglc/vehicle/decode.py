from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .emit_apply import VehicleBindError, load_bindings

QVGL_VEHICLE_DEMO_CAN_SPEED_RPM = 0x200


@dataclass
class VehicleState:
    speed_kmh: float = 0.0
    rpm: float = 0.0
    gear: int = 0
    warnings: int = 0


def vehicle_state_init() -> VehicleState:
    return VehicleState()


def decode_demo_can(can_id: int, data: bytes, st: VehicleState) -> bool:
    if len(data) < 4 or can_id != QVGL_VEHICLE_DEMO_CAN_SPEED_RPM:
        return False
    speed_raw = data[0] | (data[1] << 8)
    rpm_raw = data[2] | (data[3] << 8)
    st.speed_kmh = float(speed_raw) * 0.1
    st.rpm = float(rpm_raw)
    if len(data) >= 5:
        st.gear = data[4]
    if len(data) >= 6:
        st.warnings = data[5]
    return True


def parse_can_arg(arg: str) -> tuple[int, bytes]:
    if ":" not in arg:
        raise VehicleBindError(f"invalid --can {arg!r} (expected ID:HEXBYTES)")
    id_part, hex_part = arg.split(":", 1)
    if not hex_part:
        raise VehicleBindError(f"invalid --can {arg!r} (missing payload)")
    try:
        can_id = int(id_part, 0)
        data = bytes.fromhex(hex_part)
    except ValueError as e:
        raise VehicleBindError(f"invalid --can {arg!r}: {e}") from e
    return can_id, data


def apply_can_arg(st: VehicleState, arg: str) -> bool:
    can_id, data = parse_can_arg(arg)
    return decode_demo_can(can_id, data, st)


def prop_sets_from_state(st: VehicleState, bindings_path: Path) -> list[str]:
    bindings = load_bindings(bindings_path)
    out: list[str] = []
    for row in bindings["mappings"]:
        name = row["vehicle"]
        prop = row["property"]
        if not hasattr(st, name):
            raise VehicleBindError(f"unknown vehicle field {name!r} in bindings")
        value = getattr(st, name)
        if isinstance(value, float):
            out.append(f"{prop}={value:g}")
        else:
            out.append(f"{prop}={value}")
    return out


def prop_sets_from_can_args(can_args: list[str], bindings_path: Path) -> list[str]:
    if not bindings_path.is_file():
        raise VehicleBindError(f"vehicle bindings not found: {bindings_path}")
    st = vehicle_state_init()
    applied = False
    for arg in can_args:
        if apply_can_arg(st, arg):
            applied = True
    if not applied:
        raise VehicleBindError("no --can frame matched demo decoder (ID 0x200)")
    return prop_sets_from_state(st, bindings_path)


def default_bindings_path(qml_path: Path) -> Path:
    return qml_path.parent / "vehicle_bindings.yaml"
