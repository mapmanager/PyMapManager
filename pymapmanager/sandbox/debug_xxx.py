import sys
from qtpy import QtWidgets
import napari

app = QtWidgets.QApplication(sys.argv)

viewer = napari.Viewer()

myWidget = QtWidgets.QWidget()

# add widget to viewer
w1 = viewer.window.add_dock_widget(myWidget)

# toggle buttons in the dock (does not work)
w1.title.close_button.hide()
w1.title.hide_button.hide()

# run event loop
sys.exit(app.exec_())