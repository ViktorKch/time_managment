from django.contrib import admin
from .models import Status, State, Statistic, Queue, Timetable


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ("title", )


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('get_user', "user", "status", "on_work", )


@admin.register(Statistic)
class StatisticAdmin(admin.ModelAdmin):
    list_display = ('get_user', 'status', 'created_at', 'updated_at', 'get_time', )


@admin.register(Queue)
class QueueAdmin(admin.ModelAdmin):
    list_display = ('get_user', 'on_break', 'updated_at', )


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('break_counter', 'lunch_counter', 'start_time', 'end_time', 'is_active', )