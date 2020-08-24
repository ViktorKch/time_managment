from django.db import models
from django.conf import settings
import math


class Status(models.Model):
    title = models.CharField('Статус', max_length=100)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Статус"
        verbose_name_plural = "Статусы"


class State(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.ForeignKey(Status, verbose_name="Статус", on_delete=models.SET_NULL, null=True, blank=True)
    on_work = models.BooleanField('На работе', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_user(self):
        return f'{self.user.first_name} {self.user.last_name}'

    get_user.short_description = 'Сотрудник'

    class Meta:
        verbose_name = "Состояние"
        verbose_name_plural = "Состояния"


class Statistic(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.ForeignKey(Status, verbose_name="Статус", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField('Ушел на перерыв', auto_now_add=True)
    updated_at = models.DateTimeField('Вернулся с перерыва', auto_now=True)
    duration = models.DurationField(null=True, blank=True)

    def get_user(self):
        return f'{self.user.first_name} {self.user.last_name}'

    def get_time(self):
        if self.duration:
            return f'{int(self.duration.total_seconds() // 3600)} ч ' \
                   f'{math.ceil(int(self.duration.total_seconds() % 3600 // 60.0))} мин'
        else:
            return 'Еще не завершен'

    class Meta:
        verbose_name = "Запись статистики"
        verbose_name_plural = "Статистика"

    get_user.short_description = 'Сотрудник'
    get_time.short_description = 'Длительность'


class Queue(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    on_break = models.BooleanField('В очереди', default=False)

    def get_user(self):
        return f'{self.user.first_name} {self.user.last_name}'

    get_user.short_description = 'Сотрудник'

    class Meta:
        verbose_name = "Очередь"
        verbose_name_plural = "Очереди"


class Timetable(models.Model):
    break_counter = models.PositiveIntegerField('Максимальноe число людей на перерыве', blank=True, null=True)
    lunch_counter = models.PositiveIntegerField('Максимальноe число людей на обеде', blank=True, null=True)
    start_time = models.DateTimeField('Дата начала', blank=True, null=True)
    end_time = models.DateTimeField('Дата конца', blank=True, null=True)
    is_active = models.BooleanField('Активно', default=False)


    class Meta:
        verbose_name = "Расписание"
        verbose_name_plural = "Расписания"