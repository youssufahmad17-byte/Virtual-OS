import sys
sys.path.insert(0, '.')
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QMouseEvent
from core.kernel import Kernel
from gui.desktop import DesktopWidget, DesktopIcon

app = QApplication(sys.argv)
kernel = Kernel()
desktop = DesktopWidget(kernel)
desktop.resize(800, 600)
desktop.show()

print(f'Initial: {len(desktop._get_all_icons())} icons')
for w in desktop._get_all_icons():
    print(f'  {w.text_label.text()}: path={repr(w.item_path)}')

kernel.filesystem.mkdir('/home/user/Desktop/testfolder')
desktop.refresh_desktop()
app.processEvents()
print(f'After folder: {len(desktop._get_all_icons())} icons')

folder = [w for w in desktop.children() if isinstance(w, DesktopIcon) and w.item_path == '/home/user/Desktop/testfolder']
print(f'Folder found: {len(folder) > 0}')

# Test drag
if folder:
    f = folder[0]
    center = f.geometry().center()
    desktop.mousePressEvent(QMouseEvent(QMouseEvent.Type.MouseButtonPress, QPointF(center), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))
    desktop.mouseMoveEvent(QMouseEvent(QMouseEvent.Type.MouseMove, QPointF(500, 350), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))
    desktop.mouseReleaseEvent(QMouseEvent(QMouseEvent.Type.MouseButtonRelease, QPointF(500, 350), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))
    app.processEvents()
    print(f'After drag: pos={f.pos()}')

    for i in range(3):
        desktop.refresh_desktop()
        app.processEvents()

    folder_after = [w for w in desktop.children() if isinstance(w, DesktopIcon) and w.item_path == '/home/user/Desktop/testfolder']
    print(f'After ticks: {len(desktop._get_all_icons())} icons, folder pos={folder_after[0].pos() if folder_after else "GONE"}')
