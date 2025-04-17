from pymapmanager.interface2.stackWidgets.base.editDataclass import EditDataClass
from pymapmanager.interface2.stackWidgets import stackWidget2

class ExperimentMetadata(EditDataClass):
    _widgetName = 'Experiment Metadata'
    def __init__(self, stackWidget: stackWidget2):
        super().__init__(stackWidget)
        # grab metadata from stack
        experimentMetadata = stackWidget.getStack().getMetadata().experimentMetadata
        # build gui
        self.setDataclass(experimentMetadata)