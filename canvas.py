from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

CURSOR_DEFAULT = Qt.ArrowCursor
CURSOR_POINT = Qt.PointingHandCursor
CURSOR_DRAW = Qt.CrossCursor
CURSOR_MOVE = Qt.ClosedHandCursor
CURSOR_GRAB = Qt.OpenHandCursor

class Canvas(QWidget):
    def __init__(self, *args, **kwargs):
        super(Canvas, self).__init__(*args, **kwargs)
        self.drawingRectColor = QColor(0, 255, 0)
        self.drawingPointColor = QColor(255, 0, 0)
        self.pixmap = QPixmap()
        self._painter = QPainter(self)
        self._cursor = CURSOR_DEFAULT
        #跟踪鼠标
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)
        #产生小数
        self.scale = 1.0
        self.verified = False
        #要被 存入xml中的点坐标及矩形框点坐标
        self.points = []
        self.rectangles = []
        self.rectDrawing = False
        self.prevPoint = None

    def currentCursor(self):
        cursor = QApplication.overrideCursor()
        if cursor is not None:
            cursor = cursor.shape()
        return cursor

    def overrideCursor(self, cursor):
        self._cursor = cursor
        if self.currentCursor() is None:
            QApplication.setOverrideCursor(cursor)
        else:
            QApplication.changeOverrideCursor(cursor)
            
    def restoreCursor(self):
        QApplication.restoreOverrideCursor()
        
    def enterEvent(self, ev):
        self.overrideCursor(self._cursor)

    def leaveEvent(self, ev):
        self.restoreCursor()

    def focusOutEvent(self, ev):
        self.restoreCursor()

    #显示鼠标指的图片的哪个位置
    def transformPos(self, point):
        return point / self.scale - self.offsetToCenter()

    #鼠标移动要干的事
    def mouseMoveEvent(self, ev):
        pos = self.transformPos(ev.pos())
        window = self.parent().window()
        if window.filePath is not None:
            self.parent().window().labelCoordinates.setText('X: %d; Y: %d' %(pos.x(), pos.y()))
        self.overrideCursor(CURSOR_DRAW)
        self.prevPoint = pos
        if Qt.LeftButton & ev.buttons():
            self.rectangles[-1] = pos
        self.update()

    def mousePressEvent(self, ev):
        pos = self.transformPos(ev.pos())
        if ev.button() == Qt.LeftButton:
            self.rectDrawing = True
            self.rectangles.append(pos)
            self.rectangles.append(pos)
        if ev.button() == Qt.RightButton:
            self.points.append(pos)
        self.update()

    def mouseReleaseEvent(self, ev):
        pos = self.transformPos(ev.pos())
        if ev.button() == Qt.LeftButton:
            self.rectDrawing = False
            self.rectangles[-1] = pos
            self.update()
        if ev.button() == Qt.RightButton:
            pass
        
    def loadPixmap(self, pixmap):
        self.pixmap = pixmap
        self.repaint()

    def offsetToCenter(self):
        s = self.scale
        area = super(Canvas, self).size()
        w, h = self.pixmap.width() * s, self.pixmap.height() * s
        aw, ah = area.width(), area.height()
        x = (aw - w) / (2 * s) if aw > w else 0
        y = (ah - h) / (2 * s) if ah > h else 0
        return QPointF(x, y)

    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        if self.pixmap:
            return self.scale * self.pixmap.size()
        return super(Canvas, self).minimumSizeHint()

    #当有repaint()语句则调用此函数
    def paintEvent(self, event):
        if not self.pixmap:
            return super(Canvas, self).paintEvent(event)
        p = self._painter
        p.begin(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.HighQualityAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.scale(self.scale, self.scale)
        p.translate(self.offsetToCenter())
        p.drawPixmap(0, 0, self.pixmap)
        if self.prevPoint is not None:
            p.setPen(QColor(0, 0, 0))
            p.drawLine(self.prevPoint.x(), 0, self.prevPoint.x(), self.pixmap.height())
            p.drawLine(0, self.prevPoint.y(), self.pixmap.width(), self.prevPoint.y())
        if len(self.rectangles) > 0:
            for i in range(len(self.rectangles)//2):
                leftTop = self.rectangles[2*i]
                rightBottom = self.rectangles[2*i+1]
                rectWidth = abs(rightBottom.x() - leftTop.x())
                rectHeight = abs(rightBottom.y() - leftTop.y())
                p.setPen(self.drawingRectColor)
                brush = QBrush(Qt.BDiagPattern)
                p.setBrush(brush)
                p.drawRect(min(leftTop.x(), rightBottom.x()), min(leftTop.y(), rightBottom.y()), rectWidth, rectHeight)
        if len(self.points) > 0:
            for point in self.points:
                p.setPen(self.drawingPointColor)
                brush = QBrush(Qt.BDiagPattern)
                p.setBrush(brush)
                p.drawEllipse(point.x() - 2, point.y() - 2, 4, 4)
        p.end()

    def resetState(self):
        self.points.clear()
        self.rectangles.clear()
        #self.restoreCursor()
        #self.pixmap = None
        self.update()
