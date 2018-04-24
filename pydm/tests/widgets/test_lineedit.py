# Unit Tests for the PyDMLineEdit Widget

import pytest
import numpy as np

import logging

from ...PyQt.QtGui import QMenu
from ...widgets.line_edit import PyDMLineEdit
from ... import utilities
from ...utilities import is_pydm_app
from ...widgets.display_format import DisplayFormat, parse_value_for_display


# --------------------
# POSITIVE TEST CASES
# --------------------

@pytest.mark.parametrize("init_channel", [
    "CA://MTEST",
    "",
    None,
])
def test_construct(qtbot, init_channel):
    pydm_lineedit = PyDMLineEdit(init_channel=init_channel)
    qtbot.addWidget(pydm_lineedit)

    assert pydm_lineedit.channel == str(init_channel)
    assert pydm_lineedit._display is None
    assert pydm_lineedit._scale == 1
    assert pydm_lineedit._prec == 0
    assert pydm_lineedit.isEnabled() == False
    assert pydm_lineedit.showUnits == False
    assert isinstance(pydm_lineedit.unitMenu, QMenu) and pydm_lineedit.unitMenu.title() == "Convert Units"
    assert pydm_lineedit.displayFormat == pydm_lineedit.DisplayFormat.Default
    assert (pydm_lineedit._string_encoding == pydm_lineedit.app.get_string_encoding()
            if utilities.is_pydm_app() else "utf_8")

    action_found = find_action_from_menu(pydm_lineedit.unitMenu, "No Unit Conversions found")
    assert action_found


@pytest.mark.parametrize("display_format", [
    (DisplayFormat.Default),
    (DisplayFormat.Exponential),
    (DisplayFormat.String),
    (DisplayFormat.Binary),
    (DisplayFormat.Decimal),
    (DisplayFormat.Hex),
])
def test_change_display_format_type(qtbot, display_format):
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit.displayFormat = display_format
    assert pydm_lineedit.displayFormat == display_format


@pytest.mark.parametrize("value, display_format, precision, scale, unit, show_unit, expected_display", [
    (123, DisplayFormat.Default, 3, 1, "s", True, "123.000 s"),
    (123.47, DisplayFormat.Decimal, 3, 2, "seconds", False, "246.94"),
    (1e2, DisplayFormat.Exponential, 2, 2, "light years", True, "2.00e+02 light years"),
    (0x1FF, DisplayFormat.Hex, 0, 1, "Me", True, "0x1ff Me"),
    (0b100, DisplayFormat.Binary, 0, 1, "KB", True, "0b100 KB"),
    (np.array([123, 456]), DisplayFormat.Default, 3, 2, "light years", True, "[123 456] light years"),
])
def test_value_change(qtbot, signals, value, display_format, precision, scale, unit, show_unit, expected_display):
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit.displayFormat = display_format
    pydm_lineedit._prec = precision
    pydm_lineedit._scale = scale
    pydm_lineedit.channeltype = type(value)
    pydm_lineedit._unit = unit
    pydm_lineedit.showUnits = show_unit

    signals.new_value_signal[type(value)].connect(pydm_lineedit.channelValueChanged)
    signals.new_value_signal[type(value)].emit(value)

    assert pydm_lineedit._display == expected_display


@pytest.mark.parametrize("internal_value, display_value, channel_type, display_format, precision, scale, unit,"
                         "show_units, expected_received_value", [
    (123, "123 s", int, DisplayFormat.Default, 0, 1, "s", True, 123),
    (123, "123 s", int, DisplayFormat.Default, 0, 3, "s", True, 123),
    (123, "123.000 s", float, DisplayFormat.Default, 3, 5, "s", True, 24.6),
    (123.45, "123.4500 s", float, DisplayFormat.Default, 4, 2, "s", True, 61.725),
    (123.45, "123.45 s", float, DisplayFormat.Decimal, 4, 2, "s", True, 61.725),
    ("abc", "abc s", str, DisplayFormat.Default, 3, 5, "s", True, "abc"),
    ("abc", "abc", str, DisplayFormat.String, 3, 5, "s", False, "abc"),
    (0x1FF, "0x1ff Me", int, DisplayFormat.Hex, 0, 1, "Me", True, 0x1ff),
    (0b100, "0b100 KB", int, DisplayFormat.Binary, 0, 1, "KB", True, 0b100),
    (np.array([20, 30]), "[20 30] light years", str, DisplayFormat.Default, 0, 10, "light years", True, "[20 30]"),
])
def test_send_value(qtbot, signals, internal_value, display_value, channel_type, display_format, precision, scale, unit,
                    show_units, expected_received_value):
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit.value = internal_value
    pydm_lineedit.setText(display_value)
    pydm_lineedit.channeltype = channel_type
    pydm_lineedit.displayFormat = display_format
    pydm_lineedit._prec = precision
    pydm_lineedit._scale = scale
    pydm_lineedit._unit = unit
    pydm_lineedit.showUnits = show_units

    # Besides receiving the new channel value, simulate the update of the new value to the widget by connecting the
    # channelValueChanged slot to the same signal
    pydm_lineedit.send_value_signal[channel_type].connect(signals.receiveValue)
    pydm_lineedit.send_value_signal[channel_type].connect(pydm_lineedit.channelValueChanged)
    pydm_lineedit.send_value()

    assert signals.value == expected_received_value
    assert pydm_lineedit.displayText() == display_value


