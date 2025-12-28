# Intune Agent with Azure AI Foundry

An AI-powered agent for querying and managing Microsoft Intune via natural language using Azure AI Foundry.

## Prerequisites

- Azure subscription with an active Intune license
- Azure AI Foundry resource with a deployed model (GPT-4o or GPT-4)
- An app registration in Entra ID with Graph API permissions
- Python 3.9+

## Required Graph API Permissions

Your app registration needs these Microsoft Graph API permissions (Application permissions). The `setup.sh` script configures these automatically:

- `DeviceManagementManagedDevices.Read.All`
- `DeviceManagementManagedDevices.ReadWrite.All`
- `DeviceManagementManagedDevices.PrivilegedOperations.All`
- `DeviceManagementConfiguration.Read.All`
- `DeviceManagementConfiguration.ReadWrite.All`
- `DeviceManagementApps.Read.All`
- `DeviceManagementApps.ReadWrite.All`
- `DeviceManagementRBAC.Read.All`
- `DeviceManagementServiceConfig.Read.All`

## Setup

1. Clone the repository

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   ```

5. Edit `.env` with your settings:
   - `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key
   - `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint URL
   - `MODEL_DEPLOYMENT_NAME`: The deployed model name (e.g., `gpt-4o`)
   - `AZURE_TENANT_ID`: Your Entra ID tenant ID
   - `AZURE_CLIENT_ID`: Your app registration client ID
   - `AZURE_CLIENT_SECRET`: Your app registration client secret

## Usage

Run the agent:
```bash
python main.py
```

### Example Queries

- "Show me all non-compliant devices"
- "Which Windows devices haven't synced in 48 hours?"
- "Break down our fleet by OS"
- "Find devices without disk encryption"
- "How many devices do we have?"
- "Show me all compliance policies"

## Available Tools

| Tool | Description |
|------|-------------|
| `get_device_count` | Get total count of managed devices |
| `get_noncompliant_devices` | List all non-compliant devices |
| `get_devices_by_os` | Filter devices by operating system |
| `get_stale_devices` | Find devices that haven't synced recently |
| `get_device_breakdown_by_os` | Get device counts grouped by OS |
| `get_compliance_policies` | List all compliance policies |
| `sync_device` | Trigger a device sync |
| `get_devices_without_encryption` | Find unencrypted devices |

## Project Structure

```
intune-agent-foundry/
├── main.py           # Agent orchestration and conversation loop
├── graph_helper.py   # Microsoft Graph API client
├── intune_tools.py   # Function tools exposed to the agent
├── requirements.txt  # Python dependencies
├── setup.sh          # Azure app registration setup script
├── .env.example      # Environment variable template
└── README.md
```
