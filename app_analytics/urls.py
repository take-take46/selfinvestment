from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'summaries', views.ActivitySummaryViewSet, basename='activity_summaries')
router.register(r'insights', views.ProductivityInsightViewSet, basename='insights')
router.register(r'patterns', views.LearningPatternViewSet, basename='learning_patterns')

urlpatterns = [
    path('', include(router.urls)),
    path('generate/summary/', views.generate_activity_summary, name='generate_summary'),
    path('generate/insights/', views.generate_insights, name='generate_insights'),
    path('analyze/patterns/', views.analyze_learning_patterns, name='analyze_patterns'),
]