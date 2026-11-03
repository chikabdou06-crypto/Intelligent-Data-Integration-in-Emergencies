import re
import unicodedata

# Valencian Community municipality codes (INE 5-digit codes)
# Full list at: https://www.ine.es/daco/daco42/codmun/diccionario24.xlsx
MUNICIPIO_ALIASES = {
    # === ALICANTE PROVINCE (03) ===
    "san vicente": "03122",
    "san vicente del raspeig": "03122",
    "sant vicent del raspeig": "03122",
    "alicante": "03014",
    "alacant": "03014",
    "elche": "03065",
    "elx": "03065",
    "benidorm": "03031",
    "torrevieja": "03133",
    "orihuela": "03099",
    "alcoy": "03009",
    "alcoi": "03009",
    "denia": "03063",
    "javea": "03082",
    "xabia": "03082",
    "villena": "03140",
    "petrer": "03101",
    "novelda": "03092",
    "ibi": "03073",
    "calpe": "03047",
    "calp": "03047",
    "altea": "03017",
    "crevillent": "03060",
    "crevillente": "03060",
    "guardamar": "03071",
    "guardamar del segura": "03071",
    "jacarilla": "03075",
    "rojales": "03114",
    "bigastro": "03033",
    "benissa": "03032",
    "pego": "03100",
    "cocentaina": "03057",
    "muro": "03090",
    "villajoyosa": "03139",
    "la vila joiosa": "03139",
    "finestrat": "03066",
    "alfas del pi": "03010",
    "l alfas del pi": "03010",
    "santa pola": "03119",
    "elda": "03064",
    "aspe": "03024",
    "monover": "03087",
    "monforte del cid": "03086",
    "muchamiel": "03006",
    "mutxamel": "03006",
    # === VALENCIA PROVINCE (46) ===
    "valencia": "46250",
    "valència": "46250",
    "gandia": "46131",
    "sagunto": "46220",
    "torrent": "46244",
    "paterna": "46190",
    "mislata": "46167",
    "burjassot": "46083",
    "manises": "46156",
    "requena": "46213",
    "alzira": "46030",
    "xativa": "46145",
    "ontinyent": "46181",
    # === CASTELLÓN PROVINCE (12) ===
    "castellon": "12040",
    "castelló": "12040",
    "castellon de la plana": "12040",
    "burriana": "12032",
    "vila real": "12135",
    "villarreal": "12135",
    "benicassim": "12026",
    "onda": "12084",
    "vinaros": "12138",
    # === NATIONAL MAJOR CITIES ===
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
    """Removes accents, converts to lowercase, keeps only alphanumeric characters and spaces.
    Also strips seismic catalog suffixes like '.A', '.B' from location names (e.g. 'JACARILLA.A').
    """
    if not s:
        return ""
    # Strip seismic catalog location suffixes: "JACARILLA.A" -> "JACARILLA"
    s = re.sub(r'\.[A-Z]$', '', s.strip())
    s = unicodedata.normalize('NFD', s)
    s = "".join([c for c in s if unicodedata.category(c) != 'Mn'])
    s = s.lower()
    s = s.replace("/", " ").replace("-", " ")
    s = re.sub(r'[^a-z0-9\s]', '', s)
    # Collapse multiple spaces
    s = re.sub(r'\s+', ' ', s)
    return s.strip()
