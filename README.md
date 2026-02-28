# TrajectTower 🗼

TrajectTower is a comprehensive, desktop-based Job Application Tracker designed to streamline the job hunt process. It combines manual tracking with automated features like URL parsing and email-based status updates.

## 🚀 Features

### 📋 Job Management
- **URL Parser**: Automatically pull job descriptions from URLs using Playwright.
- **Manual Entry**: Paste job descriptions directly or upload screenshots for visual tracking.
- **Status Tracking**: Categorize your applications as **Applied**, **Rejected**, or **Interview**.
- **Search & Filter**: 
  - Real-time search by Company, Title, or Status.
  - Status-specific filtering (e.g., view only your current interviews).
  - 100ms debounced search for smooth performance.

### 🖼️ Enhanced Media Viewing
- **Zoomable Image Viewer**: View job screenshots with full Zoom In/Out, 1:1, and Auto-Fit controls.
- **Smooth Navigation**: Support for mouse-wheel scrolling and Ctrl+Scroll for zooming.
- **Independent Windows**: Multiple windows can be open without conflicting scroll behaviors.

### 📧 Automated Updates
- **Gmail Integration**: Connect your Gmail account to automatically update application statuses based on labels.
- **Label-Based Processing**: Use labels like `Internship-Interview` or `Internship-Rejected` to trigger updates.
- **Process Logs**: View a historical log of all automated status changes, ordered from most recent to oldest.

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- [Pillow](https://python-pillow.org/) for image processing
- [Playwright](https://playwright.dev/python/) for web scraping
- [Google API Client](https://github.com/googleapis/google-api-python-client) for Gmail integration

### Step-by-Step Setup

1. **Clone and Create Virtual Environment**:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright Browsers**:
   ```bash
   playwright install chromium
   ```

4. **Run the Application**:
   ```bash
   python main.py
   ```

## 📂 Project Structure

- `main.py`: The primary GUI and application logic.
- `app/`: 
  - `parse.py`: Logic for scraping job descriptions.
  - `embed.py`: Logic for handling logs and data embedding.
  - `paths.py`: Cross-platform path management.
  - `emails/`: Email provider integrations (Gmail, etc.).
- `data/`: Local storage for job data, images, and text files (stored in `%APPDATA%` on Windows).

## 🛡️ Data & Privacy
TrajectTower stores all data locally on your machine.
- **Images**: Moved to `data/jobImages` for persistent storage.
- **Descriptions**: Saved as text files in `data/pulledTextFiles`.
- **Logs**: Automated changes are tracked in `data/logs.json`.

---
*Built with ❤️ for job hunters.*
