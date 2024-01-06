import pprint
from zipfile import ZipFile

# path = '/sandbox/server/pymapmanager-0.2.1-py3-none-any.whl'
# path = 'Users\johns\Documents\GitHub\PyMapManager\sandbox\server\johnson-ftpshare\pymapmanager-0.2.1-py3-none-any.whl'
# path = 'sandbox\server\johnson-ftpshare\DEFUNCT\pymapmanager-0.2.1-py3-none-any.whl'
path = 'sandbox\server\johnson-ftpshare\pymapmanager-0.2.1-py3-none-any.whl'
names = ZipFile(path).namelist()
pprint.pprint(names)