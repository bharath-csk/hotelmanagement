from django.urls import path
from . import views

app_name = "fees"

urlpatterns = [
    path("dashboard/current/", views.student_dashboard_current, name="dashboard_current"),
    path("dashboard/history/", views.student_payment_history, name="dashboard_history"),
    path("warden/grid/", views.warden_fee_grid, name="warden_grid"),
    path("warden/due-date/", views.set_due_date, name="set_due_date"),
    path("warden/reminders/", views.send_reminders, name="send_reminders"),
    path("payment/record/", views.record_payment_success, name="record_payment_success"),
    # path("payments/success/", views.payment_success, name="payment_success"),
    path("success/", views.payment_success, name="payment_success"),
    path("payments/success/", views.payment_success, name="payment_success_legacy"),
    path("board/", views.fees_board_admin, name="feeboard"),
    path("mark-attendance/", views.mark_attendance_placeholder, name="mark_attendance"),

]
