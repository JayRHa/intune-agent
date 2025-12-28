"""
Intune Function Tools for Azure OpenAI Agent
These functions are exposed to the AI agent for querying and managing Intune.
"""
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from graph_helper import IntuneClient

client = IntuneClient()


# ==================== DEVICE TOOLS ====================

def get_device_count() -> str:
    """Get the total count of managed devices in Intune.

    :return: JSON with total device count
    """
    devices = client.get_devices()
    return json.dumps({'total': len(devices.get('value', []))})


def get_all_devices() -> str:
    """Get all managed devices with details.

    :return: JSON with all device details
    """
    result = client.get_devices()
    devices = result.get('value', [])
    summary = [{
        'id': d.get('id'),
        'deviceName': d.get('deviceName'),
        'operatingSystem': d.get('operatingSystem'),
        'osVersion': d.get('osVersion'),
        'userPrincipalName': d.get('userPrincipalName'),
        'lastSyncDateTime': d.get('lastSyncDateTime'),
        'complianceState': d.get('complianceState'),
        'managementState': d.get('managementState'),
        'isEncrypted': d.get('isEncrypted'),
        'model': d.get('model'),
        'manufacturer': d.get('manufacturer'),
        'serialNumber': d.get('serialNumber')
    } for d in devices]
    return json.dumps({'count': len(devices), 'devices': summary})


def get_noncompliant_devices() -> str:
    """Get all non-compliant devices that need attention.

    :return: JSON with non-compliant device details
    """
    result = client.get_devices("complianceState eq 'noncompliant'")
    devices = result.get('value', [])
    summary = [{
        'id': d.get('id'),
        'deviceName': d.get('deviceName'),
        'operatingSystem': d.get('operatingSystem'),
        'osVersion': d.get('osVersion'),
        'userPrincipalName': d.get('userPrincipalName'),
        'lastSyncDateTime': d.get('lastSyncDateTime'),
        'complianceState': d.get('complianceState')
    } for d in devices]
    return json.dumps({'count': len(devices), 'devices': summary})


def get_devices_by_os(operating_system: str) -> str:
    """Filter devices by operating system.

    :param operating_system: OS to filter (Windows, iOS, Android, macOS)
    :return: JSON with filtered device list
    """
    result = client.get_devices(f"operatingSystem eq '{operating_system}'")
    devices = result.get('value', [])
    summary = [{
        'id': d.get('id'),
        'deviceName': d.get('deviceName'),
        'osVersion': d.get('osVersion'),
        'userPrincipalName': d.get('userPrincipalName'),
        'lastSyncDateTime': d.get('lastSyncDateTime'),
        'complianceState': d.get('complianceState')
    } for d in devices]
    return json.dumps({'count': len(devices), 'devices': summary})


def get_stale_devices(hours: int = 48) -> str:
    """Get devices that haven't synced in the specified number of hours.

    :param hours: Number of hours since last sync (default 48)
    :return: JSON with stale device details
    """
    all_devices = client.get_devices()
    devices = all_devices.get('value', [])
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    stale = []
    for d in devices:
        last_sync = d.get('lastSyncDateTime')
        if last_sync:
            try:
                sync_time = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                if sync_time.replace(tzinfo=None) < cutoff:
                    stale.append({
                        'id': d.get('id'),
                        'deviceName': d.get('deviceName'),
                        'operatingSystem': d.get('operatingSystem'),
                        'userPrincipalName': d.get('userPrincipalName'),
                        'lastSyncDateTime': last_sync
                    })
            except:
                pass

    return json.dumps({'count': len(stale), 'devices': stale})


def get_device_breakdown_by_os() -> str:
    """Get a breakdown of all devices grouped by operating system.

    :return: JSON with device counts per OS
    """
    all_devices = client.get_devices()
    devices = all_devices.get('value', [])

    breakdown = {}
    for d in devices:
        os_name = d.get('operatingSystem', 'Unknown')
        breakdown[os_name] = breakdown.get(os_name, 0) + 1

    return json.dumps({'total': len(devices), 'breakdown': breakdown})


