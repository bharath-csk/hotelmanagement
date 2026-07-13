from decimal import Decimal

from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from .models import FeeMonth, FeePayment
from .serializers import FeeMonthSerializer, PaymentSerializer
from django.db.models import Prefetch
from students.models import Student 
from django.views.decorators.http import require_http_methods




# ---------- Warden helpers ----------
def _is_warden(user):
    return bool(user and user.is_staff)

def _get_selected_date(request):
    try:
        d = request.GET.get("date")
        if d:
            return timezone.datetime.strptime(d, "%Y-%m-%d").date()
    except Exception:
        pass
    return timezone.localdate()

def _student_block(user):
    # Prefer related profile 'student' if available
    s = getattr(user, "student", None)
    # get_full_name might be a method on Django user
    full_name = ""
    try:
        if hasattr(user, "get_full_name"):
            full_name = user.get_full_name() or ""
    except Exception:
        full_name = ""
    if not full_name:
        full_name = getattr(user, "first_name", "") or getattr(user, "username", "")

    return {
        "id": user.id,
        "full_name": full_name or getattr(user, "username", "—"),
        "admission_number": getattr(s, "admission_number", None) or getattr(user, "admission_number", "—"),
        "room_number": getattr(s, "room_number", None) or getattr(user, "room_number", None),
        "program": getattr(s, "program", "") or getattr(user, "program", "—"),
        "email": getattr(user, "email", "—"),
        "mobile": getattr(s, "mobile", "") or getattr(user, "mobile", "—"),
        "city": getattr(s, "city", "") or getattr(user, "city", "—"),
        "discipline": getattr(s, "discipline", "") or getattr(user, "discipline", "—"),
        "guardian_name": getattr(s, "guardian_name", "") or getattr(user, "guardian_name", "—"),
    }

def _stats_block(user, fm, total_days=30):
    # Replace with real attendance aggregation when available
    room_present = int(getattr(user, "room_present_count", 0) or 0)
    room_absent = int(getattr(user, "room_absent_count", 0) or 0)
    denom = max(1, room_present + room_absent)
    room_rate = round(room_present / denom * 100, 1)

    # Use FeeMonth fields consistent with your models/serializers
    # According to serializers, fields are: messabsentdays, hostelfee, basemessfee, messrebateamount, finalmessfee, ...
    mess_absent = int(getattr(fm, "mess_absent_days", None) or getattr(fm, "messabsentdays", 0) or 0)
    mess_present = max(0, total_days - mess_absent)
    mess_rate = round(mess_present / total_days * 100, 1)

    return {
        "room_present_count": room_present,
        "room_absent_count": room_absent,
        "room_attendance_percentage": room_rate,
        "mess_attendance_percentage": mess_rate,
    }

def _date_info(selected_date):
    today = timezone.localdate()
    return {
        "is_today": selected_date == today,
        "is_past": selected_date < today,
        "is_future": selected_date > today,
    }


