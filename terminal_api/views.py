from django.http import JsonResponse
from django.shortcuts import render


def get_user_balance(request):
    print("get_user_balance")
    return JsonResponse({"success": True})


def writing_off_money(request):
    print("writing_off_money")
    return JsonResponse({"success": True})


def create_receipt(request):
    print("create_receipt")
    return JsonResponse({"success": True})