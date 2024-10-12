"""
See:

https://community.plotly.com/t/adding-vertical-lines-when-clicking-on-graph/69272/18
"""

import sys

import threading

from PyQt5 import QtWidgets
from plotly import *
import dash
import dash_core_components as dcc
import dash_html_components as html
import sys
from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import QApplication
import numpy as np
import json
from dash.dependencies import Input, Output, State



def run_dash(data, layout):
    app = dash.Dash()

    app.layout = html.Div(children=[
        dcc.Graph(
            id='fig',
            figure={
                'data': data,
                'layout': layout
            }),dash.html.Div(id="debug"),
        ])
    
    @app.callback(
        Output("debug", "children"),
        Input("fig", "clickData"),
    )
    def point_clicked(clickData):
        print("point_clicked() !!!", "clickData:", clickData)
        clicked=[]
        clicked.append(clickData)

        
    app.run_server(debug=True, use_reloader=False)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):

        super(MainWindow, self).__init__()
        web = QWebEngineView()
        #web.load(QUrl("https://www.google.com"))
        web.load(QUrl("http://127.0.0.1:8050"))
        self.setCentralWidget(web)


if __name__ == '__main__':
    data = [
        {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
        {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': u'Montréal'},
    ]

    layout = {
        'title': 'Dash Data Visualization'
    }

    threading.Thread(target=run_dash, args=(data, layout), daemon=True).start()
    app = QtWidgets.QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())