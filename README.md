# MinIO API Viewer
---
## Description

MinIO API Viewer is a simple application designed for quickly counting the number of API calls. Also it allows you to explore the structure of data S3 API calls in an adjacent tab "Raw data" . The application provides an intuitive interface for navigating through the data within a specified range.
### Features 

- **API Call Counting**: Quickly count the number of API calls made. 
- **Data Exploration**: Examine the structure of data from S3 API calls. 
- **Customizable View**: Adjust the viewing direction and size of the observation window. - Use the "-" sign to invert the received data. - Set the observation window size with a numeric value (default is -10 to focus on new data).

![img1](imgs/img1.JPG)
![img1](imgs/img2.JPG)
## Getting Started
---
### Install requements

1. **Install  `pandas`, `gradio` and  `flask` (if will any troubles use venv):** 
```bash 
pip install pandas gradio flask
```
### Start App

1. **Clone the project:**
```bash
git clone https://github.com/MrEnd3y/MinIO_API_Viewer.git
cd MinIO_API_Viewer
```
2. **Running the application:**
```bash
python app.py
```
You can then access the application by opening your browser and navigating to: <http://127.0.0.1:7860/api_viewer/>.
### Check

1. **You can easily test this by sending a simple message using`curl`:**
```bash
curl -k -X POST http://localhost:9002/ -H 'Content-Type: application/json' -d '{"name": "MinIO", "message": "hello!"}'
```
## Configuring MinIO webhook
---
To set up MinIO webhook notifications, enter the following URL in the MinIO webhook settings:
<http://127.0.0.1:9002>

![img3](imgs/img3.JPG)
