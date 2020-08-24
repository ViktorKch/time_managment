from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import login, authenticate
from django.utils import timezone as tz
from django.utils.timezone import localtime
from django_pushall.models import PushUser
from django_pushall import Pushall
import time

from employee_system import settings
from .forms import LoginForm
from .models import Status, State, Statistic, Queue, Timetable
from django.contrib import messages
from datetime import datetime, timedelta, timezone
from django.utils import dateformat
import datetime
import pytz
from datetime import date



def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request,
                                username=cd['username'],
                                password=cd['password'])
        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponse('authenticate successful')
            else:
                return HttpResponse('authenticate failed')
        else:
            return HttpResponse('invalid username or password')
    else:
        form = LoginForm()
    return render(request, 'account/login.html', {'form': form})





@login_required
def dashboard(request):
    free_time = Statistic.objects.filter(user=request.user).filter(created_at__date=date.today()).filter(duration__isnull=False)
    return render(request,
                  'account/dashboard.html',
                  {'section': 'dashboard',
                   'free_time': free_time})


@login_required
def check_state(request):

    pacific = pytz.timezone('Asia/Novosibirsk')
    nine_o_clock = datetime.datetime.strptime('09:00:00', '%H:%M:%S')
    ten_o_clock = datetime.datetime.strptime('10:00:00', '%H:%M:%S')
    hour_o_clock = datetime.datetime.strptime('13:00:00', '%H:%M:%S')
    midnight_1 = datetime.datetime.strptime('1900-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    midnight_2 = datetime.datetime.strptime('1900-01-02 00:00:00', '%Y-%m-%d %H:%M:%S')
    two_o_clock = datetime.datetime.strptime('02:00:00', '%H:%M:%S')
    lunch_counter = len(State.objects.filter(status=Status.objects.get(title='Обед')))
    ex_counter = len(State.objects.filter(status=Status.objects.get(title='Экстренный перерыв')))

    try:
        if Timetable.objects.get(is_active=True):
            check_timetable = Timetable.objects.get(is_active=True)
            if check_timetable.start_time <= tz.now() <= check_timetable.end_time:
                number_of_breaks = {'1': check_timetable.break_counter, '2': check_timetable.break_counter, 'lunch': check_timetable.lunch_counter}

    except:
        number_of_breaks = {'1': 1, '2': 2, 'lunch': 2}



    if ex_counter >= 1:
        number_of_breaks = {'1': 1, '2': 1, 'lunch': 2}
    # elif ex_counter == 0:
    #     number_of_breaks = {'1': 1, '2': 2, 'lunch': 2}

    notificatopn_trigger = 1


    if request.method == 'POST':
        user_state = State.objects.get(user=request.user)
        if 'status' in request.POST:
            if 'lunch' == request.POST.get('status'):
                user_update_state = Status.objects.get(title='Обед')
                humans_on_lunch = len(State.objects.filter(status=user_update_state))
                if State.objects.get(user=request.user).status == Status.objects.get(title='Обед'):
                    messages.info(request, 'Вы уже и так на обеде')
                    return HttpResponseRedirect('/account/table/')
                if State.objects.get(user=request.user).status == Status.objects.get(title='Перерыв'):
                    messages.info(request, 'Вы не можете идти с перерыва на обед')
                    return HttpResponseRedirect('/account/table/')
                if State.objects.get(user=request.user).status == Status.objects.get(title='Экстренный перерыв'):
                    messages.info(request, 'Вы не можете идти с экстренного перерыва на обед')
                    return HttpResponseRedirect('/account/table/')
                if humans_on_lunch >= number_of_breaks['lunch'] and nine_o_clock <= datetime.datetime.\
                        strptime(request.current_time, '%H:%M:%S') <= midnight_2:
                    messages.info(request, 'Превышено допустимое количество сотрудников на обеде. Дождитесь их возвращения.')
                    return HttpResponseRedirect('/account/table/')
                if humans_on_lunch == number_of_breaks['lunch'] and midnight_1 <= datetime.datetime.\
                        strptime(request.current_time, '%H:%M:%S') <= nine_o_clock:
                    messages.info(request, 'Превышено допустимое количество сотрудников на обеде. Дождитесь их возвращения.')
                    return HttpResponseRedirect('/account/table/')
                user_state.status = user_update_state
                user_state.save()
                Statistic.objects.create(user=request.user, status=user_update_state)
            elif 'work' == request.POST.get('status'):
                user_update_state = Status.objects.get(title='Работаю')
                try:
                    user_statistic = Statistic.objects.filter(user=request.user).filter(duration=None).latest(
                        'created_at')
                    user_statistic.duration = localtime(tz.now(), timezone=pacific) - user_statistic.created_at
                    user_statistic.save()
                except:
                    pass
                queue_status = Queue.objects.filter(user=request.user)[0]
                queue_status.on_break = False
                user = User.objects.get(id=request.user.id)
                PushUser.notice_to_user(user, 'Привет', 'Пока')
                user_state.status = user_update_state
                user_state.save()
                queue_status.save()
            elif 'break' == request.POST.get('status'):
                break_status = Status.objects.get(title='Перерыв')
                humans_on_break = len(State.objects.filter(status=break_status))
                if len(Queue.objects.filter(on_break=True)) >= 3:
                    messages.info(request, 'Максимальное число людей в очереди 3. Пожалуйста, попробуйте попозже.')
                    return HttpResponseRedirect('/account/table/')
                if State.objects.get(user=request.user).status == Status.objects.get(title='Перерыв'):
                    messages.info(request, 'Вы уже и так на перерыве')
                    return HttpResponseRedirect('/account/table/')
                if State.objects.get(user=request.user).status == Status.objects.get(title='Обед'):
                    messages.info(request, 'Вы не можете идти с обеда на перерыв')
                    return HttpResponseRedirect('/account/table/')
                if State.objects.get(user=request.user).status == Status.objects.get(title='Экстренный перерыв'):
                    messages.info(request, 'Вы не можете идти с экстренного перерыва на перерыв')
                    return HttpResponseRedirect('/account/table/')
                if nine_o_clock <= datetime.datetime.strptime(request.current_time, '%H:%M:%S') <= ten_o_clock:
                    messages.info(request, 'C 9:00 до 10:00 перерывы запрещены.')
                    return HttpResponseRedirect('/account/table/')
                elif ten_o_clock <= datetime.datetime.strptime(request.current_time, '%H:%M:%S') <= hour_o_clock and humans_on_break < number_of_breaks['1']:
                    if Queue.objects.filter(on_break=True).order_by('updated_at').first() is not None:
                        if request.user != Queue.objects.filter(on_break=True).order_by('updated_at').first().user:
                            messages.info(request, 'Вы не 1-ый в очереди на перерыв')
                            return HttpResponseRedirect('/account/table/')

                    user_update_state = Status.objects.get(title='Перерыв')
                    user_state.status = user_update_state
                    queue_status = Queue.objects.filter(user=request.user)[0]
                    queue_status.on_break = False
                    user_state.save()
                    queue_status.save()
                    Statistic.objects.create(user=request.user, status=user_update_state)
                elif ten_o_clock <= datetime.datetime.strptime(request.current_time, '%H:%M:%S') <= hour_o_clock and humans_on_break == number_of_breaks['1']:
                    messages.info(request, 'Превышено допустимое количество человек на перерыве, Вы помещены в очередь.')
                    queue_status = Queue.objects.filter(user=request.user)[0]

                    if queue_status.on_break:
                        messages.info(request, 'Вы уже в очереди на перерыв')
                    else:
                        queue_status.on_break = True
                        queue_status.save()
                        messages.info(request, 'Вы добавлены в очередь на перерыв')
                    return HttpResponseRedirect('/account/table/')
                elif hour_o_clock <= datetime.datetime.strptime(request.current_time, '%H:%M:%S') <= midnight_2 and humans_on_break < number_of_breaks['2']:
                    queue_status = Queue.objects.filter(user=request.user).first()
                    if Queue.objects.filter(on_break=True).order_by('updated_at').first() is not None:
                        if request.user != Queue.objects.filter(on_break=True).order_by(
                                'updated_at').first().user and queue_status.on_break == False:
                            queue_status.on_break = True
                            queue_status.save()
                            messages.info(request, 'Вы добавлены в очередь на перерыв')
                            return HttpResponseRedirect('/account/table/')
                        elif request.user != Queue.objects.filter(on_break=True).order_by('updated_at').first().user:
                            messages.info(request, 'Вы не 1-ый в очереди на перерыв')
                            return HttpResponseRedirect('/account/table/')
                        elif request.user == Queue.objects.filter(on_break=True).order_by('updated_at').first().user:
                            user_update_state = Status.objects.get(title='Перерыв')
                            user_state.status = user_update_state
                            queue_status = Queue.objects.filter(user=request.user)[0]
                            queue_status.on_break = False
                            user_state.save()
                            queue_status.save()
                            Statistic.objects.create(user=request.user, status=user_update_state)
                        elif queue_status.on_break:
                            messages.info(request, 'Вы уже в очереди на перерыв')
                            return HttpResponseRedirect('/account/table/')
                    else:
                        user_update_state = Status.objects.get(title='Перерыв')
                        user_state.status = user_update_state
                        queue_status = Queue.objects.filter(user=request.user)[0]
                        queue_status.on_break = False
                        user_state.save()
                        queue_status.save()
                        Statistic.objects.create(user=request.user, status=user_update_state)
                elif hour_o_clock <= datetime.datetime.strptime(request.current_time, '%H:%M:%S') <= midnight_2 and humans_on_break == number_of_breaks['2']:
                    messages.info(request, 'Превышено допустимое количество человек на перерыве, Вы помещены в очередь.')
                    queue_status = Queue.objects.filter(user=request.user)[0]

                    if queue_status.on_break:
                        messages.info(request, 'Вы уже в очереди на перерыв')
                    else:
                        queue_status.on_break = True
                        queue_status.save()
                        messages.info(request, 'Вы добавлены в очередь на перерыв')
                    return HttpResponseRedirect('/account/table/')
                elif midnight_1 <= datetime.datetime.strptime(request.current_time, '%H:%M:%S') <= two_o_clock and humans_on_break == number_of_breaks['1']:
                    messages.info(request, 'На перерыве уже есть человек')
                    queue_status = Queue.objects.filter(user=request.user)[0]

                    if queue_status.on_break:
                        messages.info(request, 'Вы уже в очереди на перерыв')
                    else:
                        queue_status.on_break = True
                        queue_status.save()
                        messages.info(request, 'Вы добавлены в очередь на перерыв')
                    return HttpResponseRedirect('/account/table/')
                elif midnight_1 <= datetime.datetime.strptime(request.current_time, '%H:%M:%S') <= two_o_clock and humans_on_break < number_of_breaks['1']:
                    queue_status = Queue.objects.filter(user=request.user).first()
                    if Queue.objects.filter(on_break=True).order_by('updated_at').first() is not None:
                        if request.user != Queue.objects.filter(on_break=True).order_by('updated_at').first().user and queue_status.on_break == False:
                            queue_status.on_break = True
                            queue_status.save()
                            messages.info(request, 'Вы добавлены в очередь на перерыв')
                            return HttpResponseRedirect('/account/table/')
                        elif request.user != Queue.objects.filter(on_break=True).order_by('updated_at').first().user:
                            messages.info(request, 'Вы не 1-ый в очереди на перерыв')
                            return HttpResponseRedirect('/account/table/')
                        elif request.user == Queue.objects.filter(on_break=True).order_by('updated_at').first().user:
                            user_update_state = Status.objects.get(title='Перерыв')
                            user_state.status = user_update_state
                            queue_status = Queue.objects.filter(user=request.user)[0]
                            queue_status.on_break = False
                            user_state.save()
                            queue_status.save()
                            Statistic.objects.create(user=request.user, status=user_update_state)
                        elif queue_status.on_break:
                            messages.info(request, 'Вы уже в очереди на перерыв')
                            return HttpResponseRedirect('/account/table/')
                    else:
                        user_update_state = Status.objects.get(title='Перерыв')
                        user_state.status = user_update_state
                        queue_status = Queue.objects.filter(user=request.user)[0]
                        queue_status.on_break = False
                        user_state.save()
                        queue_status.save()
                        Statistic.objects.create(user=request.user, status=user_update_state)
                elif two_o_clock <= datetime.datetime.strptime(request.current_time, '%H:%M:%S') <= nine_o_clock and humans_on_break < number_of_breaks['1'] and lunch_counter == 0:
                    if Queue.objects.filter(on_break=True).order_by('updated_at').first() is not None:
                        if request.user != Queue.objects.filter(on_break=True).order_by('updated_at').first().user:
                            messages.info(request, 'Вы не 1-ый в очереди на перерыв')
                        return HttpResponseRedirect('/account/table/')
                    else:
                        user_update_state = Status.objects.get(title='Перерыв')
                        user_state.status = user_update_state
                        queue_status = Queue.objects.filter(user=request.user)[0]
                        queue_status.on_break = False
                        user_state.save()
                        queue_status.save()
                        Statistic.objects.create(user=request.user, status=user_update_state)

            elif 'ex_break' == request.POST.get('status'):
                if State.objects.get(user=request.user).status == Status.objects.get(title='Экстренный перерыв'):
                    messages.info(request, 'Вы уже и так на экстренном перерыве')
                    return HttpResponseRedirect('/account/table/')
                if State.objects.get(user=request.user).status == Status.objects.get(title='Перерыв'):
                    messages.info(request, 'Вы не можете идти с перерыва на экстренный перерыв')
                    return HttpResponseRedirect('/account/table/')
                if State.objects.get(user=request.user).status == Status.objects.get(title='Обед'):
                    messages.info(request, 'Вы не можете идти с обеда на экстренный перерыв')
                    return HttpResponseRedirect('/account/table/')
                user_update_state = Status.objects.get(title='Экстренный перерыв')
                user_state.status = user_update_state
                user_state.save()
                Statistic.objects.create(user=request.user, status=user_update_state)
            elif 'on_work' == request.POST.get('status'):
                user_update_state = Status.objects.get(title='Работаю')
                user_state.on_work = True
                user_state.status = user_update_state
                user_state.save()
            elif 'out_work' == request.POST.get('status'):
                user_update_state = Status.objects.get(title='Работаю')
                user_state.on_work = False
                user_state.status = user_update_state
                user_state.save()

    test = Statistic.objects.filter(duration__isnull=False).latest('updated_at').updated_at
    break_status = Status.objects.get(title='Перерыв')
    if Queue.objects.filter(on_break=True).order_by('updated_at').first() is not None:
        if request.user == Queue.objects.filter(on_break=True).order_by('updated_at').first().user and len(State.objects.filter(status=break_status)) <= (number_of_breaks['2'] - 1):
            if datetime.timedelta(seconds=0) <= datetime.datetime.now(tz=pytz.timezone('Asia/Novosibirsk')) - test <= datetime.timedelta(seconds=5):
                user = User.objects.get(id=request.user.id)
                PushUser.notice_to_user(user, 'Уведомление', 'Ты можешь идти на перерыв')
            elif datetime.timedelta(seconds=60) <= datetime.datetime.now(tz=pytz.timezone('Asia/Novosibirsk')) - test <= datetime.timedelta(seconds=65):
                user = User.objects.get(id=request.user.id)
                PushUser.notice_to_user(user, 'Уведомление', 'Ты можешь идти на перерыв')
            elif datetime.timedelta(seconds=115) <= datetime.datetime.now(tz=pytz.timezone('Asia/Novosibirsk')) - test <= datetime.timedelta(seconds=120):
                user = User.objects.get(id=request.user.id)
                PushUser.notice_to_user(user, 'Уведомление', 'Ты можешь идти на перерыв')
            elif datetime.timedelta(seconds=175) <= datetime.datetime.now(tz=pytz.timezone('Asia/Novosibirsk')) - test <= datetime.timedelta(seconds=180):
                user = User.objects.get(id=request.user.id)
                PushUser.notice_to_user(user, 'Уведомление', 'Ты можешь идти на перерыв')


    if State.objects.get(user=request.user).status == Status.objects.get(title='Обед') and \
            datetime.timedelta(seconds=3605) >= datetime.datetime.now(tz=pytz.timezone('UTC'))\
            - State.objects.get(user=request.user).updated_at >= datetime.timedelta(seconds=3600):
        user = User.objects.get(id=request.user.id)
        PushUser.notice_to_user(user, 'Предупреждение', 'Время обеда вышло')
    elif State.objects.get(user=request.user).status == Status.objects.get(title='Обед') and \
            datetime.timedelta(seconds=3605) >= datetime.datetime.now(tz=pytz.timezone('UTC'))\
            - State.objects.get(user=request.user).updated_at >= datetime.timedelta(seconds=3600):
        user = User.objects.get(id=request.user.id)
        PushUser.notice_to_user(user, 'Предупреждение', 'Время обеда вышло')
    elif State.objects.get(user=request.user).status == Status.objects.get(title='Обед') and \
            datetime.timedelta(seconds=3635) >= datetime.datetime.now(tz=pytz.timezone('UTC'))\
            - State.objects.get(user=request.user).updated_at >= datetime.timedelta(seconds=3630):
        user = User.objects.get(id=request.user.id)
        PushUser.notice_to_user(user, 'Предупреждение', 'Время обеда вышло')
    elif State.objects.get(user=request.user).status == Status.objects.get(title='Обед') and \
            datetime.timedelta(seconds=3665) >= datetime.datetime.now(tz=pytz.timezone('UTC'))\
            - State.objects.get(user=request.user).updated_at >= datetime.timedelta(seconds=3660):
        user = User.objects.get(id=request.user.id)
        PushUser.notice_to_user(user, 'Предупреждение', 'Время обеда вышло')
    elif State.objects.get(user=request.user).status == Status.objects.get(title='Обед') and \
            datetime.timedelta(seconds=3695) >= datetime.datetime.now(tz=pytz.timezone('UTC'))\
            - State.objects.get(user=request.user).updated_at >= datetime.timedelta(seconds=3690):
        user = User.objects.get(id=request.user.id)
        PushUser.notice_to_user(user, 'Предупреждение', 'Время обеда вышло')
    elif State.objects.get(user=request.user).status == Status.objects.get(title='Обед') and \
            datetime.datetime.now(tz=pytz.timezone('UTC'))\
            - State.objects.get(user=request.user).updated_at >= datetime.timedelta(seconds=3720):
        user = User.objects.get(id=request.user.id)
        PushUser.notice_to_user(user, 'Предупреждение', 'Время обеда вышло')

    if State.objects.get(user=request.user).status == Status.objects.get(title='Перерыв') and \
            datetime.timedelta(seconds=905) >= datetime.datetime.now(tz=pytz.timezone('UTC')) \
            - State.objects.get(user=request.user).updated_at >= datetime.timedelta(seconds=900):
        user = User.objects.get(id=request.user.id)
        PushUser.notice_to_user(user, 'Предупреждение', 'Время перерыва вышло')
    elif State.objects.get(user=request.user).status == Status.objects.get(title='Перерыв') and \
            datetime.timedelta(seconds=935) >= datetime.datetime.now(tz=pytz.timezone('UTC')) \
            - State.objects.get(user=request.user).updated_at >= datetime.timedelta(seconds=930):
        user = User.objects.get(id=request.user.id)
        PushUser.notice_to_user(user, 'Предупреждение', 'Время перерыва вышло')
    elif State.objects.get(user=request.user).status == Status.objects.get(title='Перерыв') and \
            datetime.timedelta(seconds=965) >= datetime.datetime.now(tz=pytz.timezone('UTC')) \
            - State.objects.get(user=request.user).updated_at >= datetime.timedelta(seconds=960):
        user = User.objects.get(id=request.user.id)
        PushUser.notice_to_user(user, 'Предупреждение', 'Время перерыва вышло')
    elif State.objects.get(user=request.user).status == Status.objects.get(title='Перерыв') and \
            datetime.datetime.now(tz=pytz.timezone('UTC')) \
            - State.objects.get(user=request.user).updated_at >= datetime.timedelta(seconds=995):
        user = User.objects.get(id=request.user.id)
        PushUser.notice_to_user(user, 'Предупреждение', 'Время перерыва вышло')


    break_status = Status.objects.get(title='Перерыв')
    queue_status = Queue.objects.filter(on_break=True).order_by('updated_at')[:3]
    lunch_status = Status.objects.get(title='Обед')
    user_state = State.objects.get(user=request.user)
    all_status = State.objects.filter(on_work=True)
    humans_on_break = len(State.objects.filter(status=break_status))
    person_on_break = State.objects.filter(status=break_status)
    humans_on_lunch = len(State.objects.filter(status=lunch_status))
    humans_on_work = len(all_status)
    return render(request, 'account/table.html', {'stats': all_status, 'user': user_state,
                                                  'humans_on_work': humans_on_work,
                                                  'humans_on_break': humans_on_break,
                                                  'humans_on_lunch': humans_on_lunch,
                                                  'person_on_break': person_on_break,
                                                  'current_time': request.current_time,
                                                  'queue_status': queue_status})

