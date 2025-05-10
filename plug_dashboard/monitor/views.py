from django.shortcuts import render,redirect
from django.http import JsonResponse
from .models import plug_reading
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg
from django.db.models.functions import TruncHour
from collections import defaultdict
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required 

# Create your views here.

@login_required
def dashboard(response):
    return render(response,'monitor/dashboard.html')


def latest_reading(response):
    reading = plug_reading.objects.latest('timestamp')
    return JsonResponse({
        'today_runtime': reading.today_runtime,
        'month_runtime': reading.month_runtime,
        'today_energy': reading.today_energy,
        'month_energy': reading.month_energy
    })


def chart_data(response):
    today = timezone.now().date()
    reading = plug_reading.objects.order_by('-timestamp')[0:15][::-1]
    reading1 = plug_reading.objects.filter(timestamp__date=today).order_by('-timestamp')[::-1]
    return JsonResponse({
        'timestamps1': [r.timestamp for r in reading1],
        'timestamps': [r.timestamp for r in reading],
        'voltage': [r.voltage_mv for r in reading],
        'current': [r.current_ma for r in reading],
        'current_power': [r.current_power for r in reading],
        'energy_wh': [r.energy_wh for r in reading1]
    })


def heatmap_data(response):
    try:
        days = int(response.GET.get('days', 7))
        if days < 1:
            days = 1
    except ValueError:
        days = 7

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_time = today - timedelta(days=days - 1)


    readings = (
        plug_reading.objects
        .filter(timestamp__gte=start_time)
        .annotate(hour=TruncHour('timestamp'))
        .values('hour')
        .annotate(
            avg_voltage=Avg('voltage_mv'),
            avg_current=Avg('current_ma')
        )
        .order_by('hour')
    )

    from collections import defaultdict
    import numpy as np

    voltage_matrix = defaultdict(lambda: [None]*24)
    current_matrix = defaultdict(lambda: [None]*24)

    for r in readings:
        dt = r['hour']
        date_str = dt.strftime('%Y-%m-%d')
        hour = dt.hour
        voltage = (r['avg_voltage'] or 0)  
        current = r['avg_current'] or 0
        voltage_matrix[date_str][hour] = round(voltage, 2)
        current_matrix[date_str][hour] = round(current, 2)

    x_labels = sorted(voltage_matrix.keys())
    y_labels = list(range(24))
    voltage_values = [voltage_matrix[day] for day in x_labels]
    current_values = [current_matrix[day] for day in x_labels]

    return JsonResponse({
        'x_labels': x_labels,
        'y_labels': y_labels,
        'voltage_values': np.transpose(voltage_values).tolist(),
        'current_values': np.transpose(current_values).tolist()
    })

def loginn(response):
    if response.method == 'POST':
        form = AuthenticationForm(response, data=response.POST)
        if form.is_valid():
            user = form.get_user()
            login(response, user)
            print("Login successful, user:", user.username)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(response,'monitor/login.html', {'form': form})

@login_required
def home(response):
    return render(response,'monitor/home.html')

def logoutt(response):
    logout(response)
    return redirect('login')

def register(response):
    if response.method == 'POST':
        form = UserCreationForm(response.POST)
        if form.is_valid():
            user = form.save()
            login(response, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(response, 'monitor/register.html', {'form':form})

