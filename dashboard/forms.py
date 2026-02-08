from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField(label='選擇由 GUI 產生的 JSON 檔案')