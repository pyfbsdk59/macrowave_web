from django.shortcuts import render, redirect
from django.contrib import messages
from .utils import update_all_data
from .models import DashboardData
from .forms import UploadFileForm
import json
import datetime

def home(request):
    """
    首頁：只負責「讀取」資料庫現有資料並顯示，不執行爬蟲。
    同時處理 JSON 檔案上傳。
    """
    # 1. 處理檔案上傳 (保留原有功能)
    if request.method == 'POST' and 'file' in request.FILES:
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file_data = json.load(request.FILES['file'])
                # 標記來源為 Upload
                file_data['source_type'] = 'JSON 上傳' 
                DashboardData.objects.create(content=file_data)
                messages.success(request, "JSON 檔案上傳並更新成功！")
                return redirect('home')
            except Exception as e:
                messages.error(request, f"上傳錯誤: {e}")
    else:
        form = UploadFileForm()

    # 2. 讀取資料庫最新一筆數據
    latest_db_data = DashboardData.objects.first() # 假設 Meta ordering = ['-updated_at']
    
    context = {}
    
    if latest_db_data:
        context = latest_db_data.content
        # 確保有 source_type 欄位，舊資料可能沒有
        source = context.get('source_type', '未知來源')
        time_str = latest_db_data.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        context['data_source_display'] = f"{source} (時間: {time_str})"
    else:
        context['data_source_display'] = "無數據 (請上傳檔案或點擊手動更新)"
        # 提供預設空值以免 Template 報錯
        context['us_jp_spread'] = {'us':0, 'jp':0, 'spread':0, 'status':'Safe'}
        context['metals'] = []
        context['mark17'] = []
        context['total_score'] = 0
        context['advice'] = "No Data"

    context['form'] = form
    return render(request, 'home.html', context)

def manual_scrape(request):
    """
    新視圖：專門執行線上爬蟲 (Render Server -> APIs)
    """
    if request.method == 'POST':
        try:
            # 呼叫 utils.py 中的爬蟲邏輯 (需確保 utils.py 不使用 Selenium)
            scraped_data = update_all_data()
            
            # 標記來源為 Crawler
            scraped_data['source_type'] = '雲端爬蟲'
            
            # 存入資料庫
            DashboardData.objects.create(content=scraped_data)
            messages.success(request, "雲端爬蟲更新成功！")
        except Exception as e:
            messages.error(request, f"更新失敗: {e}")
            
    return redirect('home')

from django.shortcuts import render, redirect
from django.http import JsonResponse # 新增
from django.views.decorators.csrf import csrf_exempt # 新增
from django.conf import settings # 新增
from .utils import update_all_data
from .models import DashboardData
from .forms import UploadFileForm
import json
import datetime

# ... (保留原本的 home 和 manual_scrape 函式不變) ...

@csrf_exempt  # 允許外部程式直接 POST，不需要網頁 token
def api_upload(request):
    """
    專門給 GUI 程式使用的上傳接口
    """
    if request.method == 'POST':
        # 1. 檢查密鑰 (安全性驗證)
        client_key = request.headers.get('X-Api-Key')
        # 如果是透過表單上傳，key 可能在 POST data 裡
        if not client_key:
            client_key = request.POST.get('api_key')

        if client_key != settings.API_UPLOAD_KEY:
            return JsonResponse({'status': 'error', 'message': '密鑰錯誤 (Invalid API Key)'}, status=403)

        try:
            # 2. 接收資料
            # 情境 A: 上傳的是檔案 (Multipart)
            if 'file' in request.FILES:
                file_data = json.load(request.FILES['file'])
                file_data['source_type'] = 'GUI 遠端上傳 (File)'
                DashboardData.objects.create(content=file_data)
                return JsonResponse({'status': 'success', 'message': '檔案上傳成功'})
            
            # 情境 B: 直接傳送 JSON 內容 (Raw Body)
            else:
                try:
                    json_data = json.loads(request.body)
                    json_data['source_type'] = 'GUI 遠端上傳 (Direct)'
                    DashboardData.objects.create(content=json_data)
                    return JsonResponse({'status': 'success', 'message': '數據同步成功'})
                except:
                    pass

            return JsonResponse({'status': 'error', 'message': '未找到有效數據'}, status=400)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)