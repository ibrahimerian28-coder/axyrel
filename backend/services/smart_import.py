"""Create-only, tenant-scoped Customer/Asset import with signed review and durable receipts."""
import hashlib
import json
import re
import time
from datetime import date
from functools import lru_cache
from pathlib import Path
from uuid import UUID, NAMESPACE_URL, uuid5

import jwt
import pycountry
from pydantic import ValidationError
from sqlalchemy import select

from backend.core.asset_lock import lock_assets
from backend.core.config import get_settings
from backend.core.tenant_isolation import require_company_id
from backend.models.asset import Asset
from backend.models.audit_log import AuditLog
from backend.models.customer import Customer
from backend.schemas.asset import AssetCreate
from backend.services.asset import AssetService
from backend.services.asset_details import prepare_asset_details, AssetDetailError
from backend.services.asset_import import serial_key
from backend.services.customer import CustomerService
from backend.services.customer_phones import normalized_phone, legacy_phones
from backend.services.smart_import_files import FIELDS, MAX_ROWS, MAX_CELL, MODES


@lru_cache
def geography():
    # One reference, shared with the existing Round 1 geography selector.
    return json.loads((Path(__file__).resolve().parents[2] / 'frontend/src/features/phase2/geography.json').read_text(encoding='utf-8'))


def resolve_country(value):
    supplied = value.strip()
    value = value.strip().casefold()
    matches = {c['code'] for c in geography()['countries'] if value in {c['code'].casefold(), c['name'].casefold()}}
    matches.update(c.alpha_2 for c in pycountry.countries if value in {str(getattr(c, key, '')).casefold() for key in ('name', 'official_name', 'common_name', 'alpha_2')})
    if len(matches) != 1: raise AssetDetailError('country', f'Country "{supplied}" was not uniquely recognized. Choose a country from the list.')
    return matches.pop()


def resolve_state(country, value):
    if not value.strip(): return None
    supplied = value.strip()
    value = value.strip().casefold()
    matches = {s['code'] for s in geography()['states'].get(country, []) if value in {s['code'].casefold(), s['name'].casefold()}}
    matches.update(s.code for s in pycountry.subdivisions.get(country_code=country) or [] if value in {s.name.casefold(), s.code.casefold()})
    if len(matches) != 1: raise AssetDetailError('state', f'Governorate / State "{supplied}" was not uniquely recognized for this country. Choose a valid governorate / state.')
    return matches.pop()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, default=str)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def request_rows(data):
    mode, columns, rows, mapping = (data.get(k) for k in ('mode', 'columns', 'rows', 'mapping'))
    if not isinstance(mode, str) or mode not in MODES or not isinstance(columns, list) or not 1 <= len(columns) <= 40 or any(not isinstance(c, str) or len(c) > 100 for c in columns):
        raise ValueError('Choose an import type and upload a supported file.')
    if not isinstance(mapping, list) or len(mapping) != len(columns) or any(not isinstance(key, str) or key not in {'', *FIELDS} for key in mapping):
        raise ValueError('Map each column to a supported field or Ignore this column.')
    selected = [key for key in mapping if key]
    if len(set(selected)) != len(selected): raise ValueError('Each destination field can be mapped only once.')
    required = {'customer_name', 'phone'} if mode != 'assets' else {'asset_type'}
    if not required.issubset(selected): raise ValueError('Map Customer Name and Phone for Customers, and Asset Type for Assets.')
    if mode == 'combined' and 'asset_type' not in selected: raise ValueError('Map Asset Type for Customers + Assets.')
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_ROWS: raise ValueError('Use 1–1000 data rows.')
    corrections = data.get('corrections', {})
    if not isinstance(corrections, dict) or len(corrections) > MAX_ROWS: raise ValueError('Invalid row corrections.')
    result = []
    for index, row in enumerate(rows, 2):
        if not isinstance(row, list) or len(row) != len(columns) or any(not isinstance(v, str) or len(v) > MAX_CELL or '\x00' in v for v in row):
            raise ValueError(f'Row {index}: use bounded plain text cells.')
        record = {key: value for key, value in zip(mapping, row) if key}
        changes = corrections.get(str(index), {})
        if not isinstance(changes, dict) or any(k not in {*FIELDS, 'customer_selection'} or not isinstance(v, str) or len(v) > MAX_CELL or '\x00' in v for k, v in changes.items()):
            raise ValueError(f'Row {index}: invalid corrections.')
        record.update(changes)
        result.append(record)
    if any(not str(key).isdigit() or not 2 <= int(key) <= len(rows) + 1 for key in corrections): raise ValueError('Invalid correction row.')
    return mode, result


