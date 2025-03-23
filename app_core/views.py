from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta

from .models import (
    LearningEntry, LearningTag, LearningAttachment,
    Habit, HabitLog,
    Book, BookNote,
    CalendarEvent, DailyJournal,
    Goal, GoalStep, GoalProgress,
    DashboardSetting, Widget
)
from .serializers import (
    LearningEntrySerializer, LearningTagSerializer, LearningAttachmentSerializer,
    HabitSerializer, HabitLogSerializer,
    BookSerializer, BookNoteSerializer,
    CalendarEventSerializer, DailyJournalSerializer,
    GoalSerializer, GoalStepSerializer, GoalProgressSerializer,
    DashboardSettingSerializer, WidgetSerializer
)


# 学習記録ビューセット
class LearningEntryViewSet(viewsets.ModelViewSet):
    """学習記録の管理用ビューセット"""
    serializer_class = LearningEntrySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """ログインユーザーの学習記録のみを取得"""
        return LearningEntry.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """作成時にユーザーを自動設定"""
        serializer.save(user=self.request.user)


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def learning_tags(request, entry_id):
    """学習記録のタグを管理するビュー"""
    entry = get_object_or_404(LearningEntry, id=entry_id, user=request.user)
    
    if request.method == 'GET':
        tags = entry.tags.all()
        serializer = LearningTagSerializer(tags, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = LearningTagSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(entry=entry)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        tag_id = request.data.get('tag_id')
        if tag_id:
            tag = get_object_or_404(LearningTag, id=tag_id, entry=entry)
            tag.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "tag_id is required"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def learning_attachments(request, entry_id):
    """学習記録の添付ファイルを管理するビュー"""
    entry = get_object_or_404(LearningEntry, id=entry_id, user=request.user)
    
    if request.method == 'GET':
        attachments = entry.attachments.all()
        serializer = LearningAttachmentSerializer(attachments, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = LearningAttachmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(entry=entry)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        attachment_id = request.data.get('attachment_id')
        if attachment_id:
            attachment = get_object_or_404(LearningAttachment, id=attachment_id, entry=entry)
            attachment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "attachment_id is required"}, status=status.HTTP_400_BAD_REQUEST)


