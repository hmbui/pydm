# Unit Tests for the PyDM drawing widgets

import pytest

from ...PyQt.QtGui import QApplication, QWidget, QColor, QPainter, QBrush, QPen, QPolygon, QPixmap, QStyle, QStyleOption
from ...PyQt.QtCore import pyqtProperty, Qt, QPoint, QSize, pyqtSlot

from ...widgets.base import PyDMWidget
from ...widgets.drawing import deg_to_qt, qt_to_deg, PyDMDrawing


@pytest.mark.parametrize("deg, expected_qt_deg", [
    (0, 0),
    (1, 16),
    (-1, -16),
])
def test_deg_to_qt(deg, expected_qt_deg):
    assert deg_to_qt(deg) == expected_qt_deg


@pytest.mark.parametrize("qt_deg, expected_deg", [
    (0, 0),
    (16, 1),
    (-16, -1),
    (-32.0, -2),
    (16.16, 1.01)
])
def test_qt_to_deg(qt_deg, expected_deg):
    assert qt_to_deg(qt_deg) == expected_deg


def test_pydmdrawing_construct(qtbot):
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    assert pydm_drawing.alarmSensitiveBorder is False
    assert pydm_drawing._rotation == 0.0
    assert pydm_drawing._brush.style() == Qt.SolidPattern
    assert pydm_drawing._default_color
    assert pydm_drawing._painter
    assert pydm_drawing._pen.style() == pydm_drawing._pen_style == Qt.NoPen
    assert pydm_drawing._pen_width == 0
    assert pydm_drawing._pen_color == QColor(0, 0, 0)


def test_pydmdrawing_sizeHint(qtbot):
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    assert pydm_drawing.sizeHint() == QSize(100, 100)


@pytest.mark.parametrize("alarm_sensitive_content", [
    True,
    False,
])
def test_pydmdrawing_paintEvent(qtbot, signals, test_alarm_style_sheet_map, alarm_sensitive_content):
    """
    Test the paintEvent handling of the widget. This test method will also execute PyDMDrawing alarm_severity_changed
    and draw_item().

    Parameters
    ----------
    qtbot
    signals
    test_alarm_style_sheet_map
    alarm_sensitive_content
    """
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    pydm_drawing.alarmSensitiveContent = alarm_sensitive_content
    signals.new_severity_signal.connect(pydm_drawing.alarmSeverityChanged)
    signals.new_severity_signal.emit(PyDMWidget.ALARM_MAJOR)

    with qtbot.waitExposed(pydm_drawing):
        pydm_drawing.show()
    pydm_drawing.setFocus()

    def wait_focus():
        return pydm_drawing.hasFocus()

    qtbot.waitUntil(wait_focus, timeout=5000)

    alarm_color = test_alarm_style_sheet_map[PyDMWidget.ALARM_CONTENT][pydm_drawing._alarm_state]

    if alarm_sensitive_content:
        assert pydm_drawing.brush.color() == QColor(alarm_color["color"])
    else:
        assert pydm_drawing.brush.color() == pydm_drawing._default_color


@pytest.mark.parametrize("widget_width, widget_height, expected_results", [
    (4.0, 4.0, (2.0, 2.0)),
    (1.0, 1.0, (0.5, 0.5)),
    (0, 0, (0, 0))
])
def test_pydmdrawing_get_center(qtbot, monkeypatch, widget_width, widget_height, expected_results):
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: widget_width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: widget_height)

    assert pydm_drawing.get_center() == expected_results


