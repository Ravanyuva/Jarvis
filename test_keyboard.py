try:
    import jarvis_vision
    print("Module imported successfully.")
    
    vision = jarvis_vision.VisionSystem()
    print("VisionSystem initialized.")
    
    print("Starting Keyboard Mode...")
    vision.start(mode="keyboard")
    
    import time
    start_time = time.time()
    while time.time() - start_time < 10:
        time.sleep(1)
        if not vision.thread.is_alive():
            print("Vision thread died unexpectedly!")
            break
            
    print("Test finished. Stopping.")
    vision.stop()
except Exception as e:
    print(f"CRASH: {e}")
    import traceback
    traceback.print_exc()