# 習慣トラッキングビューセット
class HabitViewSet(viewsets.ModelViewSet):
    """習慣の管理用ビューセット"""
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """ログインユーザーの習慣のみを取得"""
        return Habit.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """作成時にユーザーを自動設定"""
        serializer.save(user=self.request.user)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def habit_logs(request, habit_id):
    """習慣の記録を管理するビュー"""
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)
    
    if request.method == 'GET':
        # クエリパラメータから日付範囲を取得
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        logs = habit.logs.all()
        
        if start_date:
            logs = logs.filter(log_date__gte=start_date)
        if end_date:
            logs = logs.filter(log_date__lte=end_date)
        
        serializer = HabitLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = HabitLogSerializer(data=request.data)
        if serializer.is_valid():
            # 同じ日の記録が既に存在する場合は更新
            log_date = serializer.validated_data['log_date']
            existing_log = HabitLog.objects.filter(habit=habit, log_date=log_date).first()
            
            if existing_log:
                update_serializer = HabitLogSerializer(existing_log, data=request.data)
                if update_serializer.is_valid():
                    update_serializer.save()
                    return Response(update_serializer.data)
                return Response(update_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save(habit=habit)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'PUT':
        log_id = request.data.get('log_id')
        if log_id:
            log = get_object_or_404(HabitLog, id=log_id, habit=habit)
            serializer = HabitLogSerializer(log, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "log_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        log_id = request.data.get('log_id')
        if log_id:
            log = get_object_or_404(HabitLog, id=log_id, habit=habit)
            log.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "log_id is required"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def habit_summary(request):
    """習慣のサマリー情報を取得するビュー"""
    # クエリパラメータから日付範囲を取得
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    # デフォルトでは過去30日間
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    habits = Habit.objects.filter(user=request.user, is_active=True)
    
    summary = []
    for habit in habits:
        logs = HabitLog.objects.filter(
            habit=habit,
            log_date__gte=start_date,
            log_date__lte=end_date
        )
        
        total_value = sum(log.value for log in logs)
        avg_value = total_value / logs.count() if logs.count() > 0 else 0
        completion_rate = logs.count() / (datetime.strptime(end_date, '%Y-%m-%d') - 
                                          datetime.strptime(start_date, '%Y-%m-%d')).days
        
        summary.append({
            'habit_id': habit.id,
            'habit_name': habit.name,
            'category': habit.category,
            'target_value': habit.target_value,
            'unit': habit.unit_of_measure,
            'total_value': total_value,
            'avg_value': avg_value,
            'completion_rate': completion_rate,
            'log_count': logs.count()
        })
    
    return Response(summary)


# 読書管理ビューセット
class BookViewSet(viewsets.ModelViewSet):
    """本の管理用ビューセット"""
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """ログインユーザーの本のみを取得"""
        return Book.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """作成時にユーザーを自動設定"""
        serializer.save(user=self.request.user)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def book_notes(request, book_id):
    """本のメモを管理するビュー"""
    book = get_object_or_404(Book, id=book_id, user=request.user)
    
    if request.method == 'GET':
        notes = book.notes.all()
        serializer = BookNoteSerializer(notes, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = BookNoteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(book=book)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'PUT':
        note_id = request.data.get('note_id')
        if note_id:
            note = get_object_or_404(BookNote, id=note_id, book=book)
            serializer = BookNoteSerializer(note, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "note_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        note_id = request.data.get('note_id')
        if note_id:
            note = get_object_or_404(BookNote, id=note_id, book=book)
            note.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "note_id is required"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def book_summary(request):
    """読書のサマリー情報を取得するビュー"""
    books = Book.objects.filter(user=request.user)
    
    summary = {
        'total_books': books.count(),
        'completed_books': books.filter(status='completed').count(),
        'in_progress_books': books.filter(status='in_progress').count(),
        'not_started_books': books.filter(status='not_started').count(),
        'total_pages_read': sum(
            book.current_page if book.current_page else 0 
            for book in books
        ),
        'average_rating': sum(
            book.rating for book in books if book.rating
        ) / books.filter(rating__isnull=False).count() if books.filter(rating__isnull=False).count() > 0 else 0,
        'recent_books': BookSerializer(
            books.order_by('-updated_at')[:5], many=True
        ).data
    }
    
    return Response(summary)


# カレンダービューセット
class CalendarEventViewSet(viewsets.ModelViewSet):
    """カレンダーイベントの管理用ビューセット"""
    serializer_class = CalendarEventSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """ログインユーザーのイベントのみを取得"""
        queryset = CalendarEvent.objects.filter(user=self.request.user)
        
        # クエリパラメータから日付範囲を取得
        start = self.request.query_params.get('start')
        end = self.request.query_params.get('end')
        
        if start:
            queryset = queryset.filter(start_time__gte=start)
        if end:
            queryset = queryset.filter(end_time__lte=end)
        
        return queryset
    
    def perform_create(self, serializer):
        """作成時にユーザーを自動設定"""
        serializer.save(user=self.request.user)


class DailyJournalViewSet(viewsets.ModelViewSet):
    """日記の管理用ビューセット"""
    serializer_class = DailyJournalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """ログインユーザーの日記のみを取得"""
        return DailyJournal.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """作成時にユーザーを自動設定"""
        serializer.save(user=self.request.user)


# 目標管理ビューセット
class GoalViewSet(viewsets.ModelViewSet):
    """目標の管理用ビューセット"""
    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """ログインユーザーの目標のみを取得"""
        # 親目標のみを取得するかどうか
        parent_only = self.request.query_params.get('parent_only', 'false').lower() == 'true'
        
        queryset = Goal.objects.filter(user=self.request.user)
        
        if parent_only:
            queryset = queryset.filter(parent_goal__isnull=True)
        
        return queryset
    
    def perform_create(self, serializer):
        """作成時にユーザーを自動設定"""
        serializer.save(user=self.request.user)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def goal_steps(request, goal_id):
    """目標のステップを管理するビュー"""
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    
    if request.method == 'GET':
        steps = goal.goal_steps.all()
        serializer = GoalStepSerializer(steps, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = GoalStepSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(goal=goal)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'PUT':
        step_id = request.data.get('step_id')
        if step_id:
            step = get_object_or_404(GoalStep, id=step_id, goal=goal)
            serializer = GoalStepSerializer(step, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "step_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        step_id = request.data.get('step_id')
        if step_id:
            step = get_object_or_404(GoalStep, id=step_id, goal=goal)
            step.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "step_id is required"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def goal_progress(request, goal_id):
    """目標の進捗を管理するビュー"""
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    
    if request.method == 'GET':
        progress_logs = goal.progress_logs.all()
        serializer = GoalProgressSerializer(progress_logs, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = GoalProgressSerializer(data=request.data)
        if serializer.is_valid():
            # 同じ日の進捗記録があれば更新
            log_date = serializer.validated_data['date']
            existing_log = GoalProgress.objects.filter(goal=goal, date=log_date).first()
            
            if existing_log:
                update_serializer = GoalProgressSerializer(existing_log, data=request.data)
                if update_serializer.is_valid():
                    update_serializer.save()
                    return Response(update_serializer.data)
                return Response(update_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            progress_log = serializer.save(goal=goal)
            
            # 目標の進捗率を更新
            goal.progress_percentage = progress_log.progress
            goal.save(update_fields=['progress_percentage'])
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ダッシュボード設定ビューセット
class DashboardSettingViewSet(viewsets.ModelViewSet):
    """ダッシュボード設定の管理用ビューセット"""
    serializer_class = DashboardSettingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """ログインユーザーの設定のみを取得"""
        return DashboardSetting.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """作成時にユーザーを自動設定"""
        serializer.save(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """既存の設定がある場合は作成せずに更新"""
        existing_setting = DashboardSetting.objects.filter(user=request.user).first()
        if existing_setting:
            serializer = self.get_serializer(existing_setting, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        
        return super().create(request, *args, **kwargs)


class WidgetViewSet(viewsets.ModelViewSet):
    """ウィジェットの管理用ビューセット"""
    serializer_class = WidgetSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """ログインユーザーのウィジェットのみを取得"""
        return Widget.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """作成時にユーザーを自動設定"""
        serializer.save(user=self.request.user)

# Create your views here.
