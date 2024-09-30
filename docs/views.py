from django.shortcuts import render
from django.http import HttpRequest, HttpResponse


def docs(request: HttpRequest) -> HttpResponse:
    return render(request, "docs.html")
