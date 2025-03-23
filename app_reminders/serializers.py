from rest_framework import serializers
from .models import Reminder, MotivationalQuote, Achievement


class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = ['id', 'user', 'title', 'description', 'trigger_time', 'repeat_pattern',
                  'end_date', 'related_goal', 'related_habit', 'is_active',
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class MotivationalQuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = MotivationalQuote
        fields = ['id', 'content', 'author', 'source', 'category', 'created_at']
        read_only_fields = ['created_at']


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ['id', 'user', 'title', 'description', 'badge_type', 'icon', 'achieved_at']
        read_only_fields = ['achieved_at']