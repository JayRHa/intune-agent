#!/bin/bash
# Setup script for Intune Agent
# Creates Azure AD app registration with required Graph API permissions

set -e

APP_NAME="intune-agent"
ENV_FILE=".env"
GRAPH_API="00000003-0000-0000-c000-000000000000"

# Microsoft Graph Permission IDs
declare -A PERMISSIONS=(
    ["DeviceManagementManagedDevices.Read.All"]="2f51be20-0bb4-4fed-bf7b-db946066c75e"
    ["DeviceManagementManagedDevices.ReadWrite.All"]="243333ab-4d21-40cb-a475-36241daa0842"
    ["DeviceManagementManagedDevices.PrivilegedOperations.All"]="5b07b0dd-2377-4e44-a38d-703f09a0dc3c"
    ["DeviceManagementConfiguration.Read.All"]="dc377aa6-52d8-4e23-b271-2a7ae04cedf3"
    ["DeviceManagementConfiguration.ReadWrite.All"]="9241abd9-d0e6-425a-bd4f-47ba86e767a4"
    ["DeviceManagementApps.Read.All"]="7a6ee1e7-141e-4cec-ae74-d9db155731ff"
    ["DeviceManagementApps.ReadWrite.All"]="78145de6-330d-4800-a6ce-494ff2d33d07"
    ["DeviceManagementRBAC.Read.All"]="58ca0d9a-1575-47e1-a3cb-007ef2e4583b"
    ["DeviceManagementServiceConfig.Read.All"]="06a5fe6d-c49d-46a7-b082-56b1b14103c7"
)

echo "=== Intune Agent Setup ==="
echo ""

# Check Azure CLI login
az account show > /dev/null 2>&1 || { echo "Please run 'az login' first"; exit 1; }

TENANT_ID=$(az account show --query tenantId -o tsv)
echo "Tenant: $TENANT_ID"

# Check if app already exists
EXISTING_APP=$(az ad app list --display-name "$APP_NAME" --query "[0].appId" -o tsv 2>/dev/null)
if [ -n "$EXISTING_APP" ]; then
    echo "App already exists: $EXISTING_APP"
    read -p "Recreate app? (y/n): " RECREATE
    if [ "$RECREATE" = "y" ]; then
        az ad app delete --id "$EXISTING_APP"
        sleep 2
        APP_ID=""
    else
        APP_ID=$EXISTING_APP
    fi
fi

# Create app registration
if [ -z "$APP_ID" ]; then
    echo "Creating app registration..."
    APP_ID=$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)
    sleep 2
fi
echo "App ID: $APP_ID"

# Create service principal
az ad sp create --id "$APP_ID" 2>/dev/null || true
sleep 2

# Create client secret
echo "Creating client secret..."
CLIENT_SECRET=$(az ad app credential reset --id "$APP_ID" --append --years 1 --query password -o tsv)

# Add Graph API permissions
echo ""
echo "Adding Graph API permissions..."
for PERM_NAME in "${!PERMISSIONS[@]}"; do
    PERM_ID="${PERMISSIONS[$PERM_NAME]}"
    echo "  + $PERM_NAME"
    az ad app permission add --id "$APP_ID" --api "$GRAPH_API" --api-permissions "${PERM_ID}=Role" 2>/dev/null || true
done

sleep 3

# Grant admin consent
echo ""
echo "Granting admin consent..."
az ad app permission admin-consent --id "$APP_ID" 2>/dev/null || {
    echo ""
    echo "=== MANUAL CONSENT REQUIRED ==="
    echo "Open this URL in your browser:"
    echo ""
    echo "https://login.microsoftonline.com/$TENANT_ID/adminconsent?client_id=$APP_ID"
    echo ""
}

# Preserve existing OpenAI settings if present
OPENAI_ENDPOINT=$(grep "AZURE_OPENAI_ENDPOINT" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2- || echo "")
OPENAI_KEY=$(grep "AZURE_OPENAI_API_KEY" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2- || echo "")
MODEL_NAME=$(grep "MODEL_DEPLOYMENT_NAME" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2- || echo "gpt-4o")

# Write .env file with restrictive permissions (owner read/write only)
# This prevents other local users from reading the Azure client secret and
# Azure OpenAI API key. The umask is set before creating the file so the
# secret is never briefly readable by other users.
(
    umask 077
    cat > "$ENV_FILE" << EOF
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=${OPENAI_ENDPOINT:-https://your-resource.openai.azure.com/}
AZURE_OPENAI_API_KEY=${OPENAI_KEY:-your-api-key}
MODEL_DEPLOYMENT_NAME=${MODEL_NAME}

# Microsoft Graph / Entra ID App Registration
AZURE_TENANT_ID=$TENANT_ID
AZURE_CLIENT_ID=$APP_ID
AZURE_CLIENT_SECRET=$CLIENT_SECRET
EOF
)
# Belt-and-braces: enforce 0600 in case the file already existed with
# permissive bits from a prior run.
chmod 600 "$ENV_FILE"

echo ""
echo "=== Setup Complete ==="
echo "App ID: $APP_ID"
echo "Config saved to: $ENV_FILE"
echo ""
echo "Next: Update AZURE_OPENAI_* values in .env, then run: python main.py"
