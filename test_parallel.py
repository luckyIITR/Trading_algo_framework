import threading
import time

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

# Create threads
thread1 = threading.Thread(target=task1)
thread2 = threading.Thread(target=task2)

# Start threads
thread1.start()
thread2.start()

# Wait for threads to complete
thread1.join()
thread2.join()

print("Both tasks are done.")
