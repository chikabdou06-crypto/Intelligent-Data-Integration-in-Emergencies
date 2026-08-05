import re
import unicodedata

# Valencian Community municipality codes (INE 5-digit codes)
# Full list at: https://www.ine.es/daco/daco42/codmun/diccionario24.xlsx
MUNICIPIO_ALIASES = {
    "san vicente": "03122",
    "san vicente del raspeig": "03122",
    "sant vicent del raspeig": "03122",
    "alicante": "03014",
    "alacant": "03014",
    "valencia": "46250",
    "valència": "46250",
    "castellon": "12040",
    "castelló": "12040",
    "elche": "03065",
    "elx": "03065",
    "benidorm": "03031",
    "torrevieja": "03133",
    "orihuela": "03099",
    "gandia": "46131",
    "alcoy": "03009",
    "denia": "03063",
    "sagunto": "46220",
    "torrent": "46244",
    "paterna": "46190",
    # National Major Cities
    "madrid": "28079",
    "barcelona": "08019",
    "sevilla": "41091",
    "zaragoza": "50297",
    "bilbao": "48020",
    "malaga": "29067",
    "málaga": "29067",
    "palma": "07040",
    "murcia": "30030",
}

def normalize_string(s: str) -> str:
    """Removes accents, converts to lowercase, keeps only alphanumeric characters and spaces."""
    if not s:
        return ""
    s = unicodedata.normalize('NFD', s)
    s = "".join([c for c in s if unicodedata.category(c) != 'Mn'])
    s = s.lower()
    s = re.sub(r'[^a-z0-9\s]', '', s)
    return s.strip()
