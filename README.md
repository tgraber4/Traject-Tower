# TrajectTower

![TrajectTower Logo](resources/logo.png)

(Place demo video here)

## Description
TrajectTower is a simplified job application tracker designed to help job seekers manage their applications effortlessly. It allows users to:
- **Save Job Listings**: Capture and store job descriptions for future reference.
- **Import Updated Statuses**: Automatically sync and update your application status from your email.
- **Support for Multiple Formats**: Add jobs manually, pull data from a URL via automated parsing, or even upload screenshots of job postings.
- **Track Application Stages**: Easily categorize applications into *Applied*, *Rejected*, or *Interview* stages.

---

## Installation and Setup (EXE)
If you are using the pre-compiled version, follow these steps to set up the environment for job parsing (scraping).
*Note: This application has only been tested on Windows devices.*

1. **Download the EXE**: Get the latest version from the [Releases](https://github.com/your-username/TrajectTower/releases) tab.
2. **Install Playwright**: Open your terminal and run:
   ```bash
   pip install playwright
   ```
3. **Get Browsers Path**: Run `getPath.py` to identify where Playwright browsers should be installed on your machine.
   ```bash
   python getPath.py
   ```
   *Copy the path provided in the output.*
4. **Set Environment Variable**:
   - **Windows (PowerShell)**: 
     ```powershell
     $env:PLAYWRIGHT_BROWSERS_PATH = "(paste path here)"
     ```
   - **Mac (zsh/bash)**: 
     ```bash
     export PLAYWRIGHT_BROWSERS_PATH="(paste path here)"
     ```
5. **Install Playwright Browsers**:
   ```bash
   python -m playwright install
   ```

**Important**: TrajectTower currently uses **Playwright v1.57**. Using different versions may cause compatibility issues with the parsing engine.

---

## Setup Development Environment
If you wish to run the project from source or contribute, follow these steps:

1. **Create a Virtual Environment**:
   - **Windows**: `python -m venv venv`
   - **Mac/Linux**: `python3 -m venv venv`

2. **Activate the Environment**:
   - **Windows**: `.\venv\Scripts\activate`
   - **Mac/Linux**: `source venv/bin/activate`

3. **Install Dependencies**:
   Refer to `requirements.txt` for detailed installation steps.
   
4. **Get Email App Credentials**

---

## Rebuild Executable
To create a standalone executable, ensure you have PyInstaller installed and run the corresponding command for your OS:

- **Windows**:
  ```bash
  pyinstaller --onefile --add-data "resources;resources" --add-data "data;data" --icon="resources/logo.ico" main.py --name TrajectTower
  ```
- **Mac/Linux**:
  ```bash
  pyinstaller --onefile --add-data "resources:resources" --add-data "data:data" main.py --name TrajectTower
  ```

---


## Data & Privacy
TrajectTower is built with a **privacy-first approach**. 
- All application data is stored **locally on your machine**.
- Email connections (e.g., Gmail) are limited strictly to accessing specific labels (`Internship-Interview`, `Internship-Rejected`) to update job statuses. No other email data is accessed or stored.