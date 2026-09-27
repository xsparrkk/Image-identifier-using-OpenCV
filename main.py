import platform
import threading
import time
import cv2
from src.detector import MultiObjectVerifier

exit_requested = False


def play_beep_sound():
    def beep():
        try:
            if platform.system() == "Windows":
                import winsound
                winsound.Beep(1000, 150)
            else:
                print("\a", end="", flush=True)
        except Exception:
            pass

    threading.Thread(target=beep, daemon=True).start()


def on_mouse_click(event, x, y, flags, param):
    global exit_requested
    if event == cv2.EVENT_LBUTTONDOWN:
        btn_x1, btn_y1, btn_x2, btn_y2 = param["btn_coords"]
        if btn_x1 <= x <= btn_x2 and btn_y1 <= y <= btn_y2:
            exit_requested = True


def main():
    global exit_requested
    window_name = "Multi-Object Real-Time Verification"

    print("Loading Reference Images & Initializing Detector...")
    try:
        verifier = MultiObjectVerifier(reference_dir="reference_images", min_match_count=15, method="SIFT")
    except Exception as e:
        print(f"Initialization Error: {e}")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera feed.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    cv2.namedWindow(window_name)
    btn_coords = (1120, 20, 1260, 60)
    cv2.setMouseCallback(window_name, on_mouse_click, param={"btn_coords": btn_coords})

    last_beep_time = 0.0
    beep_cooldown = 1.2
    prev_time = time.time()

    print("Live Feed Active. Place multiple reference photos into 'reference_images/'. Click 'EXIT' or press 'q' to quit.")

    while not exit_requested:
        ret, frame = cap.read()
        if not ret:
            break

        # Process frame against all reference images
        frame, detections, best_match_pct, overall_color = verifier.verify_frame(frame)

        # Trigger beep if any object is detected
        curr_time = time.time()
        if len(detections) > 0 and (curr_time - last_beep_time > beep_cooldown):
            play_beep_sound()
            last_beep_time = curr_time

        # Calculate FPS
        fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0.0
        prev_time = curr_time

        # --- UI OVERLAY ---
        if len(detections) > 0:
            detected_names = ", ".join([d["name"] for d in detections])
            status_txt = f"MATCHED: {detected_names} ({best_match_pct:.1f}%)"
        else:
            status_txt = f"SEARCHING... ({best_match_pct:.1f}%)"

        cv2.putText(frame, status_txt, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, overall_color, 2)
        cv2.putText(frame, f"Active Targets: {len(verifier.ref_objects)} | FPS: {fps:.1f}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Match confidence bar
        bar_x, bar_y, bar_w, bar_h = 20, 85, 250, 12
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (50, 50, 50), -1)
        fill_w = int((best_match_pct / 100.0) * bar_w)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), overall_color, -1)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (255, 255, 255), 1)

        # Interactive Exit Button
        btn_x1, btn_y1, btn_x2, btn_y2 = btn_coords
        cv2.rectangle(frame, (btn_x1, btn_y1), (btn_x2, btn_y2), (0, 0, 180), -1)
        cv2.rectangle(frame, (btn_x1, btn_y1), (btn_x2, btn_y2), (255, 255, 255), 2)
        cv2.putText(frame, "EXIT", (btn_x1 + 35, btn_y1 + 27), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow(window_name, frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()