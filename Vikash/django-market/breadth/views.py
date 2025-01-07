import csv

from datetime import datetime

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .forms import FileUploadForm
from .models import UploadFile, MarketBreadth

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
            day_num, day, num_above_20_ema = (f'{line_count}', row[0],
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
            return('Red')

        

def process_ema_data(twenty_ema_data, Date):
    num_days_data = len(Date)
    ema_20_values = list(twenty_ema_data.values())[:num_days_data]
    ema_20_days = list(twenty_ema_data.keys())[:num_days_data]
    # ic(ema_20_values)
    # ic(ema_20_days) 
    data_size = len(ema_20_values)
    Date = Date[-num_days_data:]
    formatted_dates = get_formatted_date(Date)
    # print(f'The formatted dates : {formatted_dates}')
    # Reverse the date to show latest in last
    formatted_dates.reverse()
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
        status = decide_market_status(last_5_values)
        analysis[formatted_dates[index+4]] = {
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
                # Update entry into db
                update_analysis_to_db(analysis)
                
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
                # Update entry into db
                update_analysis_to_db(analysis)
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

def update_analysis_to_db(data):
    for date, details in data.items():
        day_num = details['day_num']
        last_five_days = details['last_five_days']
        status = details['status']
        _,created = MarketBreadth.objects.get_or_create(date=date, day_num=day_num,
                                                last_five_days=last_five_days,
                                                status=status)
        if created:
            print(f'Created entry in table for {date}')

def get_formatted_date(date_list):
    seen_dates = dict()
    formatted_dates = []
    for date in date_list:
        formatted_date = convert_to_yyyy_mm_dd(date, seen_dates)
        # print(f'date is {date}, formatted date is {formatted_date}')
        formatted_dates.append(formatted_date)
    return formatted_dates


def convert_to_yyyy_mm_dd(date_str, seen_dates):
    """
    Converts a date string like '6th Jan' into 'YYYY-MM-DD' format.
    
    Parameters:
    - date_str (str): The date string in the format like '6th Jan'.
    - seen_dates (set): A set to track already seen dates.

    Returns:
    - str: The date in 'YYYY-MM-DD' format.
    """
    # Remove ordinal suffixes (e.g., '6th' -> '6')
    date_str = date_str.replace("st", "").replace("nd", "").replace("rd", "").replace("th", "")
    
    # Add the current year to the date string
    current_date = datetime.now()
    current_year = current_date.year
    
    # Attempt to parse the date using current date
    full_date_str = f"{date_str} {current_year}"
    
    # Convert to a datetime object
    try:
        date_obj = datetime.strptime(full_date_str, "%d %b %Y")
    except ValueError:
        # Handle invalid dates like 29th Feb in a non-leap year by falling back to the previous year
        full_date_str = f"{date_str} {current_year - 1}"
        try:
            date_obj = datetime.strptime(full_date_str, "%d %b %Y")
        except ValueError:
            print(f"Invalid date: {date_str} for both current and last year.")

    # Check if the date is in the future
    if date_obj > current_date:
        full_date_str = f"{date_str} {current_year - 1}"
        date_obj = datetime.strptime(full_date_str, "%d %b %Y")
    
    # Check if the date is on Market holidays
    if is_market_holiday(date_obj):
        date_obj = date_obj.replace(year=date_obj.year - 1)

    
    # Check how many times this date has been seen
    base_date = date_obj.strftime("%d-%b")  # Base date format to track day and month

    # Check if this date has already been seen
    if base_date in seen_dates:
        # Use the previous year if it's already seen
        year_adjustment = seen_dates[base_date]
        date_obj = date_obj.replace(year=date_obj.year - year_adjustment)
        seen_dates[base_date] += 1
    else:
        # First time seeing this date
        seen_dates[base_date] = 1

    # Return the formatted date
    return date_obj.strftime("%Y-%m-%d")

# Define market holidays (weekends or specific holidays)
def is_market_holiday(date_obj):
    """
    Checks if a given date is a market holiday (weekend or predefined holiday).
    """
    # Weekends (Saturday, Sunday)
    if date_obj.weekday() in (5, 6):  # 5 = Saturday, 6 = Sunday
        return True

    # Add predefined market holidays (example: New Year's Day, Independence Day, etc.)
    market_holidays = {

        # Add other holidays here...
    }
    if date_obj.date() in market_holidays:
        return True
    
    return False

    
def breadth_analysis_view(request, slug):
    file_instance = get_object_or_404(UploadFile, slug=slug)
    decoded_file = file_instance.file.read().decode('utf-8')
    twenty_ema_data, Date = get_ema_data(decoded_file)
    analysis = process_ema_data(twenty_ema_data, Date)
    # Update entry into db
    update_analysis_to_db(analysis)
    return render(request, 'breadth/file_analysis_result.html',
                  {'data': analysis})

def analysis_on_db_data(request):
    data = MarketBreadth.objects.all()
    return render(request, 'breadth/db_analysis_result.html',
                  {'data': data})