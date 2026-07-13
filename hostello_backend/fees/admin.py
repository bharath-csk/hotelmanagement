from django.contrib import admin
from django.utils import timezone
from .models import FeeConfig, FeeMonth, FeePayment, Fine
from students.models import Student

# Attendance imports: adjust to your real models/fields
from attendance.models import MessAttendance, RoomAttendance  # update if names differ


class FineInline(admin.TabularInline):
    model = Fine
    extra = 0


class PaymentInline(admin.TabularInline):
    model = FeePayment
    extra = 0


@admin.register(FeeMonth)
class FeeMonthAdmin(admin.ModelAdmin):
    change_list_template = "admin/fees/board.html"

    list_display = (
        "student", "year", "month",
        "display_hostel_fee", "display_final_mess_fee", "display_fine_total",
        "display_total_amount", "display_paid_amount", "display_pending_amount",
        "status", "display_due_date", "display_last_reminder_at",
    )
    list_filter = ("status", "year", "month")
    search_fields = ("student__username", "student__first_name", "student__last_name")
    inlines = [FineInline, PaymentInline]

    # Admin list columns tolerant of snake/flat fields
    def display_hostel_fee(self, obj): return getattr(obj, "hostel_fee", None) or getattr(obj, "hostelfee", None)
    def display_final_mess_fee(self, obj): return getattr(obj, "final_mess_fee", None) or getattr(obj, "finalmessfee", None)
    def display_fine_total(self, obj): return getattr(obj, "fine_total", None) or getattr(obj, "finetotal", None)
    def display_total_amount(self, obj): return getattr(obj, "total_monthly_fee", None) or getattr(obj, "totalamount", None)
    def display_paid_amount(self, obj): return getattr(obj, "paid_amount", None) or getattr(obj, "paidamount", None)
    def display_pending_amount(self, obj): return getattr(obj, "pending_amount", None) or getattr(obj, "pendingamount", None)
    def display_due_date(self, obj): return getattr(obj, "due_date", None) or getattr(obj, "duedate", None)
    def display_last_reminder_at(self, obj): return getattr(obj, "last_reminder_at", None) or getattr(obj, "lastreminderat", None)

    display_hostel_fee.short_description = "Hostel fee"
    display_final_mess_fee.short_description = "Final mess fee"
    display_fine_total.short_description = "Fine total"
    display_total_amount.short_description = "Total amount"
    display_paid_amount.short_description = "Paid amount"
    display_pending_amount.short_description = "Pending amount"
    display_due_date.short_description = "Due date"
    display_last_reminder_at.short_description = "Last reminder"

    # ---- Attendance helpers ----
    def _month_range(self, year: int, month: int):
        start = timezone.datetime(year, month, 1).date()
        if month == 12:
            end = timezone.datetime(year + 1, 1, 1).date()
        else:
            end = timezone.datetime(year, month + 1, 1).date()
        return start, end

    def _mess_absent_days(self, s: Student, year: int, month: int) -> int:
        start, end = self._month_range(year, month)
        qs = MessAttendance.objects.filter(student=s, date__gte=start, date__lt=end)
        # Update status filter to your schema if different
        return int(qs.filter(status__iexact="absent").count())

    def _room_presence_stats(self, s: Student, year: int, month: int):
        start, end = self._month_range(year, month)
        qs = RoomAttendance.objects.filter(student=s, date__gte=start, date__lt=end)
        present = qs.filter(status__iexact="present").count()
        absent = qs.filter(status__iexact="absent").count()
        return int(present), int(absent)

    # ---------------- Board context ----------------
    def changelist_view(self, request, extra_context=None):
        date_str = request.GET.get("date")
        if date_str:
            try:
                selected_date = timezone.datetime.strptime(date_str, "%Y-%m-%d").date()
            except Exception:
                selected_date = timezone.localdate()
        else:
            selected_date = timezone.localdate()
        y, m = selected_date.year, selected_date.month

        per_day = 150
        total_days = 30
        base_mess_fee_default = per_day * total_days

        rows = []
        for s in Student.objects.all():
            # Mess attendance from attendance app
            mess_absent = self._mess_absent_days(s, y, m)

            # Mess fee strictly from attendance
            base_mess_fee = base_mess_fee_default
            is_rebate_eligible = mess_absent >= 4
            mess_rebate_amount = mess_absent * per_day if is_rebate_eligible else 0
            if mess_rebate_amount > base_mess_fee:
                mess_rebate_amount = base_mess_fee
            final_mess_fee = base_mess_fee - mess_rebate_amount

            # Room stats for UI
            room_present, room_absent = self._room_presence_stats(s, y, m)
            room_denom = max(1, room_present + room_absent)
            room_rate = round(room_present / room_denom * 100, 1)
            mess_present = max(0, total_days - mess_absent)
            mess_rate = round(mess_present / total_days * 100, 1)

            # Student details
            room_type = getattr(s, "room_type", "4 Seater")
            ac_type = getattr(s, "ac_type", "Non A/C")
            student_block = {
                "id": s.id,
                "full_name": getattr(s, "full_name", None) or getattr(s, "name", None) or "—",
                "admission_number": getattr(s, "admission_number", "—"),
                "room_number": getattr(s, "room_number", None),
                "program": getattr(s, "program", "—"),
                "email": getattr(s, "email", "—"),
                "mobile": getattr(s, "mobile", "—"),
                "city": getattr(s, "city", "—"),
                "discipline": getattr(s, "discipline", "—"),
                "guardian_name": getattr(s, "guardian_name", "—"),
                "room_type": room_type,
                "ac_type": ac_type,
            }

            # Hostel fee rule
            base_hostel = 2000
            room_add = 1500 if room_type == "1 Seater" else 1000 if room_type == "2 Seater" else 500 if room_type == "3 Seater" else 0
            ac_add = 1000 if str(ac_type).strip() in ["A/C", "AC"] else 0
            hostel_fee = base_hostel + room_add + ac_add

            hostel_fee_breakup = {
                "base": base_hostel,
                "room_add": room_add,
                "ac_add": ac_add,
                "subtotal": base_hostel + room_add,
                "final": hostel_fee,
            }

            # Total amount column
            total_monthly_fee = int(hostel_fee) + int(final_mess_fee)

            rows.append({
                "student": student_block,
                "stats": {
                    "room_present_count": room_present,
                    "room_absent_count": room_absent,
                    "room_attendance_percentage": room_rate,
                    "mess_attendance_percentage": mess_rate,
                },
                "mess_present_days": mess_present,
                "mess_absent_days": mess_absent,
                "mess_attendance_rate": mess_rate,

                "hostel_fee": hostel_fee,
                "hostel_fee_breakup": hostel_fee_breakup,

                "base_mess_fee": base_mess_fee,
                "mess_absent": mess_absent,
                "is_rebate_eligible": is_rebate_eligible,
                "mess_rebate_amount": mess_rebate_amount,
                "final_mess_fee": final_mess_fee,

                # 4th column total
                "total_monthly_fee": total_monthly_fee,
            })

        extra = extra_context or {}
        extra.update({
            "selected_date": selected_date,
            "date_info": {
                "is_today": selected_date == timezone.localdate(),
                "is_past": selected_date < timezone.localdate(),
                "is_future": selected_date > timezone.localdate(),
            },
            "student_data": rows,
        })
        return super().changelist_view(request, extra_context=extra)


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ("feem", "amount", "method", "reference", "paid_at")
    list_filter = ("method", "paid_at")
    search_fields = ("reference", "feem__student__username")


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ("feem", "title", "amount", "created_at")
    search_fields = ("title",)
