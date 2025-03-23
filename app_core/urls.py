from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'learning', views.LearningEntryViewSet, basename='learning')
router.register(r'habits', views.HabitViewSet, basename='habits')
router.register(r'books', views.BookViewSet, basename='books')
router.register(r'calendar', views.CalendarEventViewSet, basename='calendar')
router.register(r'journals', views.DailyJournalViewSet, basename='journals')
router.register(r'goals', views.GoalViewSet, basename='goals')
router.register(r'dashboard', views.DashboardSettingViewSet, basename='dashboard')
router.register(r'widgets', views.WidgetViewSet, basename='widgets')

urlpatterns = [
    path('', include(router.urls)),
    
    # 学習関連のエンドポイント
    path('learning/<int:entry_id>/tags/', views.learning_tags, name='learning_tags'),
    path('learning/<int:entry_id>/attachments/', views.learning_attachments, name='learning_attachments'),
    
    # 習慣関連のエンドポイント
    path('habits/<int:habit_id>/logs/', views.habit_logs, name='habit_logs'),
    path('habits/summary/', views.habit_summary, name='habit_summary'),
    
    # 本関連のエンドポイント
    path('books/<int:book_id>/notes/', views.book_notes, name='book_notes'),
    path('books/summary/', views.book_summary, name='book_summary'),
    
    # 目標関連のエンドポイント
    path('goals/<int:goal_id>/steps/', views.goal_steps, name='goal_steps'),
    path('goals/<int:goal_id>/progress/', views.goal_progress, name='goal_progress'),
]