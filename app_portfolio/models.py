from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class PortfolioReport(models.Model):
    """ポートフォリオレポートモデル"""
    
    REPORT_TYPE_CHOICES = [
        ('monthly', _('月次レポート')),
        ('quarterly', _('四半期レポート')),
        ('yearly', _('年次レポート')),
        ('custom', _('カスタムレポート')),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('html', 'HTML'),
        ('dashboard', _('ダッシュボード表示')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='portfolio_reports',
        verbose_name=_('ユーザー')
    )
    title = models.CharField(_('タイトル'), max_length=255)
    report_type = models.CharField(_('レポートタイプ'), max_length=20, choices=REPORT_TYPE_CHOICES)
    format = models.CharField(_('フォーマット'), max_length=20, choices=FORMAT_CHOICES, default='pdf')
    
    # 期間設定
    start_date = models.DateField(_('開始日'))
    end_date = models.DateField(_('終了日'))
    
    # レポート設定
    include_learning = models.BooleanField(_('学習記録を含める'), default=True)
    include_habits = models.BooleanField(_('習慣記録を含める'), default=True)
    include_books = models.BooleanField(_('読書記録を含める'), default=True)
    include_goals = models.BooleanField(_('目標進捗を含める'), default=True)
    include_analytics = models.BooleanField(_('分析データを含める'), default=True)
    
    # レポートファイル
    report_file = models.FileField(_('レポートファイル'), upload_to='portfolio_reports/', null=True, blank=True)
    
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    generated_at = models.DateTimeField(_('生成日時'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('ポートフォリオレポート')
        verbose_name_plural = _('ポートフォリオレポート')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class SkillMap(models.Model):
    """スキルマップモデル（学んだスキルの可視化）"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='skill_maps',
        verbose_name=_('ユーザー')
    )
    title = models.CharField(_('タイトル'), max_length=255)
    description = models.TextField(_('説明'), blank=True)
    
    # スキルマップデータ（JSONフィールド）
    skill_data = models.JSONField(_('スキルデータ'), default=dict)
    
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)
    
    class Meta:
        verbose_name = _('スキルマップ')
        verbose_name_plural = _('スキルマップ')
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.title


class LearningPath(models.Model):
    """学習パス・ロードマップモデル"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='learning_paths',
        verbose_name=_('ユーザー')
    )
    title = models.CharField(_('タイトル'), max_length=255)
    description = models.TextField(_('説明'), blank=True)
    
    # 進捗状況
    current_step = models.PositiveIntegerField(_('現在のステップ'), default=1)
    total_steps = models.PositiveIntegerField(_('総ステップ数'), default=1)
    
    start_date = models.DateField(_('開始日'), null=True, blank=True)
    target_end_date = models.DateField(_('目標終了日'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)
    
    class Meta:
        verbose_name = _('学習パス')
        verbose_name_plural = _('学習パス')
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.title


class LearningPathStep(models.Model):
    """学習パスのステップモデル"""
    
    learning_path = models.ForeignKey(
        LearningPath, 
        on_delete=models.CASCADE, 
        related_name='steps',
        verbose_name=_('学習パス')
    )
    title = models.CharField(_('タイトル'), max_length=255)
    description = models.TextField(_('説明'), blank=True)
    order = models.PositiveIntegerField(_('順序'), default=0)
    
    is_completed = models.BooleanField(_('完了'), default=False)
    completion_date = models.DateField(_('完了日'), null=True, blank=True)
    
    # 関連リソース（JSONフィールド）
    resources = models.JSONField(_('リソース'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)
    
    class Meta:
        verbose_name = _('学習パスステップ')
        verbose_name_plural = _('学習パスステップ')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.learning_path.title} - {self.title}"

# Create your models here.
