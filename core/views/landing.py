from django.http import FileResponse
import os
from django.conf import settings

def landing_page(request):
    file_path = os.path.join(settings.BASE_DIR, 'landing', 'index.html')
    return FileResponse(open(file_path, 'rb'))
