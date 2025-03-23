from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class ActivitySummary(models.Model):
    """活動サマリー（日次・週次・月次の活動統計）"""
    
    PERIOD_CHOICES = [
        ('daily', _('日次')),
        ('weekly', _('週次')),
        ('monthly', _('月次')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='activity_summaries',
        verbose_name=_('ユーザー')
    )
    period_type = models.CharField(_('期間タイプ'), max_length=10, choices=PERIOD_CHOICES)
    start_date = models.DateField(_('開始日'))
    end_date = models.DateField(_('終了日'))
    
    # 活動統計データ（JSONフィールド）
    activity_data = models.JSONField(_('活動データ'), default=dict)
    
    # 学習時間統計
    total_study_time = models.PositiveIntegerField(_('総学習時間（分）'), default=0)
    avg_daily_study_time = models.FloatField(_('平均日次学習時間（分）'), default=0)
    
    # 習慣達成統計
    total_habits_completed = models.PositiveIntegerField(_('総習慣達成数'), default=0)
    habit_completion_rate = models.FloatField(_('習慣達成率'), default=0)
    
    # 読書統計
    pages_read = models.PositiveIntegerField(_('読んだページ数'), default=0)
    books_completed = models.PositiveIntegerField(_('読了した本の数'), default=0)
    
    # 目標進捗統計
    goals_completed = models.PositiveIntegerField(_('達成した目標数'), default=0)
    goal_steps_completed = models.PositiveIntegerField(_('達成した目標ステップ数'), default=0)
    
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('活動サマリー')
        verbose_name_plural = _('活動サマリー')
        unique_together = ('user', 'period_type', 'start_date')
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.user.username}の{self.get_period_type_display()} {self.start_date}〜{self.end_date}"


class ProductivityInsight(models.Model):
    """生産性インサイト（分析結果）"""
    
    INSIGHT_TYPE_CHOICES = [
        ('time_pattern', _('時間帯パターン')),
        ('correlation', _('相関分析')),
        ('trend', _('トレンド分析')),
        ('recommendation', _('推奨事項')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='productivity_insights',
        verbose_name=_('ユーザー')
    )
    insight_type = models.CharField(_('インサイトタイプ'), max_length=20, choices=INSIGHT_TYPE_CHOICES)
    title = models.CharField(_('タイトル'), max_length=255)
    description = models.TextField(_('説明'))
    data = models.JSONField(_('分析データ'), default=dict)
    date_generated = models.DateTimeField(_('生成日時'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('生産性インサイト')
        verbose_name_plural = _('生産性インサイト')
        ordering = ['-date_generated']
    
    def __str__(self):
        return f"{self.title} ({self.get_insight_type_display()})"


class LearningPattern(models.Model):
    """学習パターン分析結果"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='learning_patterns',
        verbose_name=_('ユーザー')
    )
    
    # 時間帯別効率データ
    hourly_efficiency = models.JSONField(_('時間帯別効率'), default=dict)
    
    # 曜日別効率データ
    weekday_efficiency = models.JSONField(_('曜日別効率'), default=dict)
    
    # 場所別効率データ（オプション）
    location_efficiency = models.JSONField(_('場所別効率'), null=True, blank=True)
    
    # コンテンツタイプ別効率
    content_type_efficiency = models.JSONField(_('コンテンツタイプ別効率'), null=True, blank=True)
    
    generated_at = models.DateTimeField(_('生成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)
    
    class Meta:
        verbose_name = _('学習パターン')
        verbose_name_plural = _('学習パターン')
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username}の学習パターン ({self.updated_at.strftime('%Y-%m-%d')})"

# Create your models here.
