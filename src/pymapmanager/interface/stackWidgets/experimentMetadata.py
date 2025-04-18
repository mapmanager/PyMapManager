from pymapmanager.interface.stackWidgets.base.editDataclass import EditDataClass
from pymapmanager.interface.stackWidgets import stackWidget

class ExperimentMetadata(EditDataClass):
    _widgetName = 'Experiment Metadata'
    def __init__(self, stackWidget: stackWidget):
        super().__init__(stackWidget)
        # grab metadata from stack
        experimentMetadata = stackWidget.getStack().getMetadata().experimentMetadata
        # build gui
        self.setDataclass(experimentMetadata)