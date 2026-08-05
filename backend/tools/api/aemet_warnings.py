import requests
import os
import tarfile
import io
import xml.etree.ElementTree as ET
from backend.core.base_tool import BaseTool
from backend.core.registry import register_tool

# AEMET CAP area codes for all of Spain
AREA_CODES = {
    "andalucia": "61",
    "aragon": "62",
    "asturias": "63",
    "baleares": "64",
    "canarias": "65",
    "cantabria": "66",
    "castilla y leon": "67",
    "castilla-la mancha": "68",
    "cataluña": "69",
    "extremadura": "70",
    "galicia": "71",
    "madrid": "72",
    "murcia": "73",
    "navarra": "74",
    "pais vasco": "75",
    "la rioja": "76",
    "comunitat valenciana": "77",
    "ceuta": "78",
    "melilla": "79",
}

CAP_NS = "{urn:oasis:names:tc:emergency:cap:1.2}"

@register_tool(name="aemet_warnings", category="API")
class AemetWarningsTool(BaseTool):
    name = "aemet_warnings"
    description = (
        "Fetches live meteorological hazard warnings (rain, wind, heat, coastal, etc.) from the AEMET OpenData CAP API. "
        "You MUST specify a region (e.g., 'comunitat valenciana', 'madrid', 'andalucia')."
    )
    category = "API"
    cacheable = False

    def execute(self, region: str = "comunitat valenciana", api_key: str = None) -> dict:
        key = api_key or os.environ.get("AEMET_API_KEY")
        
        if not key:
            return {
                "status": "error",
                "message": "AEMET API Key is missing. Set the AEMET_API_KEY environment variable."
            }

        headers = {"api_key": key, "Accept": "application/json"}
        all_warnings = []
        
        region_clean = region.strip().lower()
        # Basic normalization for common accents
        region_clean = region_clean.replace("catalonia", "cataluña")
        if region_clean == "valencia":
            region_clean = "comunitat valenciana"
        area_code = AREA_CODES.get(region_clean)
        
        if not area_code:
            return {
                "status": "error",
                "message": f"Region '{region}' not found. Supported regions are: {', '.join(AREA_CODES.keys())}"
            }

        try:
            # Step 1: Request the data link for this area
            url = f"https://opendata.aemet.es/opendata/api/avisos_cap/ultimoelaborado/area/{area_code}"
            res1 = requests.get(url, headers=headers, timeout=10)
            res1.raise_for_status()
            meta = res1.json()

            datos_url = meta.get("datos")
            if not datos_url:
                return {
                    "status": "success",
                    "region": region,
                    "warnings": []
                }

            # Step 2: Download the tar archive
            res2 = requests.get(datos_url, timeout=15)
            res2.raise_for_status()

            # Step 3: Extract and parse CAP XML files from the tar
            tar_bytes = io.BytesIO(res2.content)
            try:
                with tarfile.open(fileobj=tar_bytes, mode="r:*") as tar:
                    for member in tar.getmembers():
                        if not member.name.endswith(".xml"):
                            continue
                        f = tar.extractfile(member)
                        if f is None:
                            continue
                        xml_content = f.read()
                        warnings = self._parse_cap_xml(xml_content, region)
                        all_warnings.extend(warnings)
            except tarfile.TarError:
                # Sometimes AEMET returns raw XML instead of tar
                warnings = self._parse_cap_xml(res2.content, region)
                all_warnings.extend(warnings)

        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Failed to fetch warnings: {str(e)}"
            }

        # Deduplicate by identifier
        seen = set()
        unique = []
        for w in all_warnings:
            wid = w.get("identifier", id(w))
            if wid not in seen:
                seen.add(wid)
                unique.append(w)

        return {
            "status": "success",
            "source": "AEMET OpenData CAP API (Live)",
            "region": region,
            "active_warnings_count": len(unique),
            "data": unique
        }

    def _parse_cap_xml(self, xml_bytes: bytes, area_name: str) -> list:
        """Parse a CAP 1.2 XML document and extract warning info blocks."""
        warnings = []
        try:
            root = ET.fromstring(xml_bytes)
            identifier = root.findtext(f"{CAP_NS}identifier", "")

            for info in root.findall(f"{CAP_NS}info"):
                lang = info.findtext(f"{CAP_NS}language", "")
                # Only take Spanish entries to avoid duplicates
                if lang and "es" not in lang.lower():
                    continue

                event = info.findtext(f"{CAP_NS}event", "")
                severity = info.findtext(f"{CAP_NS}severity", "")
                urgency = info.findtext(f"{CAP_NS}urgency", "")
                certainty = info.findtext(f"{CAP_NS}certainty", "")
                headline = info.findtext(f"{CAP_NS}headline", "")
                description = info.findtext(f"{CAP_NS}description", "")
                onset = info.findtext(f"{CAP_NS}onset", "")
                expires = info.findtext(f"{CAP_NS}expires", "")

                # Extract the AEMET-specific color level from eventCode
                level = ""
                for ec in info.findall(f"{CAP_NS}eventCode"):
                    vn = ec.findtext(f"{CAP_NS}valueName", "")
                    if "nivel" in vn.lower() or "color" in vn.lower():
                        level = ec.findtext(f"{CAP_NS}value", "")

                # Extract affected area names
                areas = []
                for area_el in info.findall(f"{CAP_NS}area"):
                    aname = area_el.findtext(f"{CAP_NS}areaDesc", "")
                    if aname:
                        areas.append(aname)

                warnings.append({
                    "identifier": identifier,
                    "event": event,
                    "severity": severity,
                    "urgency": urgency,
                    "certainty": certainty,
                    "level": level,
                    "headline": headline,
                    "description": description[:300] if description else "",
                    "onset": onset,
                    "expires": expires,
                    "affected_areas": areas,
                    "region": area_name,
                })
        except ET.ParseError:
            pass

        return warnings