# ---------- Admin/Warden Board (admin/fees/board.html) ----------
@login_required
@user_passes_test(_is_warden)
def fees_board_admin(request):
    selected_date = _get_selected_date(request)
    y, m = selected_date.year, selected_date.month

    # Pull real hostel students; remove approved filter if not needed
    qs = Student.objects.select_related("user").all()
    # If you have an approved flag, uncomment:
    # qs = qs.filter(approved=True)

    student_data = []
    for s in qs:
        u = getattr(s, "user", None)

        # Ensure FeeMonth row exists so month always renders
        fm, _ = FeeMonth.objects.get_or_create(student=(u or s.user), year=y, month=m)

        # Build student block from Student first, fallback to User
        full_name = (getattr(s, "full_name", None) or
                     (u.get_full_name() if u and hasattr(u, "get_full_name") else None) or
                     getattr(u, "username", None) or
                     getattr(s, "name", None) or "—")

        student_block = {
            "id": getattr(s, "id", None) or (u.id if u else None),
            "full_name": full_name,
            "admission_number": getattr(s, "admission_number", None) or getattr(u, "admission_number", "—"),
            "room_number": getattr(s, "room_number", None) or getattr(u, "room_number", None),
            "program": getattr(s, "program", None) or getattr(u, "program", "—"),
            "email": getattr(u, "email", None) or getattr(s, "email", "—"),
            "mobile": getattr(s, "mobile", None) or getattr(u, "mobile", "—"),
            "city": getattr(s, "city", None) or getattr(u, "city", "—"),
            "discipline": getattr(s, "discipline", None) or getattr(u, "discipline", "—"),
            "guardian_name": getattr(s, "guardian_name", None) or getattr(u, "guardian_name", "—"),
        }

        # Room and mess stats placeholders; plug in real attendance if available
        room_present = int(getattr(s, "room_present_count", 0) or 0)
        room_absent = int(getattr(s, "room_absent_count", 0) or 0)
        denom = max(1, room_present + room_absent)
        room_rate = round(room_present / denom * 100, 1)

        total_days = 30
        mess_absent = int(getattr(fm, "mess_absent_days", None) or getattr(fm, "messabsentdays", 0) or 0)
        mess_present = max(0, total_days - mess_absent)
        mess_rate = round(mess_present / total_days * 100, 1)

        stats_block = {
            "room_present_count": room_present,
            "room_absent_count": room_absent,
            "room_attendance_percentage": room_rate,
            "mess_attendance_percentage": mess_rate,
        }

        student_data.append({
            "student": student_block,
            "stats": stats_block,
            "mess_present_days": mess_present,
            "mess_absent_days": mess_absent,
            "mess_attendance_rate": mess_rate,
        })

    ctx = {
        "selected_date": selected_date,
        "date_info": _date_info(selected_date),
        "student_data": student_data,
    }
    return render(request, "admin/fees/board.html", ctx)