def customer_index(customers):
    index = {}
    for customer in customers:
        for phone in customer.phones if customer.phones is not None else legacy_phones(customer):
            try:
                value = normalized_phone(phone.get('country'), phone.get('number', ''))
            except ValueError: continue  # Never infer a country for unresolved legacy values.
            index.setdefault(value, {})[str(customer.id)] = customer
    return index


def validate(db, company_id, data):
    company_id = require_company_id(company_id)
    mode, records = request_rows(data)
    customers = list(db.scalars(select(Customer).where(Customer.company_id == company_id, Customer.status != 'Deleted')))
    phones = customer_index(customers)
    existing_serials = {serial_key(s) for s in db.scalars(select(Asset.serial_number).where(Asset.company_id == company_id)) if serial_key(s)} if mode != 'customers' else set()
    errors, preview, plan, seen_serials, groups = [], [], [], set(), {}
    def error(row, field, message, code='attention'):
        errors.append({'row': row, 'field': field, 'label': FIELDS.get(field, ('Customer',))[0], 'message': message, 'code': code})
    for number, original in enumerate(records, 2):
        row = {key: value.strip() for key, value in original.items()}
        before = len(errors)
        country, state, phone_country, normalized, matched = None, None, None, None, None
        try: country = resolve_country(row.get('country') or 'Egypt')
        except AssetDetailError as exc: error(number, exc.field, str(exc))
        if country:
            try: state = resolve_state(country, row.get('state', ''))
            except AssetDetailError as exc: error(number, exc.field, str(exc))
        try: phone_country = resolve_country(row.get('phone_country') or row.get('country') or 'Egypt')
        except AssetDetailError as exc: error(number, 'phone_country', str(exc))
        if row.get('phone') and phone_country:
            try: normalized = normalized_phone(phone_country, row['phone'])
            except ValueError as exc: error(number, 'phone', str(exc) + ' Choose the phone country and include any missing leading zero.')
        elif not row.get('phone') and not (mode == 'assets' and row.get('customer_selection')):
            error(number, 'phone', 'Enter a valid phone and choose its country so this customer can be matched safely.')
        candidates = list(phones.get(normalized, {}).values()) if normalized else []
        selection = row.get('customer_selection')
        if selection:
            chosen = [c for c in customers if c.display_id is not None and str(c.display_id) == selection]
            if len(chosen) != 1 or (len(candidates) > 1 and chosen[0] not in candidates):
                error(number, 'customer_selection', 'Choose one visible customer from your company; ambiguous phones must be resolved to a matching candidate.')
            else: matched = chosen[0]
        elif len(candidates) > 1:
            error(number, 'phone', 'Multiple customers have this phone. Select the correct existing customer; no customer will be merged automatically.')
        elif len(candidates) == 1: matched = candidates[0]
        elif mode == 'assets': error(number, 'phone', 'No existing customer was found. Select an existing customer or use Customers + Assets.')
        name = row.get('customer_name', '')
        status = row.get('status') or 'Active'
        status = {'active': 'Active', 'inactive': 'Inactive', 'نشط': 'Active', 'غير نشط': 'Inactive'}.get(status.casefold(), status)
        if status not in {'Active', 'Inactive'}: error(number, 'status', 'Choose Active or Inactive. Import cannot create deleted records.')
        if not matched and mode != 'assets' and (not name or len(name) > 200): error(number, 'customer_name', 'Enter a Customer Name of 1–200 characters.')
        label = row.get('phone_label') or 'Primary'
        if len(label) > 100: error(number, 'phone_label', 'Use a phone label of at most 100 characters.')
        if len(row.get('phone', '')) > 100: error(number, 'phone', 'Use a phone number of at most 100 characters.')
        group = normalized or f'row:{number}'
        customer_data = None
        if matched:
            group = str(matched.id)
        elif normalized and mode != 'assets':
            customer_data = {'name': name, 'phones': [{'country': phone_country, 'number': row['phone'], 'label': label}], 'status': status}
            prior = groups.get(group)
            # A shared phone is insufficient to silently combine conflicting customer identities.
            identity = (name.casefold(), label.casefold(), status)
            if prior and prior['identity'] != identity:
                error(number, 'customer_name', 'Rows sharing this phone have conflicting names, labels or status. Correct them to the same customer or select an existing customer.')
                error(prior['row'], 'customer_name', 'This phone also appears with conflicting customer details. Confirm the correct customer by correcting the rows.')
            groups.setdefault(group, {'identity': identity, 'row': number, 'data': customer_data})
        asset = None
        if mode != 'customers':
            asset = {key: value if value != '' else None for key, value in original.items() if key in {'asset_type', 'serial_number', 'manufacturer', 'model', 'area', 'address', 'location_url', 'notes'}}
            if not row.get('asset_type'): error(number, 'asset_type', 'Enter the device / asset type.')
            for key, limit in {'asset_type':150, 'serial_number':150, 'manufacturer':150, 'model':150, 'area':150, 'address':500, 'location_url':1000, 'notes':1000}.items():
                if len(original.get(key, '')) > limit: error(number, key, f'Use at most {limit} characters.')
            serial = serial_key(asset.get('serial_number'))
            if serial:
                if serial in seen_serials: error(number, 'serial_number', 'Serial number repeats in this upload. Give each asset its own serial.', 'duplicate_file')
                if serial in existing_serials: error(number, 'serial_number', 'Serial belongs to an existing or deleted asset in your company. Existing assets will not be overwritten.', 'duplicate_tenant')
                seen_serials.add(serial)
            asset.update(country=country, state=state, status=status)
            for key in ('maintenance_cycle', 'warranty_years'):
                value = row.get(key)
                if value:
                    if not re.fullmatch(r'[0-9]+', value): error(number, key, 'Enter a whole number of months.' if key == 'maintenance_cycle' else 'Enter a whole number of calendar years.')
                    else: asset[key] = int(value)
            value = row.get('installation_date')
            if value:
                try:
                    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value): raise ValueError()
                    asset['installation_date'] = date.fromisoformat(value)
                except ValueError: error(number, 'installation_date', 'Use YYYY-MM-DD or an Excel date cell. Dates such as 01/02/2026 are ambiguous.')
            try:
                asset = AssetCreate.model_validate({**asset, 'customer_id': matched.id if matched else UUID(int=0)}).model_dump(exclude_unset=True)
                asset.pop('customer_id')
                asset = prepare_asset_details(asset)
            except ValidationError as exc:
                for problem in exc.errors(include_input=False): error(number, str(problem['loc'][0]), 'Invalid value. Maintenance must be 1–1200 whole months; warranty must be 0–100 whole years.' if problem['loc'][0] in {'maintenance_cycle','warranty_years'} else 'Enter a valid value for this field.')
            except AssetDetailError as exc: error(number, exc.field, str(exc))
        row_errors = len(errors) > before
        preview.append({'row': number, 'customer': matched.name if matched else name, 'customer_number': matched.display_id if matched else None, 'match': 'Existing customer found' if matched else 'New customer', 'category': 'Needs attention' if row_errors else 'Existing matched' if matched else 'Ready', 'phone': normalized or row.get('phone', ''), 'asset_type': row.get('asset_type',''), 'serial_number': original.get('serial_number',''), 'warranty_end': str(asset.get('warranty_end') or '') if asset else '', 'values': original})
        plan.append({'row': number, 'group': group, 'existing': str(matched.id) if matched else None, 'existing_details': {'name': matched.name, 'number': matched.display_id, 'phones': matched.phones if matched.phones is not None else legacy_phones(matched), 'status': matched.status} if matched else None, 'customer': customer_data, 'asset': asset})
    bad_rows = {e['row'] for e in errors}
    for item in preview:
        if item['row'] in bad_rows: item['category'] = 'Needs attention'
    summary = {'new_customers': len({p['group'] for p in plan if not p['existing']}) if mode != 'assets' else 0, 'existing_customers': len({p['existing'] for p in plan if p['existing']}), 'new_assets': len(plan) if mode != 'customers' else 0, 'overwritten_assets': 0, 'attention_rows': len(bad_rows)}
    return {'valid': not errors, 'rows': len(records), 'preview': preview, 'errors': errors, 'summary': summary}, plan


