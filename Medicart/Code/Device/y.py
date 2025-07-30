import cv2
from pyzbar.pyzbar import decode
import numpy as np

def qr_code_reader():
    # Initialize the video capture from the camera (default is 0)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Camera not found or cannot be opened.")
        return

    print("Press 'q' to quit the QR reader.")

    while True:
        # Read a frame from the camera
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame. Exiting.")
            break

        # Decode the QR codes in the frame
        decoded_objects = decode(frame)
        for obj in decoded_objects:
            # Get the QR code data
            qr_data = obj.data.decode('utf-8')
            qr_type = obj.type
            print(f"QR Code Data: {qr_data}, Type: {qr_type}")

            # Draw a rectangle around the QR code
            points = obj.polygon
            if len(points) > 4:
                hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                points = hull
            points = [(int(point.x), int(point.y)) for point in points]

            for i in range(len(points)):
                cv2.line(frame, points[i], points[(i + 1) % len(points)], (0, 255, 0), 2)

            # Put the QR code data text on the frame
            x, y = points[0]
            cv2.putText(frame, qr_data, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # Show the frame with the QR code marked
        cv2.imshow("QR Code Reader", frame)

        # E