def get_devices_without_encryption() -> str:
    """Find devices that may not have disk encryption enabled.

    :return: JSON with devices that are not encrypted
    """
    result = client.get_devices("isEncrypted eq false")
    devices = result.get('value', [])
    summary = [{
        'id': d.get('id'),
        'deviceName': d.get('deviceName'),
        'operatingSystem': d.get('operatingSystem'),
        'userPrincipalName': d.get('userPrincipalName'),
        'isEncrypted': d.get('isEncrypted')
    } for d in devices]
    return json.dumps({'count': len(devices), 'devices': summary})


def get_device_details(device_id: str) -> str:
    """Get detailed information about a specific device.

    :param device_id: The Intune device ID
    :return: JSON with device details
    """
    device = client.get_device_by_id(device_id)
    return json.dumps(device)


# ==================== DEVICE ACTIONS ====================

def sync_device(device_id: str) -> str:
    """Trigger a sync for a specific device.

    :param device_id: The Intune device ID to sync
    :return: JSON with sync result
    """
    result = client.sync_device(device_id)
    result['deviceId'] = device_id
    return json.dumps(result)


def restart_device(device_id: str) -> str:
    """Trigger a restart for a specific device.

    :param device_id: The Intune device ID to restart
    :return: JSON with restart result
    """
    result = client.restart_device(device_id)
    result['deviceId'] = device_id
    return json.dumps(result)


def retire_device(device_id: str) -> str:
    """Retire a device from Intune management. Removes company data but keeps personal data.

    :param device_id: The Intune device ID to retire
    :return: JSON with retire result
    """
    result = client.retire_device(device_id)
    result['deviceId'] = device_id
    return json.dumps(result)


# ==================== COMPLIANCE TOOLS ====================

def get_compliance_policies() -> str:
    """Get all compliance policies configured in Intune.

    :return: JSON with compliance policy details
    """
    result = client.get_compliance_policies()
    policies = result.get('value', [])
    summary = [{
        'id': p.get('id'),
        'displayName': p.get('displayName'),
        'createdDateTime': p.get('createdDateTime'),
        'lastModifiedDateTime': p.get('lastModifiedDateTime')
    } for p in policies]
    return json.dumps({'count': len(policies), 'policies': summary})


def get_compliance_summary() -> str:
    """Get overall compliance summary across all devices.

    :return: JSON with compliance summary
    """
    try:
        report = client.get_device_compliance_report()
        return json.dumps(report)
    except Exception as e:
        return json.dumps({'error': str(e)})


# ==================== CONFIGURATION TOOLS ====================

def get_configuration_profiles() -> str:
    """Get all device configuration profiles.

    :return: JSON with configuration profile details
    """
    result = client.get_device_configurations()
    configs = result.get('value', [])
    summary = [{
        'id': c.get('id'),
        'displayName': c.get('displayName'),
        '@odata.type': c.get('@odata.type'),
        'createdDateTime': c.get('createdDateTime'),
        'lastModifiedDateTime': c.get('lastModifiedDateTime')
    } for c in configs]
    return json.dumps({'count': len(configs), 'profiles': summary})


def get_settings_catalog_policies() -> str:
    """Get all Settings Catalog configuration policies.

    :return: JSON with Settings Catalog policy details
    """
    result = client.get_configuration_policies()
    policies = result.get('value', [])
    summary = [{
        'id': p.get('id'),
        'name': p.get('name'),
        'description': p.get('description'),
        'platforms': p.get('platforms'),
        'technologies': p.get('technologies'),
        'createdDateTime': p.get('createdDateTime')
    } for p in policies]
    return json.dumps({'count': len(policies), 'policies': summary})


# ==================== APP TOOLS ====================

def get_apps() -> str:
    """Get all apps deployed via Intune.

    :return: JSON with app details
    """
    result = client.get_mobile_apps()
    apps = result.get('value', [])
    summary = [{
        'id': a.get('id'),
        'displayName': a.get('displayName'),
        '@odata.type': a.get('@odata.type'),
        'publisher': a.get('publisher'),
        'createdDateTime': a.get('createdDateTime'),
        'lastModifiedDateTime': a.get('lastModifiedDateTime')
    } for a in apps]
    return json.dumps({'count': len(apps), 'apps': summary})


