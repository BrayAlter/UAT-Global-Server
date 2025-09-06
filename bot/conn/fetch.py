import cv2
from typing import Dict, Any
from bot.conn.u2_ctrl import U2AndroidController
from bot.recog.image_matcher import image_match, compare_color_equal
from bot.recog.ocr import ocr_line
from module.umamusume.asset import MOTIVATION_LIST

def ocr_text(gray):
    return ocr_line(gray, lang="en").strip()


def read_energy(img):
    sub = img[160:161, 229:505]
    if sub.size == 0:
        return 0
    cnt = 0
    row = sub[0]
    for c in row:
        if not compare_color_equal(c, [117, 117, 117], tolerance=20):
            cnt += 1
    return int(cnt / 276 * 100)


def read_year(img):
    rois = [
        (40, 120, 0, 1280),
        (60, 140, 0, 1280),
        (74, 100, 250, 575),
    ]
    for y1, y2, x1, x2 in rois:
        sub = img[y1:y2, x1:x2]
        if sub.size == 0:
            continue
        gray = cv2.cvtColor(sub, cv2.COLOR_BGR2GRAY)
        t = ocr_text(gray).lower()
        if not t:
            continue
        if "junior" in t:
            return "Junior"
        if "classic" in t:
            return "Classic"
        if "senior" in t:
            return "Senior"
        if "finale" in t or "final" in t:
            return "Finals"
    return "Unknown"


def read_mood(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    for i in range(len(MOTIVATION_LIST)):
        res = image_match(gray, MOTIVATION_LIST[i])
        if res.find_match:
            return i + 1
    return None


def fetch_state() -> Dict[str, Any]:
    ctrl = U2AndroidController()
    ctrl.init_env()
    img = ctrl.get_screen(to_gray=False)
    top_img = img[:186, :]

    energy = read_energy(top_img)
    year = read_year(top_img)
    mood = read_mood(top_img)
    return {"year": year, "mood": mood, "energy": energy}
