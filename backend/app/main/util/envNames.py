UPLOAD_FOLDER      = 'storageFiles'
VERSION            = "1.2"
ALLOWED_EXTENSIONS = ['docx', 'pdf', 'xlsx', 'xlsm', 'xls', 'html', 'txt','csv']

import os

path = os.path.join(os.getcwd(), UPLOAD_FOLDER)
