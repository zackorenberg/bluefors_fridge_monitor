# Copy pasted from https://stackoverflow.com/questions/52615115/how-to-create-collapsible-box-in-pyqt
# Maybe I want to make it with tables? https://stackoverflow.com/questions/54385437/how-can-i-make-a-table-that-can-collapse-its-rows-into-categories-in-qt

from PyQt5 import QtCore, QtGui, QtWidgets
from localvars import *

ANIMATION_DURATION = 50 #500
class CollapsibleBox(QtWidgets.QWidget):
    collapseChangeState = QtCore.pyqtSignal()
    def __init__(self, title="", parent=None):
        super(CollapsibleBox, self).__init__(parent)

        self.toggle_button = QtWidgets.QToolButton(
            text=title, checkable=True, checked=False
        )
        self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        self.toggle_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonTextBesideIcon
        )
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow)
        self.toggle_button.pressed.connect(self.on_pressed)

        self.toggle_animation = QtCore.QParallelAnimationGroup(self)
        self.toggle_animation.finished.connect(self.on_animation_complete)
        self.content_area = QtWidgets.QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.content_area.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )

        self.content_area.setWidgetResizable(True)
        self.content_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        #self.content_area.setWidget(QtWidgets.QWidget())
        #self.content_area.setHorizontalScrollBar()
        #self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self.content_area, b"maximumHeight")
        )
        self.collapsed_width = (
                self.sizeHint().width() - self.content_area.sizeHint().width()
        )

    @QtCore.pyqtSlot()
    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(
            QtCore.Qt.DownArrow if not checked else QtCore.Qt.RightArrow
        )
        self.toggle_animation.setDirection(
            QtCore.QAbstractAnimation.Forward
            if not checked
            else QtCore.QAbstractAnimation.Backward
        )

        self.toggle_animation.start()

    def on_animation_complete(self):
        self.adjustMinimumWidth()
        self.collapseChangeState.emit()

    def adjustMinimumWidth(self):
        if self.toggle_button.isChecked() and ALLOW_SMALLER_CONTENT_WIDTH:
            #collapsed_width = (
            #        self.sizeHint().width() - self.content_area.sizeHint().width()
            #)
            self.content_area.setMinimumWidth(self.collapsed_width)
        elif not self.toggle_button.isChecked() and ALLOW_SMALLER_CONTENT_WIDTH:
            #self.content_area.adjustSize()
            content_width = self.content_widget.layout().minimumSize().width() + self.content_area.verticalScrollBar().sizeHint().width() + 2
            #content_width = self.content_widget.layout().sizeHint().width() + self.content_area.verticalScrollBar().sizeHint().width() + 2
            self.content_area.setMinimumWidth(content_width)
            #if content_width < self.content_area.width():
            #    self.content_area.resize(content_width, self.content_area.height())

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_widget = QtWidgets.QWidget()
        self.content_widget.setLayout(layout)
        #self.content_widget.setSizePolicy(
        #    QtWidgets.QSizePolicy.Minimum,
        #    QtWidgets.QSizePolicy.Minimum
        #)
        self.content_area.setWidget(self.content_widget)


        #self.content_area.setLayout(layout)
        self.content_area.setWidgetResizable(True)
        self.content_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.content_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        collapsed_height = (
            self.sizeHint().height() - self.content_area.maximumHeight()
        )
        collapsed_width = (
                self.sizeHint().width() - self.content_area.sizeHint().width()
        )
        content_height = min(MAX_COLLAPSEABLE_HEIGHT, layout.sizeHint().height() + self.content_area.horizontalScrollBar().sizeHint().height())
        content_width = layout.minimumSize().width() + self.content_area.verticalScrollBar().sizeHint().width() + 2

        # Can make it scrollable by lowering the content height, but may be better to make parent scrollable instead
        if ALLOW_SMALLER_CONTENT_WIDTH:
            self.content_area.setMinimumWidth(collapsed_width)
        else:
            #self.content_area.setMinimumWidth(layout.minimumSize().width() + self.content_area.verticalScrollBar().sizeHint().width())
            self.content_area.setMinimumWidth(content_width)

        #print(content_height)
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(ANIMATION_DURATION)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(ANIMATION_DURATION)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)


if __name__ == "__main__":
    import sys
    import random

    app = QtWidgets.QApplication(sys.argv)

    w = QtWidgets.QMainWindow()
    w.setCentralWidget(QtWidgets.QWidget())
    dock = QtWidgets.QDockWidget("Collapsible Demo")
    w.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)
    scroll = QtWidgets.QScrollArea()
    dock.setWidget(scroll)
    content = QtWidgets.QWidget()
    scroll.setWidget(content)
    scroll.setWidgetResizable(True)
    vlay = QtWidgets.QVBoxLayout(content)
    for i in range(10):
        box = CollapsibleBox("Collapsible Box Header-{}".format(i))
        vlay.addWidget(box)
        lay = QtWidgets.QVBoxLayout()
        for j in range(8):
            label = QtWidgets.QLabel("{}".format(j))
            color = QtGui.QColor(*[random.randint(0, 255) for _ in range(3)])
            label.setStyleSheet(
                "background-color: {}; color : white;".format(color.name())
            )
            label.setAlignment(QtCore.Qt.AlignCenter)
            lay.addWidget(label)

        box.setContentLayout(lay)
    vlay.addStretch()
    w.resize(640, 480)
    w.show()
    sys.exit(app.exec_())