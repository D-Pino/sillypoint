from django.shortcuts import render, get_object_or_404
from .models import Robot
import json


def robot_list(request):
    robots = Robot.objects.all()
    robots_data = {
        "robots": [
            {"id": str(robot.id), "name": robot.name, "company": robot.company, "urdf": robot.urdf} for robot in robots
        ]
    }
    return render(request=request, template_name="list.html", context={"robots": robots, "robots_json": json.dumps(obj=robots_data)})


def robot_detail(request, pk):
    robot = get_object_or_404(klass=Robot, pk=pk)
    robot_data = {"robot": {"id": str(robot.id), "name": robot.name, "company": robot.company, "urdf": robot.urdf}}
    return render(request=request, template_name="detail.html", context={"robot": robot, "robot_json": json.dumps(obj=robot_data)})