@pytest.mark.parametrize("width, height, rotation, pen_width, has_border, max_size, force_no_pen, expected", [
    # Zero rotation, with typical width, height, pen_width, and variable max_size, has_border, and force_no_pen
    # width > height
    (25.53, 10.35, 0, 2, True, True, True, (-12.765, -5.175, 25.53, 10.35)),
    (25.53, 10.35, 0, 2, True, True, False, (-12.765, -5.175, 25.53, 10.35)),
    (25.53, 10.35, 0, 2, True, False, True,  (-12.765, -5.175, 25.53, 10.35)),
    (25.53, 10.35, 0, 2, True, False, False,  (-12.765, -5.175, 25.53, 10.35)),
    (25.53, 10.35, 0, 2, False, True, True, (-12.765, -5.175, 25.53, 10.35)),
    (25.53, 10.35, 0, 2, False, True, False, (-12.765, -5.175, 25.53, 10.35)),
    (25.53, 10.35, 0, 2, False, False, True, (-12.765, -5.175, 25.53, 10.35)),

    # width < height
    (10.35, 25.53, 0, 2, True, True, True, (-5.175, -12.765, 10.35, 25.53)),
    (10.35, 25.53, 0, 2, True, True, False, (-5.175, -12.765, 10.35, 25.53)),
    (10.35, 25.53, 0, 2, True, False, True, (-5.175, -12.765, 10.35, 25.53)),
    (10.35, 25.53, 0, 2, True, False, False, (-5.175, -12.765, 10.35, 25.53)),
    (10.35, 25.53, 0, 2, False, True, True, (-5.175, -12.765, 10.35, 25.53)),
    (10.35, 25.53, 0, 2, False, True, False, (-5.175, -12.765, 10.35, 25.53)),
    (10.35, 25.53, 0, 2, False, False, True, (-5.175, -12.765, 10.35, 25.53)),

    # width == height
    (10.35, 10.35, 0, 2, True, True, True, (-5.175, -5.175, 10.35, 10.35)),

    # Variable rotation, max_size, and force_no_pen, has_border is True
    (25.53, 10.35, 45, 2, True, True, True, (-12.765, -5.175, 25.53, 10.35)),
    (25.53, 10.35, 90, 2, True, True, False, (-12.765, -5.175, 25.53, 10.35)),
    (25.53, 10.35, 180, 2, True, False, True, (-12.765, -5.175, 25.53, 10.35)),
    (25.53, 10.35, 270, 2, True, False, False, (-12.765, -5.175, 25.53, 10.35)),
    (25.53, 10.35, 360, 2, False, True, True, (-12.765, -5.175, 25.53, 10.35)),
    (25.53, 10.35, 0.72, 2, False, True, False, (-12.765, -5.175, 25.53, 10.35)),
    (25.53, 10.35, 71.333, 2, False, False, True, (-12.765, -5.175, 25.53, 10.35)),
])
def test_pydmdrawing_get_bounds(qtbot, monkeypatch, width, height, rotation, pen_width, has_border, max_size,
                                force_no_pen, expected):
    """
    Test the useful area calculations and compare the resulted tuple to the expected one
    Parameters
    ----------
    qtbot
    max_size
    force_no_pen
    expected
    """
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: height)
    monkeypatch.setattr(PyDMDrawing, "rotation", lambda *args: rotation)
    monkeypatch.setattr(PyDMDrawing, "penWidth", lambda *args: pen_width)

    if has_border:
        monkeypatch.setattr(PyDMDrawing, "has_border", lambda *args: True)
    else:
        monkeypatch.setattr(PyDMDrawing, "has_border", lambda *args: False)

    calculated_bounds = pydm_drawing.get_bounds(max_size, force_no_pen)
    assert calculated_bounds == expected


@pytest.mark.parametrize("pen_style, pen_width, expected_result", [
    (Qt.NoPen, 0, False),
    (Qt.NoPen, 1, False),
    (Qt.SolidLine, 0, False),
    (Qt.DashLine, 0, False),
    (Qt.SolidLine, 1, True),
    (Qt.DashLine, 10, True)
])
def test_pydmdrawing_has_border(qtbot, pen_style, pen_width, expected_result):
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    pydm_drawing.penStyle = pen_style
    pydm_drawing.penWidth = pen_width

    assert pydm_drawing.has_border() == expected_result


@pytest.mark.parametrize("width, height, expected_result", [
    (10, 15, False),
    (10.5, 22.333, False),
    (-10.333, -10.332, False),
    (10.333, 10.333, True),
    (-20.777, -20.777, True),
    (70, 70, True),
])
def test_pydmdrawing_is_square(qtbot, monkeypatch, width, height, expected_result):
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: height)

    assert pydm_drawing.is_square() == expected_result


@pytest.mark.parametrize("width, height, rotation, expected", [
    # Zero rotation, with typical width, height, pen_width, and variable max_size, has_border, and force_no_pen
    # width > height
    (25.53, 10.35, 0, (-12.765, -5.175, 25.53, 10.35)),
    (10.35, 25.53, 0, (-12.765, -5.175, 25.53, 10.35)),
    (25.53, 10.35, 45, (-12.765, -5.175, 25.53, 10.35)),
    (10.35, 25.53, 45, (-12.765, -5.175, 25.53, 10.35)),
    (10.35, 25.53, 360, (-12.765, -5.175, 25.53, 10.35)),
    (10.35, 25.53, -45, (-12.765, -5.175, 25.53, 10.35)),
    (10.35, 25.53, -270, (-12.765, -5.175, 25.53, 10.35)),
    (10.35, 25.53, -360, (-12.765, -5.175, 25.53, 10.35)),
])
def test_get_inner_max(qtbot, monkeypatch, width, height, rotation, expected):
    pydm_drawing = PyDMDrawing()
    qtbot.addWidget(pydm_drawing)

    monkeypatch.setattr(PyDMDrawing, "width", lambda *args: width)
    monkeypatch.setattr(PyDMDrawing, "height", lambda *args: height)
    monkeypatch.setattr(PyDMDrawing, "rotation", lambda *args: rotation)

    calculated_inner_max = pydm_drawing.get_inner_max()
    assert calculated_inner_max == expected
