import sys
from qtpy import QtWidgets
import napari

def _on_visibility_changed(visible : bool):
    print(f'_on_visibility_changed() visible: {visible}')
    # some code to ignore the hide (for my purposes)
    aDockWidget.setVisible(True)

app = QtWidgets.QApplication(sys.argv)

viewer = napari.Viewer()

myWidget = QtWidgets.QWidget()

# add_dock_widget() returns QtViewerDockWidget
aDockWidget = viewer.window.add_dock_widget(myWidget,
                      name='myWidget',
                      area='right',
                      )

aDockWidget._close_btn = False
aDockWidget._hide_btn = False # has no effect

aDockWidget.visibilityChanged.connect(_on_visibility_changed)

# run event loop
sys.exit(app.exec_())