# Real-Time Multi-Object Identifier using OpenCV

A real-time image verification and multi-object tracking system that detects reference objects in a live camera feed using feature matching and planar homography.

---

## What is OpenCV?

OpenCV (Open Source Computer Vision Library) is an open-source computer vision and machine learning software library. It provides a vast suite of tools to process images and videos, analyze visual data, detect object features, and perform real-time visual tracking. In this project, OpenCV extracts unique visual keypoints from reference objects and locates them dynamically inside a webcam stream.

---

## Architecture & Workflow

The detection pipeline consists of five key processing stages:

```text
[ Reference Images ] ---> SIFT Feature Extraction (Keypoints & Descriptors)
                                     |
                                     v
[ Live Camera Feed ] ---> KNN Matching & Lowe's Ratio Test (Filtering)
                                     |
                                     v
                     RANSAC Homography Estimation (Matrix M)
                                     |
                                     v
                   Polygon Geometry & Convexity Validation
                                     |
                                     v
              [ Dynamic UI Overlay & Audio Alert System ]```

 ---

## Project Structure ##
Image-identifier-using-OpenCV/
├── reference_images/         # Target object photos (e.g., book.jpg, remote.jpg)
│   └── reference.jpg
├── src/
│   ├── __init__.py
│   └── detector.py           # Multi-object detection & geometric validation engine
├── .gitignore
├── main.py                   # Real-time video stream loop and UI rendering
├── README.md                 # Project documentation
└── requirements.txt          # Python dependencies

Setup & Installation
Clone the Repository:

Bash
git clone [https://github.com/xsparrkk/Image-identifier-using-OpenCV.git](https://github.com/xsparrkk/Image-identifier-using-OpenCV.git)
cd Image-identifier-using-OpenCV
Install Dependencies:

Bash
pip install -r requirements.txt
How to Test with Your Own Images
Note on Adding Reference Images:
You can test this system on any custom physical object (e.g., books, game boxes, cards, product packaging, posters).

Simply take a clear, well-lit photo of the target object, name it descriptively (e.g., book.jpg, gamepad.png), and place it into the reference_images/ directory. The application automatically detects and loads all images in this folder at startup and uses the file name as the on-screen label.

Running the Application
Execute the main script to start the live detection feed:

Bash
python main.py
Exit Options: Click the red EXIT button on the top-right corner of the video window or press the q key on your keyboard.
