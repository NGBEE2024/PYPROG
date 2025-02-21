from flask import Flask, render_template, Response
from picamera2 import Picamera2
import cv2
import threading
import time

app = Flask(__name__)

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration())
picam2.start()

video_recording = False
video_thread = None

def record_video():
    global video_recording
    video_recording = True
    picam2.start_recording("video.h264")
    while video_recording:
        time.sleep(1)
    picam2.stop_recording()

@app.route('/')
def index():
    return render_template('cam.html')

@app.route('/screenshot')
def screenshot():
    picam2.capture_file('screenshot.jpg')
    return "Screenshot taken!"

@app.route('/video')
def video():
    global video_recording, video_thread
    if not video_recording:
        video_thread = threading.Thread(target=record_video)
        video_thread.start()
        return "Video recording started!"
    else:
        video_recording = False
        video_thread.join()
        return "Video recording stopped!"

def generate_frames():
    while True:
        frame = picam2.capture_array()
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
