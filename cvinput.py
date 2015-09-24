import cv2
import numpy as np

# cv2 events for the mouse
# cv2.EVENT_FLAG_ALTKEY    cv2.EVENT_LBUTTONDBLCLK  cv2.EVENT_MOUSEMOVE
# cv2.EVENT_FLAG_CTRLKEY   cv2.EVENT_LBUTTONDOWN    cv2.EVENT_RBUTTONDBLCLK
# cv2.EVENT_FLAG_LBUTTON   cv2.EVENT_LBUTTONUP      cv2.EVENT_RBUTTONDOWN
# cv2.EVENT_FLAG_MBUTTON   cv2.EVENT_MBUTTONDBLCLK  cv2.EVENT_RBUTTONUP
# cv2.EVENT_FLAG_RBUTTON   cv2.EVENT_MBUTTONDOWN
# cv2.EVENT_FLAG_SHIFTKEY  cv2.EVENT_MBUTTONUP

class Obj(object):
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            self.__setattr__(k,v)
    def __repr__(self):
        return str(self.__dict__)
    def __str__(self):
        return str(self.__dict__)

class WindowManager(object):
    """Simple and centralized window management for OpenCV"""
    def __init__(self):
        super(WindowManager, self).__init__()
        self.windows = {}
        self.last_key = 255

    def create(self, name, fullscreen = False):
        w = CVWindow(name)
        self.windows[name] = w
        if fullscreen:
            cv2.namedWindow(name, cv2.WINDOW_NORMAL)
            cv2.setWindowProperty(name,cv2.WND_PROP_FULLSCREEN, 1)
        else:
            cv2.namedWindow(name)
        cv2.setMouseCallback(name, w.mouse_event, param = name)
        return w

    def clear(self):
        cv2.destroyAllWindows()

    def event_loop(self, time = 1, close_with=[chr(27), 'q', 'Q']):
        for k,v in self.windows.items():
            v.events.clear()
        self.last_key = chr(cv2.waitKey(time) & 0xFF)
        return not (self.last_key in close_with)

    def destroy_all_windows(self):
        for name, v in self.windows.items():
            cv2.destroyWindow(name)

    def __getitem__(self, name):
        return self.windows[name]

class CVWindow(object):
    """Class to encapsulate all the mouse events and trackpad events"""
    def __init__(self, name):
        super(CVWindow, self).__init__()
        self.name = name
        self.mouse_pos = (0, 0)
        self.lb_down = False
        self.lb_drag_start = (-1,-1)
        self.rb_down = False
        self.rb_drag_start = (-1,-1)
        self.events = set()
        self.trackbars = {}

    def __str__(self):
        return str(self.__dict__)

    def mouse_event(self, event, x, y, flags, param):
        self.mouse_pos=(x,y)
        self.events.add(event)
        was_down = self.lb_down
        self.lb_down = event == cv2.EVENT_LBUTTONDOWN or was_down and cv2.EVENT_LBUTTONUP not in self.events
        was_down = self.rb_down
        self.rb_down = event == cv2.EVENT_RBUTTONDOWN or was_down and cv2.EVENT_RBUTTONUP not in self.events
        if event == cv2.EVENT_LBUTTONDOWN: self.lb_drag_start = (x,y)
        if not self.lb_down: self.lb_drag_start = (-1,-1)
        if event == cv2.EVENT_RBUTTONDOWN: self.rb_drag_start = (x,y)
        if not self.rb_down: self.rb_drag_start = (-1,-1)

    def show(self, img):
        cv2.imshow(self.name, img)

    def add_trackbar(self, name, default = 50, maxval = 100, allow_zero = True):
        self.trackbars[name] = default

        def trackpad_event(x):
            self.trackbars[name] = x
            if x==0 and not allow_zero:
                self.trackbars[name] = 1

        cv2.createTrackbar(name, self.name, default, maxval, trackpad_event)

    def __getitem__(self, name):
        return self.trackbars[name]

cvwindows = WindowManager()
