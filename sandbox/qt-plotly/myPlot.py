import sys

from qtpy import QtWidgets, QtCore, QtWebEngineWidgets, QtWebChannel
import plotly.graph_objects as go
import plotly.express as px
from ipywidgets import Output, VBox

from IPython.display import display

def plot():
    # fig = go.Figure(data=[go.Scattergl(x=[1, 2, 3], y=[4, 5, 6])])
    x=[1, 2, 3]
    y=[4, 5, 6]
    fig = go.FigureWidget([go.Scatter(x=x, y=y, mode='markers')])

    scatter = fig.data[0]
    # scatter.on_click(update_point)

    fig.show()

out = Output()

class Backend(QtCore.QObject):
    pointChanged = QtCore.Signal(float, float)

    # @QtCore.Signal(float,float)
    def pointClicked(self, x, y):
        print(x, y)
        self.pointChanged.emit(x, y)

class Widget(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # self.button = QtWidgets.QPushButton('Plot', self)
        # self.browser = QtWebEngineWidgets.QWebEngineView(self)
        self.browser = QtWebEngineWidgets.QWebEngineView()

        # self.vlayout = QtWidgets.QVBoxLayout(self)
        # self.vlayout.addWidget(self.button, alignment=QtCore.Qt.AlignHCenter)
        # self.vlayout.addWidget(self.browser)

        # self.button.clicked.connect(self.show_graph)
        self.resize(1000,800)

        # self.show_graph()
        # self.plotToBrowser()
        self.plot2()

    # @QtCore.Signal(float,float)
    def onPointChanged(self, x, y):
        print("new points")
        print(x, y)

    def plot2(self):
        # map_view = QtWebEngineWidgets.QWebEngineView()

        backend = Backend(self)
        backend.pointChanged.connect(self.onPointChanged)
        channel = QtWebChannel.QWebChannel(self)
        channel.registerObject('backend', backend)
        self.browser.page().setWebChannel(channel)

        # file = QtCore.QDir.current().absoluteFilePath("index.html")
        # map_view.load(QtCore.QUrl.fromLocalFile(file))

        x=[1, 2, 3]
        y=[4, 5, 6]
        self.fig = go.FigureWidget([go.Scatter(x=x, y=y, mode='markers')])

        scatter = self.fig.data[0]
        scatter.on_click(self.update_point)

        self.browser.setHtml(self.fig.to_html(include_plotlyjs='cdn'))

        # show in browser
        # self.fig.show()
        display(self.fig)

        self.setCentralWidget(self.browser)

    @out.capture(clear_output=True)
    def update_point(self, trace, points, selector):
        print('!!!!')
 
    def show_graph(self):
        # df = px.data.tips()
        # fig = px.box(df, x="day", y="total_bill", color="smoker")
        # fig.update_traces(quartilemethod="exclusive") # or "inclusive", or "linear" by default

        x=[1, 2, 3]
        y=[4, 5, 6]
        fig = go.FigureWidget([go.Scatter(x=x, y=y, mode='markers')])

        scatter = fig.data[0]

        scatter.on_click(self.update_point)

        self.browser.setHtml(fig.to_html(include_plotlyjs='cdn'))

    def plotToBrowser(self):
        # fig = go.Figure(data=[go.Scattergl(x=[1, 2, 3], y=[4, 5, 6])])
        x=[1, 2, 3]
        y=[4, 5, 6]
        fig = go.FigureWidget([go.Scatter(x=x, y=y, mode='markers')])

        scatter = fig.data[0]

        #####
        # out = Output()
        # @out.capture(clear_output=True)
        # def update_point(trace, points, selector):
        #     print('!')

        scatter.on_click(self.update_point)

        # fig.show()
        display(fig)

        print('b')

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    widget = Widget()
    widget.show()
    app.exec()

    # plot()