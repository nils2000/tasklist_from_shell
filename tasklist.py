import os
import os.path
import pickle
import json
import datetime
from importlib import util
readline_found = False
#from https://stackoverflow.com/a/14050282
if util.find_spec("readline"):
    import readline
    readline_found = True

taskfile = "tasks.txt"
archivedir = "completed_tasks"
archive_prefix = "tasks_"

class SortingFunction:
    def __init__(self,function,reverse=False):
        self.key_function = function
        self.reverse = reverse

class Task:
    def __init__(self,label,priority):
        self.label = label
        self.priority = priority
        self.done_date = None
        self.comment = ""
    def __repr__(self):
        return "Task: label: " + self.label + " priority: " + str(self.priority)
    def finished(self):
        """cleanup before task is archieved"""
        self.done_date = str(datetime.datetime.now())
        if hasattr(self,"group"):
            if self.group != None:
                if self.group.name != "":
                    self.group = self.group.name
            else:
                delattr(self,"group")

class TaskList:
    def __init__(self):
        self.tasks = []
        self.first = None
    def add(self,new_task):
        self.tasks.append(new_task)
        self.task_priority_changed()
    def task_priority_changed(self):
        self.tasks = sorted(self.tasks,key=lambda task:task.priority,reverse=True)
        self.first = self.tasks[0]
    def remove(self,task):
        self.tasks.remove(task)
        if len(self.tasks) == 0:
            self.first = None
        else:
            self.first = self.tasks[0]
    def is_empty(self):
        return (self.first == None)
    def first_task_finished(self):
        old_first = self.first
        self.remove(old_first)
        old_first.finished()
        archive_task(old_first)
    def get_first(self):
        if self.is_empty():
            self.add(read_task())
        return self.first

class TaskGroup():
    def __init__(self,name):
        self.name = name
        self.members = []
    def add(self,task):
        if hasattr(self,"group"):
            raise NotImplementedError("Tasks should only belong to one group, use label instead")
        else:
            self.members.append(task)
            task.group = self

def archive_task(task):
    if not os.path.exists(archivedir):
        os.mkdir(archivedir)
    today = str(datetime.date.today())
    filename = os.path.join(archivedir,archive_prefix+today+".json")
    todays_completed_tasks = []
    if file_exists_and_is_not_empty(filename):
        with open(filename,"r") as fh:
            todays_completed_tasks = json.load(fh)
    todays_completed_tasks += [task,]
    with open(filename,"w") as fh:
        json.dump(todays_completed_tasks,fh,default=lambda o: o.__dict__)

def read_task():
    label = input("Name of the task: ")
    priority = int(input("Priority: "))
    task = Task(label,priority)
    return task

def tasklist_from_file(filename):
    """returns a stored tasklist or an empty tasklist"""
    tasklist = None
    if file_exists_and_is_not_empty(filename):
        with open(filename,"rb") as fh:
            tasklist = pickle.load(fh)
    if tasklist == None:
        tasklist = TaskList()
    return tasklist

def write_tasklist_to_file(tasklist,filename):
    with open(filename,"wb") as fh:
        pickle.dump(tasklist,fh)

def display_task(task):
    print("priority: "+ str(task.priority))
    print("label: "+ task.label)
    try:
        if task.comment != "":
            print("comment: "+ task.comment)
    except AttributeError:
        pass
    try:
        if task.group != None:
            if task.group.name != "":
                print("group: " +task.group.name)
    except AttributeError:
        pass

def edit_task(task,tasklist):
    selection = input("(p:priority/l:label/c:comment)")
    if selection == "p":
        delta = int(input("Please input new priority: ")) - task.priority
        tasks = list()
        if hasattr(task,"group"):
            tasks = task.group.members
        else:
            tasks = [task,]
        print(tasks)
        for t in tasks:
            t.priority += delta
        tasklist.task_priority_changed()
    if selection == "l":
        message = "Please input new label"
        if readline_found:
            readline.add_history(task.label)
            message += "(Arrow up for old label)"
        task.label = input(message+": ")
    if selection == "c":
        message = "Please input new comment"
        if readline_found:
            readline.add_history(task.comment)
            message += "(Arrow up for old comment)"
        task.comment = input(message+": ")

def file_exists_and_is_not_empty(filename):
    return os.path.exists(filename) and os.path.isfile(filename) and os.stat(filename).st_size != 0

tasklist = tasklist_from_file(taskfile)
selection = ""
while True:
    task = tasklist.get_first()
    display_task(task)
    selection = input("(n:new task/f:finish task/c:close/e:edit/l:list/ff:free form):")
    if selection == "c":
        write_tasklist_to_file(tasklist,taskfile)
        #print(json.dumps(tasklist,default=lambda o: o.__dict__))
        break
    if selection == "n":
        new_task = read_task()
        tasklist.add(new_task)
        continue
    if selection == "f":
        tasklist.first_task_finished()
        continue
    if selection == "e":
        edit_task(task,tasklist)
        continue
    if selection == "l":
        for t in tasklist.tasks:
            display_task(t)
    if selection == "ff":
        free_form = input("[Group name:]priority:Task label[->Task 2 label[-> ....]]")
        priority_str,tasklabels = free_form.split(":",1)
        groupname = ""
        try:
            prio = int(priority_str)
            #print(priority_str,tasklabels)
        except ValueError:
            groupname = priority_str
            priority_str,tasklabels = tasklabels.split(":",1)
            prio = int(priority_str)
        (tasklabel,sep,rest) = tasklabels.partition("->")
        #print(tasklabel,"Sept:",sep,"Rest:",rest)
        t = Task(tasklabel,prio)
        tasklist.add(t)
        if sep == "":
            continue
        taskgroup = TaskGroup(groupname)
        taskgroup.add(t)
        #create new Task and task group
        while(sep == "->"):
        #create new Task and add to task group with increased priority each time
            (tasklabel,sep,rest) = rest.partition("->")
            prio -= 1
            t = Task(tasklabel,prio)
            tasklist.add(t)
            taskgroup.add(t)


