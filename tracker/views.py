from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import ExpenseSerializer
from .models import Expense
from django.utils.timezone import now
from django.db.models import Sum
from datetime import date

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_expense(request):
    data = request.data

    serializer = ExpenseSerializer(data={**data, "user": request.user.id})

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