# Optional placeholder so the template's JS fetch won't 404
@login_required
@user_passes_test(_is_warden)
def mark_attendance_placeholder(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Only POST allowed"}, status=405)
    # TODO: implement real attendance write + return mess_status for update
    return JsonResponse({"success": True, "message": "Marked (placeholder)", "mess_status": "present"})


# ---------- Existing “new” board kept for reference; renders same template ----------
@login_required
def fees_board_new(request):
    today = timezone.localdate()
    y, m = today.year, today.month

    User = get_user_model()
    users = User.objects.all()

    student_data = []
    for u in users:
        student_block = {
            "id": u.id,
            "full_name": u.get_full_name() if hasattr(u, "get_full_name") else u.username,
            "admission_number": getattr(u, "admission_number", "—"),
            "room_number": getattr(u, "room_number", None),
            "program": getattr(u, "program", "—"),
            "email": getattr(u, "email", "—"),
            "mobile": getattr(u, "mobile", "—"),
            "city": getattr(u, "city", "—"),
            "discipline": getattr(u, "discipline", "—"),
            "guardian_name": getattr(u, "guardian_name", "—"),
        }

        fm = FeeMonth.objects.filter(student=u, year=y, month=m).first()
        if not fm:
            continue

        total_days = 30
        mess_absent = int(getattr(fm, "mess_absent_days", None) or getattr(fm, "messabsentdays", 0) or 0)
        mess_present = max(0, total_days - mess_absent)
        room_present = int(getattr(u, "room_present_count", 0) or 0)
        room_absent = int(getattr(u, "room_absent_count", 0) or 0)

        room_total = room_present + room_absent if (room_present + room_absent) > 0 else 1
        room_rate = round((room_present / room_total) * 100, 1)
        mess_rate = round((mess_present / total_days) * 100, 1)

        stats_block = {
            "room_present_count": room_present,
            "room_absent_count": room_absent,
            "room_attendance_percentage": room_rate,
            "mess_attendance_percentage": mess_rate,
        }

        student_data.append({
            "student": student_block,
            "stats": stats_block,
            "mess_present_days": mess_present,
            "mess_absent_days": mess_absent,
            "mess_attendance_rate": mess_rate,
            "fees": {
                # Be tolerant of either snake_case or camelCase fields
                "hostel_fee": getattr(fm, "hostel_fee", None) or getattr(fm, "hostelfee", 0),
                "base_mess_fee": getattr(fm, "base_mess_fee", None) or getattr(fm, "basemessfee", 0),
                "mess_rebate_amount": getattr(fm, "mess_rebate_amount", None) or getattr(fm, "messrebateamount", 0),
                "final_mess_fee": getattr(fm, "final_mess_fee", None) or getattr(fm, "finalmessfee", 0),
                "total_monthly_fee": getattr(fm, "total_monthly_fee", None) or getattr(fm, "totalamount", 0),
                "status": fm.status,
            }
        })

    ctx = {
        "selected_date": today,
        "date_info": {"is_today": True, "is_past": False, "is_future": False},
        "student_data": student_data,
    }
    return render(request, "admin/fees/board.html", ctx)


# ---------- Shared helpers ----------
def ensure_fee_month(student, year, month, room_type: str, ac: bool):
    feem, _ = FeeMonth.objects.get_or_create(student=student, year=year, month=month)
    absent = int(getattr(feem, "mess_absent_days", None) or getattr(feem, "messabsentdays", 0) or 0)
    # preserve current absent days
    if hasattr(feem, "mess_absent_days"):
        feem.mess_absent_days = absent
    else:
        # If the real field is messabsentdays, set it
        try:
            setattr(feem, "messabsentdays", absent)
        except Exception:
            pass

    # Your FeeMonth likely exposes compute_* with snake_case per services.py/serializers;
    # If names differ, adjust below accordingly.
    if hasattr(feem, "compute_hostel_fee"):
        feem.compute_hostel_fee(room_type=room_type, ac=ac)
    if hasattr(feem, "compute_mess_fee"):
        feem.compute_mess_fee()
    if hasattr(feem, "recompute_totals"):
        feem.recompute_totals()
    feem.save()
    return feem

def _user_room_ctx(user):
    room_type = getattr(user, "room_type", "4 Seater")
    ac_text = (getattr(user, "ac_type", "") or "").strip()
    ac = ac_text in ["A/C", "AC", "Ac", "a/c"]
    return room_type, ac


# ---------- HTML: Student fees page ----------
@login_required
def student_fees(request):
    today = timezone.localdate()
    room_type, ac = _user_room_ctx(request.user)
    feem = ensure_fee_month(request.user, today.year, today.month, room_type, ac)

    total_mess_entries = 30  # replace with real attendance if available
    mess_absent = int(getattr(feem, "mess_absent_days", None) or getattr(feem, "messabsentdays", 0) or 0)
    mess_present = max(0, total_mess_entries - mess_absent)

    ctx = {
        "student": request.user,
        "room_number": getattr(request.user, "room_number", "Not Assigned"),
        "room_type": room_type,
        "ac_type": getattr(request.user, "ac_type", "Not Specified"),
        "total_mess_entries": total_mess_entries,
        "mess_present": mess_present,
        "mess_absent": mess_absent,
        "base_mess_fee": getattr(feem, "base_mess_fee", None) or getattr(feem, "basemessfee", 0),
        "mess_rebate_amount": getattr(feem, "mess_rebate_amount", None) or getattr(feem, "messrebateamount", 0),
        "final_mess_fee": getattr(feem, "final_mess_fee", None) or getattr(feem, "finalmessfee", 0),
        "hostel_fee": getattr(feem, "hostel_fee", None) or getattr(feem, "hostelfee", 0),
        "total_monthly_fee": getattr(feem, "total_monthly_fee", None) or getattr(feem, "totalamount", 0),
        "is_rebate_eligible": getattr(feem, "is_rebate_eligible", None) or getattr(feem, "isrebateeligible", False),
        "feem_id": feem.id,
    }
    return render(request, "fees/student_dashboard_fees.html", ctx)


def _get_student_from_session(request):
    sid = request.session.get("student_id")
    if sid:
        try:
            return Student.objects.get(pk=sid)
        except Student.DoesNotExist:
            return None
    return None

# keep existing decorator and imports
@require_http_methods(["GET","POST"])
def payment_success(request):
    amount   = request.POST.get("amount")
    feem_id  = request.POST.get("feem_id")
    reference = request.POST.get("reference") or request.POST.get("tx_ref") or ""

    # --- ADD 1: absorb default login redirect when next=/fees/success/ ---
    # If the request is a GET and looks like the login-redirect landing (no form data),
    # render a minimal success page instead of letting Django 404 on /accounts/login/.
    if request.method == "GET" and not amount and not feem_id:
        ctx_min = {
            "amount": None,
            "total_monthly_fee": None,
            "tx_ref": None,
            "order_id": None,
            "student": getattr(request, "user", None),
            "hostel_fee": None,
            "final_mess_fee": None,
            "mess_rebate_amount": None,
            "current_month": timezone.localdate().strftime("%B %Y"),
            "is_rebate_eligible": False,
            "mess_absent": 0,
            "base_mess_fee": 0,
        }
        return render(request, "payments/success.html", ctx_min)
    # --- END ADD 1 ---

    # 1) Resolve via FeeMonth (primary)
    feem = None
    student_obj = None
    if feem_id:
        try:
            feem = FeeMonth.objects.select_related("student").get(id=feem_id)  # expects FK named 'student'
            student_obj = getattr(feem, "student", None)
        except FeeMonth.DoesNotExist:
            feem = None

    # 2) Fallback: session set from dashboard
    if student_obj is None:
        student_obj = _get_student_from_session(request)  # safe fallback when feem_id missing

    # 3) Last resort: explicit identifiers in POST
    if student_obj is None:
        admit_no = request.POST.get("admission_number") or ""
        email    = request.POST.get("email") or ""
        if admit_no:
            try:
                student_obj = Student.objects.get(admission_number=admit_no)  # real field on Student
            except Student.DoesNotExist:
                student_obj = None
        if student_obj is None and email:
            try:
                student_obj = Student.objects.get(email=email)  # also a real field
            except Student.DoesNotExist:
                student_obj = None

    # --- ADD 2: remember minimal POST so refresh can render even after redirect ---
    if request.method == "POST":
        request.session["fees_success_cache"] = {
            "amount": amount,
            "feem_id": feem_id,
            "reference": reference,
        }
    # --- END ADD 2 ---

    # If still missing, render with graceful defaults (no crash, shows —)
    if request.method == "POST" and amount:
        if feem is None and feem_id and student_obj:
            # ensure FeeMonth matches the same student to avoid leaking data
            feem = get_object_or_404(FeeMonth, id=feem_id, student=student_obj)

        if feem is not None:
            pay = FeePayment.objects.create(
                feem=feem,
                amount=Decimal(str(amount)),
                method=request.POST.get("method", "online"),
                reference=reference,
                note=request.POST.get("note", ""),
            )
            if hasattr(feem, "recompute_totals"):
                feem.recompute_totals()
            feem.save()
            tx_ref = pay.reference or f"FM{feem.id}-{pay.id}"
            order_id = str(feem.id)
            hostel_fee = getattr(feem, "hostel_fee", None) or getattr(feem, "hostelfee", 0)
            final_mess_fee = getattr(feem, "final_mess_fee", None) or getattr(feem, "finalmessfee", 0)
            mess_rebate_amount = getattr(feem, "mess_rebate_amount", None) or getattr(feem, "messrebateamount", 0)
            is_rebate_eligible = (getattr(feem, "mess_absent", 0) or 0) >= 4
            mess_absent = getattr(feem, "mess_absent", 0) or 0
            base_mess_fee = getattr(feem, "base_mess_fee", None) or getattr(feem, "basemessfee", 0)
        else:
            # no FeeMonth; render with posted values so page still shows
            tx_ref = reference or request.POST.get("tx_ref")
            order_id = request.POST.get("order_id") or request.POST.get("feem_id")
            hostel_fee = request.POST.get("hostel_fee")
            final_mess_fee = request.POST.get("final_mess_fee")
            mess_rebate_amount = request.POST.get("mess_rebate_amount")
            is_rebate_eligible = False
            mess_absent = request.POST.get("mess_absent") or 0
            base_mess_fee = request.POST.get("base_mess_fee") or 0

        ctx = {
            "amount": amount,
            "total_monthly_fee": amount,
            "tx_ref": tx_ref,
            "order_id": order_id,
            "student": student_obj,  # if None, template shows —, not errors
            "hostel_fee": hostel_fee,
            "final_mess_fee": final_mess_fee,
            "mess_rebate_amount": mess_rebate_amount,
            "current_month": timezone.localdate().strftime("%B %Y"),
            "is_rebate_eligible": is_rebate_eligible,
            "mess_absent": mess_absent,
            "base_mess_fee": base_mess_fee,
        }
        return render(request, "payments/success.html", ctx)

    # --- ADD 3: GET fallback uses cached POST if present (after any redirect) ---
    cached = request.session.pop("fees_success_cache", {}) if request.method == "GET" else {}
    amount_cached = cached.get("amount")
    feem_cached   = cached.get("feem_id")
    ref_cached    = cached.get("reference")
    if request.method == "GET" and (amount_cached or ref_cached or feem_cached):
        return render(request, "payments/success.html", {
            "amount": amount_cached,
            "total_monthly_fee": amount_cached,
            "tx_ref": ref_cached,
            "order_id": feem_cached,
            "student": student_obj,
            "hostel_fee": None,
            "final_mess_fee": None,
            "mess_rebate_amount": None,
            "current_month": timezone.localdate().strftime("%B %Y"),
            "is_rebate_eligible": False,
            "mess_absent": 0,
            "base_mess_fee": 0,
        })
    # --- END ADD 3 ---

    # GET or missing amount
    return render(request, "payments/success.html", {
        "amount": amount,
        "total_monthly_fee": amount,
        "tx_ref": reference,
        "order_id": request.POST.get("order_id") or request.POST.get("feem_id"),
        "student": student_obj,
        "hostel_fee": request.POST.get("hostel_fee"),
        "final_mess_fee": request.POST.get("final_mess_fee"),
        "mess_rebate_amount": request.POST.get("mess_rebate_amount"),
        "current_month": timezone.localdate().strftime("%B %Y"),
        "is_rebate_eligible": False,
        "mess_absent": request.POST.get("mess_absent") or 0,
        "base_mess_fee": request.POST.get("base_mess_fee") or 0,
    })


# ---------- HTML: Simple fees board (separate) ----------
@login_required
def fee_board(request):
    today = timezone.localdate()
    feemonths = FeeMonth.objects.filter(year=today.year, month=today.month).select_related("student")
    rows = []
    for f in feemonths:
        user = f.student
        room_type = getattr(user, "room_type", "4 Seater")
        ac_type = getattr(user, "ac_type", "Non A/C")

        total_mess_entries = 30
        mess_absent = int(getattr(f, "mess_absent_days", None) or getattr(f, "messabsentdays", 0) or 0)
        mess_present = max(0, total_mess_entries - mess_absent)

        # Hostel fee calc (example constants)
        base_hostel = 2000
        room_add = {"1 Seater": 1500, "2 Seater": 1000, "3 Seater": 500, "4 Seater": 0}.get(room_type, 0)
        ac_add = 1000 if ac_type in ["A/C", "AC"] else 0
        hostel_fee = base_hostel + room_add + ac_add

        base_mess_fee = getattr(f, "base_mess_fee", None) or getattr(f, "basemessfee", 0)
        rebate = mess_absent * 150 if mess_absent >= 4 else 0
        rebate = min(rebate, base_mess_fee)
        final_mess_fee = base_mess_fee - rebate

        total_monthly_fee = hostel_fee + final_mess_fee

        rows.append({
            "student": {
                "full_name": getattr(user, "get_full_name", lambda: user.username)(),
                "room_number": getattr(user, "room_number", "Not Assigned"),
                "room_type": room_type,
                "ac_type": ac_type,
            },
            "att": {
                "room_present": 0,
                "room_absent": 0,
                "mess_present": mess_present,
                "mess_absent": mess_absent,
                "total_mess_entries": total_mess_entries,
            },
            "fee": {
                "hostel_fee": hostel_fee,
                "base_mess_fee": base_mess_fee,
                "mess_rebate_amount": rebate,
                "final_mess_fee": final_mess_fee,
                "total_monthly_fee": total_monthly_fee,
                "status": f.status,
            },
            "mark_url": f"/admin/fees/feemonth/mark-paid/{f.id}/",
        })

    return render(request, "fees/board.html", {"rows": rows, "month": today.strftime("%B %Y")})


# ---------- API: Student ----------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_dashboard_current(request):
    today = timezone.localdate()
    year, month = today.year, today.month
    student = request.user
    room_type, ac = _user_room_ctx(student)
    feem = ensure_fee_month(student, year, month, room_type, ac)
    data = {
        "hostel_fee": str(getattr(feem, "hostel_fee", None) or getattr(feem, "hostelfee", 0)),
        "base_mess_fee": str(getattr(feem, "base_mess_fee", None) or getattr(feem, "basemessfee", 0)),
        "final_mess_fee": str(getattr(feem, "final_mess_fee", None) or getattr(feem, "finalmessfee", 0)),
        "mess_absent": int(getattr(feem, "mess_absent_days", None) or getattr(feem, "messabsentdays", 0) or 0),
        "mess_rebate_amount": str(getattr(feem, "mess_rebate_amount", None) or getattr(feem, "messrebateamount", 0)),
        "total_monthly_fee": str(getattr(feem, "total_monthly_fee", None) or getattr(feem, "totalamount", 0)),
        "is_rebate_eligible": bool(getattr(feem, "is_rebate_eligible", None) or getattr(feem, "isrebateeligible", False)),
        "due_date": feem.due_date.isoformat() if getattr(feem, "due_date", None) else None,
        "status": feem.status,
        "paid_amount": str(getattr(feem, "paid_amount", None) or getattr(feem, "paidamount", 0)),
        "pending_amount": str(getattr(feem, "pending_amount", None) or getattr(feem, "pendingamount", 0)),
        "feem_id": feem.id,
    }
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_payment_history(request):
    qs = FeeMonth.objects.filter(student=request.user)
    month = request.GET.get("month")
    year = request.GET.get("year")
    status = request.GET.get("status")
    if month:
        qs = qs.filter(month=int(month))
    if year:
        qs = qs.filter(year=int(year))
    if status in {"paid", "unpaid", "overdue"}:
        qs = qs.filter(status=status)
    ser = FeeMonthSerializer(qs.order_by("-year", "-month"), many=True)
    return Response(ser.data)


# ---------- API: Warden/Admin ----------
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def warden_fee_grid(request):
    qs = FeeMonth.objects.all().select_related("student")
    status = request.GET.get("status")
    month = request.GET.get("month")
    year = request.GET.get("year")
    room = request.GET.get("room")
    name = request.GET.get("name")
    fines_only = request.GET.get("fines_only")

    if status in {"paid", "unpaid", "overdue"}:
        qs = qs.filter(status=status)
    if month:
        qs = qs.filter(month=int(month))
    if year:
        qs = qs.filter(year=int(year))
    if room:
        qs = qs.filter(Q(student__room_number__icontains=room))
    if name:
        qs = qs.filter(Q(student__first_name__icontains=name) | Q(student__last_name__icontains=name))
    if fines_only in {"1", "true", "True"}:
        qs = qs.filter(fine_total__gt=0)

    order = request.GET.get("order")
    if order in {"name", "-name"}:
        qs = qs.order_by(("-" if order.startswith("-") else "") + "student__first_name")
    elif order in {"room", "-room"}:
        qs = qs.order_by(("-" if order.startswith("-") else "") + "student__room_number")
    elif order in {"amount", "-amount"}:
        qs = qs.order_by(("-" if order.startswith("-") else "") + "pending_amount")
    elif order in {"status", "-status"}:
        qs = qs.order_by(("-" if order.startswith("-") else "") + "status")
    else:
        qs = qs.order_by("-year", "-month", "student_id")

    ser = FeeMonthSerializer(qs, many=True)
    return Response(ser.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminUser])
