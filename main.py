"""
Intune Agent with Azure OpenAI
An AI-powered agent for querying and managing Microsoft Intune via natural language.
"""
import os
import json
import logging
from datetime import datetime
from openai import AzureOpenAI
from dotenv import load_dotenv

# Setup logging - file only, not console
LOG_FILE = f"intune_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE)
    ]
)
logger = logging.getLogger(__name__)

from intune_tools import (
    get_device_count, get_all_devices, get_noncompliant_devices, get_devices_by_os,
    get_stale_devices, get_device_breakdown_by_os, get_devices_without_encryption,
    get_device_details, sync_device, restart_device, retire_device,
    get_compliance_policies, get_compliance_summary,
    get_configuration_profiles, get_settings_catalog_policies,
    get_apps, get_detected_apps, get_powershell_scripts, get_shell_scripts,
    get_autopilot_devices, get_autopilot_profiles, get_update_rings, get_feature_updates
)

load_dotenv()

# Map function names to actual functions
TOOL_FUNCTIONS = {
    'get_device_count': get_device_count,
    'get_all_devices': get_all_devices,
    'get_noncompliant_devices': get_noncompliant_devices,
    'get_devices_by_os': get_devices_by_os,
    'get_stale_devices': get_stale_devices,
    'get_device_breakdown_by_os': get_device_breakdown_by_os,
    'get_devices_without_encryption': get_devices_without_encryption,
    'get_device_details': get_device_details,
    'sync_device': sync_device,
    'restart_device': restart_device,
    'retire_device': retire_device,
    'get_compliance_policies': get_compliance_policies,
    'get_compliance_summary': get_compliance_summary,
    'get_configuration_profiles': get_configuration_profiles,
    'get_settings_catalog_policies': get_settings_catalog_policies,
    'get_apps': get_apps,
    'get_detected_apps': get_detected_apps,
    'get_powershell_scripts': get_powershell_scripts,
    'get_shell_scripts': get_shell_scripts,
    'get_autopilot_devices': get_autopilot_devices,
    'get_autopilot_profiles': get_autopilot_profiles,
    'get_update_rings': get_update_rings,
    'get_feature_updates': get_feature_updates
}

