import cv2

def check_camera():
    print("Opening camera...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open camera index 0.")
        return

    print("Reading frame...")
    ret, frame = cap.read()
    if ret:
        print(f"SUCCESS: Frame captured. Shape: {frame.shape}")
    else:
        print("ERROR: Failed to read frame.")
    
    cap.release()

if __name__ == "__main__":
    check_camera()
