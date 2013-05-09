#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Pydun.py - mapping tool
#copyright (c) 2013 WATAHIKI Hiroyuki
#url: http://sourceforge.jp/projects/pydun/
#email: hrwatahiki at gmail.com


import sys
import os.path
import codecs
import locale
import webbrowser
from PySide import QtCore, QtGui
import yaml


_mapengine = None
_mapimages = None
_undomanager = None

projecturl = "http://sourceforge.jp/projects/pydun/"
projectversion = "1.0.3"


class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        global _mapengine
        global _mapimages
        global _undomanager
        super(MainWindow, self).__init__(parent)

        _undomanager = UndoManager()
        _mapimages = MapImages()
        self.setmenu()
        _undomanager.changed.connect(self.updateundostate)

        self.new()
        if len(sys.argv) >= 2:
            self.open(unicode(sys.argv[1], locale.getpreferredencoding()))

        self.mainframe = MainFrame(self)
        self.setCentralWidget(self.mainframe)

        self.statusbar = QtGui.QStatusBar(self)
        self.statusbar.showMessage(u"")
        self.setStatusBar(self.statusbar)
        if "windowSize" in config:
            self.resize(
                QtCore.QSize(
                    config["windowSize"]["width"],
                    config["windowSize"]["height"]))

    def setmenu(self):
        #File menu
        filemenu = self.menuBar().addMenu(u"ファイル(&F)")

        newact = QtGui.QAction(u"新規(&N)", self)
        newact.triggered.connect(self.new_triggered)
        newact.setShortcut(QtGui.QKeySequence.New)
        filemenu.addAction(newact)

        openact = QtGui.QAction(u"開く(&O)...", self)
        openact.triggered.connect(self.open_triggered)
        openact.setShortcut(QtGui.QKeySequence.Open)
        filemenu.addAction(openact)

        saveact = QtGui.QAction(u"上書き保存(&S)", self)
        saveact.triggered.connect(self.save_triggered)
        saveact.setShortcut(QtGui.QKeySequence.Save)
        filemenu.addAction(saveact)

        saveasact = QtGui.QAction(u"名前をつけて保存(&A)...", self)
        saveasact.triggered.connect(self.saveas_triggered)
        saveasact.setShortcut(QtGui.QKeySequence.SaveAs)
        filemenu.addAction(saveasact)

        exitact = QtGui.QAction(u"終了(&E)", self)
        exitact.triggered.connect(self.exit_triggered)
        exitact.setShortcut(QtGui.QKeySequence.Quit)
        filemenu.addAction(exitact)

        #Edit menu
        editmenu = self.menuBar().addMenu(u"編集(&E)")
        self.undoact = QtGui.QAction(u"元に戻す(&U)", self)
        self.undoact.triggered.connect(self.undo_triggered)
        self.undoact.setShortcut(QtGui.QKeySequence.Undo)
        editmenu.addAction(self.undoact)
        self.redoact = QtGui.QAction(u"やり直し(&R)", self)
        self.redoact.triggered.connect(self.redo_triggered)
        self.redoact.setShortcut(QtGui.QKeySequence.Redo)
        editmenu.addAction(self.redoact)
        editmenu.addSeparator()
        setmapsizeact = QtGui.QAction(u"マップのサイズ(&S)", self)
        setmapsizeact.triggered.connect(self.setmapsize_triggered)
        editmenu.addAction(setmapsizeact)
        setorigineact = QtGui.QAction(u"座標設定(&O)", self)
        setorigineact.triggered.connect(self.setorigine_triggered)
        editmenu.addAction(setorigineact)

        #Help menu
        helpmenu = self.menuBar().addMenu(u"ヘルプ(&H)")
        tutorialact = QtGui.QAction(u"ヘルプの表示(&H)", self)
        tutorialact.triggered.connect(self.tutorial_triggered)
        tutorialact.setShortcut(QtGui.QKeySequence.HelpContents)
        helpmenu.addAction(tutorialact)
        projectact = QtGui.QAction(u"プロジェクトのWebサイト(&W)", self)
        projectact.triggered.connect(self.project_triggered)
        helpmenu.addAction(projectact)
        aboutact = QtGui.QAction(u"Pydunについて(&A)...", self)
        aboutact.triggered.connect(self.about_triggered)
        helpmenu.addAction(aboutact)

    @QtCore.Slot(bool, bool)
    def updateundostate(self, canundo, canredo):
        if canundo:
            self.undoact.setEnabled(True)
        else:
            self.undoact.setDisabled(True)
        if canredo:
            self.redoact.setEnabled(True)
        else:
            self.redoact.setDisabled(True)

    def setTitle(self, filename):
        if filename == None:
            s = u"新規作成"
        else:
            s = os.path.basename(filename)
        s ="Pydun - " + s
        self.setWindowTitle(s)

    @QtCore.Slot()
    def new_triggered(self):
        if QtGui.QMessageBox.Ok == QtGui.QMessageBox.question(
            self, u"確認", u"新しいマップを作成しますか?",
            (QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)):
            self.new()

    def new(self):
        global _mapengine
        _mapengine = MapEngine(20, 20, 1, -1, 0, +19)
        _undomanager.clear()
        _undomanager.save(_mapengine.savestring())
        self.setTitle(None)
        try:
            self.mainframe.mapframe.repaint()
        except:
            pass

    @QtCore.Slot()
    def open_triggered(self):
        d = ""
        try:
            d = os.path.dirname(_mapengine.filename)
        except:
            pass
        filename = QtGui.QFileDialog.getOpenFileName(
            dir=d,
            filter=u"*.pydun;;*.*", selectedFilter=u"*.pydun")
        if filename[0] != u"":
            self.open(filename[0])

    def open(self, filename):
        _mapengine.load(filename)
        _undomanager.clear()
        _undomanager.save(_mapengine.savestring())
        self.setTitle(_mapengine.filename)
        try:
            self.mainframe.mapframe.repaint()
        except:
            pass

    @QtCore.Slot()
    def save_triggered(self):
        if _mapengine.filename:
            self.save(_mapengine.filename)
        else:
            self.saveas_triggered()

    @QtCore.Slot()
    def saveas_triggered(self):
        d = ""
        try:
            d = os.path.dirname(_mapengine.filename)
        except:
            pass
        filename = QtGui.QFileDialog.getSaveFileName(
            dir=d,
            filter=u"*.pydun;;*.*", selectedFilter=u"*.pydun")
        if filename[0] != u"":
            self.save(filename[0])

    def save(self, filename):
        _mapengine.save(filename)
        self.setTitle(_mapengine.filename)

    @QtCore.Slot()
    def exit_triggered(self):
        self.close()

    def closeEvent(self, event):
        if self.exit():
            event.accept()
        else:
            event.ignore()

    def exit(self):
        global config
        global configfilename
        if QtGui.QMessageBox.Ok == QtGui.QMessageBox.question(
            self, u"確認", u"終了しますか?",
            (QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)):
            config["windowSize"] = dict()
            config["windowSize"]["width"] = self.size().width()
            config["windowSize"]["height"] = self.size().height()
            with open(configfilename, "w") as f:
                yaml.safe_dump(config, f, default_flow_style=False)
            sys.exit()
            return True
        return False

    @QtCore.Slot()
    def undo_triggered(self):
        global _mapengine
        _mapengine.loadfromstring(_undomanager.undo())
        self.mainframe.mapframe.repaint()

    @QtCore.Slot()
    def redo_triggered(self):
        global _mapengine
        _mapengine.loadfromstring(_undomanager.redo())
        self.mainframe.mapframe.repaint()

    @QtCore.Slot()
    def setorigine_triggered(self):
        title = u"座標設定"
        if self.mainframe.mapframe.setoriginemode:
            QtGui.QMessageBox.information(
                self, title, u"座標設定を中止します。", QtGui.QMessageBox.Ok)
            self.mainframe.mapframe.setoriginemode = False
        else:
            if QtGui.QMessageBox.Ok == QtGui.QMessageBox.information(
                self, title, u"基準にする地点をクリックしてください。",
                (QtGui.QMessageBox.Ok| QtGui.QMessageBox.Cancel)):
                self.mainframe.mapframe.setoriginemode = True

    @QtCore.Slot()
    def setmapsize_triggered(self):
        dlg = SetSizeDialog(self)
        dlg.setoriginalsize(_mapengine.width, _mapengine.height)
        dlg.exec_()
        if dlg.result() == QtGui.QDialog.Accepted:
            top, bottom, left, right = dlg.getsize()
            _mapengine.changesize(top, bottom, left, right)
            _undomanager.save(_mapengine.savestring())
            self.mainframe.mapframe.repaint()

    @QtCore.Slot()
    def tutorial_triggered(self):
        url = os.path.dirname(os.path.abspath(__file__)) + "/help/index.html"
        webbrowser.open_new_tab(url)

    @QtCore.Slot()
    def project_triggered(self):
        webbrowser.open_new_tab(projecturl)

    @QtCore.Slot()
    def about_triggered(self):
        QtGui.QMessageBox.about(self, "Pydun",
        u"<h1>Pydun.py "+ projectversion + "</h1>"
        u"<p>Copyright (c) 2013 WATAHIKI Hiroyuki</p>"
        u"<p>url: <a href='" + projecturl + "'>" + projecturl + "</a></p>"
        u"<p>e-mail: hrwatahiki at gmail.com</p>"
        u"<p>このソフトウェアはMITライセンスです。</p>"
        u"<p>このソフトウェアは以下のソフトウェアを使用しています。: "
        u"Python, PySide, PyYAML "
        u"これらの作成者に深く感謝いたします。</p>"
        u"<p>詳細はLICENCE.txtを参照してください。</p>")


