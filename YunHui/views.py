from django.shortcuts import render,redirect
from django.shortcuts import HttpResponse
from . import utils
import uuid
from .models import Tieba,User
import time
from django.shortcuts import reverse
import logging

# Create your views here.
stoken = 'e7f5d88e4f9128fe12a5b0d76f9ec21c59a006e1b720bf4dd83c14dd645ad5c1'
logging.basicConfig(filename='./app.log',format='%(asctime)s %(filename)s[line:%(lineno)d] %(message)s',datefmt='%Y-%m-%d')



def index(request):
    if request.method == "GET":
        return render(request,'index.html')
    elif request.method == "POST":
        bduss = request.POST.get('bduss','default')
        if len(bduss) != 192:
            return render(request,'index.html',{'msg':'BDUSS长度错误～'})
        else:
            name,reply,at = utils.getNameReplyAtByBduss(bduss)
            if name:
                token = str(uuid.uuid1())
                try:
                    user = User.objects.get(username=name)
                    user.idDel = False
                    user.bduss=bduss
                except Exception:
                    user = User(bduss=bduss, username=name, token=token)
                finally:
                    user.save()
                    request.session['user'] = user.username
                    request.session['token'] = user.token
                    return redirect(reverse(info))
            else:
                return redirect(reverse(info))

def info(request):
    if request.method == "GET":
        token = request.session.get('token',None)
        if token:
            u = User.objects.get(token=token)
            t = u.tieba_set.all()
            return render(request, 'info.html',{'data':t})
        else:
            return render(request, 'info.html')
    elif request.method == "POST":
        return redirect('/')

def login(request):
    if request.method == "GET":
        return render(request,'login.html')
    elif request.method == "POST":
        val = request.POST.get('unsure')
        print(val)
        if (len(val) != 192) and (len(val) != 36):
            return render(request,'login.html',{'msg':'BDUSS或TOKEN长度错误'})
        elif len(val) == 192:
            try:
                u = User.objects.get(bduss=val)
                request.session['user'] = u.username
                request.session['token'] = u.token
                return redirect(reverse(info))
            except Exception:
                return render(request, 'login.html', {'msg': 'BDUSS错误'})
        elif len(val) == 36:
            try:
                u = User.objects.get(token=val)
                request.session['user'] = u.username
                request.session['token'] = u.token
                return redirect(reverse(info))
            except Exception:
                return render(request, 'login.html', {'msg': 'TOKEN错误'})

def logout(request):
    del request.session['user']
    del request.session['token']
    return redirect(reverse(index))


def delete(request,id):
    if request.method == "POST":
        return HttpResponse("请求方法错误")
    elif request.method == "GET":
        user = request.session.get('user',None)
        if user:
            try:
                u = User.objects.get(username=user)
                t = Tieba.objects.get(id=id, user=u)
                t.delete()
                return redirect(reverse(info))
            except Exception:
                return render(request,'info.html',{'msg':'越权访问'})
        else:
            return render(request,'info.html',{'msg':'未登录'})




def add(request):
    if request.method == 'GET':
        return render(request,'add.html')
    elif request.method == 'POST':
        username = request.session.get('user')
        user = User.objects.get(username=username)
        lou = request.POST.get('lou')
        tid = request.POST.get('tid')
        _time = request.POST.get('time')
        floor = request.POST.get('floor')
        tbna = utils.getFname(tid)
        fid = utils.getFid(tbna)
        if lou == 'yes':
            louBin = True
            Qid = utils.getQid(tid, floor)
        elif lou == 'no':
            louBin = False
            Qid = None
        t = Tieba(name=tbna, fid=fid, tid=tid, isLou=louBin, floor=floor, qid=Qid,time=_time)
        t.save()
        t.user.add(user)
        t.save()
        msg = '帖子'+tid+'添加成功'
        return render(request,'add.html',{'msg':msg})

def about(request):
    return render(request,'about.html')

def do(request):
    u = User.objects.all()
    content = "以下是你的重要信息，请记住"
    for i in u:
        for j in i.tieba_set.all():
            if time.localtime().tm_min % j.time == 0:
                if j.isLou:
                    try:
                        res = utils.LouZhongLou(i.bduss, content, j.name, j.fid, j.tid, j.qid, j.floor)
                        if res['err_code'] == 0:
                            j.success = j.success + 1
                        else:
                            j.fail = j.fail + 1
                    except Exception as e:
                        logging.info(e)
                    finally:
                        j.save()
                else:
                    try:
                        ser = utils.HuiTie(i.bduss, content, j.tid, j.fid, j.name)
                        if ser['err_code'] == 0:
                            j.success = j.success + 1
                        else:
                            j.fail = j.fail + 1
                    except Exception as e:
                        logging.info(e)
                    finally:
                        j.save()
    return HttpResponse('poi~')
