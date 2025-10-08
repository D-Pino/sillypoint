from django.shortcuts import render

def home(request):
    return render(request, "home.html")


def sim(request):
    return render(request, "sim.html")

