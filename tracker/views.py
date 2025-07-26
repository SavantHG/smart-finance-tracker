from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import ExpenseSerializer
from .models import Expense
from django.utils.timezone import now
from django.db.models import Sum
from datetime import date
from .parser import parse_expense_input

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_expense(request):
    message = request.data.get("message")
    parsed_data = parse_expense_input(message)

    if parsed_data is None:
        return Response({"error": "Invalid input. Use format like '500 grocery dal, masale'"}, status=400)

    serializer = ExpenseSerializer(data={**parsed_data, "user": request.user.id})

    if serializer.is_valid():
        expense = serializer.save()

        user = request.user

        today = date.today()
        start_of_month = today.replace(day=1)

        total_this_month = Expense.objects.filter(
            user=user,
            timestamp__date__gte=start_of_month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        total_today = Expense.objects.filter(
            user=user,
            timestamp__date=today
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        total_category = Expense.objects.filter(
            user=user,
            category=expense.category
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        message = (
            f"Saved\n"
            f"{expense.amount:.2f}\n"
            f"Category: {expense.category}\n"
            f"Comment: {expense.description}\n\n"
            f"---\n"
            f"This month: {total_this_month:.2f}\n"
            f"Today: {total_today:.2f}\n"
            f"Category total: {total_category:.2f}"
        )

        return Response({'message': message}, status=201)
    return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_expenses(request):
    user = request.user
    today = date.today()
    start_of_month = today.replace(day=1)
    expenses = Expense.objects.filter(
        user=user,
        timestamp__date__gte=start_of_month
    ).order_by('-timestamp')
    serializer = ExpenseSerializer(expenses, many=True)

    days_passed = (today - start_of_month).days + 1

    total_this_month = Expense.objects.filter(
        user=user,
        timestamp__date__gte=start_of_month
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    avg_per_day = total_this_month / days_passed

    # Category-wise total for current month
    from django.db.models import Count
    current_month_category_totals = Expense.objects.filter(
        user=user,
        timestamp__date__gte=start_of_month
    ).values('category').annotate(total=Sum('amount'))

    # Previous month calculation
    if start_of_month.month == 1:
        prev_month = start_of_month.replace(year=start_of_month.year - 1, month=12)
    else:
        prev_month = start_of_month.replace(month=start_of_month.month - 1)

    from calendar import monthrange
    days_in_prev_month = monthrange(prev_month.year, prev_month.month)[1]

    end_of_prev_month = start_of_month
    start_of_prev_month = prev_month

    prev_month_total = Expense.objects.filter(
        user=user,
        timestamp__date__gte=start_of_prev_month,
        timestamp__date__lt=end_of_prev_month
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    avg_per_day_prev_month = prev_month_total / days_in_prev_month

    prev_month_category_totals = Expense.objects.filter(
        user=user,
        timestamp__date__gte=start_of_prev_month,
        timestamp__date__lt=end_of_prev_month
    ).values('category').annotate(total=Sum('amount'))

    return Response({
        "expenses": serializer.data,
        "summary": {
            "total_this_month": round(total_this_month, 2),
            "avg_per_day_till_now": round(avg_per_day, 2),
            "category_totals_this_month": list(current_month_category_totals),
            "prev_month_total": round(prev_month_total, 2),
            "avg_per_day_prev_month": round(avg_per_day_prev_month, 2),
            "category_totals_prev_month": list(prev_month_category_totals)
        }
    })