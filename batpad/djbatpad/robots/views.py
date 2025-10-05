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
    return render(request, "list.html", {"robots": robots, "robots_json": json.dumps(robots_data)})


def robot_detail(request, pk):
    robot = get_object_or_404(Robot, pk=pk)
    robot_data = {"robot": {"id": str(robot.id), "name": robot.name, "company": robot.company, "urdf": robot.urdf}}
    return render(request, "detail.html", {"robot": robot, "robot_json": json.dumps(robot_data)})
