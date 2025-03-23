from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'reports', views.PortfolioReportViewSet, basename='reports')
router.register(r'skills', views.SkillMapViewSet, basename='skills')
router.register(r'learning-paths', views.LearningPathViewSet, basename='learning_paths')

urlpatterns = [
    path('', include(router.urls)),
    path('reports/generate/', views.generate_report, name='generate_report'),
    path('reports/download/<int:report_id>/', views.download_report, name='download_report'),
    path('learning-paths/<int:path_id>/steps/', views.learning_path_steps, name='learning_path_steps'),
]
