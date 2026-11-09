# Home Assistant BorgWarehouse Integration

Custom integration for [Home Assistant](https://www.home-assistant.io/) to monitor backup repositories hosted on [BorgWarehouse](https://borgwarehouse.com/).

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

## Features

- **Device per Repository**: Each backup repository configured in BorgWarehouse is automatically registered as an individual Device.
- **Sensors**:
  - **Storage Used** (GB, state class measurement, data size class)
  - **Storage Quota** (GB, data size class)
  - **Storage Usage Percentage** (%)
  - **Last Backup** (timestamp)
- **Binary Sensors**:
  - **Problem / Health Status** (alerts if unreachable or failing)
- **UI Config Flow**: Simple setup via Home Assistant UI using your BorgWarehouse URL and API token.
- **Efficient Polling**: Uses Home Assistant's `DataUpdateCoordinator` to query the `/api/v1/repositories` endpoint in a single batch request every 15 minutes.

---

## Prerequisites

1. Access to a running **BorgWarehouse** instance.
2. An API Key with `read` permissions:
   - In BorgWarehouse, navigate to **Account > Integrations**.
   - Click **Generate API key**, name your token, and select **read** permissions.
   - Copy the generated token.

---

## Installation

### Method 1: HACS (Recommended)

1. Open **HACS** in Home Assistant.
2. Click the three dots in the top right corner and choose **Custom repositories**.
3. Add this repository URL (`https://github.com/<your-username>/ha-borgwarehouse`) and select Category: **Integration**.
4. Click **Download**, then restart Home Assistant.

### Method 2: Manual Installation

1. Copy the `custom_components/borgwarehouse` folder into your Home Assistant installation's `config/custom_components/` directory.
2. Restart Home Assistant.

---

## Configuration

1. In Home Assistant, navigate to **Settings > Devices & Services**.
2. Click **Add Integration** and search for **BorgWarehouse**.
3. Enter:
   - **Server URL**: Your BorgWarehouse instance URL (e.g., `https://borgwarehouse.example.com`).
   - **API Key**: The Bearer token generated from BorgWarehouse.
4. Click **Submit**.

---

## Entities Created

For each repository (e.g. `Server Backup`):

| Entity | Domain | Description |
|---|---|---|
| `Server Backup Storage used` | `sensor` | Current repository disk usage in GB |
| `Server Backup Quota` | `sensor` | Quota allocated to the repository in GB |
| `Server Backup Storage usage` | `sensor` | Percentage of quota used |
| `Server Backup Last backup` | `sensor` | Date & time of the latest backup archive |
| `Server Backup Problem` | `binary_sensor` | Turns `on` if status is unhealthy/down |
