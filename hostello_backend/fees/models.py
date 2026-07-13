# fees/models.py
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from students.models import Student

class FeeConfig(models.Model):
    base_hostel_4 = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("2000.00"))
    delta_3 = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("2500.00"))
    delta_2 = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("3000.00"))
    delta_1 = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("3500.00"))
    ac_addon = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1000.00"))
    base_mess = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("4500.00"))
    rebate_min_days = models.PositiveIntegerField(default=4)
    mess_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("150.00"))
    default_due_day = models.PositiveIntegerField(default=10)

    def __str__(self):
        return "Fee Config"

    @classmethod
    def get_solo(cls):
        obj = cls.objects.first()
        return obj or cls.objects.create()

class FeeMonth(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="fee_months")
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    due_date = models.DateField(null=True, blank=True)
    mess_absent_days = models.PositiveIntegerField(default=0)

    hostel_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    base_mess_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    mess_rebate_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    final_mess_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    fine_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    pending_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    status = models.CharField(
        max_length=10,
        choices=[("paid", "Paid"), ("unpaid", "Unpaid"), ("overdue", "Overdue")],
        default="unpaid",
    )
    is_rebate_eligible = models.BooleanField(default=False)

    last_reminder_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "year", "month")
        ordering = ["-year", "-month", "student_id"]

    def __str__(self):
        return f"{self.student} {self.month}/{self.year}"

    def compute_hostel_fee(self, *, room_type: str, ac: bool):
        cfg = FeeConfig.get_solo()
        amount = cfg.base_hostel_4
        if room_type == "3-seater":
            amount += cfg.delta_3
        elif room_type == "2-seater":
            amount += cfg.delta_2
        elif room_type == "1-seater":
            amount += cfg.delta_1
        if ac:
            amount += cfg.ac_addon
        self.hostel_fee = amount

    def compute_mess_fee(self):
        cfg = FeeConfig.get_solo()
        self.base_mess_fee = cfg.base_mess
        if self.mess_absent_days >= cfg.rebate_min_days:
            self.is_rebate_eligible = True
            rebate = Decimal(self.mess_absent_days) * cfg.mess_per_day
            if rebate > self.base_mess_fee:
                rebate = self.base_mess_fee
            self.mess_rebate_amount = rebate
        else:
            self.is_rebate_eligible = False
            self.mess_rebate_amount = Decimal("0.00")
        self.final_mess_fee = self.base_mess_fee - self.mess_rebate_amount

    def recompute_totals(self):
        fine_sum = self.fines.aggregate(s=models.Sum("amount"))["s"] or Decimal("0.00")
        self.fine_total = fine_sum
        gross = self.hostel_fee + self.final_mess_fee + self.fine_total
        self.total_amount = gross
        paid = self.payments.aggregate(s=models.Sum("amount"))["s"] or Decimal("0.00")
        self.paid_amount = paid
        self.pending_amount = gross - paid
        if self.pending_amount <= Decimal("0.00"):
            self.status = "paid"
            self.pending_amount = Decimal("0.00")
        else:
            today = timezone.localdate()
            if self.due_date and today > self.due_date:
                self.status = "overdue"
            else:
                self.status = "unpaid"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.recompute_totals()
        super().save(update_fields=["fine_total", "total_amount", "paid_amount", "pending_amount", "status"])

class Fine(models.Model):
    feem = models.ForeignKey(FeeMonth, on_delete=models.CASCADE, related_name="fines")
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.amount}"

class FeePayment(models.Model):
    feem = models.ForeignKey(FeeMonth, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    method = models.CharField(
        max_length=20,
        choices=[("online", "Online"), ("cash", "Cash"), ("upi", "UPI"), ("card", "Card")],
        default="online",
    )
    reference = models.CharField(max_length=100, blank=True)
    note = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Payment {self.amount} on {self.paid_at:%Y-%m-%d}"
