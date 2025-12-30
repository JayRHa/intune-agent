"""
Intune Agent with Microsoft Agent Framework
An AI-powered agent for querying and managing Microsoft Intune via natural language.
Uses the Microsoft Agent Framework (successor to Semantic Kernel and AutoGen).
"""
import asyncio
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Annotated

from dotenv import load_dotenv
from agent_framework import ai_function
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import ClientSecretCredential

from graph_helper import IntuneClient

# Setup logging
LOG_FILE = f"intune_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[logging.FileHandler(LOG_FILE)]
)
logger = logging.getLogger(__name__)

load_dotenv()

# Global Intune client instance
intune_client = IntuneClient()


# ==================== DEVICE TOOLS ====================

@ai_function(description="Get the total count of managed devices in Intune")
def get_device_count() -> str:
    """Get the total count of managed devices."""
    devices = intune_client.get_devices()
    return json.dumps({'total': len(devices.get('value', []))})


@ai_function(description="Get all managed devices with full details including ID, name, OS, compliance state, encryption status")
def get_all_devices() -> str:
    """Get all managed devices with details."""
    result = intune_client.get_devices()
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


@ai_function(description="Get all non-compliant devices that need attention")
def get_noncompliant_devices() -> str:
    """Get all non-compliant devices."""
    result = intune_client.get_devices("complianceState eq 'noncompliant'")
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


@ai_function(description="Filter devices by operating system (Windows, iOS, Android, or macOS)")
def get_devices_by_os(
    operating_system: Annotated[str, "Operating system: Windows, iOS, Android, or macOS"]
) -> str:
    """Filter devices by operating system."""
    result = intune_client.get_devices(f"operatingSystem eq '{operating_system}'")
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


@ai_function(description="Get devices that haven't synced in the specified number of hours (default 48)")
def get_stale_devices(
    hours: Annotated[int, "Number of hours since last sync"] = 48
) -> str:
    """Get stale devices that haven't synced recently."""
    all_devices = intune_client.get_devices()
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


@ai_function(description="Get a breakdown of all devices grouped by operating system")
def get_device_breakdown_by_os() -> str:
    """Get device counts grouped by OS."""
    all_devices = intune_client.get_devices()
    devices = all_devices.get('value', [])

    breakdown = {}
    for d in devices:
        os_name = d.get('operatingSystem', 'Unknown')
        breakdown[os_name] = breakdown.get(os_name, 0) + 1

    return json.dumps({'total': len(devices), 'breakdown': breakdown})


@ai_function(description="Find devices that may not have disk encryption enabled")
def get_devices_without_encryption() -> str:
    """Find unencrypted devices."""
    result = intune_client.get_devices("isEncrypted eq false")
    devices = result.get('value', [])
    summary = [{
        'id': d.get('id'),
        'deviceName': d.get('deviceName'),
        'operatingSystem': d.get('operatingSystem'),
        'userPrincipalName': d.get('userPrincipalName'),
        'isEncrypted': d.get('isEncrypted')
    } for d in devices]
    return json.dumps({'count': len(devices), 'devices': summary})


@ai_function(description="Get detailed information about a specific device by its ID")
def get_device_details(
    device_id: Annotated[str, "The Intune device ID"]
) -> str:
    """Get detailed info about a specific device."""
    device = intune_client.get_device_by_id(device_id)
    return json.dumps(device)


# ==================== DEVICE ACTIONS ====================

@ai_function(description="Trigger a sync for a specific device to get latest policies and configurations")
def sync_device(
    device_id: Annotated[str, "The device ID to sync"]
) -> str:
    """Trigger sync for a device."""
    result = intune_client.sync_device(device_id)
    result['deviceId'] = device_id
    return json.dumps(result)


@ai_function(description="Restart a device remotely")
def restart_device(
    device_id: Annotated[str, "The device ID to restart"]
) -> str:
    """Restart a device."""
    result = intune_client.restart_device(device_id)
    result['deviceId'] = device_id
    return json.dumps(result)


@ai_function(description="Retire a device from Intune management. This removes company data but keeps personal data. USE WITH CAUTION!")
def retire_device(
    device_id: Annotated[str, "The device ID to retire"]
) -> str:
    """Retire a device."""
    result = intune_client.retire_device(device_id)
    result['deviceId'] = device_id
    return json.dumps(result)


# ==================== COMPLIANCE TOOLS ====================

@ai_function(description="Get all compliance policies configured in Intune")
def get_compliance_policies() -> str:
    """Get all compliance policies."""
    result = intune_client.get_compliance_policies()
    policies = result.get('value', [])
    summary = [{
        'id': p.get('id'),
        'displayName': p.get('displayName'),
        'createdDateTime': p.get('createdDateTime'),
        'lastModifiedDateTime': p.get('lastModifiedDateTime')
    } for p in policies]
    return json.dumps({'count': len(policies), 'policies': summary})


@ai_function(description="Get overall compliance summary across all devices")
def get_compliance_summary() -> str:
    """Get overall compliance summary."""
    try:
        report = intune_client.get_device_compliance_report()
        return json.dumps(report)
    except Exception as e:
        return json.dumps({'error': str(e)})


# ==================== CONFIGURATION TOOLS ====================

@ai_function(description="Get all device configuration profiles")
def get_configuration_profiles() -> str:
    """Get all device configuration profiles."""
    result = intune_client.get_device_configurations()
    configs = result.get('value', [])
    summary = [{
        'id': c.get('id'),
        'displayName': c.get('displayName'),
        '@odata.type': c.get('@odata.type'),
        'createdDateTime': c.get('createdDateTime'),
        'lastModifiedDateTime': c.get('lastModifiedDateTime')
    } for c in configs]
    return json.dumps({'count': len(configs), 'profiles': summary})


