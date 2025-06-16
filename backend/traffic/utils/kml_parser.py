from lxml import etree
from bs4 import BeautifulSoup
import re

def parse_kml_to_intersections(kml_path):
    with open(kml_path, 'rb') as f:
        tree = etree.parse(f)

    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    placemarks = tree.findall('.//kml:Placemark', namespaces=ns)

    intersections = []

    for placemark in placemarks:
        name_el = placemark.find('kml:name', namespaces=ns)
        description_el = placemark.find('kml:description', namespaces=ns)
        coord_el = placemark.find('.//kml:coordinates', namespaces=ns)

        if coord_el is None or coord_el.text is None:
            continue

        try:
            coord_text = coord_el.text.strip()
            lon, lat, *_ = map(float, coord_text.split(','))
        except:
            continue

        # ⛳ 안전하게 name 파싱
        if name_el is not None and name_el.text:
            road_name = name_el.text.strip()
        else:
            road_name = "Unnamed"

        # ⛳ RED SEMAFORICA가 있으면 교체
        if description_el is not None and description_el.text:
            soup = BeautifulSoup(description_el.text, 'html.parser')
            desc = soup.get_text()
            match = re.search(r"RED SEMAFORICA: (.+)", desc)
            if match:
                road_name = match.group(1).strip()

        # 도로 이름이 100자를 초과하지 않도록 제한
        road_name = road_name[:100]

        intersections.append({
            "name": road_name,
            "latitude": lat,
            "longitude": lon,
        })

    print(f"✅ 총 {len(intersections)}개 교차로 파싱 완료")
    return intersections
