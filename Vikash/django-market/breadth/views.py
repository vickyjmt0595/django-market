from django.shortcuts import render
from django.http import HttpResponse
from .forms import FileUploadForm
# Create your views here.

def home(request):
    text_content = "This is a simple text file.\nIt contains some sample text."

    # Response 
    return HttpResponse(text_content, content_type='text/plain')

def upload_file_view(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']

            # Analyze the file
            if uploaded_file.name.endswith('.csv'):
                return HttpResponse('Uploaded Successfully, will analyze later',
                                    content_type='text/plain')
    else:
        form = FileUploadForm()
    
    return render(request, 'breadth/file_upload.html',
                  {'form': form})
            