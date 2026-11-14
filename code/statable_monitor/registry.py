"""XML からレジストリを構築。"""
import zlib
from dataclasses import dataclass
from xml.etree import ElementTree as ET


@dataclass
class VariableInfo:
    id: int
    name: str
    c_type: str
    unit: str = "-"
    group: str = "-"
    description: str = ""


@dataclass
class RegistryInfo:
    variables: list
    crc32: int


def load_xml(path):
    root = ET.parse(path).getroot()
    vs = []
    for i, el in enumerate(root.findall(".//variable")):
        raw = el.get("type", "uint32_t")
        t = raw.replace("volatile", "").replace("const", "").strip()
        vs.append(VariableInfo(
            id=i,
            name=el.get("name", f"var{i}"),
            c_type=t,
            unit=el.get("unit", "-"),
            group=el.get("group", "-"),
            description=el.get("description", ""),
        ))
    payload = "\n".join(f"{v.name}:{v.c_type}" for v in vs)
    crc = zlib.crc32(payload.encode("utf-8")) & 0xFFFFFFFF
    return RegistryInfo(vs, crc)
