from adb_visual_mcp import actions


class FakeAdb:
    def __init__(self):
        self.calls = []

    def shell(self, command, serial=None, timeout=None, check=True):
        self.calls.append(command)
        return ""

    def screen_size(self, serial):
        return 1080, 2340

    @staticmethod
    def quote(text):
        return repr(text)


def test_click_and_keyboard():
    adb = FakeAdb()
    assert actions.click(adb, "fake", 10, 20, 2)["count"] == 2
    assert adb.calls == ["input tap 10 20", "input tap 10 20"]
    actions.keyboard(adb, "fake", "press", keys=["home", "back"])
    assert adb.calls[-1] == "input keyevent KEYCODE_HOME KEYCODE_BACK"


def test_drag_and_scroll():
    adb = FakeAdb()
    actions.mouse(adb, "fake", "drag", x=1, y=2, to_x=3, to_y=4, duration_ms=250)
    assert adb.calls[-1] == "input swipe 1 2 3 4 250"
    result = actions.mouse(adb, "fake", "scroll", delta=-120)
    assert result["steps"] == 1
