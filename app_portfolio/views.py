from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.utils import timezone
import os
import tempfile
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from io import BytesIO

from .models import PortfolioReport, SkillMap, LearningPath, LearningPathStep
from .serializers import (
    PortfolioReportSerializer, SkillMapSerializer, 
    LearningPathSerializer, LearningPathStepSerializer
)

from app_core.models import (
    LearningEntry, Habit, HabitLog, Book, Goal, GoalStep
)
from app_analytics.models import ActivitySummary


class PortfolioReportViewSet(viewsets.ModelViewSet):
    """ポートフォリオレポートの管理用ビューセット"""
    serializer_class = PortfolioReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """ログインユーザーのレポートのみを取得"""
        return PortfolioReport.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """作成時にユーザーを自動設定"""
        serializer.save(user=self.request.user)


class SkillMapViewSet(viewsets.ModelViewSet):
    """スキルマップの管理用ビューセット"""
    serializer_class = SkillMapSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """ログインユーザーのスキルマップのみを取得"""
        return SkillMap.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """作成時にユーザーを自動設定"""
        serializer.save(user=self.request.user)


class LearningPathViewSet(viewsets.ModelViewSet):
    """学習パスの管理用ビューセット"""
    serializer_class = LearningPathSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """ログインユーザーの学習パスのみを取得"""
        return LearningPath.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """作成時にユーザーを自動設定"""
        serializer.save(user=self.request.user)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def learning_path_steps(request, path_id):
    """学習パスのステップを管理するビュー"""
    learning_path = get_object_or_404(LearningPath, id=path_id, user=request.user)
    
    if request.method == 'GET':
        steps = learning_path.steps.all().order_by('order')
        serializer = LearningPathStepSerializer(steps, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = LearningPathStepSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(learning_path=learning_path)
            
            # 総ステップ数を更新
            learning_path.total_steps = learning_path.steps.count()
            learning_path.save(update_fields=['total_steps'])
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'PUT':
        step_id = request.data.get('step_id')
        if step_id:
            step = get_object_or_404(LearningPathStep, id=step_id, learning_path=learning_path)
            serializer = LearningPathStepSerializer(step, data=request.data)
            if serializer.is_valid():
                serializer.save()
                
                # ステップの完了状態が変更された場合、現在のステップを更新
                if 'is_completed' in request.data and request.data['is_completed']:
                    update_learning_path_progress(learning_path)
                
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "step_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        step_id = request.data.get('step_id')
        if step_id:
            step = get_object_or_404(LearningPathStep, id=step_id, learning_path=learning_path)
            step.delete()
            
            # 総ステップ数と現在のステップを更新
            learning_path.total_steps = learning_path.steps.count()
            update_learning_path_progress(learning_path)
            learning_path.save(update_fields=['total_steps', 'current_step'])
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "step_id is required"}, status=status.HTTP_400_BAD_REQUEST)


