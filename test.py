import cv2
from ultralytics import YOLO

from Service.QAService import PARENT_SPECIES, PART_CLASSES, apply_qa_routing

# 1. Load your model
model = YOLO('runs/detect/train-2/weights/best.pt')

# 2. Species list, part classes, and QA pass/fail rules now live in
# Service/QAService.py — shared with the FastAPI backend so the desktop QA
# station and the live API always agree on what counts as a PASS.

# 3. Start the Webcam
cap = cv2.VideoCapture(0)

print("\n" + "="*50)
print("  WISP-FLOW QA STATION INITIALIZED")
print("  Press SPACEBAR to capture and scan.")
print("  Press 'q' to quit.")
print("="*50 + "\n")

while cap.isOpened():
    # Read the live feed
    success, frame = cap.read()
    if not success:
        print("Camera disconnected.")
        break

    # Make a copy of the frame just to show the live preview UI
    preview_frame = frame.copy()
    cv2.putText(preview_frame, "LIVE PREVIEW - Ready for Insect", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    cv2.putText(preview_frame, "Press SPACEBAR to Capture | Press 'Q' to Quit", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    # Show the live feed
    cv2.imshow("WISP-FLOW QA Station", preview_frame)

    # Listen for key presses
    key = cv2.waitKey(1) & 0xFF

    # If user presses 'q', quit the program
    if key == ord('q'):
        break

    # If user presses SPACEBAR, run the scan!
    elif key == ord(' '):
        print("\nCapturing image and running AI scan...")

        # 4. Run YOLO on the single frozen frame
        results = model(frame, conf=0.5, verbose=False)
        annotated_frame = results[0].plot()

        insects = []
        parts = []

        # 5. Sort boxes
        for box in results[0].boxes:
            class_id = int(box.cls[0].item())
            raw_class_name = model.names[class_id]

            # Normalize the name: "Heteropteryx dilatata" -> "heteropteryx_dilatata"
            class_name = raw_class_name.lower().replace(' ', '_')

            coords = box.xyxy[0].tolist()

            if class_name in PARENT_SPECIES:
                insects.append({'species': class_name, 'coords': coords})
            elif class_name in PART_CLASSES:
                parts.append({'name': class_name, 'coords': coords})
            # Anything matching neither (e.g. graphium_weiskei) is ignored.

        # --- Fallback if no insect is detected ---
        if len(insects) == 0:
            print("⚠️ QA RESULT: NO MAIN INSECT DETECTED - FLAGGED")
            print("   -> Tip: Adjust the insect, check lighting, and try scanning again.\n")
            cv2.putText(annotated_frame, "STATUS: NO INSECT DETECTED", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # 6. Apply QA routing to each insect found
        for index, insect in enumerate(insects):
            bx1, by1, bx2, by2 = insect['coords']
            species_name = insect['species']

            found_parts = {p: 0 for p in PART_CLASSES}

            for part in parts:
                px1, py1, px2, py2 = part['coords']
                center_x = (px1 + px2) / 2
                center_y = (py1 + py2) / 2

                if (bx1 <= center_x <= bx2) and (by1 <= center_y <= by2):
                    found_parts[part['name']] += 1

            qa_status, _required_parts = apply_qa_routing(species_name, found_parts)
            is_pass = (qa_status == 'PASS')

            # 7. Draw Status Text and Print to Terminal
            if is_pass:
                status_text = f"[{species_name.upper()}] STATUS: PASS"
                text_color = (0, 255, 0) # Green
                print(f"✅ QA RESULT: [{species_name.upper()}] - PASS")
            else:
                status_text = f"[{species_name.upper()}] STATUS: FLAGGED"
                text_color = (0, 0, 255) # Red
                print(f"❌ QA RESULT: [{species_name.upper()}] - FLAGGED")

            # Print the exact parts it found to the console for easy debugging
            print(f"   -> Parts Counted: {found_parts}\n")

            parts_text = "Found: " + ", ".join([f"{count} {p}" for p, count in found_parts.items() if count > 0])

            text_x = int(bx1)
            text_y = max(20, int(by1) - 30) # Prevent text from going off the top of the screen

            cv2.putText(annotated_frame, status_text, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
            cv2.putText(annotated_frame, parts_text, (text_x, text_y + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Add a banner letting the user know the system is paused
        cv2.putText(annotated_frame, "QA COMPLETE - Press ANY KEY to return to Live View", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Show the frozen result frame
        cv2.imshow("WISP-FLOW QA Station", annotated_frame)

        # This completely freezes the video loop until the artisan presses any key
        cv2.waitKey(0)
        print("Returning to live feed...")

# Clean up
cap.release()
cv2.destroyAllWindows()
