"""
Graph API Helper for Intune
Handles authentication and API calls to Microsoft Graph for Intune operations.
Supports pagination for large result sets.
"""
import os
import requests
import logging
from azure.identity import ClientSecretCredential

logger = logging.getLogger(__name__)


class IntuneClient:
    """Client for interacting with Microsoft Intune via Graph API."""

    def __init__(self):
        self.credential = ClientSecretCredential(
            tenant_id=os.environ['AZURE_TENANT_ID'],
            client_id=os.environ['AZURE_CLIENT_ID'],
            client_secret=os.environ['AZURE_CLIENT_SECRET']
        )
        self.base_url = 'https://graph.microsoft.com/v1.0'
        self.beta_url = 'https://graph.microsoft.com/beta'

    def _headers(self) -> dict:
        """Get authorization headers with a fresh token."""
        token = self.credential.get_token('https://graph.microsoft.com/.default')
        return {'Authorization': f'Bearer {token.token}'}

    def _get_paginated(self, url: str, max_items: int = None) -> list:
        """
        Get all items from a paginated API endpoint.

        Args:
            url: The API endpoint URL
            max_items: Maximum number of items to return (None for all)

        Returns:
            List of all items across all pages
        """
        all_items = []
        headers = self._headers()

        while url:
            logger.debug(f"Fetching: {url}")
            response = requests.get(url, headers=headers)

            if not response.ok:
                error_detail = response.json() if response.content else {}
                error_msg = error_detail.get('error', {}).get('message', response.text)
                raise Exception(f"Graph API Error {response.status_code}: {error_msg}")

            data = response.json()
            items = data.get('value', [])
            all_items.extend(items)

            # Check if we've reached max_items
            if max_items and len(all_items) >= max_items:
                all_items = all_items[:max_items]
                break

            # Get next page URL
            url = data.get('@odata.nextLink')

        logger.info(f"Fetched {len(all_items)} items total")
        return all_items

    # ==================== DEVICES ====================

    def get_devices(self, filter_query: str = None, top: int = None) -> dict:
        """Get managed devices from Intune with pagination support."""
        url = f'{self.base_url}/deviceManagement/managedDevices'
        params = []
        if filter_query:
            params.append(f'$filter={filter_query}')
        if top:
            params.append(f'$top={top}')
        if params:
            url += '?' + '&'.join(params)

        items = self._get_paginated(url)
        return {'value': items}

    def get_device_by_id(self, device_id: str) -> dict:
        """Get a specific device by ID."""
        url = f'{self.base_url}/deviceManagement/managedDevices/{device_id}'
        response = requests.get(url, headers=self._headers())
        if not response.ok:
            raise Exception(f"Device not found: {response.status_code}")
        return response.json()

    def sync_device(self, device_id: str) -> dict:
        """Trigger a sync for a specific device."""
        url = f'{self.base_url}/deviceManagement/managedDevices/{device_id}/syncDevice'
        response = requests.post(url, headers=self._headers())
        if response.status_code == 204:
            return {"success": True}
        else:
            error_msg = response.text if response.text else f"HTTP {response.status_code}"
            return {"success": False, "error": error_msg}

    def restart_device(self, device_id: str) -> dict:
        """Trigger a restart for a specific device."""
        url = f'{self.base_url}/deviceManagement/managedDevices/{device_id}/rebootNow'
        response = requests.post(url, headers=self._headers())
        if response.status_code == 204:
            return {"success": True}
        else:
            error_msg = response.text if response.text else f"HTTP {response.status_code}"
            return {"success": False, "error": error_msg}

    def wipe_device(self, device_id: str, keep_enrollment: bool = True) -> dict:
        """Wipe a device. Use with caution!"""
        url = f'{self.base_url}/deviceManagement/managedDevices/{device_id}/wipe'
        body = {"keepEnrollmentData": keep_enrollment, "keepUserData": False}
        response = requests.post(url, headers=self._headers(), json=body)
        if response.status_code == 204:
            return {"success": True}
        else:
            error_msg = response.text if response.text else f"HTTP {response.status_code}"
            return {"success": False, "error": error_msg}

    def retire_device(self, device_id: str) -> dict:
        """Retire a device from Intune management."""
        url = f'{self.base_url}/deviceManagement/managedDevices/{device_id}/retire'
        response = requests.post(url, headers=self._headers())
        if response.status_code == 204:
            return {"success": True}
        else:
            error_msg = response.text if response.text else f"HTTP {response.status_code}"
            return {"success": False, "error": error_msg}

    # ==================== COMPLIANCE ====================

    def get_compliance_policies(self) -> dict:
        """Get all device compliance policies."""
        url = f'{self.base_url}/deviceManagement/deviceCompliancePolicies'
        items = self._get_paginated(url)
        return {'value': items}

    def get_compliance_policy_device_status(self, policy_id: str) -> dict:
        """Get device status for a compliance policy."""
        url = f'{self.base_url}/deviceManagement/deviceCompliancePolicies/{policy_id}/deviceStatuses'
        items = self._get_paginated(url)
        return {'value': items}

    # ==================== CONFIGURATION ====================

    def get_configuration_policies(self) -> dict:
        """Get all configuration policies (Settings Catalog)."""
        url = f'{self.base_url}/deviceManagement/configurationPolicies'
        items = self._get_paginated(url)
        return {'value': items}

    def get_device_configurations(self) -> dict:
        """Get all device configuration profiles."""
        url = f'{self.base_url}/deviceManagement/deviceConfigurations'
        items = self._get_paginated(url)
        return {'value': items}

    def get_group_policy_configurations(self) -> dict:
        """Get all Administrative Templates (Group Policy)."""
        url = f'{self.beta_url}/deviceManagement/groupPolicyConfigurations'
        items = self._get_paginated(url)
        return {'value': items}

    # ==================== APPS ====================

    def get_mobile_apps(self) -> dict:
        """Get all mobile apps."""
        url = f'{self.beta_url}/deviceAppManagement/mobileApps'
        items = self._get_paginated(url)
        return {'value': items}

    def get_app_assignments(self, app_id: str) -> dict:
        """Get assignments for a specific app."""
        url = f'{self.beta_url}/deviceAppManagement/mobileApps/{app_id}/assignments'
        items = self._get_paginated(url)
        return {'value': items}

    def get_detected_apps(self) -> dict:
        """Get all detected apps across devices."""
        url = f'{self.beta_url}/deviceManagement/detectedApps'
        items = self._get_paginated(url)
        return {'value': items}

    def get_app_install_status(self, app_id: str) -> dict:
        """Get installation status for an app."""
        url = f'{self.beta_url}/deviceAppManagement/mobileApps/{app_id}/deviceStatuses'
        items = self._get_paginated(url)
        return {'value': items}

    # ==================== SCRIPTS ====================

    def get_device_scripts(self) -> dict:
        """Get all PowerShell scripts."""
        url = f'{self.beta_url}/deviceManagement/deviceManagementScripts'
        items = self._get_paginated(url)
        return {'value': items}

    def get_shell_scripts(self) -> dict:
        """Get all Shell scripts (macOS/Linux)."""
        url = f'{self.beta_url}/deviceManagement/deviceShellScripts'
        items = self._get_paginated(url)
        return {'value': items}

    # ==================== GROUPS ====================

    def get_groups(self, filter_query: str = None) -> dict:
        """Get Azure AD groups."""
        url = f'{self.base_url}/groups'
        if filter_query:
            url += f'?$filter={filter_query}'
        items = self._get_paginated(url)
        return {'value': items}

    def get_group_members(self, group_id: str) -> dict:
        """Get members of a group."""
        url = f'{self.base_url}/groups/{group_id}/members'
        items = self._get_paginated(url)
        return {'value': items}

    # ==================== AUTOPILOT ====================

    def get_autopilot_devices(self) -> dict:
        """Get all Windows Autopilot devices."""
        url = f'{self.beta_url}/deviceManagement/windowsAutopilotDeviceIdentities'
        items = self._get_paginated(url)
        return {'value': items}

    def get_autopilot_profiles(self) -> dict:
        """Get all Autopilot deployment profiles."""
        url = f'{self.beta_url}/deviceManagement/windowsAutopilotDeploymentProfiles'
        items = self._get_paginated(url)
        return {'value': items}

    # ==================== UPDATES ====================

    def get_windows_update_rings(self) -> dict:
        """Get Windows Update for Business rings."""
        url = f"{self.beta_url}/deviceManagement/deviceConfigurations?$filter=isof('microsoft.graph.windowsUpdateForBusinessConfiguration')"
        items = self._get_paginated(url)
        return {'value': items}

    def get_feature_update_profiles(self) -> dict:
        """Get Windows feature update profiles."""
        url = f'{self.beta_url}/deviceManagement/windowsFeatureUpdateProfiles'
        items = self._get_paginated(url)
        return {'value': items}

    # ==================== REPORTING ====================

    def get_device_compliance_report(self) -> dict:
        """Get device compliance summary."""
        url = f'{self.base_url}/deviceManagement/deviceCompliancePolicyDeviceStateSummary'
        response = requests.get(url, headers=self._headers())
        if not response.ok:
            raise Exception(f"Failed to get compliance report: {response.status_code}")
        return response.json()