def update_learning_path_progress(learning_path):
    """学習パスの進捗状況を更新する関数"""
    steps = learning_path.steps.all().order_by('order')
    
    completed_steps = 0
    for step in steps:
        if step.is_completed:
            completed_steps += 1
    
    if completed_steps == 0:
        current_step = 1
    else:
        # 次のステップを特定
        for i, step in enumerate(steps, 1):
            if not step.is_completed:
                current_step = i
                break
        else:
            # 全てのステップが完了している場合
            current_step = len(steps)
    
    learning_path.current_step = current_step
    learning_path.save(update_fields=['current_step'])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_report(request):
    """ポートフォリオレポートを生成するAPI"""
    # リクエストデータの取得
    report_data = {
        'title': request.data.get('title', f"{request.user.username}のポートフォリオレポート"),
        'report_type': request.data.get('report_type', 'monthly'),
        'format': request.data.get('format', 'pdf'),
        'start_date': request.data.get('start_date'),
        'end_date': request.data.get('end_date'),
        'include_learning': request.data.get('include_learning', True),
        'include_habits': request.data.get('include_habits', True),
        'include_books': request.data.get('include_books', True),
        'include_goals': request.data.get('include_goals', True),
        'include_analytics': request.data.get('include_analytics', True),
    }
    
    # 日付範囲のデフォルト値設定
    if not report_data['start_date'] or not report_data['end_date']:
        end_date = datetime.now().date()
        
        if report_data['report_type'] == 'monthly':
            # 月次レポート: 先月1ヶ月分
            start_date = end_date.replace(day=1) - timedelta(days=1)
            start_date = start_date.replace(day=1)
        elif report_data['report_type'] == 'quarterly':
            # 四半期レポート: 過去3ヶ月分
            start_date = end_date - timedelta(days=90)
        elif report_data['report_type'] == 'yearly':
            # 年次レポート: 過去1年分
            start_date = end_date.replace(year=end_date.year-1, month=end_date.month, day=end_date.day)
        else:  # custom
            # デフォルトでは過去30日分
            start_date = end_date - timedelta(days=30)
        
        report_data['start_date'] = start_date.strftime('%Y-%m-%d')
        report_data['end_date'] = end_date.strftime('%Y-%m-%d')
    
    # レポートの作成または更新
    report, created = PortfolioReport.objects.get_or_create(
        user=request.user,
        title=report_data['title'],
        report_type=report_data['report_type'],
        defaults=report_data
    )
    
    if not created:
        # 既存のレポートを更新
        for key, value in report_data.items():
            setattr(report, key, value)
        report.save()
    
    # レポートの生成
    if report_data['format'] == 'pdf':
        generate_pdf_report(report)
    
    # 生成日時を更新
    report.generated_at = timezone.now()
    report.save(update_fields=['generated_at'])
    
    serializer = PortfolioReportSerializer(report)
    return Response(serializer.data)


