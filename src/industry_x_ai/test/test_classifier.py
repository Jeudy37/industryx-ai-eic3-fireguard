import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")
from industry_x_ai.classifier import classify_attributes, classify_image


def _img(color_rgb, shape, noise=0):
    im = np.full((240, 320, 3), (70, 70, 72), np.uint8)       # tapis gris
    if shape == "cube":
        cv2.rectangle(im, (140, 100), (180, 140), color_rgb, -1)
    else:
        cv2.circle(im, (160, 120), 21, color_rgb, -1)
    if noise:
        rng = np.random.default_rng(0)
        im = np.clip(im.astype(int) + rng.normal(0, noise, im.shape), 0, 255).astype(np.uint8)
    return im


@pytest.mark.parametrize("name,rgb,bin_", [("red", (225, 25, 25), "A"), ("green", (25, 180, 50), "B"), ("blue", (25, 75, 225), "C")])
@pytest.mark.parametrize("shape", ["cube", "cylinder"])
@pytest.mark.parametrize("noise", [0, 8])
def test_opencv_color_and_shape(name, rgb, bin_, shape, noise):
    r = classify_image(_img(rgb, shape, noise))
    assert r["color"] == name and r["shape"] == shape and r["bin"] == bin_


def test_empty_belt_returns_none():
    assert classify_image(np.full((240, 320, 3), (70, 70, 72), np.uint8)) is None


def test_attribute_rule():
    assert classify_attributes("blue", "cube")["bin"] == "C"
