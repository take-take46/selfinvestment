from rest_framework import serializers
from .models import PortfolioReport, SkillMap, LearningPath, LearningPathStep


class PortfolioReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioReport
        fields = ['id', 'user', 'title', 'report_type', 'format', 'start_date', 'end_date',
                  'include_learning', 'include_habits', 'include_books', 'include_goals',
                  'include_analytics', 'report_file', 'created_at', 'generated_at']
        read_only_fields = ['created_at', 'generated_at', 'report_file']


class SkillMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillMap
        fields = ['id', 'user', 'title', 'description', 'skill_data', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class LearningPathStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningPathStep
        fields = ['id', 'learning_path', 'title', 'description', 'order', 'is_completed',
                  'completion_date', 'resources', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class LearningPathSerializer(serializers.ModelSerializer):
    steps = LearningPathStepSerializer(many=True, read_only=True)
    
    class Meta:
        model = LearningPath
        fields = ['id', 'user', 'title', 'description', 'current_step', 'total_steps',
                  'start_date', 'target_end_date', 'created_at', 'updated_at', 'steps']
        read_only_fields = ['created_at', 'updated_at']