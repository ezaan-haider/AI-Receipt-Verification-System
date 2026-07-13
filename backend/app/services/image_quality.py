import cv2


def assess_image_quality(image_path: str):
    image = cv2.imread(image_path)

    if image is None:
        return {
            "score": 0,
            "flags": ["Could not read image"],
        }

    flags = []
    score = 100

    height, width = image.shape[:2]

    if width < 600 or height < 600:
        flags.append("Low resolution image")
        score -= 25

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    if blur_score < 80:
        flags.append("Image appears blurry")
        score -= 30

    brightness = gray.mean()
    if brightness < 60:
        flags.append("Image appears too dark")
        score -= 20
    elif brightness > 220:
        flags.append("Image appears too bright")
        score -= 20

    contrast = gray.std()
    if contrast < 35:
        flags.append("Low contrast image")
        score -= 20

    score = max(score, 0)

    return {
        "score": round(score, 2),
        "flags": flags,
    }