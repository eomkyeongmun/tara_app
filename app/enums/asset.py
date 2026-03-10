from enum import Enum


class AssetCategory(str, Enum):
    CAN_COMMUNICATION_DATA = "CAN_Communication_Data"
    ETHERNET_COMMUNICATION_DATA = "Ethernet_Communication_Data"
    WIFI_COMMUNICATION_DATA = "Wi-Fi_Communication_Data"
    BLUETOOTH_COMMUNICATION_DATA = "Bluetooth_Communication_Data"
    PNC_COMMUNICATION_DATA = "PnC_Communication_Data"
    CELLULAR_COMMUNICATION_DATA = "Cellular_Communication_Data"
    NFC_COMMUNICATION_DATA = "NFC_Communication_Data"
    RF_LF_SIGNAL_DATA = "RF_LF_signal_Data"
    GPS_SIGNAL_DATA = "GPS_signal_Data"
    STORED_DATA_IN_EXTERNAL_STORAGE = "Stored_Data_in_External_Storage"
    STORED_DATA_IN_ECU_SYSTEM = "Stored_Data_in_ECU_system"
    STORED_DATA_IN_EEPROM = "Stored_Data_in_EEPROM"
    FIRMWARE_FILE = "Firmware_File"
    DAB_RADIO_RDS_SIGNAL_DATA = "DAB/RADIO/RDS_signal_Data"
    V2V_COMMUNICATION_DATA = "V2V_communication_Data"
    CHOOSE_FROM_ASSET_TYPE = "Choose_from_Asset_Type"


class AssetType(str, Enum):
    DATA_IN_FIRMWARE = "Data in Firmware"
    DRIVING_DATA = "Driving Data (e.g. mileage, driving speed, driving directions, etc.)"
    VEHICLE_ELECTRONIC_ID = "Vehicle’s electronic ID"
    IDENTITY = "Identity (User ID etc)"
    SYSTEM_DIAGNOSTIC_DATA = "System diagnostic data"
    CONFIGURATION_PARAMETERS = "Configuration parameters (vehicle’s key functions, such as brake data, airbag deployed threshold, etc)"
    CHARGING_PARAMETERS = "Charging parameters (charging voltage, charging power, battery temperature, etc.)"
    LOG_DATA = "Log Data"
    MONITORING_RULESET = "Monitoring Ruleset"
    COPYRIGHT_OR_PROPRIETARY_SW = "Copyright or proprietary S/W"
    OWNER_PRIVACY_INFORMATION = "Owner's privacy information"
    CRYPTOGRAPHIC_KEYS = "Cryptographic Keys"
    FOD_CERTIFICATE = "FoD Certificate"