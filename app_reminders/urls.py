from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'reminders', views.ReminderViewSet, basename='reminders')
router.register(r'quotes', views.MotivationalQuoteViewSet, basename='quotes')
router.register(r'achievements', views.AchievementViewSet, basename='achievements')

urlpatterns = [
    path('', include(router.urls)),
    path('quotes/random/', views.random_quote, name='random_quote'),
    path('reminders/check/', views.check_reminders, name='check_reminders'),
    path('achievements/earn/', views.earn_achievement, name='earn_achievement'),
]