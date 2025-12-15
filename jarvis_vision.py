import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector
import time
import numpy as np
import threading
import math
from pynput.keyboard import Controller
import pyautogui
# Fail-safe for pyautogui
pyautogui.FAILSAFE = False

try:
    import google.generativeai as genai
except ImportError:
    genai = None

class VisionSystem:
    def __init__(self, api_key=None):
        self.camera_index = 0
        self.cap = None
        self.detector = HandDetector(detectionCon=0.8, maxHands=2)
        self.keyboard = Controller()
        self.running = False
        self.thread = None
        
        # Virtual Keyboard Config
        self.keys = [
            ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
            ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";"],
            ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"]
        ]
        self.buttonList = []
        self.create_buttons()
        self.last_click_time = 0
        
        # Mode: 'monitoring', 'keyboard', 'mouse', 'gestures', 'drawing'
        self.mode = "monitoring" 
        
        # Mouse Config
        self.wScr, self.hScr = pyautogui.size()
        self.wCam, self.hCam = 1280, 720 # Camera resolution set below
        self.frameR = 200 # Frame Reduction to reach edges
        self.smoothening = 3
        self.plocX, self.plocY = 0, 0
        self.clocX, self.clocY = 0, 0
        
        # Drawing Config
        self.draw_points = [[]] # List of strokes
        self.draw_color = (0, 0, 255)
        self.brush_thickness = 15
        self.annotation_canvas = None # Initialized in loop
        
        # AI Setup
        self.api_key = api_key
        if self.api_key and genai:
             genai.configure(api_key=self.api_key)
             self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
             self.model = None

    def create_buttons(self):
        for i, row in enumerate(self.keys):
            for j, key in enumerate(row):
                self.buttonList.append(Button([100 * j + 50, 100 * i + 50], key))

    def start(self, mode="monitoring"):
        print(f"[DEBUG] VisionSystem.start called with mode: {mode}")
        if self.running:
            print("[DEBUG] VisionSystem already running. Switching mode.")
            self.mode = mode 
            return
            
        self.mode = mode
        self.running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        print("[DEBUG] VisionSystem thread started.")

    def stop(self):
        print("[DEBUG] VisionSystem stopping...")
        self.running = False
        
        # Give thread a moment to exit loop
        if self.thread:
            self.thread.join(timeout=2.0)
        
        # Force close camera and windows
        try:
            if self.cap:
                self.cap.release()
            cv2.destroyAllWindows()
            # Force window destruction on Windows
            cv2.waitKey(1)
            self.cap = None
        except Exception as e:
            print(f"[WARN] Error during cleanup: {e}")
            
        print("[DEBUG] VisionSystem stopped.")

    def _run_loop(self):

        print(f"[DEBUG] Opening Camera Index {self.camera_index}...")
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        
        # Try alternate index if first fails
        if not self.cap.isOpened() or not self.cap.read()[0]:
             self.cap.release()
             print(f"[WARN] Camera Index {self.camera_index} failed. Trying Index 1...")
             self.camera_index = 1
             self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)

        self.cap.set(3, 1280) # Width
        self.cap.set(4, 720)  # Height
        
        if not self.cap.isOpened():
             print("[ERROR] Could not open ANY video source.")
             self.running = False
             return

        # Clear drawing canvas
        self.annotation_canvas = np.zeros((720, 1280, 3), np.uint8) 
        
        try:
            no_frame_count = 0
            loop_count = 0
            while self.running:
                loop_count += 1
                if loop_count % 30 == 0:
                    print(f"[DEBUG] Vision Loop Alive. Mode: {self.mode}")
                
                try:
                    success, img = self.cap.read()
                except Exception as e:
                    # Only log the first few errors to avoid flooding
                    if no_frame_count < 3:
                        print(f"[WARN] Camera read exception: {e}")
                    success = False
                    img = None
                    time.sleep(0.5)

                if not success:
                    no_frame_count += 1
                    if no_frame_count % 50 == 0:
                         print("[WARN] Camera frame read failing repeatedly. Camera may be effectively dead.")
                    
                    # Auto-stop if too many failures (e.g. 100 frames ~ 10-20 seconds)
                    if no_frame_count > 100:
                         print("[ERROR] Camera failure limit reached. Stopping Vision System to prevent spam.")
                         self.running = False
                         break
                         
                    time.sleep(0.1)
                    continue
                
                # Check for invalid frame dimensions
                if img is None or img.size == 0:
                     continue
                
                # Reset fail count
                no_frame_count = 0
                
                try:
                    # 1. Flip for mirror effect
                    img = cv2.flip(img, 1)
                except Exception as e:
                    print(f"[WARN] Flip failed: {e}")
                    continue
                
                # 2. Hand Tracking
                hands, img = self.detector.findHands(img, draw=True) # Ensure draw=True
                
                # 3. Features based on Mode
                if self.mode == "keyboard":
                    img = self._handle_keyboard(img, hands)
                elif self.mode == "counting":
                    img = self._handle_counting(img, hands)
                elif self.mode == "mouse":
                    img = self._handle_mouse(img, hands)
                elif self.mode == "gestures":
                    img = self._handle_gestures(img, hands)
                elif self.mode == "drawing":
                    img = self._handle_drawing(img, hands)
                else:
                     cv2.putText(img, "Vision Active", (50, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
                
                # 4. Display
                try:
                    cv2.imshow("Jarvis Vision", img)
                    key = cv2.waitKey(1)
                    if key & 0xFF == ord('q'):
                        self.running = False
                        break
                except Exception as e:
                    print(f"[ERROR] cv2.imshow failed: {e}")
                    
        except Exception as e:
            print(f"[CRASH] Vision Thread crashed: {e}")
            import traceback
            traceback.print_exc()
        finally:
             print("[DEBUG] Clean exit from run_loop.")
        
        self.cap.release()
        cv2.destroyAllWindows()
        self.cap = None

    # --- FEATURES ---

    def _handle_mouse(self, img, hands):
        cv2.rectangle(img, (self.frameR, self.frameR), (1280 - self.frameR, 720 - self.frameR), (255, 0, 255), 2)
        
        if hands:
            hand = hands[0]
            lmList = hand["lmList"]
            
            # Tip of Index and Middle
            x1, y1 = lmList[8][:2]
            
            # Check which fingers are up
            fingers = self.detector.fingersUp(hand)
            
            # Moving Mode: Only Index Finger Up
            if fingers[1] == 1 and fingers[2] == 0:
                # Convert Coordinates
                x3 = np.interp(x1, (self.frameR, 1280 - self.frameR), (0, self.wScr))
                y3 = np.interp(y1, (self.frameR, 720 - self.frameR), (0, self.hScr))
                
                # Smoothening
                self.clocX = self.plocX + (x3 - self.plocX) / self.smoothening
                self.clocY = self.plocY + (y3 - self.plocY) / self.smoothening
                
                # Move Mouse
                try:
                    pyautogui.moveTo(self.clocX, self.clocY)
                except: pass
                
                cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
                self.plocX, self.plocY = self.clocX, self.clocY

            # Clicking Mode: Both Index and Middle are up
            if fingers[1] == 1 and fingers[2] == 1:
                # Find distance between fingers
                length, lineInfo, img = self.detector.findDistance(8, 12, img)
                
                # Click if short distance
                if length < 40:
                    cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                    # Debounce
                    if time.time() - self.last_click_time > 0.5:
                         pyautogui.click()
                         self.last_click_time = time.time()
        
        return img

        return img

    def _handle_gestures(self, img, hands):
        if hands:
            hand = hands[0]
            lmList = hand["lmList"]
            
            # --- VOLUME (Index + Thumb) ---
            x1, y1 = lmList[4][:2]
            x2, y2 = lmList[8][:2]
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            
            length = math.hypot(x2 - x1, y2 - y1)
            
            # --- SWIPE (Presentation) ---
            # Center of hand
            curr_x, curr_y = hand['center']
            
            # Detect Swipe if hand is Open (5 fingers up) or Index up
            fingers = self.detector.fingersUp(hand)
            
            # Only swipe if not pinching (Length > 60)
            if length > 60:
                # Check Horizontal Movement
                # We need history. Let's use plocX/Y from self but strictly for gestures here
                # Or just use local static variable if possible? No, need self state.
                # Let's use self.gesture_last_x
                if not hasattr(self, 'gesture_last_x'):
                    self.gesture_last_x = curr_x
                    self.gesture_last_time = time.time()
                
                # Check speed
                dt = time.time() - self.gesture_last_time
                dx = curr_x - self.gesture_last_x
                
                if dt > 0.1: # Check every 100ms
                    speed = dx / dt # pixels per second
                    
                    if speed > 500: # Fast Right
                        cv2.putText(img, "Next Slide", (200, 200), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
                        pyautogui.press("right")
                        self.gesture_last_x = curr_x
                        self.gesture_last_time = time.time()
                        time.sleep(0.5) # Debounce
                        
                    elif speed < -500: # Fast Left
                        cv2.putText(img, "Prev Slide", (200, 200), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 255), 3)
                        pyautogui.press("left")
                        self.gesture_last_x = curr_x
                        self.gesture_last_time = time.time()
                        time.sleep(0.5) # Debounce
                    
                    self.gesture_last_x = curr_x
                    self.gesture_last_time = time.time()

            # --- VOLUME RENDER ---
            # Draw pinch line
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.circle(img, (cx, cy), 10, (255, 0, 255), cv2.FILLED)
            
            # Hand Range: 50 - 250
            # Vol Range: 0 - 100
            vol = np.interp(length, [50, 220], [0, 100])
            
            # Visual Bar
            volBar = np.interp(length, [50, 220], [400, 150])
            cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 3)
            cv2.rectangle(img, (50, int(volBar)), (85, 400), (0, 255, 0), cv2.FILLED)
            cv2.putText(img, f'{int(vol)}%', (40, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 3)
            
            # Actuate Volume
            # If Pinching Hard (<50) -> Down
            # If Wide Open (>220) and Index is up -> Up
            if length < 50:
                 cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)
                 pyautogui.press("volumedown")
            elif length > 220:
                 # Only up if we are intentionally interacting (e.g. index/thumb aligned)
                 # Simpler: just distance
                 pyautogui.press("volumeup")
                 pass

        return img

    def _handle_drawing(self, img, hands):
        # Draw on separate canvas and merge
        if hands:
            hand = hands[0]
            lmList = hand["lmList"]
            
            # Tip of Index (8)
            x1, y1 = lmList[8][:2]
            fingers = self.detector.fingersUp(hand)
            
            # Draw Mode: Index finger up
            if fingers[1] == 1 and fingers[2] == 0:
                cv2.circle(img, (x1, y1), 15, self.draw_color, cv2.FILLED)
                
                if self.plocX == 0 and self.plocY == 0:
                    self.plocX, self.plocY = x1, y1
                
                cv2.line(self.annotation_canvas, (self.plocX, self.plocY), (x1, y1), self.draw_color, self.brush_thickness)
                self.plocX, self.plocY = x1, y1
            
            # Lift Mode: Index and Middle up (Don't draw, just move)
            elif fingers[1] == 1 and fingers[2] == 1:
                self.plocX, self.plocY = 0, 0
                
            # Clear Mode: All fingers up (Palm)
            elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 1:
                self.annotation_canvas = np.zeros((720, 1280, 3), np.uint8) 

        # Merge Canvas
        # Create mask
        imgGray = cv2.cvtColor(self.annotation_canvas, cv2.COLOR_BGR2GRAY)
        _, imgInv = cv2.threshold(imgGray, 50, 255, cv2.THRESH_BINARY_INV)
        imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
        
        # Simple weighted add
        img = cv2.addWeighted(img, 0.5, self.annotation_canvas, 0.5, 0)
        
        return img


    def _handle_keyboard(self, img, hands):
        # Draw Buttons
        img = self.draw_all_buttons(img, self.buttonList)
        
        if hands:
            for hand in hands:
                lmList = hand["lmList"]
                # Index finger tip: 8, Middle finger tip: 12
                # We use Index (8) and Thumb (4) for 'click' or just Index tip for hover
                
                # Check clicks
                if lmList:
                     try:
                         for button in self.buttonList:
                             x, y = button.pos
                             w, h = button.size
                             
                             # Check if Index finger is over the button
                             # lmList[8] is [x, y, z]
                             if len(lmList) > 8 and x < lmList[8][0] < x + w and y < lmList[8][1] < y + h:
                                 cv2.rectangle(img, (x - 5, y - 5), (x + w + 5, y + h + 5), (175, 0, 175), cv2.FILLED)
                                 cv2.putText(img, button.text, (x + 20, y + 65), cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
                                 
                                 # Distance between index (8) and middle (12) or index(8) and thumb(4)
                                 # Let's use Index and Thumb for click (Pincher gesture)
                                 try:
                                     length, _, _ = self.detector.findDistance(8, 4, img, draw=False)
                                 except Exception as e:
                                     print(f"[WARN] findDistance failed: {e}")
                                     continue
                                 
                                 if length < 30:
                                     # Debounce
                                     if time.time() - self.last_click_time > 0.3:
                                         try:
                                             self.keyboard.press(button.text)
                                             self.keyboard.release(button.text)
                                             cv2.rectangle(img, button.pos, (x + w, y + h), (0, 255, 0), cv2.FILLED)
                                             cv2.putText(img, button.text, (x + 20, y + 65), cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
                                             self.last_click_time = time.time()
                                         except Exception as e:
                                             print(f"[WARN] Keyboard press failed: {e}")
                     except Exception as e:
                         print(f"[WARN] Button interaction error: {e}")
                                     
        return img
    
    def draw_all_buttons(self, img, buttonList):
        for button in buttonList:
            x, y = button.pos
            w, h = button.size
            cvzone.cornerRect(img, (button.pos[0], button.pos[1], button.size[0], button.size[1]), 20, rt=0)
            cv2.rectangle(img, button.pos, (x + w, y + h), (255, 0, 255), cv2.FILLED)
            cv2.putText(img, button.text, (x + 20, y + 65), cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
        return img

    def _handle_counting(self, img, hands):
        if hands:
            # Only support first hand for counting simple demo
            hand1 = hands[0]
            lmList1 = hand1["lmList"]
            bbox1 = hand1["bbox"]
            centerPoint1 = hand1['center']
            
            fingers1 = self.detector.fingersUp(hand1)
            count = fingers1.count(1)
            
            cv2.putText(img, f"Fingers: {count}", (bbox1[0], bbox1[1] - 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
            
            # Optional: Describe what this number means?
            # kept simple for now
        return img

    def take_photo(self):
        # If running, use current frame
        if self.running and self.cap and self.cap.isOpened():
             success, img = self.cap.read()
             if success:
                 filename = f"capture_{int(time.time())}.jpg"
                 cv2.imwrite(filename, img)
                 return filename
        else:
            # Open temp camera
            try:
                cap = cv2.VideoCapture(self.camera_index)
                cap.set(3, self.wCam)
                cap.set(4, self.hCam)
                success, img = cap.read()
                cap.release()
                if success:
                     filename = f"capture_{int(time.time())}.jpg"
                     cv2.imwrite(filename, img)
                     return filename
            except Exception as e:
                print(f"[ERROR] Capture failed: {e}")
        return None

    def describe_scene(self):
        """Captures a single frame and asks AI to describe it."""
        if not self.cap or not self.cap.isOpened():
             # If not running loop, open briefly
             temp_cap = cv2.VideoCapture(self.camera_index)
             ret, frame = temp_cap.read()
             temp_cap.release()
             if not ret:
                 return "Camera not available."
        else:
             # Grab from running stream
             ret, frame = self.cap.read()
             if not ret:
                 return "Failed to grab frame."
        
        # Process for AI
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        
        if self.model:
            try:
                response = self.model.generate_content(["Describe this image briefly. What objects or fingers do you see?", pil_img])
                return response.text
            except Exception as e:
                return f"AI Vision Error: {e}"
        else:
            return "AI Vision model not configured."


class Button:
    def __init__(self, pos, text, size=[85, 85]):
        self.pos = pos
        self.size = size
        self.text = text

if __name__ == "__main__":
    # Test
    vision = VisionSystem()
    vision.start(mode="keyboard")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        vision.stop()