@pytest.mark.parametrize("new_write_access, is_channel_connected, tooltip, is_app_read_only", [
    (True, True, "Write Access and Connected Channel", False),
    (False, True, "Only Connected Channel", False),
    (True, False, "Only Write Access", False),
    (False, False, "No Write Access and No Connected Channel", False),

    (True, True, "Write Access and Connected Channel", True),
    (False, True, "Only Connected Channel", True),
    (True, False, "Only Write Access", True),
    (False, False, "No Write Access and No Connected Channel", True),

    (True, True, "", False),
    (True, True, "", True),
])
def test_write_access_changed(qtbot, signals, new_write_access, is_channel_connected, tooltip, is_app_read_only):
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit.channel = "CA://MTEST"
    pydm_lineedit._conneted = is_channel_connected
    pydm_lineedit.setToolTip(tooltip)
    pydm_lineedit.app.__read_only = is_app_read_only

    signals.write_access_signal.connect(pydm_lineedit.writeAccessChanged)
    signals.write_access_signal.emit(new_write_access)

    # The widget is expected to be always enabled
    assert pydm_lineedit.isEnabled()
    assert pydm_lineedit.isReadOnly() == (not new_write_access)

    actual_tooltip = pydm_lineedit.toolTip()
    if not pydm_lineedit._connected:
        assert "PV is disconnected." in actual_tooltip
    elif not new_write_access:
        if is_pydm_app() and is_app_read_only:
            assert "Running PyDM on Read-Only mode." in actual_tooltip
        else:
            assert "Access denied by Channel Access Security." in actual_tooltip


@pytest.mark.parametrize("is_precision_from_pv, pv_precision, non_pv_precision", [
    (True, 1, 3),
    (False, 5, 3),
    (True, 6, 0),
    (True, 3, None),
    (False, 3, None),
])
def test_precision_change(qtbot, signals, is_precision_from_pv, pv_precision, non_pv_precision):
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit.precisionFromPV = is_precision_from_pv
    pydm_lineedit.precision = non_pv_precision

    if is_precision_from_pv:
        signals.prec_signal[type(pv_precision)].connect(pydm_lineedit.precisionChanged)
        signals.prec_signal.emit(pv_precision)

    if is_precision_from_pv:
        assert pydm_lineedit._prec == pv_precision
    else:
        assert pydm_lineedit._prec == non_pv_precision if non_pv_precision else pydm_lineedit._prec == 0


@pytest.mark.parametrize("new_unit", [
    "s",
    "light years",
    "",
])
def test_unit_change(qtbot, signals, new_unit):
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    signals.unit_signal[str].connect(pydm_lineedit.unitChanged)
    signals.unit_signal.emit(new_unit)

    assert pydm_lineedit._unit == new_unit


def find_action_from_menu(menu, action_name):
    for action in menu.actions():
        if action.menu():
            find_action_from_menu(action.menu())
        elif not action.isSeparator():
            if action_name == action.text():
                return True
    return False


@pytest.mark.parametrize("value, precision, unit, show_unit, expected_format_string", [
    (123, 0, "s", True, "{:.0f} s"),
    (123.456, 3, "mV", True, "{:.3f} mV"),
])
def test_apply_conversion(qtbot, value, precision, unit, show_unit, expected_format_string):
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit.value = value
    pydm_lineedit._unit = unit
    pydm_lineedit._prec = precision
    pydm_lineedit.showUnits = show_unit

    pydm_lineedit.apply_conversion(unit)
    assert pydm_lineedit.format_string == expected_format_string