def generate_pdf_report(report):
    """PDFレポートを生成する関数"""
    start_date = datetime.strptime(report.start_date.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
    end_date = datetime.strptime(report.end_date.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
    
    # 一時ファイルを作成
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_filepath = temp_file.name
    
    # PDFファイルの作成
    with PdfPages(temp_filepath) as pdf:
        # タイトルページ
        plt.figure(figsize=(8.5, 11))
        plt.axis('off')
        plt.text(0.5, 0.8, report.title, fontsize=24, ha='center')
        plt.text(0.5, 0.7, f"期間: {start_date} 〜 {end_date}", fontsize=16, ha='center')
        plt.text(0.5, 0.6, f"作成日: {datetime.now().strftime('%Y-%m-%d')}", fontsize=16, ha='center')
        plt.text(0.5, 0.5, f"ユーザー: {report.user.username}", fontsize=16, ha='center')
        pdf.savefig()
        plt.close()
        
        # 目次ページ
        plt.figure(figsize=(8.5, 11))
        plt.axis('off')
        plt.text(0.5, 0.9, "目次", fontsize=20, ha='center')
        
        y_pos = 0.8
        page_num = 2  # タイトルページの次から
        
        if report.include_learning:
            plt.text(0.3, y_pos, "1. 学習記録サマリー", fontsize=14)
            plt.text(0.7, y_pos, f"Page {page_num}", fontsize=14)
            y_pos -= 0.05
            page_num += 1
        
        if report.include_habits:
            plt.text(0.3, y_pos, "2. 習慣トラッキングサマリー", fontsize=14)
            plt.text(0.7, y_pos, f"Page {page_num}", fontsize=14)
            y_pos -= 0.05
            page_num += 1
        
        if report.include_books:
            plt.text(0.3, y_pos, "3. 読書サマリー", fontsize=14)
            plt.text(0.7, y_pos, f"Page {page_num}", fontsize=14)
            y_pos -= 0.05
            page_num += 1
        
        if report.include_goals:
            plt.text(0.3, y_pos, "4. 目標進捗サマリー", fontsize=14)
            plt.text(0.7, y_pos, f"Page {page_num}", fontsize=14)
            y_pos -= 0.05
            page_num += 1
        
        if report.include_analytics:
            plt.text(0.3, y_pos, "5. 分析データ", fontsize=14)
            plt.text(0.7, y_pos, f"Page {page_num}", fontsize=14)
        
        pdf.savefig()
        plt.close()
        
        # 各セクションのページを生成
        if report.include_learning:
            generate_learning_summary_page(pdf, report.user, start_date, end_date)
        
        if report.include_habits:
            generate_habits_summary_page(pdf, report.user, start_date, end_date)
        
        if report.include_books:
            generate_books_summary_page(pdf, report.user, start_date, end_date)
        
        if report.include_goals:
            generate_goals_summary_page(pdf, report.user, start_date, end_date)
        
        if report.include_analytics:
            generate_analytics_page(pdf, report.user, start_date, end_date)
    
    # レポートファイルを保存
    with open(temp_filepath, 'rb') as f:
        report.report_file.save(f"{report.title.replace(' ', '_')}_{report.report_type}.pdf", BytesIO(f.read()))
    
    # 一時ファイルを削除
    os.unlink(temp_filepath)


def generate_learning_summary_page(pdf, user, start_date, end_date):
    """学習記録のサマリーページを生成"""
    plt.figure(figsize=(8.5, 11))
    plt.suptitle("学習記録サマリー", fontsize=16, y=0.95)
    
    # 学習記録の取得
    learning_entries = LearningEntry.objects.filter(
        user=user,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).order_by('-created_at')
    
    # カテゴリ別の学習記録数
    categories = {}
    for entry in learning_entries:
        categories[entry.category] = categories.get(entry.category, 0) + 1
    
    # カテゴリ別の学習記録数の円グラフ
    if categories:
        plt.subplot(2, 1, 1)
        plt.pie(categories.values(), labels=categories.keys(), autopct='%1.1f%%')
        plt.title("カテゴリ別学習記録数", fontsize=14)
    
    # 学習記録リスト
    plt.subplot(2, 1, 2)
    plt.axis('off')
    plt.title("最近の学習記録", fontsize=14, pad=20)
    
    recent_entries = learning_entries[:10]  # 最新10件
    
    if recent_entries:
        table_data = []
        for i, entry in enumerate(recent_entries, 1):
            date_str = entry.created_at.strftime('%Y-%m-%d')
            title = entry.title[:30] + "..." if len(entry.title) > 30 else entry.title
            table_data.append([str(i), date_str, title, entry.category])
        
        plt.table(
            cellText=table_data,
            colLabels=["#", "日付", "タイトル", "カテゴリ"],
            loc='center',
            cellLoc='center',
            colWidths=[0.1, 0.2, 0.5, 0.2]
        )
    else:
        plt.text(0.5, 0.5, "この期間の学習記録はありません", ha='center', fontsize=12)
    
    pdf.savefig()
    plt.close()


def generate_habits_summary_page(pdf, user, start_date, end_date):
    """習慣トラッキングのサマリーページを生成"""
    plt.figure(figsize=(8.5, 11))
    plt.suptitle("習慣トラッキングサマリー", fontsize=16, y=0.95)
    
    # 習慣データの取得
    habits = Habit.objects.filter(user=user, is_active=True)
    habit_logs = HabitLog.objects.filter(
        habit__in=habits,
        log_date__gte=start_date,
        log_date__lte=end_date
    )
    
    # 習慣の達成状況
    habits_data = {}
    for habit in habits:
        logs = habit_logs.filter(habit=habit)
        total_days = (end_date - start_date).days + 1
        completion_rate = logs.count() / total_days * 100 if total_days > 0 else 0
        habits_data[habit.name] = completion_rate
    
    # 習慣の達成率の棒グラフ
    if habits_data:
        plt.subplot(2, 1, 1)
        plt.barh(list(habits_data.keys()), list(habits_data.values()))
        plt.xlabel("達成率 (%)")
        plt.xlim(0, 100)
        plt.title("習慣の達成率", fontsize=14)
        
        # y軸のラベルが長すぎる場合は省略
        plt.yticks(fontsize=8)
        plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # 習慣のカレンダーヒートマップ
    plt.subplot(2, 1, 2)
    plt.axis('off')
    plt.title("習慣の達成カレンダー（過去30日間）", fontsize=14, pad=20)
    
    # 過去30日間の日付リスト
    end_date_30 = min(end_date, datetime.now().date())
    start_date_30 = max(start_date, end_date_30 - timedelta(days=29))
    date_list = [(start_date_30 + timedelta(days=i)).strftime('%Y-%m-%d') for i in range((end_date_30 - start_date_30).days + 1)]
    
    # 習慣の達成データを集計
    habit_calendar_data = []
    for habit in habits:
        habit_row = [habit.name]
        for date_str in date_list:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            log = habit_logs.filter(habit=habit, log_date=date).first()
            habit_row.append("✓" if log else "")
        habit_calendar_data.append(habit_row)
    
    if habit_calendar_data:
        # 日付ラベルを短縮形式に変換
        date_labels = ["習慣"] + [d.split("-")[2] for d in date_list]
        
        plt.table(
            cellText=habit_calendar_data,
            colLabels=date_labels,
            loc='center',
            cellLoc='center'
        )
    else:
        plt.text(0.5, 0.5, "この期間の習慣記録はありません", ha='center', fontsize=12)
    
    pdf.savefig()
    plt.close()


def generate_books_summary_page(pdf, user, start_date, end_date):
    """読書サマリーページを生成"""
    plt.figure(figsize=(8.5, 11))
    plt.suptitle("読書サマリー", fontsize=16, y=0.95)
    
    # 読書データの取得
    books = Book.objects.filter(user=user)
    books_completed = books.filter(
        status='completed',
        finish_date__gte=start_date,
        finish_date__lte=end_date
    )
    books_in_progress = books.filter(status='in_progress')
    
    # 読書状況のサマリー
    plt.subplot(2, 2, 1)
    plt.axis('off')
    plt.title("読書サマリー", fontsize=14)
    
    summary_data = [
        ["期間内の読了数", str(books_completed.count())],
        ["読書中の本", str(books_in_progress.count())],
        ["読了ページ数", str(sum(b.page_count or 0 for b in books_completed))],
    ]
    
    plt.table(
        cellText=summary_data,
        loc='center',
        cellLoc='center',
        colWidths=[0.6, 0.4]
    )
    
    # 読書状況の円グラフ
    plt.subplot(2, 2, 2)
    book_status_counts = {
        '読了': books.filter(status='completed').count(),
        '読書中': books.filter(status='in_progress').count(),
        '未読': books.filter(status='not_started').count(),
        'その他': books.filter(status__in=['on_hold', 'abandoned']).count()
    }
    
    # 0のカテゴリを除外
    book_status_counts = {k: v for k, v in book_status_counts.items() if v > 0}
    
    if book_status_counts:
        plt.pie(book_status_counts.values(), labels=book_status_counts.keys(), autopct='%1.1f%%')
        plt.title("読書状況", fontsize=14)
    
    # 読了した本のリスト
    plt.subplot(2, 1, 2)
    plt.axis('off')
    plt.title("期間内に読了した本", fontsize=14, pad=20)
    
    if books_completed:
        table_data = []
        for i, book in enumerate(books_completed, 1):
            title = book.title[:30] + "..." if len(book.title) > 30 else book.title
            author = book.author[:20] + "..." if len(book.author) > 20 else book.author
            finish_date_str = book.finish_date.strftime('%Y-%m-%d') if book.finish_date else "N/A"
            rating = str(book.rating) if book.rating else "未評価"
            
            table_data.append([str(i), title, author, finish_date_str, rating])
        
        plt.table(
            cellText=table_data,
            colLabels=["#", "タイトル", "著者", "読了日", "評価"],
            loc='center',
            cellLoc='center',
            colWidths=[0.1, 0.4, 0.2, 0.2, 0.1]
        )
    else:
        plt.text(0.5, 0.5, "この期間に読了した本はありません", ha='center', fontsize=12)
    
    pdf.savefig()
    plt.close()


def generate_goals_summary_page(pdf, user, start_date, end_date):
    """目標進捗サマリーページを生成"""
    plt.figure(figsize=(8.5, 11))
    plt.suptitle("目標進捗サマリー", fontsize=16, y=0.95)
    
    # 目標データの取得
    goals = Goal.objects.filter(user=user)
    completed_goals = goals.filter(
        status='completed',
        updated_at__date__gte=start_date,
        updated_at__date__lte=end_date
    )
    in_progress_goals = goals.filter(status='in_progress')
    
    # 目標の状態分布
    plt.subplot(2, 2, 1)
    goal_status_counts = {
        '達成済み': goals.filter(status='completed').count(),
        '進行中': goals.filter(status='in_progress').count(),
        '未開始': goals.filter(status='not_started').count(),
        '放棄': goals.filter(status='abandoned').count()
    }
    
    # 0のカテゴリを除外
    goal_status_counts = {k: v for k, v in goal_status_counts.items() if v > 0}
    
    if goal_status_counts:
        plt.pie(goal_status_counts.values(), labels=goal_status_counts.keys(), autopct='%1.1f%%')
        plt.title("目標の状態分布", fontsize=14)
    
    # 目標の進捗率分布
    plt.subplot(2, 2, 2)
    progress_bins = [0, 25, 50, 75, 100]
    progress_labels = ['0-25%', '26-50%', '51-75%', '76-100%']
    
    goal_progress_counts = []
    for i in range(len(progress_bins) - 1):
        count = goals.filter(
            progress_percentage__gte=progress_bins[i],
            progress_percentage__lte=progress_bins[i+1]
        ).count()
        goal_progress_counts.append(count)
    
    if sum(goal_progress_counts) > 0:
        plt.bar(progress_labels, goal_progress_counts)
        plt.title("目標の進捗率分布", fontsize=14)
        plt.xticks(rotation=45)
    
    # 達成した目標のリスト
    plt.subplot(2, 1, 2)
    plt.axis('off')
    plt.title("期間内に達成した目標", fontsize=14, pad=20)
    
    if completed_goals:
        table_data = []
        for i, goal in enumerate(completed_goals, 1):
            title = goal.title[:30] + "..." if len(goal.title) > 30 else goal.title
            start_date_str = goal.start_date.strftime('%Y-%m-%d')
            due_date_str = goal.due_date.strftime('%Y-%m-%d') if goal.due_date else "なし"
            priority = goal.get_priority_display()
            
            table_data.append([str(i), title, start_date_str, due_date_str, priority])
        
        plt.table(
            cellText=table_data,
            colLabels=["#", "タイトル", "開始日", "期限日", "優先度"],
            loc='center',
            cellLoc='center',
            colWidths=[0.1, 0.4, 0.2, 0.2, 0.1]
        )
    else:
        plt.text(0.5, 0.5, "この期間に達成した目標はありません", ha='center', fontsize=12)
    
    pdf.savefig()
    plt.close()


def generate_analytics_page(pdf, user, start_date, end_date):
    """分析データページを生成"""
    plt.figure(figsize=(8.5, 11))
    plt.suptitle("分析データ", fontsize=16, y=0.95)
    
    # 活動サマリーデータの取得
    activity_summaries = ActivitySummary.objects.filter(
        user=user,
        start_date__gte=start_date,
        end_date__lte=end_date
    )
    
    # 時系列データの準備
    dates = []
    study_times = []
    habit_completion_rates = []
    
    for summary in activity_summaries:
        dates.append(summary.start_date)
        study_times.append(summary.avg_daily_study_time)
        habit_completion_rates.append(summary.habit_completion_rate)
    
    # 学習時間の時系列グラフ
    plt.subplot(2, 1, 1)
    if dates and study_times:
        plt.plot(dates, study_times, marker='o')
        plt.title("平均日次学習時間の推移", fontsize=14)
        plt.ylabel("学習時間（分）")
        plt.xticks(rotation=45)
        plt.grid(True, linestyle='--', alpha=0.7)
    else:
        plt.axis('off')
        plt.text(0.5, 0.5, "学習時間データがありません", ha='center', fontsize=12)
    
    # 習慣達成率の時系列グラフ
    plt.subplot(2, 1, 2)
    if dates and habit_completion_rates:
        plt.plot(dates, habit_completion_rates, marker='o', color='green')
        plt.title("習慣達成率の推移", fontsize=14)
        plt.ylabel("達成率（%）")
        plt.xticks(rotation=45)
        plt.grid(True, linestyle='--', alpha=0.7)
    else:
        plt.axis('off')
        plt.text(0.5, 0.5, "習慣達成率データがありません", ha='center', fontsize=12)
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    pdf.savefig()
    plt.close()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_report(request, report_id):
    """レポートファイルをダウンロードするAPI"""
    report = get_object_or_404(PortfolioReport, id=report_id, user=request.user)
    
    if not report.report_file:
        return Response({"error": "Report file not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # ファイルレスポンスを返す
    return FileResponse(report.report_file.open(), content_type='application/pdf')