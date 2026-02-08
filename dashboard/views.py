from django.shortcuts import render, redirect
from .utils import update_all_data
from .models import DashboardData
from .forms import UploadFileForm
import json
import datetime

def home(request):
    # 1. 處理檔案上傳
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # 讀取上傳的 JSON 檔案
                file_data = json.load(request.FILES['file'])
                # 存入資料庫
                DashboardData.objects.create(content=file_data)
                return redirect('home')
            except Exception as e:
                print(f"Upload error: {e}")
    else:
        form = UploadFileForm()

    # 2. 決定顯示數據來源
    # 優先從資料庫撈取最新的一筆
    latest_db_data = DashboardData.objects.first()
    
    context = {}
    data_source = "雲端爬蟲 (Live)"

    if latest_db_data:
        # 如果資料庫有資料，直接使用
        context = latest_db_data.content
        context['last_updated'] = latest_db_data.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        data_source = "本地上傳 (Uploaded)"
    else:
        # 資料庫是空的，執行原本的爬蟲 (Fallback)
        context = update_all_data()
        context['last_updated'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    context['form'] = form
    context['data_source'] = data_source
    
    return render(request, 'home.html', context)