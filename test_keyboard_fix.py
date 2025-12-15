import jarvis_vision
import time

def test_keyboard():
    print("Initializing Vision System...")
    vision = jarvis_vision.VisionSystem()
    
    print("Starting in KEYBOARD mode...")
    vision.start(mode="keyboard")
    
    print("Vision system started. Window should appear. Running for 10 seconds...")
    try:
        for i in range(10):
            print(f"Time: {i+1}/10")
            time.sleep(1)
    except KeyboardInterrupt:
        pass
        
    print("Stopping...")
    vision.stop()
    print("Test Complete.")

if __name__ == "__main__":
    test_keyboard()
