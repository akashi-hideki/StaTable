"""XML 変数モデルからレジストリ（ID 順）を構築。"""
from dataclasses import dataclass
from typing import Iterable
import zlib

_C_TYPE_SIZE = {
    "uint8_t": 1, "int8_t": 1, "bool": 1,
    "uint16_t": 2, "int16_t": 2,
    "uint32_t": 4, "int32_t": 4, "float": 4,
}


def _normalize_type(t: str) -> str:
    return t.replace("volatile", "").replace("const", "").strip()


@dataclass(frozen=True)
class VarMeta:
    id: int
    name: str
    c_type: str
    size: int
    unit: str = "-"
    group: str = "-"
    description: str = ""


def build_registry(variables: Iterable[dict]) -> list[VarMeta]:
    result: list[VarMeta] = []
    for i, v in enumerate(variables):
        t = _normalize_type(v["type"])
        if t not in _C_TYPE_SIZE:
            raise ValueError(f"unsupported type: {v['type']} ({v['name']})")
        result.append(VarMeta(
            id=i,
            name=v["name"],
            c_type=t,
            size=_C_TYPE_SIZE[t],
            unit=v.get("unit", "-"),
            group=v.get("group", "-"),
            description=v.get("description", ""),
        ))
    return result


def registry_crc32(vars_: list[VarMeta]) -> int:
    payload = "\n".join(f"{v.name}:{v.c_type}" for v in vars_)
    return zlib.crc32(payload.encode("utf-8")) & 0xFFFFFFFF
