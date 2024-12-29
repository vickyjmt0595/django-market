import csv

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .forms import FileUploadForm
from .models import UploadFile

from django.core.exceptions import ValidationError

# API related imports below
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from .serializer import FileUploadSerializer
# Create your views here.

def get_ema_data(decoded_file, file=False):
    if file:
        csv_file = open(decoded_file)
        csv_reader = csv.reader(csv_file, delimiter=',')
    else:
        csv_reader = csv.reader(decoded_file.splitlines())
    line_count = 0
    breadth_details = {}
    Date = []
    for row in csv_reader:
        if line_count:
            day_num, day, num_above_20_ema = (f'day{line_count}', row[0],
                                                row[5])
            breadth_details[day_num] = num_above_20_ema
            Date.append(day)
            line_count += 1
        else:
            line_count += 1
    if file:
        csv_file.close()

    return breadth_details, Date

def decide_market_status(last_5_values):
    day1, day2, day3, day4, day5 = [int(val)
                                    for val in
                                    last_5_values]
    if day1 >= 800:
        if (day1 > day2 > day3 > day4 > day5):
            if day1 < 1300:
                return('Light Green')
            if day1 > 1300:
                return('Bright Green')
                if day5 < 400:
                    return('Bright Green '
                           'Fresh Bullish trend possible')
        elif (day1 < day2 < day3 < max(day4, day5)):
            if day1 < 1200:
                return('Light Red')
            else:
                return('Bright to Light Green')
        elif all([(750 < int(val) < 1200) for val in last_5_values]):
            return('Yellow to Red')
        elif all([(900 < int(val) < 1300) for val in last_5_values]):
            return('Yellow to Green')
        elif all([(450 < int(val) < 1100) for val in last_5_values]):
            return('Red to Yellow')
        elif all([(1200 < int(val)) for val in last_5_values]):
            return('Light Green')
        else:
            return('Green to Yellow')
    elif day1 < 800:
        if (day1 < day2 < day3 < day4):
            return('Dark Red')
        elif (day1 > day2 > day3 > day4):
            return('Red to Yellow')
        else:
            return('Light Red')

        

def process_ema_data(twenty_ema_data, Date):
    num_days_data = 200
    ema_20_values = list(twenty_ema_data.values())[:num_days_data]
    ema_20_days = list(twenty_ema_data.keys())[:num_days_data]
    # ic(ema_20_values)
    # ic(ema_20_days) 
    data_size = len(ema_20_values)
    # Reverse the date to show latest in last
    Date.reverse()
    Date = Date[-num_days_data:]
    start_index = -5
    end_index = 0
    index = 0
    analysis = {}
    while index <= data_size-5:
        if not index:
            last_5_values = ema_20_values[start_index:]
        else:
            last_5_values = ema_20_values[start_index:end_index]
        days = ema_20_days[start_index]
        """
        print('---------------------------')
    
        print(days)
        print(Date[index+4])
        print(last_5_values[::-1])
        """
        status = decide_market_status(last_5_values)
        analysis[Date[index+4]] = {
            'day_num': days,
            'last_five_days': last_5_values[::-1],
            'status': status 
        }
        index += 1
        start_index -= 1
        end_index -= 1
    # Reverse the order to show latest date first
    return dict(reversed(analysis.items()))


def home(request):
    return render(request, 'breadth/home.html')

def upload_file_view(request):
    # Pass updated files to the template
    recent_files = UploadFile.objects.order_by('-id')[:10]
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']

            # Analyze the file
            if uploaded_file.name.endswith('.csv'):
                #return HttpResponse('Uploaded Successfully, will analyze later',
                #                    content_type='text/plain')
                try:
                    file_instance = UploadFile.objects.create(
                                           file=uploaded_file)
                    # file_instance.save()
                except ValidationError as err:
                    return HttpResponse(err,
                                        content_type='text/plain')
                decoded_file = file_instance.file.read().decode('utf-8')
                twenty_ema_data, Date = get_ema_data(decoded_file)
                analysis = process_ema_data(twenty_ema_data, Date)
                
                return render(request, 'breadth/file_analysis_result.html',
                              {'data': analysis}
                              )
            else:
                return render(request, 'breadth/file_upload.html',
                              {'form': form,
                               'error': 'Unsupported file type'
                               })
    else:
        form = FileUploadForm()
    
    return render(request, 'breadth/file_upload.html',
                  {'form': form,
                  'uploads': recent_files})

class FileUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    renderer_classes = [TemplateHTMLRenderer]

    def post(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_file = serializer.validated_data['file']

            # Save the file if needed
            # with open(f'media/uploads/{uploaded_file.name}', 'wb+') as destination:
            #    for chunk in uploaded_file.chunks():
            #        destination.write(chunk)
            if uploaded_file.name.endswith('.csv'):
                try:
                    file_instance = UploadFile.objects.create(
                                           file=uploaded_file)
                    file_instance.save()
                except ValidationError as err:
                    return HttpResponse(err,
                                        content_type='text/plain')
                print(file_instance.file.path)
                print(file_instance.file.url)
                decoded_file = uploaded_file.read().decode('utf-8')
                print(decoded_file)
                twenty_ema_data, Date = get_ema_data(file_instance.file.path,
                                                     file=True)
                print(twenty_ema_data)
                analysis = process_ema_data(twenty_ema_data, Date)
                # print({'data': analysis})
                return Response({'data': analysis},
                                template_name='breadth/file_analysis_result.html')
            else:
                return Response({'form': None,
                               'error': 'Unsupported file type'
                               }, template_name= 'breadth/file_upload.html')

            #return Response({'message': 'File uploaded successfully!', 'file_name': uploaded_file.name}, status=status.HTTP_201_CREATED)
            
        return Response({'error': 'Invalid form data'},
                        template_name= 'breadth/file_upload.html')
    
def file_analysis_view(request, slug):
    file_instance = get_object_or_404(UploadFile, slug=slug)
    decoded_file = file_instance.file.read().decode('utf-8')
    twenty_ema_data, Date = get_ema_data(decoded_file)
    analysis = process_ema_data(twenty_ema_data, Date)
    return render(request, 'breadth/file_analysis_result.html',
                  {'data': analysis})