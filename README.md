# Recorde File Auto Categorization
This program automatically sorts recording files from a recorder device into corresponding course folders based on time and class schedule information.

## Features
* Automatic File Categorization:
    * Categorizes note recordings based on course schedule information and audio length estimation.
    * Places recordings in corresponding course folders for easy organization.
    * Optionally, separates call recordings from note recordings and stores them in designated folders.
* Backup and Integrity Verification:
    * Performs MD5 checksum verification to ensure file integrity during transfers.
    * Creates backup copies of all original recordings for safety and recovery.
    * Separates backups by date for further organization.
* Detailed Logging:
    * Generates comprehensive logs for each run, including start/end timestamps, file processing details, and error messages.
    * Provides a progress bar to track file processing status and estimated time remaining.
* User Customization:
    * Uses JSON configuration files to specify file paths, course schedule, and optional course names.
    * Allows users to customize the categorization logic based on their specific needs.
* Hardware Verification:
    * Optionally, checks for the presence of a connected recorder device and verifies its model information.
    * Provides an extra layer of assurance for proper device compatibility.

## Process Flow
1. **Read Configuration**: The program reads configuration data (course schedule, file paths) from JSON files.
2. **Log Initialization**: A log file is created to record program actions and errors.
3. **Hardware Check**: The program searches for a connected recorder device based on its serial number. If not found, the program exits.
4. **Log Tree**: A log of the recorder's directory structure is recorded.
5. **File Count**: The total number of files on the device is calculated for progress tracking.
6. **Traverse Files**:
    * Call Recordings:
        * Copies call recordings to a backup directory with timestamps.
        * Optionally, separates call recordings by date and copies them to a designated "CALLS" folder within the backup directory.
    * Note Recordings:
        * Copies note recordings to a raw backup directory with timestamps.
        * Copies note recordings to a transferred backup directory with timestamps.
        * Attempts to categorize note recordings based on:
            * Audio length estimation
            * Course schedule information from class_time.json
            * Week number calculation relative to semester start date
            * Course name lookup from class_id.json (optional)
        * Recordings that cannot be categorized due to time mismatch are placed in a separate "dismatched" folder within the backup directory.
7. Verify File Integrity: MD5 checksums are used to verify the success of each file copy operation.
8. Delete all content in the recorder if every file copy operation success.

## Success/Failure Reports
The program outputs messages to the console indicating the success or failure of each file copy operation. Additionally, logs are recorded for successful and failed file transfers.

## Logs
The program generates a log file named with the current date and a sequential index. The log file contains:
* Program start/end timestamps.
* Information messages about file processing and categorization.
* Error messages for any issues encountered.
* A progress bar indicating completion percentage and estimated time remaining.

## Requirements
* Python 3.x
* Libraries:
    * `json`
    * `os`
    * `subprocess`
    * `shutil`
    * `wave`
    * `hashlib`

## Instructions
1. Prepare three JSON files in the const directory:
    * `class_time.json`: Contains a dictionary mapping weekdays and time slots to corresponding course IDs.
    * `class_id.json`: Contains a dictionary mapping course IDs to full course names.
    * `paths.json`: Contains a dictionary specifying file paths:
        * `root_path`: Base directory for storing classified recordings.
        * `backup_path`: Subdirectory for storing backup copies of original recordings (relative to root_path).
        * `destination_path`: Subdirectory structure for storing classified recordings (relative to root_path).
        * `log_dir`: Subdirectory for storing program logs (relative to backup_path).
2. Connect to the hardware device.
3. Run the script: python record_file_categorization.py

## Disclaimer
This script is provided as-is without warranty. It's recommended to test the program functionality on a non-critical dataset before deploying it in a production environment.