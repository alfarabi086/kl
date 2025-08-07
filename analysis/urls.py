from django.urls import path
from .views import (
    UploadNetCDFView,
    WindStatisticsView,
    WindDistributionView,
    BestDistributionView,
    DistributionParametersView,
    EnergyPotentialView,
    WindDataFileListView,
    WindDataFileDetailView
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # File management
    path('files/', WindDataFileListView.as_view(), name='windfile-list'),
    path('files/<int:pk>/', WindDataFileDetailView.as_view(), name='windfile-detail'),
    
    # Analysis endpoints
    path('upload/', UploadNetCDFView.as_view(), name='upload-netcdf'),
    path('statistics/', WindStatisticsView.as_view(), name='wind-statistics'),
    path('distribution/', WindDistributionView.as_view(), name='wind-distribution'),
    path('best-distribution/', BestDistributionView.as_view(), name='best-distribution'),
    path('distribution-params/', DistributionParametersView.as_view(), name='distribution-params'),
    path('energy-potential/', EnergyPotentialView.as_view(), name='energy-potential'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
