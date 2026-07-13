# fees/services.py
from django.utils import timezone
from calendar import monthrange
from django.db.models import Q
from fees.models import FeeMonth
from attendance.models import MessAttendance
from datetime import date

def update_fee_from_attendance(user, year=None, month=None):
    """Aggregate monthly mess absence and recompute FeeMonth."""
    today = timezone.localdate()
    y = year or today.year
    m = month or today.month

    # Count days where ALL meals absent (or no present meal) per day
    # If your logic is: absent day when mess_status == 'absent', implement by checking meals
    qs = MessAttendance.objects.filter(student__user=user, date__year=y, date__month=m)

    # Derive day-level presence: any present meal -> day present
    days_present = set(qs.filter(status='present').values_list('date', flat=True))
    # Days with only absent or no present -> absent days count
    all_days = set(qs.values_list('date', flat=True))
    mess_absent_days = 0
    for d in all_days:
        if d not in days_present:
            mess_absent_days += 1

    # Get room context
    room_type = getattr(user, "room_type", "4 Seater")
    ac = (getattr(user, "ac_type", "") in ["A/C","AC"])

    # Update or create FeeMonth
    fm, _ = FeeMonth.objects.get_or_create(student=user, year=y, month=m)
    fm.mess_absent_days = mess_absent_days
    fm.compute_hostel_fee(room_type=room_type, ac=ac)
    fm.compute_mess_fee()
    fm.recompute_totals()
    fm.save()
    return fm
