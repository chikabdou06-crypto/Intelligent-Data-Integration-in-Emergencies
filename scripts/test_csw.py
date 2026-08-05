import requests
url = 'http://catalogo.icv.gva.es/geonetwork/srv/spa/csw'
payload = """<?xml version="1.0"?>
<csw:GetRecords xmlns:csw="http://www.opengis.net/cat/csw/2.0.2" service="CSW" version="2.0.2" resultType="results" maxRecords="3">
  <csw:Query typeNames="csw:Record">
    <csw:ElementSetName>brief</csw:ElementSetName>
  </csw:Query>
</csw:GetRecords>"""
res = requests.post(url, data=payload, headers={'Content-Type': 'application/xml'})
print("Status:", res.status_code)
print(res.text[:1000])
