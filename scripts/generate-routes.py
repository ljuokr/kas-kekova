#!/usr/bin/env python3
"""Generate route-data.json and all GPX/KML exports from route-source.json.

Requires Python 3.9+ and its standard library. Run with --check to verify that
committed exports are current without writing files. Coordinates are [lon, lat].
"""
import argparse
import copy
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
GPX_NS = 'http://www.topografix.com/GPX/1/1'
KML_NS = 'http://www.opengis.net/kml/2.2'
COLORS = ['#1465a0', '#7a3fb1', '#bd5a19', '#287b50']


def distance_km(p1, p2):
    """WGS84 inverse Vincenty distance, suitable for these short local legs."""
    if p1 == p2:
        return 0.0
    a, f = 6378137.0, 1 / 298.257223563
    b = (1 - f) * a
    lon1, lat1, lon2, lat2 = map(math.radians, [*p1, *p2])
    u1, u2 = math.atan((1 - f) * math.tan(lat1)), math.atan((1 - f) * math.tan(lat2))
    su1, cu1, su2, cu2 = math.sin(u1), math.cos(u1), math.sin(u2), math.cos(u2)
    dl = lon2 - lon1
    lam = dl
    for _ in range(200):
        sl, cl = math.sin(lam), math.cos(lam)
        ss = math.hypot(cu2 * sl, cu1 * su2 - su1 * cu2 * cl)
        cs = su1 * su2 + cu1 * cu2 * cl
        sigma = math.atan2(ss, cs)
        sa = cu1 * cu2 * sl / ss
        csa = 1 - sa * sa
        c2sm = cs - 2 * su1 * su2 / csa if csa else 0.0
        c = f / 16 * csa * (4 + f * (4 - 3 * csa))
        previous = lam
        lam = dl + (1 - c) * f * sa * (sigma + c * ss * (c2sm + c * cs * (-1 + 2 * c2sm * c2sm)))
        if abs(lam - previous) < 1e-12:
            break
    else:
        raise ValueError('Vincenty did not converge; source contains an unsupported long leg.')
    u2sq = csa * (a * a - b * b) / (b * b)
    aa = 1 + u2sq / 16384 * (4096 + u2sq * (-768 + u2sq * (320 - 175 * u2sq)))
    bb = u2sq / 1024 * (256 + u2sq * (-128 + u2sq * (74 - 47 * u2sq)))
    ds = bb * ss * (c2sm + bb / 4 * (cs * (-1 + 2 * c2sm * c2sm)
        - bb / 6 * c2sm * (-3 + 4 * ss * ss) * (-3 + 4 * c2sm * c2sm)))
    return b * aa * (sigma - ds) / 1000


def length(points):
    return sum(distance_km(a, b) for a, b in zip(points, points[1:]))


def expand(source, stage):
    """Use only original consecutive points; reverse when returning west."""
    points = []
    ids = [stage['from'], *stage['via'], stage['to']]
    for start, end in zip(ids, ids[1:]):
        a, b = source['anchors'][start], source['anchors'][end]
        step = 1 if b >= a else -1
        segment = [source['coordinates'][i] for i in range(a, b + step, step)]
        points.extend(segment if not points else segment[1:])
    stage['coordinates'] = points
    stage['distanceKm'] = round(length(points), 6)
    return stage


def make_data(source):
    data = {k: copy.deepcopy(source[k]) for k in [
        'schemaVersion', 'title', 'coordinateOrder', 'distanceMethod',
        'provenance', 'planningNote', 'waypoints', 'variants', 'options'
    ]}
    data['defaultVariant'] = 'gokkaya'
    data['anchors'] = {key: source['coordinates'][i] for key, i in source['anchors'].items()}
    for variant in data['variants'].values():
        for i, day in enumerate(variant['days']):
            expand(source, day)
            day['color'] = COLORS[i]
        variant['totalDistanceKm'] = round(sum(day['distanceKm'] for day in variant['days']), 6)
        variant['roundTrip'] = True
    for option in data['options'].values():
        expand(source, option)
        option['color'] = '#657078'
        option['roundTrip'] = False
    return data


def xml_text(element, namespace):
    ET.register_namespace('', namespace)
    ET.indent(element, space='  ')
    return ET.tostring(element, encoding='utf-8', xml_declaration=True).decode() + '\n'


def add(parent, namespace, name, text=None, **attributes):
    child = ET.SubElement(parent, '{' + namespace + '}' + name, attributes)
    if text is not None:
        child.text = str(text)
    return child


