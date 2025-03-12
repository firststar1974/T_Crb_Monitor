# T CrB Global Monitoring Project

The T CrB Global Monitoring Project aims to conduct high time-resolution (minute-level) observations of the recurrent nova T CrB by leveraging a global network of amateur and professional astronomers. This project emphasizes real-time data processing, collaborative observations, and efficient data sharing to study transient astronomical phenomena.

---

## Overview

The project is comprised of two main Python scripts:

- **Client Script (`T_CrB_client-E_github.py`)**
  - **Purpose:**  
    Continuously monitors a specified directory for new observational FITS files, processes these images using automated photometry routines, and sends the extracted photometric data to a central server.
  - **Key Features:**  
    - Automated image alignment and photometric analysis using libraries such as `astroalign` and `SEP`.
    - Real-time scheduling to periodically scan directories and process new files.
    - Integration with a configuration file (`cfg.txt`) to define observation settings, including station identifiers, filter types, and target coordinates.
    - Data transmission via TCP to the server.

- **Server Script (`T_server_github.py`)**
  - **Purpose:**  
    Receives observational data from client systems, parses and aggregates the photometric measurements, updates records in Excel files, and generates visualizations (such as light curves and median magnitude trends).
  - **Key Features:**  
    - Acts as a TCP server to listen for incoming data from multiple client systems.
    - Processes and organizes the received data for real-time monitoring and historical record-keeping.
    - Generates plots for various time spans and triggers alerts when significant brightness changes are detected.
    - Implements a backup system to archive snapshot images and maintain historical data files.

---

## Prerequisites

Before running the scripts, please ensure the following:

- **Python Environment:**  
  Python 3.6 or later is required.
  
- **Operating System:**  
  The client script is designed for Windows (due to dependencies on Windows-based observational software and file path conventions). The server script is platform-independent as long as the required Python packages are supported.

- **Required Libraries:**  
  The scripts rely on standard scientific libraries (such as NumPy, Astropy, Pandas, and Matplotlib) and specialized packages like `astroalign`, `SEP`, and `schedule`. Make sure these are installed in your Python environment.

- **Configuration File:**  
  A configuration file (`cfg.txt`) should be placed in the same directory as the client script. This file contains important settings (e.g., station ID, filter information, target coordinates) necessary for data processing.

---

## How It Works

1. **Data Acquisition and Processing (Client Side):**  
   - Observers store FITS images in a monitored directory.
   - The client script automatically detects new files, aligns the images using template files, and performs photometry to extract brightness data.
   - Processed photometric data is formatted and sent to the server via a TCP connection.

2. **Data Aggregation and Visualization (Server Side):**  
   - The server script listens for incoming data from clients.
   - Received data is parsed, aggregated, and stored in Excel files for both real-time and historical analysis.
   - The script generates visualizations (e.g., light curves, median magnitude trends) to help monitor T CrB’s eruption in real time.
   - An alert mechanism is in place to notify operators if significant brightness variations are detected.
   - The server also manages data backups and file rotations to preserve historical records.

3. **Collaboration and Community:**  
   - By combining data from multiple observation sites, the project overcomes spatial and temporal limitations of individual observatories.
   - This collaborative model enhances the scientific value of the observations and encourages public participation in astronomical research.

---

## Getting Started

To set up and run the project:

1. **Prepare your Environment:**  
   Install Python 3.6+ and all necessary libraries in your working environment.

2. **Configure the Client:**  
   Place the `cfg.txt` file in the same directory as the client script, and specify the directory where your FITS images are stored.

3. **Run the Scripts:**  
   - Start the client script on your Windows machine to begin monitoring and processing observational data.
   - Launch the server script on a designated machine to receive data, generate plots, and manage data aggregation.

---

## Contributing

Contributions to improve the codebase or add new features are welcome. To contribute:
- Fork the repository and implement your changes.
- Submit a pull request with a detailed description of your improvements.
- For major changes, please open an issue first to discuss your proposed modifications.

---

## License

This project is open-source. Please refer to the [LICENSE](LICENSE) file for details.

---

## Acknowledgements

We extend our sincere gratitude to all the observers participating in the T CrB Global Monitoring Project. Special thanks go to the astronomy team at Tsinghua University for their significant assistance in technical support and data analysis, as well as to all colleagues who provided valuable suggestions and support during the development of these scripts.

---

By participating in this project, you contribute to advancing the study of transient astronomical phenomena and the development of a global observational network. Happy observing!