def set_due_date(request):
    ids = request.data.get("ids", [])
    due_date = request.data.get("due_date")
    if not ids or not due_date:
        return HttpResponseBadRequest("ids and due_date required")
    updated = FeeMonth.objects.filter(id__in=ids).update(due_date=due_date)
    return Response({"updated": updated})


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminUser])
def send_reminders(request):
    ids = request.data.get("ids", [])
    if not ids:
        return HttpResponseBadRequest("ids required")
    now = timezone.now()
    for fm in FeeMonth.objects.filter(id__in=ids):
        fm.last_reminder_at = now
        fm.save(update_fields=["last_reminder_at"])
    return Response({"count": len(ids), "sent_at": now})


# ---------- API: Payment webhook/success ----------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def record_payment_success(request):
    feem_id = request.data.get("feem_id")
    amount = request.data.get("amount")
    method = request.data.get("method", "online")
    reference = request.data.get("reference", "")
    if not feem_id or not amount:
        return HttpResponseBadRequest("feem_id and amount required")

    feem = get_object_or_404(FeeMonth, id=feem_id, student=request.user)
    pay = FeePayment.objects.create(
        feem=feem,
        amount=Decimal(str(amount)),
        method=method,
        reference=reference,
        note=request.data.get("note", ""),
    )
    if hasattr(feem, "recompute_totals"):
        feem.recompute_totals()
    feem.save()
    return Response(PaymentSerializer(pay).data)
