import argparse
import json
import mysql.connector
from mysql.connector import errorcode



def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--file', required=True, help='JSON file containing an array of wells')
    p.add_argument('--host', default='127.0.0.1')
    p.add_argument('--user', required=True)
    p.add_argument('--password', default = None)
    p.add_argument('--database', default='dsci560_wells')
    p.add_argument('--commit', action='store_true', help='Commit to DB')
    return p.parse_args()

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    args = parse_args()
    data = load_json(args.file)
    print(f"Loaded {len(data)} records from {args.file}")

    if args.password:
        cnx = mysql.connector.connect(
            host=args.host,
            user=args.user,
            password=args.password,
            database=args.database
        )
    else:
        cnx = mysql.connector.connect(
            host=args.host,
            user=args.user,
            database=args.database
        )
    cur = cnx.cursor()

    # Prepared upsert for wells: uses ON DUPLICATE KEY UPDATE for unique api
    wells_sql = """
    INSERT INTO wells
      (api, well_name, well_number, address, city, county, state, zip,
       latitude, longitude, status, well_type, closest_city,
       barrels_oil, barrels_gas, raw_text, notes)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
      well_name=VALUES(well_name),
      well_number=VALUES(well_number),
      address=VALUES(address),
      city=VALUES(city),
      county=VALUES(county),
      state=VALUES(state),
      zip=VALUES(zip),
      latitude=VALUES(latitude),
      longitude=VALUES(longitude),
      status=VALUES(status),
      well_type=VALUES(well_type),
      closest_city=VALUES(closest_city),
      barrels_oil=VALUES(barrels_oil),
      barrels_gas=VALUES(barrels_gas),
      raw_text=VALUES(raw_text),
      notes=VALUES(notes)
    """

    stim_sql = """
    INSERT INTO stimulation (well_api, stage, fluid_vol, proppant_lbs, chemicals, other_fields)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    inserted = 0
    for item in data:
        api = item.get('api') 
        if not api:
            print("Skipping record without api:", item)
            continue

        well_name = item.get('well_name') or item.get('wellName') or None
        well_number = item.get('well_number') or None
        address = item.get('address') or None
        city = item.get('city') or None
        county = item.get('county') or None
        state = item.get('state') or None
        zipc = item.get('zip') or item.get('postal') or None
        latitude = item.get('latitude')
        longitude = item.get('longitude')
        status = item.get('status') or None
        well_type = item.get('well_type') or item.get('type') or None
        closest_city = item.get('closest_city') or None
        barrels_oil = safe_float(item.get('oil_prod') or item.get('barrels_oil'))
        barrels_gas = safe_float(item.get('gas_prod') or item.get('barrels_gas'))
        raw_text = json.dumps(item, ensure_ascii=False)

        # Insert/upsert well
        cur.execute(wells_sql, (
            api, well_name, well_number, address, city, county, state, zipc,
            latitude, longitude, status, well_type, closest_city,
            barrels_oil, barrels_gas, raw_text, None
        ))

        # Insert stimulation row (one stage default). If stim_volume or stim_proppant missing -> NULL
        stim_volume = safe_float(item.get('stim_volume'))
        stim_proppant = safe_float(item.get('stim_proppant'))
        other_fields = json.dumps({k: item.get(k) for k in ('stim_volume','stim_proppant') if k in item}, ensure_ascii=False) or None

        # Only insert stimulation row if at least one stim field
        if ('stim_volume' in item) or ('stim_proppant' in item):
            cur.execute(stim_sql, (api, 1, stim_volume, stim_proppant, None, other_fields))

        inserted += 1

    print(f"Processed {inserted} records.")
    if args.commit:
        cnx.commit()
        print("Changes committed to database.")
    else:
        cnx.rollback()
        print("No changes were committed.")

    cur.close()
    cnx.close()

def safe_float(x):
    try:
        if x is None: return None
        return float(x)
    except Exception:
        return None

if __name__ == '__main__':
    main()