# Define tools for OpenAI function calling
TOOLS = [
    # Device Tools
    {"type": "function", "function": {"name": "get_device_count", "description": "Get the total count of managed devices", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_all_devices", "description": "Get all managed devices with full details including ID, name, OS, compliance state, encryption status", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_noncompliant_devices", "description": "Get all non-compliant devices", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_devices_by_os", "description": "Filter devices by operating system", "parameters": {"type": "object", "properties": {"operating_system": {"type": "string", "description": "OS: Windows, iOS, Android, or macOS"}}, "required": ["operating_system"]}}},
    {"type": "function", "function": {"name": "get_stale_devices", "description": "Get devices that haven't synced recently", "parameters": {"type": "object", "properties": {"hours": {"type": "integer", "description": "Hours since last sync (default 48)"}}, "required": []}}},
    {"type": "function", "function": {"name": "get_device_breakdown_by_os", "description": "Get device counts grouped by OS", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_devices_without_encryption", "description": "Find unencrypted devices", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_device_details", "description": "Get detailed info about a specific device", "parameters": {"type": "object", "properties": {"device_id": {"type": "string", "description": "The Intune device ID"}}, "required": ["device_id"]}}},

    # Device Actions
    {"type": "function", "function": {"name": "sync_device", "description": "Trigger sync for a device", "parameters": {"type": "object", "properties": {"device_id": {"type": "string", "description": "The device ID to sync"}}, "required": ["device_id"]}}},
    {"type": "function", "function": {"name": "restart_device", "description": "Restart a device", "parameters": {"type": "object", "properties": {"device_id": {"type": "string", "description": "The device ID to restart"}}, "required": ["device_id"]}}},
    {"type": "function", "function": {"name": "retire_device", "description": "Retire a device (removes company data)", "parameters": {"type": "object", "properties": {"device_id": {"type": "string", "description": "The device ID to retire"}}, "required": ["device_id"]}}},

    # Compliance
    {"type": "function", "function": {"name": "get_compliance_policies", "description": "Get all compliance policies", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_compliance_summary", "description": "Get overall compliance summary", "parameters": {"type": "object", "properties": {}, "required": []}}},

    # Configuration
    {"type": "function", "function": {"name": "get_configuration_profiles", "description": "Get all device configuration profiles", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_settings_catalog_policies", "description": "Get Settings Catalog policies", "parameters": {"type": "object", "properties": {}, "required": []}}},

    # Apps
    {"type": "function", "function": {"name": "get_apps", "description": "Get all apps deployed via Intune", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_detected_apps", "description": "Get all detected apps across devices", "parameters": {"type": "object", "properties": {}, "required": []}}},

    # Scripts
    {"type": "function", "function": {"name": "get_powershell_scripts", "description": "Get all PowerShell scripts", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_shell_scripts", "description": "Get all Shell scripts (macOS/Linux)", "parameters": {"type": "object", "properties": {}, "required": []}}},

    # Autopilot
    {"type": "function", "function": {"name": "get_autopilot_devices", "description": "Get all Windows Autopilot devices", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_autopilot_profiles", "description": "Get Autopilot deployment profiles", "parameters": {"type": "object", "properties": {}, "required": []}}},

    # Updates
    {"type": "function", "function": {"name": "get_update_rings", "description": "Get Windows Update rings", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_feature_updates", "description": "Get feature update profiles", "parameters": {"type": "object", "properties": {}, "required": []}}}
]

SYSTEM_PROMPT = """You are an Intune device management assistant.
Use your available tools to query real-time data from Intune.

IMPORTANT RULES:
- Be action-oriented. Execute tasks immediately without excessive confirmation questions.
- Only ask for confirmation on truly destructive actions like wipe or retire.
- For sync, restart, or query operations: just do it.
- Keep responses concise.
- If the user says "all devices", get all devices and perform the action on each.
- Don't ask multiple clarifying questions - make reasonable assumptions and act."""


def execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool function by name with given arguments."""
    logger.info(f"TOOL CALL: {name} | Args: {arguments}")
    if name in TOOL_FUNCTIONS:
        func = TOOL_FUNCTIONS[name]
        try:
            result = func(**arguments) if arguments else func()
            logger.info(f"TOOL RESULT: {name} | Success | {result[:500]}...")
            return result
        except Exception as e:
            logger.error(f"TOOL ERROR: {name} | {str(e)}")
            return json.dumps({"error": str(e)})
    logger.warning(f"UNKNOWN TOOL: {name}")
    return json.dumps({"error": f"Unknown tool: {name}"})


def main():
    client = AzureOpenAI(
        api_key=os.environ['AZURE_OPENAI_API_KEY'],
        api_version="2024-10-21",
        azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT']
    )

    model = os.environ['MODEL_DEPLOYMENT_NAME']

    logger.info(f"=== Intune Agent Started ===")
    print(f"Intune Agent | Log: {LOG_FILE}")
    print("Type 'quit' to exit.\n")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        user_input = input('You: ').strip()
        if not user_input:
            continue
        if user_input.lower() in ['quit', 'exit']:
            logger.info("=== Session Ended ===")
            print("Goodbye!")
            break

        logger.info(f"USER: {user_input}")
        messages.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        assistant_message = response.choices[0].message
        messages.append(assistant_message)

        while assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

                print(f"  [{func_name}]")
                result = execute_tool(func_name, func_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto"
            )
            assistant_message = response.choices[0].message
            messages.append(assistant_message)

        if assistant_message.content:
            logger.info(f"ASSISTANT: {assistant_message.content[:500]}")
            print(f"\nAgent: {assistant_message.content}\n")


if __name__ == '__main__':
    main()
