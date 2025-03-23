from rest_framework import serializers
from .models import ActivitySummary, ProductivityInsight, LearningPattern


class ActivitySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivitySummary
        fields = ['id', 'user', 'period_type', 'start_date', 'end_date', 'activity_data',
                  'total_study_time', 'avg_daily_study_time', 'total_habits_completed',
                  'habit_completion_rate', 'pages_read', 'books_completed',
                  'goals_completed', 'goal_steps_completed', 'created_at']
        read_only_fields = ['created_at']


class ProductivityInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductivityInsight
        fields = ['id', 'user', 'insight_type', 'title', 'description', 'data', 'date_generated']
        read_only_fields = ['date_generated']


class LearningPatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningPattern
        fields = ['id', 'user', 'hourly_efficiency', 'weekday_efficiency', 
                  'location_efficiency', 'content_type_efficiency', 
                  'generated_at', 'updated_at']
        read_only_fields = ['generated_at', 'updated_at']