from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from django.shortcuts import render

# Create your views here.
def index(request:HttpRequest):
    return HttpResponse('Main page')

def page_not_found(request:HttpRequest,exception):
    return HttpResponseNotFound('<h1>Ошибка 404</h1><br>Страница не найдена')