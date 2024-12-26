import threading
import time

def run_in_threads(*functions):
    threads = []
    for func in functions:
        thread = threading.Thread(target=func, name=f"{func.__name__}_thread")
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

# Create a shared event for signaling
stop_event = threading.Event()

def task1():
    for i in range(5):  # Simulate a task with 5 iterations
        if stop_event.is_set():
            print("Task1: Interrupted by Task2.")
            return
        print(f"Task1: Running iteration {i + 1}")
        time.sleep(1)  # Simulate some processing
    print("Task1: Completed execution.")
    stop_event.set()  # Signal other threads to stop

def task2():
    while not stop_event.is_set():
        print("Task2: Running...")
        time.sleep(0.5)  # Simulate continuous processing
    print("Task2: Interrupted by Task1.")

run_in_threads(task1, task2)

print("Both tasks are done.")