class MainFrame(QtGui.QFrame):
    create_wall_menu_triggered_signal = QtCore.Signal(int, int, str, int)

    def __init__(self, parent=None):
        super(MainFrame, self).__init__(parent)

        self.mapframe = MapFrame(self)
        scrollarea = QtGui.QScrollArea(self)
        scrollarea.setWidget(self.mapframe)

        self.detail = QtGui.QLabel(self)
        self.detail.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.detail.setText(u"")
        self.detail.setMaximumHeight(100)
        self.detail.setMinimumHeight(100)

        self.boxdrawbutton = QtGui.QRadioButton(self)
        self.boxdrawbutton.setText(u"ボックス形式で壁を描画(&B)")
        self.boxdrawbutton.setChecked(True)
        self.boxdrawbutton.setSizePolicy(
            QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

        self.growdrawbutton = QtGui.QRadioButton(self)
        self.growdrawbutton.setText(u"足跡形式で壁を描画(&G)")
        self.growdrawbutton.setChecked(False)
        self.growdrawbutton.setSizePolicy(
            QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

        self.backcolorbutton = QtGui.QRadioButton(self)
        self.backcolorbutton.setText(u"背景色(&C)")
        self.backcolorbutton.setChecked(False)
        self.backcolorbutton.setSizePolicy(
            QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

        self.setbackcolorbutton = QtGui.QPushButton(self)
        self.setbackcolorbutton.setText(u"背景色を設定(&S)...")
        self.setbackcolorbutton.setSizePolicy(
            QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

        self.backcolorbox = ColorBox(self)
        self.backcolorbox.setMinimumSize(30, 30)
        self.backcolorbox.setSizePolicy(
            QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)


        layout = QtGui.QGridLayout(self)
        layout.addWidget(scrollarea, 0, 0, 1, 3)
        layout.addWidget(self.detail, 1, 0, 4, 1)
        layout.addWidget(self.boxdrawbutton, 1, 1, 1, 2)
        layout.addWidget(self.growdrawbutton, 2, 1, 1, 2)
        layout.addWidget(self.backcolorbutton, 3, 1, 1, 2)
        layout.addWidget(self.setbackcolorbutton, 4, 1, 1, 1)
        layout.addWidget(self.backcolorbox, 4, 2, 1, 1)

        self.setLayout(layout)

        self.h_wall_menu = self.create_wall_menu("h")
        self.v_wall_menu = self.create_wall_menu("v")

        self.mapframe.mouse_moved.connect(self.mouse_moved)
        self.mapframe.mouse_released.connect(self.mouse_released)
        self.mapframe.mouse_drag_released.connect(self.mouse_drag_released)
        self.create_wall_menu_triggered_signal.connect(
            self.create_wall_menu_triggered)
        self.setbackcolorbutton.clicked.connect(
            self.setbackcolorbutton_clicked)

    def create_wall_menu(self, direction):
        menu = QtGui.QMenu(self)
        for idx, img in enumerate(_mapimages.wall_icons):
            act = QtGui.QAction(self)
            act.setIcon(img[direction])

            def triggerd(idx):
                def emit():
                    self.create_wall_menu_triggered_signal.emit(menu.x, menu.y, direction, idx)
                return emit

            act.triggered.connect(triggerd(idx))
            menu.addAction(act)
        return menu

    @QtCore.Slot(int, int, int)
    def mouse_moved(self, x=0, y=0, b=QtCore.Qt.MouseButton.NoButton):
        cood = u"({x}, {y})\n".format(x=_mapengine.viewx(x), y=_mapengine.viewy(y))
        self.detail.setText(cood + _mapengine.getdetail(x, y))
        self.mapframe.repaint()

    @QtCore.Slot(int, int, int, int, int)
    def mouse_drag_released(self, x1, y1, x2, y2, eraseonly):
        if self.boxdrawbutton.isChecked():
            _mapengine.growwall(x1, y1, x2, y2, eraseonly, True)
        elif self.growdrawbutton.isChecked():
            _mapengine.growwall(x1, y1, x2, y2, eraseonly, False)
        elif self.backcolorbutton.isChecked():
            if eraseonly:
                backcolor = ""
            else:
                backcolor = getcolorstring(self.backcolorbox.color)
            _mapengine.fillbackcolor(x1, y1, x2, y2, backcolor)
        _undomanager.save(_mapengine.savestring())
        self.mapframe.repaint()

    @QtCore.Slot(int, int, str)
    def mouse_released(self, x1, y1, direction):
        #座標設定モード
        if self.mapframe.setoriginemode:
            dlg = SetOrigineDialog(self)
            dlg.setcurrent(_mapengine.viewx(x1), _mapengine.viewy(y1))
            dlg.exec_() #showでは処理がとまらない。
            if dlg.result() == QtGui.QDialog.Accepted:
                _mapengine.setoffset(
                    dlg.originex - _mapengine.viewx(x1) + _mapengine.offsetx,
                    dlg.originey - _mapengine.viewy(y1) + _mapengine.offsety
                )
                _undomanager.save(_mapengine.savestring())
            self.mapframe.setoriginemode = False
            return

        if direction == "c":
            dlg = DetailDialog(self)
            dlg.setvalue(_mapengine.viewx(x1), _mapengine.viewy(y1),
                _mapengine.getmark(x1, y1), _mapengine.getdetail(x1, y1),
                getcolorfromstring(_mapengine.getforecolor(x1, y1)))
            dlg.exec_() #showでは処理がとまらない。
            if dlg.result() == QtGui.QDialog.Accepted:
                forecolor = getcolorstring(dlg.forecolorbox.color)
                _mapengine.setmark(x1, y1, dlg.marktext.text())
                _mapengine.setdetail(x1, y1, dlg.detailtext.toPlainText())
                _mapengine.setforecolor(x1, y1, forecolor)
                _undomanager.save(_mapengine.savestring())
                self.mapframe.repaint()
            else:
                pass
        else:
            if direction == "h":
                menu = self.h_wall_menu
            elif direction == "v":
                menu = self.v_wall_menu
            menu.x = x1
            menu.y = y1
            menu.popup(QtGui.QCursor.pos())

    @QtCore.Slot(int, int, str, int)
    def create_wall_menu_triggered(self, x1, y1, direction, wall):
        _mapengine.setdata(x1, y1, direction, wall)
        _undomanager.save(_mapengine.savestring())
        self.mapframe.repaint()

    @QtCore.Slot()
    def setbackcolorbutton_clicked(self):
        global config
        dlg = PydunColorDialog(self, config.get("customColor", dict()))
        dlg.setCurrentColor(self.backcolorbox.color)
        dlg.exec_()
        config["customColor"] = dlg.config
        if dlg.result() == QtGui.QDialog.Accepted:
            self.backcolorbox.color = dlg.currentColor()
            self.backcolorbutton.setChecked(True)


class MapFrame(QtGui.QFrame):
    mouse_moved = QtCore.Signal(int, int, int)
    mouse_released = QtCore.Signal(int, int, str)
    mouse_drag_released = QtCore.Signal(int, int, int, int, int)
    global _mapengine
    global _mapimages

    def __init__(self, parent=None):
        super(MapFrame, self).__init__(parent)
        self._pressedbutton = QtCore.Qt.MouseButton.NoButton
        self._x1 = 0
        self._y1 = 0
        self._x2 = 0
        self._y2 = 0
        self._px1 = 0
        self._py1 = 0
        self._px2 = 0
        self._py2 = 0
        self._dragging = False
        self.setoriginemode = False
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.resize(
            _mapimages.width * (_mapengine.width) + _mapimages.widthoffset * 2,
            _mapimages.height * (_mapengine.height) + _mapimages.heightoffset * 2
        )

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.fillRect(0, 0, self.width(), self.height(), QtGui.QColor(255, 255, 255))
        w = _mapimages.width - 1
        v = _mapimages.height - 1
        ho = _mapimages.heightoffset
        wo = _mapimages.widthoffset

        #エリアサイズを再計算
        self.resize(
            w * (_mapengine.width) + _mapimages.widthoffset * 2,
            v * (_mapengine.height) + _mapimages.heightoffset * 2
        )

        #backcolor
        for x in range(_mapengine.width):
            xx = x * w
            for y in range(_mapengine.height):
                yy = y * v
                backcolor = _mapengine.getbackcolor(x, y)
                if backcolor:
                    painter.fillRect(wo + xx, ho + yy, w, v,
                        getcolorfromstring(backcolor))

        #grid
        for x in range(_mapengine.width + 1):
            xx = x * w
            for y in range(_mapengine.height + 1):
                yy = y * v
                if x != _mapengine.width:
                    painter.drawImage(wo + xx, yy,
                        _mapimages.wall(0, "h"))
                if y != _mapengine.height:
                    painter.drawImage(xx, ho + yy,
                        _mapimages.wall(0, "v"))

        #wall(gridは描画しない)
        for x in range(_mapengine.width + 1):
            xx = x * w
            for y in range(_mapengine.height + 1):
                yy = y * v
                if x != _mapengine.width and _mapengine.getdata(x, y, "h") != 0:
                    painter.drawImage(wo + xx, yy,
                        _mapimages.wall(_mapengine.getdata(x, y, "h"), "h"))
                if y != _mapengine.height and _mapengine.getdata(x, y, "v") != 0:
                    painter.drawImage(xx, ho + yy,
                        _mapimages.wall(_mapengine.getdata(x, y, "v"), "v"))
                mark = _mapengine.getmark(x, y)
                if mark != "":
                    painter.setPen(getcolorfromstring(_mapengine.getforecolor(x, y)))
                    painter.drawText(wo + xx + 2, ho + yy + 2, w - 2, v - 2,
                        QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter,
                        mark)

        #座標設定中はdrawing box を表示しない。
        if self.setoriginemode:
            return

        #drawing box
        if self._pressedbutton != QtCore.Qt.MouseButton.NoButton:
            if self._pressedbutton == QtCore.Qt.MouseButton.LeftButton:
                if self._x1 == self._x2 and self._y1 == self._y2:
                    painter.setPen(QtGui.QColor(255, 0, 0))
                elif self._x1 == self._x2 or self._y1 == self._y2:
                    painter.setPen(QtGui.QColor(0, 255, 0))
                else:
                    painter.setPen(QtGui.QColor(255, 0, 0))
            elif self._pressedbutton == QtCore.Qt.MouseButton.RightButton:
                painter.setPen(QtGui.QColor(0, 0, 255))
            painter.drawRect(self._px1, self._py1,
                self._px2 - self._px1, self._py2 - self._py1)

    def eventFilter(self, obj, event):
        def xpos():
            return ((event.pos().x() - _mapimages.widthoffset) // (_mapimages.width - 1))

        def ypos():
            return ((event.pos().y() - _mapimages.heightoffset) // (_mapimages.height - 1))

        if obj == self:
            et = event.type()

            if et == QtCore.QEvent.MouseButtonPress:
                self._x1 = xpos()
                self._y1 = ypos()
                self._pos1 = event.pos()
                self._px1 = event.pos().x()
                self._py1 = event.pos().y()
                self._x2 = xpos()
                self._y2 = ypos()
                self._px2 = event.pos().x()
                self._py2 = event.pos().y()
                self._pressedbutton = event.buttons()
                self._dragging = False
                return True

            elif et == QtCore.QEvent.MouseMove:
                self._x2 = xpos()
                self._y2 = ypos()
                self._px2 = event.pos().x()
                self._py2 = event.pos().y()
                if (self._pressedbutton != QtCore.Qt.MouseButton.NoButton and
                    (event.pos() - self._pos1).manhattanLength() >=
                     QtGui.QApplication.startDragDistance()):
                    self._dragging = True
                self.mouse_moved.emit(self._x2, self._y2, event.buttons())
                return True

            elif et == QtCore.QEvent.MouseButtonRelease:
                drag_emit = False
                release_emit = False
                if self._dragging:
                    drag_emit = True
                    if self._pressedbutton == QtCore.Qt.MouseButton.LeftButton:
                        eraseonly = False
                    elif self._pressedbutton == QtCore.Qt.MouseButton.RightButton:
                        eraseonly = True
                else:
                    release_emit = True
                if self.setoriginemode:
                    release_emit = True

                self._pressedbutton = QtCore.Qt.MouseButton.NoButton
                self._dragging = False
                if drag_emit:
                    self.mouse_drag_released.emit(
                        self._x1, self._y1, self._x2, self._y2, eraseonly)
                if release_emit:
                    rpx = self._px2 - self._x2 * (_mapimages.width - 1) - _mapimages.widthoffset
                    rpy = self._py2 - self._y2 * (_mapimages.height - 1) - _mapimages.heightoffset
                    rdx = rpx - (_mapimages.width - 1) // 2
                    rdy = rpy - (_mapimages.height - 1) // 2
                    if rpx <= _mapimages.widthoffset and abs(rdx) > abs(rdy):
                        rx = self._x2
                        ry = self._y2
                        d = "v"
                    elif rpx >= _mapimages.width - _mapimages.widthoffset and abs(rdx) > abs(rdy):
                        rx = self._x2 + 1
                        ry = self._y2
                        d = "v"
                    elif rpy <= _mapimages.heightoffset and abs(rdx) <= abs(rdy):
                        rx = self._x2
                        ry = self._y2
                        d = "h"
                    elif rpy >= _mapimages.height - _mapimages.heightoffset and abs(rdx) <= abs(rdy):
                        rx = self._x2
                        ry = self._y2 + 1
                        d = "h"
                    else:
                        rx = self._x2
                        ry = self._y2
                        d = "c"
                    self.mouse_released.emit(rx, ry, d)
                return True

            else:
                return False
        else:
            # pass the event on to the parent class
            return False


class ColorBox(QtGui.QFrame):
    def __init__(self, parent=None):
        super(ColorBox, self).__init__(parent)
        self.color = QtGui.QColor(255, 255, 255)
        self.bordercolor = QtGui.QColor(0, 0, 0)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.fillRect(0, 0, self.width(), self.height(), self.color)
        painter.setPen(self.bordercolor)
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)


class DetailDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(DetailDialog, self).__init__(parent)

        marklabel = QtGui.QLabel(self)
        marklabel.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        marklabel.setText(u"マーク(&M)")
        marklabel.setSizePolicy(
            QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

        self.marktext = QtGui.QLineEdit(self)
        self.marktext.setMaxLength(1)
        self.marktext.setText(u"")
        self.marktext.setMinimumWidth(20)
        self.marktext.setSizePolicy(
            QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        marklabel.setBuddy(self.marktext)

        self.forecolorbutton = QtGui.QPushButton(self)
        self.forecolorbutton.setText(u"文字色(&C)...")
        self.forecolorbutton.clicked.connect(self.forecolorbutton_clicked)

        self.forecolorbox = ColorBox(self)
        self.forecolorbox.setMinimumSize(30, 30)
        self.forecolorbox.setSizePolicy(
            QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

        detaillabel = QtGui.QLabel(self)
        detaillabel.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignRight)
        detaillabel.setText(u"詳細(&D)")

        self.detailtext = QtGui.QTextEdit(self)
        self.detailtext.setText(u"")
        detaillabel.setBuddy(self.detailtext)

        self.buttonBox = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout = QtGui.QGridLayout()
        layout.addWidget(marklabel, 0, 0, 1, 1)
        layout.addWidget(self.marktext, 0, 1, 1, 1)
        layout.addWidget(self.forecolorbutton, 0, 2, 1, 1)
        layout.addWidget(self.forecolorbox, 0, 3, 1, 1)
        layout.addWidget(detaillabel, 1, 0, 1, 1)
        layout.addWidget(self.detailtext, 1, 1, 1, 3)
        layout.addWidget(self.buttonBox, 2, 0, 1, 4)
        self.setLayout(layout)
        self.setModal(True)

    def setvalue(self, x, y, mark, detail, color):
        self.setWindowTitle("({x},{y})".format(x=x, y=y))
        self.marktext.setText(mark)
        self.detailtext.setText(detail)
        self.forecolorbox.color = color

    def forecolorbutton_clicked(self):
        global config
        dlg = PydunColorDialog(self, config.get("customColor", dict()))
        dlg.setCurrentColor(self.forecolorbox.color)
        dlg.exec_()
        config["customColor"] = dlg.config
        if dlg.result() == QtGui.QDialog.Accepted:
            self.forecolorbox.color = dlg.currentColor()

class SetOrigineDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(SetOrigineDialog, self).__init__(parent)
        self.setWindowTitle(u"座標設定")

        promptlabel = QtGui.QLabel(self)
        promptlabel.setAlignment(
            QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        promptlabel.setText(u"この地点の座標を入力してください。")

        self.currentlabel = QtGui.QLabel(self)
        self.currentlabel.setAlignment(
            QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        self.currentlabel.setText(u"")

        xlabel = QtGui.QLabel(self)
        xlabel.setAlignment(
            QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        xlabel.setText(u"&X")

        self.xbox = QtGui.QSpinBox(self)
        self.xbox.setRange(-999, +999)
        self.xbox.setSingleStep(1)
        self.xbox.setValue(0)
        xlabel.setBuddy(self.xbox)

        ylabel = QtGui.QLabel(self)
        ylabel.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        ylabel.setText(u"&Y")

        self.ybox = QtGui.QSpinBox(self)
        self.ybox.setRange(-999, +999)
        self.ybox.setSingleStep(1)
        self.ybox.setValue(0)
        ylabel.setBuddy(self.ybox)

        self.buttonBox = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout = QtGui.QGridLayout()
        layout.addWidget(promptlabel, 0, 0, 1, 4)
        layout.addWidget(self.currentlabel, 1, 0, 1, 4)
        layout.addWidget(xlabel, 2, 0, 1, 1)
        layout.addWidget(self.xbox, 2, 1, 1, 1)
        layout.addWidget(ylabel, 2, 2, 1, 1)
        layout.addWidget(self.ybox, 2, 3, 1, 1)
        layout.addWidget(self.buttonBox, 3, 0, 1, 4)
        self.setLayout(layout)
        self.setModal(True)

    def setcurrent(self, x, y):
        self.xbox.setValue(x)
        self.ybox.setValue(y)
        self.currentlabel.setText(u"現在の座標 ({x}, {y})".format(x=x, y=y))

    @property
    def originex(self):
        return self.xbox.value()

    @property
    def originey(self):
        return self.ybox.value()


class SetSizeDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(SetSizeDialog, self).__init__(parent)
        self.setWindowTitle(u"マップのサイズ")

        self.topbutton = QtGui.QRadioButton(self)
        self.topbutton.setText(u"上(&T)")
        self.topbutton.clicked.connect(self.updatewidgets)

        self.topsize = QtGui.QSpinBox(self)
        self.topsize.setSingleStep(1)
        self.topsize.setValue(0)
        self.topsize.valueChanged.connect(self.updatewidgets)

        self.bottombutton = QtGui.QRadioButton(self)
        self.bottombutton.setText(u"下(&B)")
        self.bottombutton.clicked.connect(self.updatewidgets)

        self.bottomsize = QtGui.QSpinBox(self)
        self.bottomsize.setSingleStep(1)
        self.bottomsize.setValue(0)
        self.bottomsize.valueChanged.connect(self.updatewidgets)

        self.leftbutton = QtGui.QRadioButton(self)
        self.leftbutton.setText(u"左(&L)")
        self.leftbutton.clicked.connect(self.updatewidgets)

        self.leftsize = QtGui.QSpinBox(self)
        self.leftsize.setSingleStep(1)
        self.leftsize.setValue(0)
        self.leftsize.valueChanged.connect(self.updatewidgets)

        self.rightbutton = QtGui.QRadioButton(self)
        self.rightbutton.setText(u"右(&R)")
        self.rightbutton.clicked.connect(self.updatewidgets)

        self.rightsize = QtGui.QSpinBox(self)
        self.rightsize.setSingleStep(1)
        self.rightsize.setValue(0)
        self.rightsize.valueChanged.connect(self.updatewidgets)

        self.sizelabel = QtGui.QLabel(self)
        self.sizelabel .setAlignment(
            QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        self.sizelabel.setText(u"この地点の座標を入力してください。")

        self.buttonbox = QtGui.QDialogButtonBox(
        QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        verticalgroup = QtGui.QButtonGroup(self)
        verticalgroup.addButton(self.topbutton)
        verticalgroup.addButton(self.bottombutton)

        holizontalgroup = QtGui.QButtonGroup(self)
        holizontalgroup.addButton(self.leftbutton)
        holizontalgroup.addButton(self.rightbutton)

        self.topbutton.setChecked(True)
        self.bottombutton.setChecked(False)
        self.leftbutton.setChecked(True)
        self.rightbutton.setChecked(False)

        layout = QtGui.QGridLayout(self)
        layout.addWidget(self.topbutton, 0, 2, 1, 1)
        layout.addWidget(self.topsize, 0, 3, 1, 1)
        layout.addWidget(self.leftbutton, 1, 0, 1, 1)
        layout.addWidget(self.leftsize, 1, 1, 1, 1)
        layout.addWidget(self.sizelabel, 1, 2, 1, 2)
        layout.addWidget(self.rightbutton, 1, 4, 1, 1)
        layout.addWidget(self.rightsize, 1, 5, 1, 1)
        layout.addWidget(self.bottombutton, 2, 2, 1, 1)
        layout.addWidget(self.bottomsize, 2, 3, 1, 1)
        layout.addWidget(self.buttonbox, 3, 0, 1, 6)
        self.setLayout(layout)
        self.setModal(True)

    def setoriginalsize(self, width, height):
        self._width = width
        self._height = height
        self.topsize.setRange(-height+1, +100)
        self.bottomsize.setRange(-height+1, +100)
        self.leftsize.setRange(-width+1, +100)
        self.rightsize.setRange(-width+1, +100)
        self.updatewidgets()

    def updatewidgets(self):
        dh = 0
        dw = 0

        if self.topbutton.isChecked():
            dh = self.topsize.value()
            self.topsize.setEnabled(True)
            self.bottomsize.setDisabled(True)
        elif self.bottombutton.isChecked():
            dh = self.bottomsize.value()
            self.topsize.setDisabled(True)
            self.bottomsize.setEnabled(True)
        if self.leftbutton.isChecked():
            dw = self.leftsize.value()
            self.leftsize.setEnabled(True)
            self.rightsize.setDisabled(True)
        elif self.rightbutton.isChecked():
            dw = self.rightsize.value()
            self.leftsize.setDisabled(True)
            self.rightsize.setEnabled(True)

        self.sizelabel.setText(
            u"変更前のサイズ: {w1} x {h1}\n変更後のサイズ: {w2} x {h2}".format(
                w1=self._width, h1=self._height,
                w2=self._width+dw, h2=self._height+dh))

    def getsize(self):
        top = 0
        bottom = 0
        left = 0
        right = 0
        if self.topbutton.isChecked():
            top = self.topsize.value()
        elif self.bottombutton.isChecked():
            bottom = self.bottomsize.value()
        if self.leftbutton.isChecked():
            left = self.leftsize.value()
        elif self.rightbutton.isChecked():
            right = self.rightsize.value()
        return (top, bottom, left, right)


class MapImages(object):
    def __init__(self):
        self.wall_images = list()
        self.wall_icons = list()
        for index in range(10):
            self.wall_images.append(dict())
            self.wall_icons.append(dict())
            for direction in ["v", "h"]:
                filename = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    u"images",
                    u"wall_{direction}_{index:02}.png".format(
                        direction=direction, index=index))
                self.wall_images[index][direction] = QtGui.QImage()
                self.wall_images[index][direction].load(filename)
                self.wall_icons[index][direction] = QtGui.QIcon(filename)

    @property
    def width(self):
        return self.wall_images[0]["h"].width()

    @property
    def height(self):
        return self.wall_images[0]["v"].height()

    @property
    def widthoffset(self):
        return self.wall_images[0]["v"].width()//2

    @property
    def heightoffset(self):
        return self.wall_images[0]["h"].height()//2

    def wall(self, index, direction):
        return self.wall_images[index][direction]


class MapEngine(object):
    hwall = " -#WMwmHVA"
    vwall = " |#PCpc=DG"

    def __init__(self, width, height, signx, signy, offsetx, offsety):
        self._width = width
        self._height = height
        self._signx = signx
        self._signy = signy
        self._offsetx = offsetx
        self._offsety = offsety
        self.filename = None

        self.initdata()
        self.inityaml()
        self._note = dict()

    def initdata(self):
        width = self.width + 1
        height = self.height + 1
        self._data = self.initialdata(width, height)

    def initialdata(self, width, height):
        dt = list()
        for x in range(width):
            dt.append(list())
            for y in range(height):
                dt[x].append(dict())
                for d in ["h", "v"]:
                    dt[x][y][d] = 0
        return dt

    def inityaml(self):
        #yaml !python/Unicode出力抑止おまじない
        def represent_unicode(dumper, data):
            return dumper.represent_scalar("tag:yaml.org,2002:str", data)
        def construct_unicode(loader, node):
            return unicode(loader.construct_scalar(node))
        yaml.add_representer(unicode, represent_unicode)
        yaml.add_constructor("tag:yaml.org,2002:str", construct_unicode)

    def getdata(self, x, y, direction):
        return self._data[x][y][direction]

    def setdata(self, x, y, direction, value):
        self._data[x][y][direction] = value

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def signx(self):
        return self._signx

    @property
    def signy(self):
        return self._signy

    @property
    def offsetx(self):
        return self._offsetx

    @property
    def offsety(self):
        return self._offsety

    def setoffset(self, x, y):
        self._offsetx = x
        self._offsety = y

    def getmark(self, x, y):
        return self.unescape(self.getnote(x, y)["mark"])

    def getdetail(self, x, y):
        return self.unescape(self.getnote(x, y)["detail"])

    def getforecolor(self, x, y):
        return self.getnote(x, y)["forecolor"]

    def getbackcolor(self, x, y):
        return self.getnote(x, y)["backcolor"]

    def getnote(self, x, y):
        return self._note.get(
            self.coodtokey(x, y), {"mark":u"", "detail":u"", "forecolor":u"#000000", "backcolor":u""})

    def coodtokey(self, x, y):
        return u"{x:+05d}_{y:+05d}".format(x=x, y=y)

    def keytocood(self, key):
        return map(int, key.split("_"))

    def setmark(self, x, y, mark):
        note = self.getnote(x, y)
        note["mark"] = self.escape(mark)
        self.setnote(x, y, note)

    def setdetail(self, x, y, detail):
        note = self.getnote(x, y)
        note["detail"] = self.escape(detail)
        self.setnote(x, y, note)

    def setforecolor(self, x, y, color):
        note = self.getnote(x, y)
        note["forecolor"] = color
        self.setnote(x, y, note)

    def setbackcolor(self, x, y, color):
        note = self.getnote(x, y)
        note["backcolor"] = color
        self.setnote(x, y, note)

    def setnote(self, x, y, note):
        self._note[self.coodtokey(x, y)] = note

    def escape(self, s):
        return s.replace("\\", "\\\\").replace("\n", r"\n")

    def unescape(self, s):
        return s.replace(r"\n", "\n").replace("\\\\", "\\")

    def viewx(self, x):
        return x * self.signx + self.offsetx

    def viewy(self, y):
        return y * self.signy + self.offsety

    def worldx(self, x):
        return (x - self.offsetx) / self.signx

    def worldy(self, y):
        return (y - self.offsety) / self.signy

    def changesize(self, top, bottom, left, right):
        oldoffsetx = max(-left, 0)
        newoffsetx = max(left, 0)
        newwidth = self.width + left + right
        oldoffsety = max(-top, 0)
        newoffsety = max(top, 0)
        newheight = self.height + top + bottom

        newdata = self.initialdata(newwidth + 1, newheight + 1)
        newnote = dict()
        for x in range(min(self._width, newwidth) + 1):
            for y in range(min(self._height, newheight) + 1):
                for d in ["h", "v"]:
                    newdata[x+newoffsetx][y+newoffsety][d] = self._data[x+oldoffsetx][y+oldoffsety][d]
                newnote[self.coodtokey(x+newoffsetx, y+newoffsety)] = self.getnote(x+oldoffsetx, y+oldoffsety)
        self._width = newwidth
        self._height = newheight
        self.setoffset(self.offsetx -self.signx * left, self.offsety -self.signy * top)
        self._data = newdata
        self._note = newnote

    def growwall(self, x1, y1, x2, y2, eraseonly, alwaysbox):
        stepx, stepy = self.getstep(x1, y1, x2, y2)
        offsetx, offsety = self.getoffset(x1, y1, x2, y2)

        #delete inner walls.
        for x in range(x1, x2+stepx, stepx):
            for y in range(y1+stepy+offsety, y2+stepy+offsety, stepy):
                self._data[x][y]["h"] = 0
        for x in range(x1+stepx+offsetx, x2+stepx+offsetx, stepx):
            for y in range(y1, y2+stepy, stepy):
                self._data[x][y]["v"] = 0

        if not eraseonly:
            #draw OUTER wall if it exists.
            if alwaysbox or (x1 == x2 and y1 == y2):
                hline = False
                vline = False
            elif x1 == x2:
                hline = True
                vline = False
            elif y1 == y2:
                hline = False
                vline = True
            else:
                hline = False
                vline = False

            for x in range(x1, x2+stepx, stepx):
                if not (vline and x == x1):
                    if not hline:
                        if self._data[x][y1+offsety]["h"] == 0:
                            self._data[x][y1+offsety]["h"] = 1
                    if self._data[x][y2+stepy+offsety]["h"] == 0:
                        self._data[x][y2+stepy+offsety]["h"] = 1
            for y in range(y1, y2+stepy, stepy):
                if not (hline and y == y1):
                    if not vline:
                        if self._data[x1+offsetx][y]["v"] == 0:
                            self._data[x1+offsetx][y]["v"] = 1
                    if self._data[x2+stepx+offsetx][y]["v"] == 0:
                        self._data[x2+stepx+offsetx][y]["v"] = 1

    def fillbackcolor(self, x1, y1, x2, y2, backcolor):
        stepx, stepy = self.getstep(x1, y1, x2, y2)
        for x in range(x1, x2+stepx, stepx):
            for y in range(y1, y2+stepy, stepy):
                self.setbackcolor(x, y, backcolor)

    def getstep(self, x1, y1, x2, y2):
        if x1 <= x2:
            stepx = 1
        else:
            stepx = -1
        if y1 <= y2:
            stepy = 1
        else:
            stepy = -1
        return (stepx, stepy)

    def getoffset(self, x1, y1, x2, y2):
        if x1 <= x2:
            offsetx = 0
        else:
            offsetx = 1
        if y1 <= y2:
            offsety = 0
        else:
            offsety = 1
        return (offsetx, offsety)

    def save(self, filename):
        dt = self.savestring()
        with codecs.open(filename, "w") as f:
            f.write(dt)
            self.filename = filename

    def savestring(self):
        data = dict()
        data["size"] = {"x":self.width, "y":self.height}
        data["offset"] = {"x":self.offsetx, "y":self.offsety}
        data["sign"] = {"x":self.signx, "y":self.signy}
        data["map"] = self.getmapstring()

        #noteは表示用に座標変換する。
        n = dict()
        for nk, ni in self._note.items():
            if ni["mark"] != "" or ni["detail"] != "" or ni["backcolor"]:
                x, y = self.keytocood(nk)
                n[self.coodtokey(self.viewx(x), self.viewy(y))] = ni
        data["note"] = n
        return yaml.safe_dump(data, allow_unicode=True,
                default_flow_style=False, encoding='utf-8')

    def getmapstring(self):
        #出力用マップ作成
        m = []
        for y in range(self.height):
            s = [" "]
            for x in range(self.width):
                s.append("+")
                s.append(self.hwall[self._data[x][y]["h"]])
            s.append("+")
            s.append(" ")
            m.append("".join(s))
            s = [" "]
            for x in range(self.width):
                s.append(self.vwall[self._data[x][y]["v"]])
                s.append(" ")
            s.append(self.vwall[self._data[self.width][y]["v"]])
            s.append(" ")
            m.append("".join(s))
        y = self.height
        s = [" "]
        for x in range(self.width):
            s.append("+")
            s.append(self.hwall[self._data[x][y]["h"]])
        s.append("+")
        s.append(" ")
        m.append("".join(s))
        return m

    def load(self, filename):
        with codecs.open(filename, "r", encoding="utf-8") as f:
            st = f.read()
        self.loadfromstring(st)
        self.filename = filename

    def loadfromstring(self, st):
        data = yaml.safe_load(st)

        #基本情報
        self._width = data["size"]["x"]
        self._height = data["size"]["y"]
        self._signx = data["sign"]["x"]
        self._signy = data["sign"]["y"]
        self._offsetx = data["offset"]["x"]
        self._offsety = data["offset"]["y"]

        #マップ
        self.initdata()
        for y in range(self.height):
            for x in range(self.width):
                self._data[x][y]["h"] = self.hwall.find(data["map"][y*2][1+x*2+1])
                self._data[x][y]["v"] = self.vwall.find(data["map"][y*2+1][1+x*2])
        x = self.width
        for y in range(self.height):
            self._data[x][y]["v"] = self.vwall.find(data["map"][y*2+1][1+x*2])
        y = self.height
        for x in range(self.width):
            self._data[x][y]["h"] = self.hwall.find(data["map"][y*2][1+x*2+1])

        #noteは内部用に座標変換する。
        n = dict()
        for nk, ni in data["note"].items():
            if ni["mark"] != "" or ni["detail"] != "" or ni["backcolor"] != "":
                x, y = self.keytocood(nk)
                n[self.coodtokey(self.worldx(x), self.worldy(y))] = ni

        self._note = n


class UndoManager(QtCore.QObject):
    MAX_UNDO_COUNT = 128
    changed = QtCore.Signal(bool, bool)

    def __init__(self):
        super(UndoManager, self).__init__()
        self.clear()

    def clear(self):
        self._undo = [None for x in range(self.MAX_UNDO_COUNT)]
        self._index = 0
        self._undocount = 0
        self.changed.emit(self.canundo, self.canredo)

    def save(self, obj):
        if self._index >= self.MAX_UNDO_COUNT:
            self._undo = self._undo[1:]
            self._index -= 1
            self._undo.append(None)
        self._undo[self._index] = obj
        self._index += 1
        self._undocount = 0
        self.changed.emit(self.canundo, self.canredo)

    def undo(self):
        self._index -= 1
        self._undocount += 1
        self.changed.emit(self.canundo, self.canredo)
        return self._undo[self._index - 1]

    def redo(self):
        self._index += 1
        self._undocount -= 1
        self.changed.emit(self.canundo, self.canredo)
        return self._undo[self._index - 1]

    @property
    def canundo(self):
        return (self._index > 1)

    @property
    def canredo(self):
        return (self._undocount > 0)


class PydunColorDialog(QtGui.QColorDialog):
    def __init__(self, parent, config):
        super(PydunColorDialog, self).__init__(parent)
        for index in range(self.customCount()):
            self.setCustomColor(index,
                getcolorfromstring(
                    config.get(index, "#FFFFFF")).rgb())
        self.updateconfig()

    def updateconfig(self):
        self._config = dict()
        for index in range(self.customCount()):
            self._config[index] = getcolorstring(
                QtGui.QColor.fromRgb(self.customColor(index)))

    def exec_(self):
        super(PydunColorDialog, self).exec_()
        self.updateconfig()

    @property
    def config(self):
        return self._config


def getcolorstring(color):
    return "#{r:02x}{g:02x}{b:02x}".format(r=color.red(), g=color.green(), b=color.blue())

def getcolorfromstring(colorstring):
    return QtGui.QColor.fromRgb(
        int(colorstring[1:3], 16),
        int(colorstring[3:5], 16),
        int(colorstring[5:7], 16))


def main():
    loadconfig()
    app = QtGui.QApplication(sys.argv)
    mainWin = MainWindow()
    app.installEventFilter(mainWin.centralWidget().mapframe)
    mainWin.show()
    sys.exit(app.exec_())

def loadconfig():
    global config
    global configfilename
    configfilename = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        u"Pydun.config")
    try:
        with open(configfilename, "r") as f:
            config = yaml.safe_load(f)
    except:
        config = dict()

if __name__ == '__main__':
    main()
