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
        self.next = None
        self.prev = None
        self.done_date = None
        self.comment = ""
    def __repr__(self):
        return "Task: label: " + self.label + " priority: " + str(self.priority)
    def add(self,new_task,sorting_function):
        """will return either self or new_task, whichever is more important
        """
        [t1,t2] = sorted([self,new_task],key=sorting_function.key_function,reverse=sorting_function.reverse)
        #print(t1,t2)
        t1.add_below(t2,sorting_function)
        return t1
    def add_below(self,less_important_task,sorting_function):
        if self.next == None:
            self.next = less_important_task
            less_important_task.prev = self
        else:
            self.next = self.next.add(less_important_task,sorting_function)
            self.next.prev = self
    def finished(self):
        ret = self.next
        self.next = None
        self.prev = None
        self.done_date = str(datetime.datetime.now())
        return ret

class TaskList:
    def __init__(self):
        self.first = None
    def add(self,new_task):
        if self.first == None:
            self.first = new_task
        else:
            new_first = self.first.add(new_task,self.sorting_function)
            self.first = new_first
    def remove(self,task):
        p = task.prev
        n = task.next
        task.prev = None
        task.next = None
        if p == None and n == None:
            self.first = None
            return task
        if p == None:
            self.first = n
            n.prev = None
            return task
        if n == None:
            p.next = None
            return task
        p.next = n
        n.prev = p
        return task
    def is_empty(self):
        return (self.first == None)
    def first_task_finished(self):
        old_first = self.first
        self.first = self.first.finished()
        archive_task(old_first)
        del old_first
    def get_first(self):
        if self.first == None:
            self.first = read_task()
        return self.first
    def tasks(self):
        if self.first != None:
            yield(self.first)
            next_task = self.first.next
            while next_task != None:
                yield(next_task)
                next_task = next_task.next

class TaskGroup():
    def __init__(self,name):
        self.name = name
        self.members = []
    def add(self,task):
        if hasattr(task,"group"):
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

def tasklist_from_file(filename,sort_func):
    """returns a stored tasklist or an empty tasklist"""
    tasklist = None
    if file_exists_and_is_not_empty(filename):
        with open(filename,"rb") as fh:
            tasklist = pickle.load(fh)
    if tasklist == None:
        tasklist = TaskList()
    tasklist.sorting_function = sort_func
    return tasklist

def write_tasklist_to_file(tasklist,filename):
    tasklist.sorting_function = None
    with open(filename,"wb") as fh:
        pickle.dump(tasklist,fh)

def display_task(task):
    print("priority: "+ str(task.priority))
    print("label: "+ task.label)
    try:
        print("comment: "+ task.comment)
    except AttributeError:
        task.comment = ""
        print("comment: "+ task.comment)

def edit_task(task,tasklist):
    selection = input("(p:priority/l:label/c:comment)")
    if selection == "p":
        readline.insert_text(str(task.priority))
        task.priority = int(input("Please input new priority: "))
        tasklist.remove(task)
        tasklist.add(task)
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

tasklist = tasklist_from_file(taskfile,SortingFunction(function=lambda task:task.priority,reverse=True))
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
        for t in tasklist.tasks():
            display_task(t)
    if selection == "ff":
        free_form = input("priority:Task label[->Task 2 label[-> ....]]")
        priority_str,tasklabels = free_form.split(":",1)
        #print(priority_str,tasklabels)
        (tasklabel,sep,rest) = tasklabels.partition("->")
        #print(tasklabel,"Sept:",sep,"Rest:",rest)
        prio = int(priority_str)
        tasklist.add(Task(tasklabel,prio))
        if sep != "":
            taskgroup = TaskGroup("")
        #create new Task and task group
        while(sep == "->"):
        #create new Task and add to task group with increased priority each time
            (tasklabel,sep,rest) = rest.partition("->")
            prio -= 1
            t = Task(tasklabel,prio)
            tasklist.add(t)
            taskgroup.add(t)


