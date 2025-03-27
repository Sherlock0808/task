from django.urls import path
from .views import upload_file, results_view, file_history_view

urlpatterns = [
    path('', upload_file, name='upload_file'),
    path('results/<int:file_id>/', results_view, name='results'),
    path("history/", file_history_view, name="file_history"),
]