def make_gpx(data, trip, stages):
    gpx = ET.Element('{' + GPX_NS + '}gpx', version='1.1', creator='Kaş–Kekova route generator')
    meta = add(gpx, GPX_NS, 'metadata')
    add(meta, GPX_NS, 'name', trip['label'])
    add(meta, GPX_NS, 'desc', data['planningNote'] + ' ' + trip.get('note', ''))
    for point in data['waypoints']:
        if point['id'] not in trip['waypointIds']:
            continue
        lon, lat = point['coordinates']
        wpt = add(gpx, GPX_NS, 'wpt', lat=f'{lat:.5f}', lon=f'{lon:.5f}')
        add(wpt, GPX_NS, 'name', point['name'])
        if point.get('note'):
            add(wpt, GPX_NS, 'desc', point['note'])
    for stage in stages:
        trk = add(gpx, GPX_NS, 'trk')
        add(trk, GPX_NS, 'name', stage['label'])
        add(trk, GPX_NS, 'desc', f"{stage['distanceKm']:.2f} km entlang der Planlinie. {stage.get('date', '')}".strip())
        seg = add(trk, GPX_NS, 'trkseg')
        for lon, lat in stage['coordinates']:
            add(seg, GPX_NS, 'trkpt', lat=f'{lat:.5f}', lon=f'{lon:.5f}')
    return xml_text(gpx, GPX_NS)


def make_kml(data, trip, stages):
    kml = ET.Element('{' + KML_NS + '}kml')
    doc = add(kml, KML_NS, 'Document')
    add(doc, KML_NS, 'name', trip['label'])
    add(doc, KML_NS, 'description', data['planningNote'] + ' ' + trip.get('note', ''))
    for stage in stages:
        style = add(doc, KML_NS, 'Style', id=stage['id'])
        line = add(style, KML_NS, 'LineStyle')
        color = stage['color'].lstrip('#')
        add(line, KML_NS, 'color', 'ff' + color[4:6] + color[2:4] + color[0:2])
        add(line, KML_NS, 'width', 4)
    for point in data['waypoints']:
        if point['id'] not in trip['waypointIds']:
            continue
        placemark = add(doc, KML_NS, 'Placemark')
        add(placemark, KML_NS, 'name', point['name'])
        if point.get('note'):
            add(placemark, KML_NS, 'description', point['note'])
        geometry = add(placemark, KML_NS, 'Point')
        add(geometry, KML_NS, 'coordinates', ','.join(map(str, point['coordinates'])) + ',0')
    for stage in stages:
        placemark = add(doc, KML_NS, 'Placemark')
        add(placemark, KML_NS, 'name', f"{stage['label']} · {stage['distanceKm']:.1f} km")
        add(placemark, KML_NS, 'description', stage.get('date', trip.get('note', '')))
        add(placemark, KML_NS, 'styleUrl', '#' + stage['id'])
        line = add(placemark, KML_NS, 'LineString')
        add(line, KML_NS, 'tessellate', 1)
        add(line, KML_NS, 'coordinates', ' '.join(f'{lon:.5f},{lat:.5f},0' for lon, lat in stage['coordinates']))
    return xml_text(kml, KML_NS)


def validate(source, data):
    original_edges = {(tuple(a), tuple(b)) for a, b in zip(source['coordinates'], source['coordinates'][1:])}
    allowed = original_edges | {(b, a) for a, b in original_edges}
    all_stages = list(data['options'].values())
    for variant in data['variants'].values():
        days = variant['days']
        assert len(days) == 4, 'Round trip must have four days.'
        assert days[0]['coordinates'][0] == days[-1]['coordinates'][-1] == data['anchors']['kas']
        for a, b in zip(days, days[1:]):
            assert a['coordinates'][-1] == b['coordinates'][0], 'Discontinuous day boundary.'
        all_stages.extend(days)
    for stage in all_stages:
        for a, b in zip(stage['coordinates'], stage['coordinates'][1:]):
            assert (tuple(a), tuple(b)) in allowed, 'Generated route uses an unverified shortcut.'
        assert stage['coordinates'][0] == data['anchors'][stage['from']]
        assert stage['coordinates'][-1] == data['anchors'][stage['to']]
    assert data['options']['andriake']['coordinates'][-1] == data['anchors']['andriake']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check generated outputs without writing.')
    args = parser.parse_args()
    source = json.loads((ROOT / 'route-source.json').read_text())
    data = make_data(source)
    validate(source, data)
    outputs = {'route-data.json': json.dumps(data, ensure_ascii=False, indent=2) + '\n'}
    for trip in [*data['variants'].values(), *data['options'].values()]:
        stages = trip.get('days', [trip])
        outputs[trip['files']['gpx']] = make_gpx(data, trip, stages)
        outputs[trip['files']['kml']] = make_kml(data, trip, stages)
    for filename, text in outputs.items():
        path = ROOT / filename
        if filename.endswith(('.gpx', '.kml')):
            ET.fromstring(text)
        if args.check:
            assert path.exists() and path.read_text() == text, f'Out of date: {filename}'
        else:
            path.write_text(text)
    for trip in data['variants'].values():
        print(f"{trip['label']}: {trip['totalDistanceKm']:.2f} km")
        print('  ' + ' / '.join(f"{day['distanceKm']:.2f}" for day in trip['days']))
    print(f"Andriake extension: {data['options']['andriake']['distanceKm']:.2f} km")
    print(f"{'Verified' if args.check else 'Generated'} {len(outputs)} files.")


if __name__ == '__main__':
    main()
