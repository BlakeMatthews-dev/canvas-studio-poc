import asyncio
import base64
import io

import pytest
from PIL import Image


@pytest.fixture
def minimal_png_data_url():
    img = Image.new("RGBA", (64, 64), (128, 128, 128, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


@pytest.fixture
def fake_sheet_image(minimal_png_data_url):
    return minimal_png_data_url
