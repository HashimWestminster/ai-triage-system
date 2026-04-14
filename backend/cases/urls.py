# cases/urls.py - all the case-related API routes

from django.urls import path
from . import views

urlpatterns = [
    # patient endpoints
    path('submit/', views.PatientSubmitCase.as_view(), name='submit_case'),
    path('my-cases/', views.PatientMyCases.as_view(), name='my_cases'),

    # staff endpoints
    path('list/', views.ClinicianCaseList.as_view(), name='case_list'),
    path('<uuid:id>/', views.CaseDetail.as_view(), name='case_detail'),
    path('<uuid:case_id>/decide/', views.clinician_decide, name='clinician_decide'),
    path('<uuid:case_id>/close/', views.navigator_close_case, name='navigator_close'),

    # dashboard stats
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
]
