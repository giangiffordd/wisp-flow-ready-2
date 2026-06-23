import cv2
import numpy as np
from typing import Tuple

PART_COLORS: dict = {
    'wing':       (255, 255, 0),
    'antenna':    (0, 255, 255),
    'leg':        (0, 255, 0),
    'shell_wing': (0, 165, 255),
    'horn':       (255, 0, 255),
}
SPECIES_COLOR: Tuple[int, int, int] = (255, 100, 0)


def draw_rounded_rect(
    img: np.ndarray,
    pt1: Tuple[int, int],
    pt2: Tuple[int, int],
    color: Tuple[int, int, int],
    thickness: int,
    radius: int = 8,
) -> None:
    x1, y1 = pt1
    x2, y2 = pt2
    r = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    if r < 1:
        cv2.rectangle(img, pt1, pt2, color, thickness)
        return
    cv2.line(img, (x1 + r, y1), (x2 - r, y1), color, thickness)
    cv2.line(img, (x1 + r, y2), (x2 - r, y2), color, thickness)
    cv2.line(img, (x1, y1 + r), (x1, y2 - r), color, thickness)
    cv2.line(img, (x2, y1 + r), (x2, y2 - r), color, thickness)
    cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness)
    cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness)
    cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness)
    cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness)


def draw_label(
    img: np.ndarray,
    text: str,
    position: Tuple[int, int],
    bg_color: Tuple[int, int, int],
    text_color: Tuple[int, int, int] = (255, 255, 255),
    font_scale: float = 0.5,
    thickness: int = 1,
) -> None:
    font = cv2.FONT_HERSHEY_SIMPLEX
    (text_w, text_h), _ = cv2.getTextSize(text, font, font_scale, thickness)
    x, y = position
    cv2.rectangle(img, (x, y - text_h - 6), (x + text_w + 8, y + 2), bg_color, -1)
    cv2.putText(img, text, (x + 4, y - 3), font, font_scale, text_color, thickness, cv2.LINE_AA)


def is_center_inside(
    part_box: list,
    parent_box: list,
) -> bool:
    px1, py1, px2, py2 = part_box
    bx1, by1, bx2, by2 = parent_box
    center_x = (px1 + px2) / 2
    center_y = (py1 + py2) / 2
    return (bx1 <= center_x <= bx2) and (by1 <= center_y <= by2)
