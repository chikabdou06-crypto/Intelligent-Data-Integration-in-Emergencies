import requests
url = 'http://catalogo.icv.gva.es/geonetwork/srv/spa/csw'
payload = """<?xml version="1.0"?>
<csw:GetRecords xmlns:csw="http://www.opengis.net/cat/csw/2.0.2" service="CSW" version="2.0.2" resultType="results" maxRecords="2">
  <csw:Query typeNames="csw:Record">
    <csw:ElementSetName>full</csw:ElementSetName>
    <csw:Constraint version="1.1.0">
      <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
        <ogc:PropertyIsLike wildCard="*" singleChar="." escapeChar="!">
          <ogc:PropertyName>AnyText</ogc:PropertyName>
          <ogc:Literal>*riesgo*</ogc:Literal>
        </ogc:PropertyIsLike>
      </ogc:Filter>
    </csw:Constraint>
  </csw:Query>
</csw:GetRecords>"""
res = requests.post(url, data=payload, headers={'Content-Type': 'application/xml'})
print(res.text[:2000])
