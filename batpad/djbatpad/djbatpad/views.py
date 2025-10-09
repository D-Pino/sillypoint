from django.shortcuts import render

def home(request):
    return render(request=request, template_name="home.html")


def sim(request):
    return render(request=request, template_name="sim.html")

