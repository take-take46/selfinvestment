from rest_framework import serializers
from .models import (
    LearningEntry, LearningTag, LearningAttachment,
    Habit, HabitLog,
    Book, BookNote,
    CalendarEvent, DailyJournal,
    Goal, GoalStep, GoalProgress,
    DashboardSetting, Widget
)


# 学習記録シリアライザー
class LearningTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningTag
        fields = ['id', 'tag_name']


class LearningAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningAttachment
        fields = ['id', 'file', 'file_name', 'uploaded_at']


class LearningEntrySerializer(serializers.ModelSerializer):
    tags = LearningTagSerializer(many=True, read_only=True)
    attachments = LearningAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = LearningEntry
        fields = ['id', 'title', 'content', 'category', 'created_at', 'updated_at', 'tags', 'attachments']
        read_only_fields = ['created_at', 'updated_at']


# 習慣トラッキングシリアライザー
class HabitLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = HabitLog
        fields = ['id', 'log_date', 'value', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class HabitSerializer(serializers.ModelSerializer):
    logs = HabitLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = Habit
        fields = ['id', 'name', 'description', 'category', 'target_value', 'unit_of_measure', 
                  'created_at', 'is_active', 'logs']
        read_only_fields = ['created_at']


# 読書管理シリアライザー
class BookNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookNote
        fields = ['id', 'content', 'page_number', 'highlight', 'created_at']
        read_only_fields = ['created_at']


class BookSerializer(serializers.ModelSerializer):
    notes = BookNoteSerializer(many=True, read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'publisher', 'published_date', 'page_count',
                  'cover_image', 'description', 'status', 'start_date', 'finish_date', 'current_page',
                  'rating', 'review', 'created_at', 'updated_at', 'notes', 'progress_percentage']
        read_only_fields = ['created_at', 'updated_at']


# カレンダーシリアライザー
class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = ['id', 'title', 'description', 'start_time', 'end_time', 'all_day', 
                  'category', 'location', 'is_recurring', 'recurring_pattern', 'recurring_end_date',
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class DailyJournalSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyJournal
        fields = ['id', 'date', 'content', 'mood', 'productivity_rating', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


# 目標管理シリアライザー
class GoalStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalStep
        fields = ['id', 'title', 'description', 'order', 'is_completed', 'due_date', 
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class GoalProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalProgress
        fields = ['id', 'date', 'progress', 'notes', 'created_at']
        read_only_fields = ['created_at']


class GoalSerializer(serializers.ModelSerializer):
    goal_steps = GoalStepSerializer(many=True, read_only=True)
    progress_logs = GoalProgressSerializer(many=True, read_only=True)
    sub_goals = serializers.SerializerMethodField()
    
    class Meta:
        model = Goal
        fields = ['id', 'parent_goal', 'title', 'description', 'start_date', 'due_date',
                  'status', 'priority', 'progress_percentage', 'created_at', 'updated_at',
                  'goal_steps', 'progress_logs', 'sub_goals']
        read_only_fields = ['created_at', 'updated_at', 'progress_percentage']
    
    def get_sub_goals(self, obj):
        # 子目標を再帰的に取得しないようにシンプルなシリアライザーを使用
        sub_goals = obj.sub_goals.all()
        if sub_goals:
            return SimpleGoalSerializer(sub_goals, many=True).data
        return []


class SimpleGoalSerializer(serializers.ModelSerializer):
    """再帰を防ぐための簡易版ゴールシリアライザー"""
    class Meta:
        model = Goal
        fields = ['id', 'title', 'status', 'progress_percentage']


# ダッシュボード設定シリアライザー
class WidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Widget
        fields = ['id', 'widget_type', 'title', 'is_enabled', 'position', 'settings',
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class DashboardSettingSerializer(serializers.ModelSerializer):
    widgets = WidgetSerializer(many=True, read_only=True, source='user.widgets')
    
    class Meta:
        model = DashboardSetting
        fields = ['id', 'theme', 'default_view', 'widget_layout', 'show_streak_counts',
                  'show_goal_progress', 'show_habit_summary', 'show_reading_stats',
                  'created_at', 'updated_at', 'widgets']
        read_only_fields = ['created_at', 'updated_at']