# def test_widget_ctx_menu(qtbot, unit):
#     """
#     Call crate_unit_options before creating the context menu
#     Parameters
#     ----------
#     qtbot
#     unit
#
#     Returns
#     -------
#
#     """
#     pydm_lineedit = PyDMLineEdit()
#     qtbot.addWidget(pydm_lineedit)
#
#     pydm_lineedit._unit = unit
#     pydm_lineedit.create_unit_options()
#
#     menu = pydm_lineedit.widget_ctx_menu()
#     action_menu = menu.menuAction().menu()
#
#     units = utilities.find_unit_options(pydm_lineedit._unit)
#     for unit in units:
#         assert find_action_from_menu(action_menu, unit)
#
#
@pytest.mark.parametrize("value, has_focus, channel_type, display_format, precision, scale, unit, show_units", [
    (123, True, int, DisplayFormat.Default, 3, 1, "s", True),
    (123, False, int, DisplayFormat.Default, 3, 1, "s", True),
    (123, True, int, DisplayFormat.Default, 3, 1, "s", False),
    (123, False, int, DisplayFormat.Default, 3, 1, "s", False),
    (123.45, True, float, DisplayFormat.Decimal, 3, 2, "m", True),
    (1e3, True, int, DisplayFormat.Exponential, 2, 2, "GHz", True),
    (0x1FF, True, int, DisplayFormat.Hex, 0, 1, "Me", True),
    (0b100, True, int, DisplayFormat.Binary, 0, 1, "KB", True),
    (np.array([123, 456]), str, True, DisplayFormat.Default, 3, 2, "degree", True),
])
def test_set_display(qtbot, value, has_focus, channel_type, display_format, precision, scale, unit, show_units):
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit.value = value
    pydm_lineedit._unit = unit
    pydm_lineedit.displayFormat = display_format
    pydm_lineedit._scale = scale
    pydm_lineedit.channeltype = channel_type
    pydm_lineedit.showUnits = show_units
    pydm_lineedit._prec = precision

    pydm_lineedit.clearFocus()
    if has_focus:
        pydm_lineedit.setFocus()

    pydm_lineedit.set_display()

    new_value = value
    if not isinstance(value, (str, np.ndarray)):
        new_value *= pydm_lineedit.channeltype(pydm_lineedit._scale)

    new_value = parse_value_for_display(value=new_value, precision=precision, display_format_type=display_format,
                                        widget=pydm_lineedit)

    expected_display = str(new_value)
    if display_format == DisplayFormat.Default and not isinstance(value, np.ndarray):
        if isinstance(value, (int, float)):
            expected_display = str(pydm_lineedit.format_string.format(value))
    elif pydm_lineedit.showUnits:
        expected_display += " {}".format(unit)

    assert pydm_lineedit._display == expected_display


@pytest.mark.parametrize("display_value", [
    "123 s",
    "123.456 d",
    "",
])
def test_focus_out_event(qtbot, display_value):
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit._display = display_value
    pydm_lineedit.clearFocus()

    # Make sure the widget still retains the previously set value after the focusOut event
    assert pydm_lineedit._display == display_value


# --------------------
# NEGATIVE TEST CASES
# --------------------

@pytest.mark.parametrize("value, precision, initial_unit, unit, show_unit, expected", [
    (123, 0, None, int, True, "Warning: Attempting to convert PyDMLineEdit unit, but no initial units supplied"),
    (123.456, 3, float, int, True,
     "Warning: Attempting to convert PyDMLineEdit unit, but '<class 'float'>' can not be converted to "
     "'<class 'int'>'."),
    (123.456, 3, float, "foo", True,
      "Warning: Attempting to convert PyDMLineEdit unit, but '<class 'float'>' can not be converted to 'foo'."),
    ("123.456", 3, "light years", "light years", False,
     "Warning: Attempting to convert PyDMLineEdit unit, but 'light years' can not be converted to 'light years'."),
])
def test_apply_conversion_wrong_unit(qtbot, caplog, value, precision, initial_unit, unit, show_unit, expected):
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit.value = value
    pydm_lineedit._unit = initial_unit
    pydm_lineedit._prec = precision
    pydm_lineedit.showUnits = show_unit

    pydm_lineedit.apply_conversion(unit)

    for record in caplog.records:
        assert record.levelno == logging.WARNING
    assert expected in caplog.text



@pytest.mark.parametrize("internal_value, display_value, channel_type, display_format, precision, scale, unit,"
                         "show_units, expected", [
    (123, "123.000 s", int, DisplayFormat.Default, 3, 1, "s", True,
     "Error trying to set data '123.000 s' with type '<class 'int'>'"),
    (123, "120.000 s", int, DisplayFormat.Default, None, 3, "s", True,
      "Error trying to set data '120.000 s' with type '<class 'int'>'"),
    (123, "123.000 s", int, DisplayFormat.Default, 3, 4, "s", True,
     "Error trying to set data '123.000 s' with type '<class 'int'>'"),
])
def test_send_value(qtbot, signals, caplog, internal_value, display_value, channel_type, display_format, precision,
                    scale, unit, show_units, expected):
    pydm_lineedit = PyDMLineEdit()
    qtbot.addWidget(pydm_lineedit)

    pydm_lineedit.value = internal_value
    pydm_lineedit.setText(display_value)
    pydm_lineedit.channeltype = channel_type
    pydm_lineedit.displayFormat = display_format
    pydm_lineedit._prec = precision
    pydm_lineedit._scale = scale
    pydm_lineedit._unit = unit
    pydm_lineedit.showUnits = show_units

    # Besides receiving the new channel value, simulate the update of the new value to the widget by connecting the
    # channelValueChanged slot to the same signal
    pydm_lineedit.send_value_signal[channel_type].connect(signals.receiveValue)
    pydm_lineedit.send_value_signal[channel_type].connect(pydm_lineedit.channelValueChanged)

    if not precision:
        with pytest.raises(ValueError):
            pydm_lineedit.send_value()
    else:
        pydm_lineedit.send_value()

    for record in caplog.records:
        assert record.levelno == logging.ERROR
    assert expected in caplog.text
