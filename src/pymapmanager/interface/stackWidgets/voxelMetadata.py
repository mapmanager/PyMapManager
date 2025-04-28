from pymapmanager.interface.stackWidgets.base.editDataclass import EditDataClass
from pymapmanager.interface.stackWidgets import stackWidget
from pymapmanager._logger import logger, setLogLevel

class VoxelMetadata(EditDataClass):
    # _widgetName = 'Voxel Metadata'
    def __init__(self, stackWidget: stackWidget):
        super().__init__(stackWidget)

        self._stackWidget = stackWidget
        # grab metadata from stack
        voxelMetadata = stackWidget.getStack().getMetadata().voxelMetadata
        # build gui
        self.setDataclass(voxelMetadata)