def preview_token(data, company_id, user_id, plan):
    return jwt.encode({'purpose': 'smart-import', 'company': str(company_id), 'user': str(user_id), 'sha': digest(data), 'plan': digest(plan), 'exp': int(time.time()) + 900}, get_settings().secret_key, algorithm='HS256')


def commit(db, company_id, user_id, data, token, retry_key):
    company_id = require_company_id(company_id)
    claims = jwt.decode(token, get_settings().secret_key, algorithms=['HS256'], options={'verify_exp': False, 'require': ['exp']})
    if any(claims.get(k) != value for k, value in {'purpose':'smart-import', 'company':str(company_id), 'user':str(user_id), 'sha':digest(data)}.items()):
        raise ValueError('Review does not match these rows or this account. Review again.')
    retry_key = str(UUID(str(retry_key)))
    lock_assets(db, company_id)
    receipt_id = uuid5(NAMESPACE_URL, f'axyrel:smart-import:{company_id}:{user_id}:{retry_key}')
    receipt = db.scalar(select(AuditLog).where(AuditLog.id == receipt_id, AuditLog.company_id == company_id, AuditLog.actor_user_id == user_id, AuditLog.action == 'SMART_IMPORT_COMMITTED'))
    if receipt:
        if receipt.event_metadata.get('checksum') != digest(data): raise ValueError('Retry key belongs to a different import.')
        return {**receipt.event_metadata['result'], 'replayed': True}
    if claims['exp'] < time.time(): raise ValueError('Review expired. Review the rows again.')
    # Serialize against all customer API writers and lock rows against soft deletion.
    db.execute(select(Customer).where(Customer.company_id == company_id, Customer.status != 'Deleted').order_by(Customer.id).with_for_update()).all()
    result, plan = validate(db, company_id, data)
    if not result['valid']: return result
    if digest(plan) != claims.get('plan'): raise ValueError('Customer matches or row details changed since review. Review again before importing.')
    created_customers, created_assets, groups = [], [], {}
    for row in plan:
        if row['existing']: customer_id = UUID(row['existing'])
        elif row['group'] in groups: customer_id = groups[row['group']]
        else:
            customer = CustomerService().create_customer(db, company_id, dict(row['customer']))
            customer_id = customer.id; groups[row['group']] = customer_id; created_customers.append(customer.display_id)
        if row['asset'] is not None:
            asset = AssetService().create_asset(db, company_id, {**row['asset'], 'customer_id': customer_id})
            created_assets.append(asset.display_id)
    response = {'valid': True, 'summary': result['summary'], 'customer_numbers': created_customers, 'asset_numbers': created_assets, 'replayed': False}
    db.add(AuditLog(id=receipt_id, company_id=company_id, actor_user_id=user_id, action='SMART_IMPORT_COMMITTED', entity_type='smart_import', event_metadata={'checksum':digest(data), 'result':response}))
    db.flush()
    return response