@ai_function(description="Get all Settings Catalog configuration policies")
def get_settings_catalog_policies() -> str:
    """Get Settings Catalog policies."""
    result = intune_client.get_configuration_policies()
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

@ai_function(description="Get all apps deployed via Intune")
def get_apps() -> str:
    """Get all apps deployed via Intune."""
    result = intune_client.get_mobile_apps()
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


@ai_function(description="Get all detected apps across all managed devices")
def get_detected_apps() -> str:
    """Get all detected apps across devices."""
    result = intune_client.get_detected_apps()
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

@ai_function(description="Get all PowerShell scripts configured in Intune")
def get_powershell_scripts() -> str:
    """Get all PowerShell scripts."""
    result = intune_client.get_device_scripts()
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


@ai_function(description="Get all Shell scripts (macOS/Linux) configured in Intune")
def get_shell_scripts() -> str:
    """Get all Shell scripts (macOS/Linux)."""
    result = intune_client.get_shell_scripts()
    scripts = result.get('value', [])
    summary = [{
        'id': s.get('id'),
        'displayName': s.get('displayName'),
        'description': s.get('description'),
        'createdDateTime': s.get('createdDateTime')
    } for s in scripts]
    return json.dumps({'count': len(scripts), 'scripts': summary})


# ==================== AUTOPILOT TOOLS ====================

@ai_function(description="Get all Windows Autopilot registered devices")
def get_autopilot_devices() -> str:
    """Get all Windows Autopilot devices."""
    result = intune_client.get_autopilot_devices()
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


@ai_function(description="Get all Windows Autopilot deployment profiles")
def get_autopilot_profiles() -> str:
    """Get Autopilot deployment profiles."""
    result = intune_client.get_autopilot_profiles()
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

@ai_function(description="Get Windows Update for Business update rings")
def get_update_rings() -> str:
    """Get Windows Update rings."""
    try:
        result = intune_client.get_windows_update_rings()
        rings = result.get('value', [])
        summary = [{
            'id': r.get('id'),
            'displayName': r.get('displayName'),
            'description': r.get('description')
        } for r in rings]
        return json.dumps({'count': len(rings), 'rings': summary})
    except Exception as e:
        return json.dumps({'error': str(e)})


@ai_function(description="Get Windows feature update profiles")
def get_feature_updates() -> str:
    """Get feature update profiles."""
    try:
        result = intune_client.get_feature_update_profiles()
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


# List of all tools
ALL_TOOLS = [
    get_device_count,
    get_all_devices,
    get_noncompliant_devices,
    get_devices_by_os,
    get_stale_devices,
    get_device_breakdown_by_os,
    get_devices_without_encryption,
    get_device_details,
    sync_device,
    restart_device,
    retire_device,
    get_compliance_policies,
    get_compliance_summary,
    get_configuration_profiles,
    get_settings_catalog_policies,
    get_apps,
    get_detected_apps,
    get_powershell_scripts,
    get_shell_scripts,
    get_autopilot_devices,
    get_autopilot_profiles,
    get_update_rings,
    get_feature_updates
]


SYSTEM_PROMPT = """You are an Intune device management assistant powered by Microsoft Agent Framework.
Use your available tools to query real-time data from Microsoft Intune.

IMPORTANT RULES:
- Be action-oriented. Execute tasks immediately without excessive confirmation questions.
- Only ask for confirmation on truly destructive actions like wipe or retire.
- For sync, restart, or query operations: just do it.
- Keep responses concise.
- If the user says "all devices", get all devices and perform the action on each.
- Don't ask multiple clarifying questions - make reasonable assumptions and act."""


async def main():
    """Main entry point for the Intune Agent using Microsoft Agent Framework."""

    # Create Azure OpenAI client using environment variables
    client = AzureOpenAIChatClient(
        endpoint=os.environ['AZURE_OPENAI_ENDPOINT'],
        deployment_name=os.environ['MODEL_DEPLOYMENT_NAME'],
        credential=ClientSecretCredential(
            tenant_id=os.environ['AZURE_TENANT_ID'],
            client_id=os.environ['AZURE_CLIENT_ID'],
            client_secret=os.environ['AZURE_CLIENT_SECRET']
        ),
        api_version="2024-10-21"
    )

    # Create the agent with tools
    agent = client.create_agent(
        name="IntuneAgent",
        instructions=SYSTEM_PROMPT,
        tools=ALL_TOOLS
    )

    logger.info("=== Intune Agent (Microsoft Agent Framework) Started ===")
    print(f"Intune Agent (Microsoft Agent Framework) | Log: {LOG_FILE}")
    print("Type 'quit' to exit.\n")

    while True:
        user_input = input('You: ').strip()
        if not user_input:
            continue
        if user_input.lower() in ['quit', 'exit']:
            logger.info("=== Session Ended ===")
            print("Goodbye!")
            break

        logger.info(f"USER: {user_input}")

        try:
            # Run the agent
            result = await agent.run(user_input)

            response_text = result.text if hasattr(result, 'text') else str(result)
            logger.info(f"ASSISTANT: {response_text[:500]}")
            print(f"\nAgent: {response_text}\n")

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(error_msg)
            print(f"\n{error_msg}\n")


if __name__ == '__main__':
    asyncio.run(main())
