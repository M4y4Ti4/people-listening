import cv2
import numpy as np
from pythonosc import udp_client


cap = cv2.VideoCapture(r"C:\Tracking\videos\cheesymelt.mp4")
client = udp_client.SimpleUDPClient("127.0.0.1", 4560)  # change 4560 to match!


ret, frame1 = cap.read()
ret, frame2 = cap.read()

threshold_x = 350
min_contour_area = 200

pitch_min, pitch_max = 40, 80

dur_min, dur_max = 0.2, 2.0

crossed = {}

def map_value(value, in_min, in_max, out_min, out_max):
    return out_min + (value - in_min) / (in_max - in_min) * (out_max - out_min)



heights = []
widths = []

while cap.isOpened():
    diff = cv2.absdiff(frame1, frame2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    _, thresh = cv2.threshold(blur, 15, 255, cv2.THRESH_BINARY)
    dilated = cv2.dilate(thresh, None, iterations=3)
    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    frame_height, frame_width = frame1.shape[:2]

    cv2.line(frame1, (threshold_x, 0), (threshold_x, frame_height), (0, 0, 255), 2)


    for i, contour in enumerate(contours):
        if cv2.contourArea(contour) < min_contour_area:  # ✅ filter first
            continue

        (x, y, w, h) = cv2.boundingRect(contour)
        centroid_x = x + w // 2
        centroid_y = y + h // 2

        print(centroid_x)

        cv2.rectangle(frame1, (x,y), (x+w, y+h), (0, 255, 0), 2)
        cv2.circle(frame1, (centroid_x, centroid_y), 4, (255, 0, 0), -1)

        is_crossing = (x < threshold_x < x + w)
        
        if is_crossing and i not in crossed:
            pitch = int(map_value(h, 50, 300, pitch_min, pitch_max))
            duration = round(map_value(w, 20, 200, dur_min, dur_max), 2)

            pitch = max(pitch_min, min(pitch_max, pitch))
            duration = max(dur_min, min(dur_max, duration))

            client.send_message("/trigger/note", [pitch, duration])

            crossed[i] = True
        
        elif not is_crossing and i in crossed:
            crossed.pop(i)
                

        heights.append(h)                   
        widths.append(w)
        cv2.rectangle(frame1, (x,y), (x+w, y+h), (0, 255, 0), 2)


    cv2.imshow("feed", frame1)
    frame1 = frame2
    ret, frame2 = cap.read()

    if cv2.waitKey(40) == 27:
        break

np.save('heights', arr=heights)
cv2.destroyAllWindows()
cap.release()