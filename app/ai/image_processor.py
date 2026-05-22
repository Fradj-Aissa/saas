import cv2
import numpy as np


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """تحويل الصورة إلى رمادي لتحسين نتائج OCR."""
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def denoise_image(image: np.ndarray) -> np.ndarray:
    """إزالة الضوضاء باستخدام فلتر متوسط ومعدل Gaussian."""
    return cv2.fastNlMeansDenoising(image, None, h=10, templateWindowSize=7, searchWindowSize=21)


def deskew_image(image: np.ndarray) -> np.ndarray:
    """محاولة تصحيح الانحراف الزاوي للصورة بعد تحويلها للرمادي."""
    coords = np.column_stack(np.where(image > 0))
    if coords.size == 0:
        return image

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def apply_clahe(image: np.ndarray) -> np.ndarray:
    """تعزيز التباين المحلي باستخدام CLAHE."""
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    return clahe.apply(image)


def adaptive_threshold(image: np.ndarray) -> np.ndarray:
    """تحويل الصورة إلى صورة ثنائية مناسبة للـ OCR."""
    return cv2.adaptiveThreshold(
        image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2,
    )


def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
    """سلسلة المعالجة المسبقة لتحسين صورة الإدخال قبل OCR."""
    gray = to_grayscale(image)
    denoised = denoise_image(gray)
    deskewed = deskew_image(denoised)
    enhanced = apply_clahe(deskewed)
    return adaptive_threshold(enhanced)
