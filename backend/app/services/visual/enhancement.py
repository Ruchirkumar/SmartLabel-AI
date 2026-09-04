from pathlib import Path

import cv2


def enhance_image(
    input_path: str,
    output_path: str,
) -> str:
    input_file = Path(input_path)
    output_file = Path(output_path)

    image = cv2.imread(str(input_file))

    if image is None:
        raise ValueError("Unable to read input image.")

    # Convert to LAB color space for local contrast enhancement.
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

    l_channel, a_channel, b_channel = cv2.split(lab)

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    enhanced_l = clahe.apply(l_channel)

    enhanced_lab = cv2.merge(
        (enhanced_l, a_channel, b_channel)
    )

    enhanced = cv2.cvtColor(
        enhanced_lab,
        cv2.COLOR_LAB2BGR,
    )

    # Mild sharpening to improve text edges.
    blurred = cv2.GaussianBlur(
        enhanced,
        (0, 0),
        1.0,
    )

    sharpened = cv2.addWeighted(
        enhanced,
        1.25,
        blurred,
        -0.25,
        0,
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    success = cv2.imwrite(
        str(output_file),
        sharpened,
    )

    if not success:
        raise ValueError("Unable to save enhanced image.")

    return str(output_file)