def get_detected_apps() -> str:
    """Get all detected apps across all devices.

    :return: JSON with detected app details
    """
    result = client.get_detected_apps()
    apps = result.get('value', [])
    summary = [{
        'id': a.get('id'),
        'displayName': a.get('displayName'),
        'version': a.get('version'),
        'deviceCount': a.get('deviceCount'),
        'platform': a.get('platform')
    } for a in apps]
    return json.dumps({'count': len(apps), 'apps': summary})


# ==================== SCRIPT TOOLS ====================

def get_powershell_scripts() -> str:
    """Get all PowerShell scripts configured in Intune.

    :return: JSON with script details
    """
    result = client.get_device_scripts()
    scripts = result.get('value', [])
    summary = [{
        'id': s.get('id'),
        'displayName': s.get('displayName'),
        'description': s.get('description'),
        'runAsAccount': s.get('runAsAccount'),
        'enforceSignatureCheck': s.get('enforceSignatureCheck'),
        'createdDateTime': s.get('createdDateTime')
    } for s in scripts]
    return json.dumps({'count': len(scripts), 'scripts': summary})


def get_shell_scripts() -> str:
    """Get all Shell scripts (macOS/Linux) configured in Intune.

    :return: JSON with script details
    """
    result = client.get_shell_scripts()
    scripts = result.get('value', [])
    summary = [{
        'id': s.get('id'),
        'displayName': s.get('displayName'),
        'description': s.get('description'),
        'createdDateTime': s.get('createdDateTime')
    } for s in scripts]
    return json.dumps({'count': len(scripts), 'scripts': summary})


# ==================== AUTOPILOT TOOLS ====================

def get_autopilot_devices() -> str:
    """Get all Windows Autopilot registered devices.

    :return: JSON with Autopilot device details
    """
    result = client.get_autopilot_devices()
    devices = result.get('value', [])
    summary = [{
        'id': d.get('id'),
        'serialNumber': d.get('serialNumber'),
        'model': d.get('model'),
        'manufacturer': d.get('manufacturer'),
        'groupTag': d.get('groupTag'),
        'enrollmentState': d.get('enrollmentState'),
        'lastContactedDateTime': d.get('lastContactedDateTime')
    } for d in devices]
    return json.dumps({'count': len(devices), 'devices': summary})


def get_autopilot_profiles() -> str:
    """Get all Windows Autopilot deployment profiles.

    :return: JSON with Autopilot profile details
    """
    result = client.get_autopilot_profiles()
    profiles = result.get('value', [])
    summary = [{
        'id': p.get('id'),
        'displayName': p.get('displayName'),
        'description': p.get('description'),
        'deviceType': p.get('deviceType'),
        'createdDateTime': p.get('createdDateTime')
    } for p in profiles]
    return json.dumps({'count': len(profiles), 'profiles': summary})


# ==================== UPDATE TOOLS ====================

def get_update_rings() -> str:
    """Get Windows Update for Business update rings.

    :return: JSON with update ring details
    """
    try:
        result = client.get_windows_update_rings()
        rings = result.get('value', [])
        summary = [{
            'id': r.get('id'),
            'displayName': r.get('displayName'),
            'description': r.get('description')
        } for r in rings]
        return json.dumps({'count': len(rings), 'rings': summary})
    except Exception as e:
        return json.dumps({'error': str(e)})


def get_feature_updates() -> str:
    """Get Windows feature update profiles.

    :return: JSON with feature update profile details
    """
    try:
        result = client.get_feature_update_profiles()
        profiles = result.get('value', [])
        summary = [{
            'id': p.get('id'),
            'displayName': p.get('displayName'),
            'description': p.get('description'),
            'featureUpdateVersion': p.get('featureUpdateVersion'),
            'createdDateTime': p.get('createdDateTime')
        } for p in profiles]
        return json.dumps({'count': len(profiles), 'profiles': summary})
    except Exception as e:
        return json.dumps({'error': str(e)})
