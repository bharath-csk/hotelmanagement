from rest_framework import serializers
from .models import FeeMonth, FeePayment, Fine

class FineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fine
        fields = ["id","title","amount","created_at"]

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeePayment
        fields = ["id","amount","method","reference","note","paid_at"]

class FeeMonthSerializer(serializers.ModelSerializer):
    fines = FineSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = FeeMonth
        fields = ["id","student","year","month","due_date","mess_absent_days","hostel_fee","base_mess_fee","mess_rebate_amount","final_mess_fee","fine_total","total_amount","paid_amount","pending_amount","status","is_rebate_eligible","last_reminder_at","fines","payments"]
