from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class LearningEntry(models.Model):
    """学習記録エントリー"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='learning_entries',
        verbose_name=_('ユーザー')
    )
    title = models.CharField(_('タイトル'), max_length=255)
    content = models.TextField(_('内容'))
    category = models.CharField(_('カテゴリ'), max_length=100)
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)
    
    class Meta:
        verbose_name = _('学習記録')
        verbose_name_plural = _('学習記録')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class LearningTag(models.Model):
    """学習記録に付けるタグ"""
    
    entry = models.ForeignKey(
        LearningEntry, 
        on_delete=models.CASCADE, 
        related_name='tags',
        verbose_name=_('学習記録')
    )
    tag_name = models.CharField(_('タグ名'), max_length=50)
    
    class Meta:
        verbose_name = _('学習タグ')
        verbose_name_plural = _('学習タグ')
        unique_together = ('entry', 'tag_name')
    
    def __str__(self):
        return self.tag_name


class LearningAttachment(models.Model):
    """学習記録に添付するファイル"""
    
    entry = models.ForeignKey(
        LearningEntry, 
        on_delete=models.CASCADE, 
        related_name='attachments',
        verbose_name=_('学習記録')
    )
    file = models.FileField(_('ファイル'), upload_to='learning_attachments/')
    file_name = models.CharField(_('ファイル名'), max_length=255)
    uploaded_at = models.DateTimeField(_('アップロード日時'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('添付ファイル')
        verbose_name_plural = _('添付ファイル')
    
    def __str__(self):
        return self.file_name