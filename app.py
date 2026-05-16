from flask import Flask, render_template, request
import os
import re
import ast
import traceback
import textwrap

app = Flask(__name__)

common_modules = {
    'math': 'import math',
    'random': 'import random',
    'json': 'import json',
    'os': 'import os',
    'sys': 'import sys',
    'datetime': 'import datetime',
    're': 'import re',
    'collections': 'from collections import deque',
    # Add more as needed
}

def normalize_text(text):
    return text.lower().strip()

def safe_compile(code):
    try:
        compile(code, "<string>", "exec")
        return True, ""
    except Exception as e:
        return False, str(e)

# Comprehensive hardcoded code generators for a wide variety of program types
# Expanded to cover basics, games, utilities, data structures, and more (now 40+ templates)
# This allows generation of "any" common Python program via keyword prompts. For truly arbitrary, consider LLM integration.
def generate_hello_world_code():
    return """print("Hello, World!")"""

def generate_add_numbers_code():
    return """num1 = float(input("Enter first number: "))
num2 = float(input("Enter second number: "))
sum_result = num1 + num2
print(f"Sum: {sum_result}")"""

def generate_square_root_code():
    return """import math
num = float(input("Enter a number: "))
if num < 0:
    print("Square root not real for negative numbers.")
else:
    sqrt = math.sqrt(num)
    print(f"Square root of {num} is {sqrt}")"""

def generate_fizzbuzz_code():
    return """for i in range(1, 101):
    if i % 3 == 0 and i % 5 == 0:
        print("FizzBuzz")
    elif i % 3 == 0:
        print("Fizz")
    elif i % 5 == 0:
        print("Buzz")
    else:
        print(i)"""

def generate_remove_duplicates_code():
    return """lst = input("Enter list elements separated by space: ").split()
unique = list(dict.fromkeys(lst))  # Preserves order
print(f"List without duplicates: {unique}")"""

def generate_magic_8_ball_code():
    return """import random
answers = [
    "Yes - definitely!",
    "It is certain.",
    "Reply hazy, try again.",
    "Don't count on it.",
    "My sources say no."
]
question = input("Ask a yes/no question: ")
print(random.choice(answers))"""

def generate_pig_latin_code():
    return """def pig_latin(word):
    if word[0] in 'aeiouAEIOU':
        return word + 'way'
    else:
        consonants = ''
        i = 0
        while i < len(word) and word[i] not in 'aeiouAEIOU':
            consonants += word[i]
            i += 1
        return word[i:] + consonants + 'ay'

text = input("Enter a word: ")
print(pig_latin(text))"""

def generate_mad_libs_code():
    return """noun = input("Enter a noun: ")
verb = input("Enter a verb: ")
adjective = input("Enter an adjective: ")
print(f"The {adjective} {noun} {verb} over the moon.")"""

def generate_hangman_code():
    return """import random
words = ['python', 'code', 'hangman', 'game']
word = random.choice(words)
guesses = ''
turns = 6

while turns > 0:
    missing = 0
    for char in word:
        if char in guesses:
            print(char, end='')
        else:
            print('_', end='')
            missing += 1
    if missing == 0:
        print("\\nYou win!")
        break
    guess = input("\\nGuess a letter: ")
    guesses += guess
    if guess not in word:
        turns -= 1
        print(f"Wrong! {turns} turns left.")
else:
    print(f"\\nYou lose! Word was {word}")"""

def generate_tic_tac_toe_code():
    return """board = [' ' for _ in range(9)]

def print_board():
    for row in [board[i*3:(i+1)*3] for i in range(3)]:
        print('|'.join(row))
        if row != board[6:]: print('-' * 5)

def check_win(player):
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    return any(board[a] == board[b] == board[c] == player for a,b,c in wins)

player = 'X'
for _ in range(9):
    print_board()
    pos = int(input(f"Player {player}, choose position (0-8): "))
    if board[pos] == ' ':
        board[pos] = player
        if check_win(player):
            print_board()
            print(f"Player {player} wins!")
            break
        player = 'O' if player == 'X' else 'X'
else:
    print("It's a tie!")"""

def generate_dice_roller_code():
    return """import random
sides = int(input("Enter number of sides: "))
rolls = int(input("Enter number of rolls: "))
for _ in range(rolls):
    print(random.randint(1, sides))"""

def generate_acronym_generator_code():
    return """text = input("Enter phrase: ").split()
acronym = ''.join(word[0].upper() for word in text)
print(acronym)"""

def generate_alarm_clock_code():
    return """import time
alarm_time = input("Set alarm time (HH:MM): ")
while True:
    if time.strftime("%H:%M") == alarm_time:
        print("Wake up!")
        break
    time.sleep(60)"""

def generate_email_slicer_code():
    return """email = input("Enter email: ")
username = email.split('@')[0]
domain = email.split('@')[1]
print(f"Username: {username}, Domain: {domain}")"""

def generate_story_generator_code():
    return """import random
nouns = ['dragon', 'wizard', 'castle']
verbs = ['flew', 'cast', 'entered']
adjs = ['brave', 'mysterious', 'ancient']
story = f"The {random.choice(adjs)} {random.choice(nouns)} {random.choice(verbs)} into the {random.choice(adjs)} {random.choice(nouns)}."
print(story)"""

def generate_qr_code_code():
    return """# Requires 'qrcode' and 'Pillow' - install if needed
import qrcode
data = input("Enter text for QR: ")
qr = qrcode.QRCode(version=1, box_size=10, border=5)
qr.add_data(data)
qr.make(fit=True)
img = qr.make_image(fill='black', back_color='white')
img.save('qr_code.png')
print("QR code saved as qr_code.png")"""

def generate_guess_number_code():
    return """import random
secret = random.randint(1, 100)
guess = 0
while guess != secret:
    guess = int(input("Guess the number (1-100): "))
    if guess < secret:
        print("Too low!")
    elif guess > secret:
        print("Too high!")
print("Correct!")"""

# Existing ones (prime, palindrome, etc.) - keeping for completeness
def generate_prime_code():
    return """def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

num = int(input("Enter a number: "))
if is_prime(num):
    print(f"{num} is a prime number.")
else:
    print(f"{num} is not a prime number.")
"""

def generate_palindrome_code():
    return """def is_palindrome(s):
    return s == s[::-1]

text = input("Enter a string: ").strip().lower()
if is_palindrome(text):
    print(f"'{text}' is a palindrome.")
else:
    print(f"'{text}' is not a palindrome.")
"""

def generate_factorial_code():
    return """def factorial(n):
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)

n = int(input("Enter a non-negative integer: "))
if n < 0:
    print("Factorial is not defined for negative numbers.")
else:
    print(f"Factorial of {n} is {factorial(n)}")
"""

def generate_fibonacci_code():
    return """def fibonacci(n):
    if n <= 0:
        return []
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[-1] + fib[-2])
    return fib

limit = int(input("Enter the number of Fibonacci terms: "))
sequence = fibonacci(limit)
print("Fibonacci sequence:", " ".join(map(str, sequence)))"""

def generate_sort_list_code():
    return """def sort_list(lst):
    return sorted(lst)

numbers = list(map(int, input("Enter numbers separated by space: ").split()))
sorted_nums = sort_list(numbers)
print(f"Sorted list: {sorted_nums}")"""

def generate_calculator_code():
    return """def calculator():
    num1 = float(input("Enter first number: "))
    op = input("Enter operator (+, -, *, /): ")
    num2 = float(input("Enter second number: "))
    
    if op == '+':
        print(f"Result: {num1 + num2}")
    elif op == '-':
        print(f"Result: {num1 - num2}")
    elif op == '*':
        print(f"Result: {num1 * num2}")
    elif op == '/':
        if num2 != 0:
            print(f"Result: {num1 / num2}")
        else:
            print("Error: Division by zero!")
    else:
        print("Invalid operator!")

calculator()
"""

def generate_gcd_code():
    return """def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

num1 = int(input("Enter first number: "))
num2 = int(input("Enter second number: "))
print(f"GCD of {num1} and {num2} is {gcd(num1, num2)}")
"""

def generate_binary_search_code():
    return """def binary_search(arr, target):
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1

numbers = sorted(list(map(int, input("Enter sorted numbers separated by space: ").split())))
target = int(input("Enter target to search: "))
index = binary_search(numbers, target)
if index != -1:
    print(f"Target found at index {index}")
else:
    print("Target not found")
"""

def generate_todo_list_code():
    return """todos = []

def add_todo(task):
    todos.append(task)
    print(f"Added: {task}")

def view_todos():
    if todos:
        print("To-Do List:")
        for i, todo in enumerate(todos, 1):
            print(f"{i}. {todo}")
    else:
        print("No tasks!")

def remove_todo(index):
    if 0 < index <= len(todos):
        removed = todos.pop(index - 1)
        print(f"Removed: {removed}")
    else:
        print("Invalid index!")

while True:
    print("\\n1. Add Task  2. View Tasks  3. Remove Task  4. Quit")
    choice = input("Choose: ")
    if choice == '1':
        task = input("Enter task: ")
        add_todo(task)
    elif choice == '2':
        view_todos()
    elif choice == '3':
        view_todos()
        idx = int(input("Enter index to remove: "))
        remove_todo(idx)
    elif choice == '4':
        break
"""

def generate_file_reader_code():
    return """filename = input("Enter filename: ")
try:
    with open(filename, 'r') as file:
        content = file.read()
        print("File content:")
        print(content)
except FileNotFoundError:
    print("File not found!")
except Exception as e:
    print(f"Error: {e}")
"""

def generate_web_scraper_code():
    return """# Requires 'requests' and 'beautifulsoup4' - install if needed
import requests
from bs4 import BeautifulSoup

url = input("Enter URL: ")
try:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    titles = soup.find_all('h1')
    for title in titles:
        print(title.text.strip())
except Exception as e:
    print(f"Error: {e}")
"""

def generate_linear_search_code():
    return """def linear_search(arr, target):
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1

numbers = list(map(int, input("Enter numbers separated by space: ").split()))
target = int(input("Enter target to search: "))
index = linear_search(numbers, target)
if index != -1:
    print(f"Target found at index {index}")
else:
    print("Target not found")
"""

def generate_matrix_mult_code():
    return """def matrix_multiply(a, b):
    rows_a = len(a)
    cols_a = len(a[0])
    cols_b = len(b[0])
    result = [[0 for _ in range(cols_b)] for _ in range(rows_a)]
    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += a[i][k] * b[k][j]
    return result

mat1 = [[int(x) for x in input("Enter 2x2 matrix A (space-separated): ").split()],
        [int(x) for x in input("Enter next row: ").split()]]
mat2 = [[int(x) for x in input("Enter 2x2 matrix B (space-separated): ").split()],
        [int(x) for x in input("Enter next row: ").split()]]
product = matrix_multiply(mat1, mat2)
print("Product:", product)
"""

def generate_json_parser_code():
    return """import json

json_str = input("Enter JSON string: ")
try:
    data = json.loads(json_str)
    print("Parsed JSON:", data)
    print("Type:", type(data))
except json.JSONDecodeError as e:
    print(f"Invalid JSON: {e}")
"""

def generate_password_gen_code():
    return """import random
import string

def generate_password(length=12):
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))

length = int(input("Enter password length: "))
pwd = generate_password(length)
print(f"Generated Password: {pwd}")
"""

def generate_rock_paper_scissors_code():
    return """import random

choices = ['rock', 'paper', 'scissors']

def play_rps():
    player = input("Enter your choice (rock/paper/scissors): ").lower()
    if player not in choices:
        print("Invalid choice!")
        return
    computer = random.choice(choices)
    print(f"Computer chose: {computer}")
    if player == computer:
        print("Tie!")
    elif (player == 'rock' and computer == 'scissors') or \
         (player == 'paper' and computer == 'rock') or \
         (player == 'scissors' and computer == 'paper'):
        print("You win!")
    else:
        print("Computer wins!")

play_rps()
"""

def generate_bmi_calc_code():
    return """def calculate_bmi(weight_kg, height_m):
    return weight_kg / (height_m ** 2)

weight = float(input("Enter weight in kg: "))
height = float(input("Enter height in meters: "))
bmi = calculate_bmi(weight, height)
print(f"BMI: {bmi:.2f}")
if bmi < 18.5:
    print("Underweight")
elif bmi < 25:
    print("Normal")
else:
    print("Overweight")
"""

def generate_unit_converter_code():
    return """def celsius_to_fahrenheit(c):
    return (c * 9/5) + 32

temp_c = float(input("Enter temperature in Celsius: "))
temp_f = celsius_to_fahrenheit(temp_c)
print(f"{temp_c}°C = {temp_f:.2f}°F")
"""

def generate_simple_gui_code():
    return """import tkinter as tk
from tkinter import messagebox

def show_message():
    messagebox.showinfo("Greeting", "Hello, World!")

root = tk.Tk()
root.title("Simple GUI")
button = tk.Button(root, text="Click Me", command=show_message)
button.pack(pady=20)
root.mainloop()
"""

def generate_sqlite_db_code():
    return """import sqlite3

conn = sqlite3.connect('example.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)''')

name = input("Enter name to insert: ")
cursor.execute("INSERT INTO users (name) VALUES (?)", (name,))
conn.commit()

cursor.execute("SELECT * FROM users")
print("Users:", cursor.fetchall())
conn.close()
"""

def generate_email_sender_code():
    return """import smtplib
from email.mime.text import MIMEText

# Note: Configure SMTP details (use your own)
sender = "your_email@example.com"
receiver = input("Enter receiver email: ")
msg = MIMEText("Hello from generated code!")
msg['Subject'] = "Test Email"
msg['From'] = sender
msg['To'] = receiver

try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender, "your_password")  # Replace with real creds
    server.send_message(msg)
    server.quit()
    print("Email sent!")
except Exception as e:
    print(f"Error: {e}")
"""

def generate_bubble_sort_code():
    return """def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

numbers = list(map(int, input("Enter numbers separated by space: ").split()))
sorted_arr = bubble_sort(numbers)
print(f"Sorted: {sorted_arr}")"""

def generate_linked_list_code():
    return """class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None
    
    def append(self, data):
        new_node = Node(data)
        if not self.head:
            self.head = new_node
            return
        last = self.head
        while last.next:
            last = last.next
        last.next = new_node
    
    def print_list(self):
        temp = self.head
        while temp:
            print(temp.data, end=" -> ")
            temp = temp.next
        print("None")

ll = LinkedList()
ll.append(1)
ll.append(2)
ll.append(3)
ll.print_list()"""

def generate_stack_code():
    return """stack = []

def push(item):
    stack.append(item)
    print(f"Pushed {item}")

def pop():
    if stack:
        return stack.pop()
    return "Stack empty"

def peek():
    return stack[-1] if stack else "Stack empty"

# Example
push(1)
push(2)
print(f"Popped: {pop()}")
print(f"Peek: {peek()}")"""

def generate_queue_code():
    return """from collections import deque

queue = deque()

def enqueue(item):
    queue.append(item)
    print(f"Enqueued {item}")

def dequeue():
    if queue:
        return queue.popleft()
    return "Queue empty"

# Example
enqueue(1)
enqueue(2)
print(f"Dequeued: {dequeue()}")"""

def generate_bfs_graph_code():
    return """from collections import deque

graph = {
    'A': ['B', 'C'],
    'B': ['A', 'D', 'E'],
    'C': ['A', 'F'],
    'D': ['B'],
    'E': ['B', 'F'],
    'F': ['C', 'E']
}

def bfs(start):
    visited = set()
    queue = deque([start])
    visited.add(start)
    while queue:
        node = queue.popleft()
        print(node, end=' ')
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

bfs('A')"""

# Additional DSA generators
def generate_selection_sort_code():
    return """def selection_sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i+1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr

numbers = list(map(int, input("Enter numbers separated by space: ").split()))
sorted_arr = selection_sort(numbers)
print(f"Sorted: {sorted_arr}")"""

def generate_insertion_sort_code():
    return """def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and key < arr[j]:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr

numbers = list(map(int, input("Enter numbers separated by space: ").split()))
sorted_arr = insertion_sort(numbers)
print(f"Sorted: {sorted_arr}")"""

def generate_merge_sort_code():
    return """def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

numbers = list(map(int, input("Enter numbers separated by space: ").split()))
sorted_arr = merge_sort(numbers)
print(f"Sorted: {sorted_arr}")"""

def generate_quick_sort_code():
    return """def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

numbers = list(map(int, input("Enter numbers separated by space: ").split()))
sorted_arr = quick_sort(numbers)
print(f"Sorted: {sorted_arr}")"""

def generate_heap_sort_code():
    return """def heapify(arr, n, i):
    largest = i
    l = 2 * i + 1
    r = 2 * i + 2
    if l < n and arr[l] > arr[largest]:
        largest = l
    if r < n and arr[r] > arr[largest]:
        largest = r
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest)

def heap_sort(arr):
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)
    for i in range(n - 1, 0, -1):
        arr[i], arr[0] = arr[0], arr[i]
        heapify(arr, i, 0)
    return arr

numbers = list(map(int, input("Enter numbers separated by space: ").split()))
sorted_arr = heap_sort(numbers)
print(f"Sorted: {sorted_arr}")"""

def generate_hash_table_code():
    return """class HashTable:
    def __init__(self):
        self.table = [[] for _ in range(10)]

    def hash_function(self, key):
        return hash(key) % len(self.table)

    def insert(self, key, value):
        hash_key = self.hash_function(key)
        key_exists = False
        bucket = self.table[hash_key]
        for i, kv in enumerate(bucket):
            k, v = kv
            if key == k:
                key_exists = True
                break
        if key_exists:
            bucket[i] = ((key, value))
        else:
            bucket.append((key, value))

    def search(self, key):
        hash_key = self.hash_function(key)
        bucket = self.table[hash_key]
        for kv in bucket:
            k, v = kv
            if key == k:
                return v
        return None

ht = HashTable()
ht.insert("key1", "value1")
ht.insert("key2", "value2")
print(ht.search("key1"))"""

def generate_binary_search_tree_code():
    return """class Node:
    def __init__(self, key):
        self.left = None
        self.right = None
        self.val = key

def insert(root, key):
    if root is None:
        return Node(key)
    else:
        if root.val == key:
            return root
        elif root.val < key:
            root.right = insert(root.right, key)
        else:
            root.left = insert(root.left, key)
    return root

def inorder(root):
    if root:
        inorder(root.left)
        print(root.val, end=' ')
        inorder(root.right)

r = Node(50)
r = insert(r, 30)
r = insert(r, 20)
r = insert(r, 40)
r = insert(r, 70)
r = insert(r, 60)
r = insert(r, 80)

print("Inorder traversal:")
inorder(r)"""

def generate_dijkstra_code():
    return """import heapq

def dijkstra(graph, start):
    queue = [(0, start)]
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    while queue:
        current_distance, current_node = heapq.heappop(queue)
        if current_distance > distances[current_node]:
            continue
        for neighbor, weight in graph[current_node].items():
            distance = current_distance + weight
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                heapq.heappush(queue, (distance, neighbor))
    return distances

graph = {
    'A': {'B': 1, 'C': 4},
    'B': {'A': 1, 'C': 2, 'D': 5},
    'C': {'A': 4, 'B': 2, 'D': 1},
    'D': {'B': 5, 'C': 1}
}
print(dijkstra(graph, 'A'))"""

def generate_dynamic_programming_fib_code():
    return """def fib(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 2:
        return 1
    memo[n] = fib(n - 1, memo) + fib(n - 2, memo)
    return memo[n]

n = int(input("Enter n: "))
print(f"Fibonacci({n}): {fib(n)}")"""

def generate_backtracking_nqueens_code():
    return """def solve_nqueens(n):
    board = [['.' for _ in range(n)] for _ in range(n)]
    def is_safe(row, col):
        for i in range(row):
            if board[i][col] == 'Q':
                return False
        for i, j in zip(range(row-1, -1, -1), range(col-1, -1, -1)):
            if board[i][j] == 'Q':
                return False
        for i, j in zip(range(row-1, -1, -1), range(col+1, n)):
            if board[i][j] == 'Q':
                return False
        return True
    def solve(row):
        if row == n:
            print_board()
            return True
        for col in range(n):
            if is_safe(row, col):
                board[row][col] = 'Q'
                if solve(row + 1):
                    return True
                board[row][col] = '.'
        return False
    def print_board():
        for row in board:
            print(' '.join(row))
        print()
    solve(0)

n = int(input("Enter n for N-Queens: "))
solve_nqueens(n)"""


# ── NEW TEMPLATES ─────────────────────────────────────────────────────────────

def generate_caesar_cipher_code():
    return """def caesar_cipher(text, shift, encrypt=True):
    result = ""
    if not encrypt:
        shift = -shift
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            result += chr((ord(char) - base + shift) % 26 + base)
        else:
            result += char
    return result

text = input("Enter text: ")
shift = int(input("Enter shift (1-25): "))
choice = input("Encrypt or Decrypt? (e/d): ").lower()
encrypted = caesar_cipher(text, shift, encrypt=(choice == 'e'))
print(f"Result: {encrypted}")"""

def generate_number_to_words_code():
    return """ones = ['', 'one', 'two', 'three', 'four', 'five', 'six',
        'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve',
        'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen',
        'eighteen', 'nineteen']
teens = ones
tens = ['', '', 'twenty', 'thirty', 'forty', 'fifty',
        'sixty', 'seventy', 'eighty', 'ninety']

def number_to_words(n):
    if n == 0:
        return 'zero'
    if n < 0:
        return 'negative ' + number_to_words(-n)
    if n < 20:
        return ones[n]
    if n < 100:
        return tens[n // 10] + (' ' + ones[n % 10] if n % 10 else '')
    if n < 1000:
        return ones[n // 100] + ' hundred' + (' ' + number_to_words(n % 100) if n % 100 else '')
    return str(n) + ' (out of range for this demo)'

num = int(input("Enter a number (0-999): "))
print(number_to_words(num))"""

def generate_word_frequency_code():
    return """import re
from collections import Counter

text = input("Enter text: ")
words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
freq = Counter(words)
print("\nWord frequencies (top 10):")
for word, count in freq.most_common(10):
    print(f"  {word}: {count}")"""

def generate_temperature_converter_code():
    return """def convert_temp(value, from_unit, to_unit):
    # Convert to Celsius first
    if from_unit == 'f':
        celsius = (value - 32) * 5 / 9
    elif from_unit == 'k':
        celsius = value - 273.15
    else:
        celsius = value
    # Convert from Celsius to target
    if to_unit == 'f':
        return celsius * 9 / 5 + 32
    elif to_unit == 'k':
        return celsius + 273.15
    return celsius

units = {'c': 'Celsius', 'f': 'Fahrenheit', 'k': 'Kelvin'}
val = float(input("Enter temperature value: "))
from_u = input("From unit (c/f/k): ").lower()
to_u = input("To unit (c/f/k): ").lower()
if from_u in units and to_u in units:
    result = convert_temp(val, from_u, to_u)
    print(f"{val}° {units[from_u]} = {result:.2f}° {units[to_u]}")
else:
    print("Invalid unit. Use c, f, or k.")"""

def generate_simple_bank_code():
    return """class BankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance
        self.transactions = []

    def deposit(self, amount):
        if amount <= 0:
            print("Deposit amount must be positive.")
            return
        self.balance += amount
        self.transactions.append(f"Deposit: +{amount}")
        print(f"Deposited {amount}. New balance: {self.balance}")

    def withdraw(self, amount):
        if amount <= 0:
            print("Withdrawal amount must be positive.")
            return
        if amount > self.balance:
            print("Insufficient funds!")
            return
        self.balance -= amount
        self.transactions.append(f"Withdrawal: -{amount}")
        print(f"Withdrew {amount}. New balance: {self.balance}")

    def get_balance(self):
        print(f"Balance: {self.balance}")

    def show_history(self):
        print("Transaction history:")
        for t in self.transactions:
            print(f"  {t}")

name = input("Enter account holder name: ")
account = BankAccount(name)

while True:
    print("\n1. Deposit  2. Withdraw  3. Balance  4. History  5. Quit")
    choice = input("Choose: ")
    if choice == '1':
        account.deposit(float(input("Amount: ")))
    elif choice == '2':
        account.withdraw(float(input("Amount: ")))
    elif choice == '3':
        account.get_balance()
    elif choice == '4':
        account.show_history()
    elif choice == '5':
        break"""

def generate_contact_book_code():
    return """contacts = {}

def add_contact(name, phone, email=""):
    contacts[name] = {'phone': phone, 'email': email}
    print(f"Contact '{name}' added.")

def search_contact(name):
    if name in contacts:
        c = contacts[name]
        print(f"Name: {name}, Phone: {c['phone']}, Email: {c.get('email', 'N/A')}")
    else:
        print("Contact not found.")

def delete_contact(name):
    if name in contacts:
        del contacts[name]
        print(f"Contact '{name}' deleted.")
    else:
        print("Contact not found.")

def list_contacts():
    if contacts:
        for name, info in contacts.items():
            print(f"  {name}: {info['phone']}")
    else:
        print("No contacts saved.")

while True:
    print("\n1. Add  2. Search  3. Delete  4. List  5. Quit")
    choice = input("Choose: ")
    if choice == '1':
        n = input("Name: ")
        p = input("Phone: ")
        e = input("Email (optional): ")
        add_contact(n, p, e)
    elif choice == '2':
        search_contact(input("Search name: "))
    elif choice == '3':
        delete_contact(input("Delete name: "))
    elif choice == '4':
        list_contacts()
    elif choice == '5':
        break"""

def generate_dfs_code():
    return """graph = {
    'A': ['B', 'C'],
    'B': ['A', 'D', 'E'],
    'C': ['A', 'F'],
    'D': ['B'],
    'E': ['B', 'F'],
    'F': ['C', 'E']
}

def dfs_recursive(node, visited=None):
    if visited is None:
        visited = set()
    visited.add(node)
    print(node, end=' ')
    for neighbor in graph.get(node, []):
        if neighbor not in visited:
            dfs_recursive(neighbor, visited)
    return visited

print("DFS traversal:")
dfs_recursive('A')"""

def generate_coin_change_code():
    return """def coin_change(coins, amount):
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    for coin in coins:
        for x in range(coin, amount + 1):
            dp[x] = min(dp[x], dp[x - coin] + 1)
    return dp[amount] if dp[amount] != float('inf') else -1

coins_input = input("Enter coin denominations (space-separated): ")
coins = list(map(int, coins_input.split()))
amount = int(input("Enter target amount: "))
result = coin_change(coins, amount)
if result == -1:
    print("Cannot make that amount with given coins.")
else:
    print(f"Minimum coins needed: {result}")"""


# ── EXTRA TEMPLATES (batch 2) ──────────────────────────────────────────────

def generate_countdown_timer_code():
    return """import time
seconds = int(input("Enter countdown seconds: "))
print(f"Starting countdown from {seconds}...")
for i in range(seconds, 0, -1):
    print(f"{i}...", end=" ", flush=True)
    time.sleep(1)
print("\nTime\'s up!")"""

def generate_number_reverse_code():
    return """num = input("Enter a number: ")
reversed_num = num[::-1]
print(f"Reversed: {reversed_num}")
if num == reversed_num:
    print("It is also a palindrome!")"""

def generate_armstrong_code():
    return """def is_armstrong(n):
    digits = str(n)
    power = len(digits)
    return n == sum(int(d) ** power for d in digits)

num = int(input("Enter a number: "))
if is_armstrong(num):
    print(f"{num} is an Armstrong number.")
else:
    print(f"{num} is not an Armstrong number.")"""

def generate_lcm_code():
    return """import math
a = int(input("Enter first number: "))
b = int(input("Enter second number: "))
lcm = abs(a * b) // math.gcd(a, b)
print(f"LCM of {a} and {b} is {lcm}")"""

def generate_number_patterns_code():
    return """rows = int(input("Enter number of rows: "))
print("Pattern 1 - Right triangle:")
for i in range(1, rows + 1):
    print("* " * i)
print("\nPattern 2 - Pyramid:")
for i in range(1, rows + 1):
    print(" " * (rows - i) + "* " * i)
print("\nPattern 3 - Numbers:")
for i in range(1, rows + 1):
    print(" ".join(str(j) for j in range(1, i + 1)))"""

def generate_anagram_code():
    return """def is_anagram(s1, s2):
    return sorted(s1.lower().replace(" ","")) == sorted(s2.lower().replace(" ",""))

word1 = input("Enter first word: ")
word2 = input("Enter second word: ")
if is_anagram(word1, word2):
    print(f"\"{word1}\" and \"{word2}\" ARE anagrams!")
else:
    print(f"\"{word1}\" and \"{word2}\" are NOT anagrams.")"""

def generate_vowel_counter_code():
    return """text = input("Enter a string: ")
vowels = "aeiouAEIOU"
count = sum(1 for ch in text if ch in vowels)
vowel_list = [ch for ch in text if ch in vowels]
print(f"Vowel count: {count}")
print(f"Vowels found: {', '.join(vowel_list) if vowel_list else 'none'}")"""

def generate_string_reverse_code():
    return """text = input("Enter a string: ")
reversed_text = text[::-1]
print(f"Reversed: {reversed_text}")"""

def generate_multiplication_table_code():
    return """num = int(input("Enter a number: "))
rows = int(input("How many rows? (default 10): ") or 10)
print(f"\nMultiplication table for {num}:")
for i in range(1, rows + 1):
    print(f"  {num} x {i:2} = {num * i}")"""

def generate_even_odd_code():
    return """num = int(input("Enter a number: "))
if num % 2 == 0:
    print(f"{num} is Even")
else:
    print(f"{num} is Odd")"""

def generate_leap_year_code():
    return """year = int(input("Enter a year: "))
if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
    print(f"{year} is a Leap Year.")
else:
    print(f"{year} is NOT a Leap Year.")"""

def generate_sum_digits_code():
    return """num = input("Enter a number: ")
total = sum(int(d) for d in num if d.isdigit())
print(f"Sum of digits in {num}: {total}")"""

def generate_simple_interest_code():
    return """principal = float(input("Enter principal amount: "))
rate = float(input("Enter annual interest rate (%): "))
time = float(input("Enter time in years: "))
si = (principal * rate * time) / 100
print(f"Simple Interest: {si:.2f}")
print(f"Total Amount: {principal + si:.2f}")"""

def generate_compound_interest_code():
    return """principal = float(input("Enter principal amount: "))
rate = float(input("Enter annual interest rate (%): "))
time = float(input("Enter time in years: "))
n = int(input("Compounding frequency per year (e.g. 12 for monthly): "))
amount = principal * (1 + rate / (100 * n)) ** (n * time)
ci = amount - principal
print(f"Compound Interest: {ci:.2f}")
print(f"Total Amount: {amount:.2f}")"""

def generate_area_calculator_code():
    return """import math
print("Area Calculator")
print("1. Circle  2. Rectangle  3. Triangle  4. Square")
choice = input("Choose shape: ")
if choice == "1":
    r = float(input("Enter radius: "))
    print(f"Area of Circle: {math.pi * r ** 2:.2f}")
elif choice == "2":
    l = float(input("Enter length: "))
    w = float(input("Enter width: "))
    print(f"Area of Rectangle: {l * w:.2f}")
elif choice == "3":
    b = float(input("Enter base: "))
    h = float(input("Enter height: "))
    print(f"Area of Triangle: {0.5 * b * h:.2f}")
elif choice == "4":
    s = float(input("Enter side: "))
    print(f"Area of Square: {s ** 2:.2f}")
else:
    print("Invalid choice.")"""

def generate_currency_converter_code():
    return """rates = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "INR": 83.5,
    "JPY": 149.5,
    "CAD": 1.36,
    "AUD": 1.53,
}
print("Available currencies:", ", ".join(rates.keys()))
from_cur = input("Convert FROM: ").upper()
to_cur = input("Convert TO: ").upper()
amount = float(input("Enter amount: "))
if from_cur in rates and to_cur in rates:
    result = amount / rates[from_cur] * rates[to_cur]
    print(f"{amount} {from_cur} = {result:.2f} {to_cur}")
else:
    print("Currency not found.")"""

def generate_prime_range_code():
    return """def sieve_of_eratosthenes(limit):
    primes = [True] * (limit + 1)
    primes[0] = primes[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if primes[i]:
            for j in range(i*i, limit + 1, i):
                primes[j] = False
    return [i for i, is_p in enumerate(primes) if is_p]

limit = int(input("Find all primes up to: "))
result = sieve_of_eratosthenes(limit)
print(f"Found {len(result)} primes up to {limit}:")
print(result)"""

def generate_number_guessing_hard_code():
    return """import random
secret = random.randint(1, 1000)
attempts = 0
max_attempts = 10
print(f"Guess a number between 1 and 1000. You have {max_attempts} attempts.")
while attempts < max_attempts:
    guess = int(input(f"Attempt {attempts+1}/{max_attempts}: "))
    attempts += 1
    if guess == secret:
        print(f"Correct! You got it in {attempts} attempt(s)!")
        break
    elif guess < secret:
        diff = secret - guess
        hint = "very close" if diff < 10 else "close" if diff < 50 else "far"
        print(f"Too low! ({hint})")
    else:
        diff = guess - secret
        hint = "very close" if diff < 10 else "close" if diff < 50 else "far"
        print(f"Too high! ({hint})")
else:
    print(f"Out of attempts! The number was {secret}.")"""

def generate_roman_numeral_code():
    return """def to_roman(num):
    val = [1000,900,500,400,100,90,50,40,10,9,5,4,1]
    syms = ["M","CM","D","CD","C","XC","L","XL","X","IX","V","IV","I"]
    result = ""
    for i in range(len(val)):
        while num >= val[i]:
            result += syms[i]
            num -= val[i]
    return result

def from_roman(s):
    roman = {"I":1,"V":5,"X":10,"L":50,"C":100,"D":500,"M":1000}
    result = 0
    for i in range(len(s)):
        if i + 1 < len(s) and roman[s[i]] < roman[s[i+1]]:
            result -= roman[s[i]]
        else:
            result += roman[s[i]]
    return result

choice = input("Convert to Roman (r) or from Roman (f)? ").lower()
if choice == "r":
    n = int(input("Enter integer (1-3999): "))
    print(f"Roman numeral: {to_roman(n)}")
elif choice == "f":
    r = input("Enter Roman numeral: ").upper()
    print(f"Integer value: {from_roman(r)}")"""

def generate_typing_speed_code():
    return """import time, random
sentences = [
    "The quick brown fox jumps over the lazy dog",
    "Python is a great programming language",
    "Practice makes perfect every single day",
]
sentence = random.choice(sentences)
print(f"Type this sentence:\n\n  {sentence}\n")
input("Press Enter when ready...")
start = time.time()
typed = input(">>> ")
end = time.time()
elapsed = end - start
words = len(sentence.split())
wpm = (words / elapsed) * 60
accuracy = sum(a == b for a, b in zip(typed, sentence)) / len(sentence) * 100
print(f"\nTime: {elapsed:.2f}s | WPM: {wpm:.1f} | Accuracy: {accuracy:.1f}%")
if typed == sentence:
    print("Perfect typing!")"""

def generate_morse_code_code():
    return """MORSE = {
    'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.','H':'....','I':'..','J':'.---',
    'K':'-.-','L':'.-..','M':'--','N':'-.','O':'---','P':'.--.','Q':'--.-','R':'.-.','S':'...','T':'-',
    'U':'..-','V':'...-','W':'.--','X':'-..-','Y':'-.--','Z':'--..',
    '0':'-----','1':'.----','2':'..---','3':'...--','4':'....-','5':'.....','6':'-....','7':'--...','8':'---..','9':'----.'
}
REVERSE = {v: k for k, v in MORSE.items()}

def encode(text):
    return ' '.join(MORSE.get(c.upper(), '?') for c in text if c != ' ')

def decode(code):
    return ''.join(REVERSE.get(c, '?') for c in code.split())

choice = input("Encode (e) or Decode (d)? ").lower()
if choice == 'e':
    text = input("Enter text: ")
    print(f"Morse code: {encode(text)}")
elif choice == 'd':
    code = input("Enter morse code (space-separated): ")
    print(f"Decoded: {decode(code)}")"""

def generate_snake_game_code():
    return """# Snake game - requires a terminal that supports ANSI codes
import random, time, sys

try:
    import curses
except ImportError:
    print("curses not available on this system.")
    sys.exit()

def main(stdscr):
    curses.curs_set(0)
    sh, sw = stdscr.getmaxyx()
    w = curses.newwin(sh, sw, 0, 0)
    w.keypad(1)
    w.timeout(100)

    snk_x = sw // 4
    snk_y = sh // 2
    snake = [[snk_y, snk_x], [snk_y, snk_x-1], [snk_y, snk_x-2]]
    food = [sh//2, sw//2]
    w.addch(food[0], food[1], curses.ACS_PI)
    score = 0
    key = curses.KEY_RIGHT

    while True:
        next_key = w.getch()
        key = key if next_key == -1 else next_key
        if key == curses.KEY_DOWN:   new = [snake[0][0]+1, snake[0][1]]
        elif key == curses.KEY_UP:   new = [snake[0][0]-1, snake[0][1]]
        elif key == curses.KEY_LEFT: new = [snake[0][0], snake[0][1]-1]
        elif key == curses.KEY_RIGHT:new = [snake[0][0], snake[0][1]+1]
        else: break
        snake.insert(0, new)
        if snake[0] == food:
            score += 1
            food = [random.randint(1,sh-2), random.randint(1,sw-2)]
            w.addch(food[0], food[1], curses.ACS_PI)
        else:
            tail = snake.pop()
            w.addch(tail[0], tail[1], ' ')
        if (snake[0][0] in [0,sh] or snake[0][1] in [0,sw] or snake[0] in snake[1:]):
            break
        w.addch(snake[0][0], snake[0][1], '#')
    stdscr.addstr(sh//2, sw//2-10, f"Game Over! Score: {score}")
    stdscr.refresh()
    time.sleep(2)

curses.wrapper(main)"""

def generate_calendar_code():
    return """import calendar
year = int(input("Enter year: "))
month = int(input("Enter month (1-12): "))
print()
print(calendar.month(year, month))
print(f"This month has {calendar.monthrange(year, month)[1]} days.")
if calendar.isleap(year):
    print(f"{year} is a leap year.")"""
def generate_print_hari_code():
    return """print("Hari")"""
def generate_text_statistics_code():
    return """text = input("Enter your text: ")
words = text.split()
sentences = text.count('.') + text.count('!') + text.count('?')
chars = len(text)
chars_no_space = len(text.replace(' ', ''))
unique_words = len(set(w.lower().strip('.,!?') for w in words))
avg_word_len = sum(len(w) for w in words) / len(words) if words else 0

print(f"\n--- Text Statistics ---")
print(f"Characters (with spaces): {chars}")
print(f"Characters (no spaces):   {chars_no_space}")
print(f"Words:                    {len(words)}")
print(f"Unique words:             {unique_words}")
print(f"Sentences:                {sentences}")
print(f"Avg word length:          {avg_word_len:.1f} chars")"""

def generate_number_base_converter_code():
    return """print("Number Base Converter")
num = input("Enter a number: ")
from_base = int(input("From base (2/8/10/16): "))
to_base = int(input("To base (2/8/10/16): "))
try:
    decimal = int(num, from_base)
    if to_base == 2:
        result = bin(decimal)[2:]
    elif to_base == 8:
        result = oct(decimal)[2:]
    elif to_base == 10:
        result = str(decimal)
    elif to_base == 16:
        result = hex(decimal)[2:].upper()
    else:
        result = "Unsupported base"
    print(f"{num} (base {from_base}) = {result} (base {to_base})")
except ValueError:
    print("Invalid number for the given base.")"""

def generate_random_quote_code():
    return """import random
quotes = [
    ("The only way to do great work is to love what you do.", "Steve Jobs"),
    ("In the middle of every difficulty lies opportunity.", "Albert Einstein"),
    ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
    ("Life is what happens when you're busy making other plans.", "John Lennon"),
    ("The future belongs to those who believe in their dreams.", "Eleanor Roosevelt"),
    ("Success is not final, failure is not fatal: it is the courage to continue.", "Churchill"),
    ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
    ("Act as if what you do makes a difference. It does.", "William James"),
]
quote, author = random.choice(quotes)
print(f"\n\"{quote}\"")
print(f"  — {author}")"""

def generate_simple_encryption_code():
    return """def xor_encrypt(text, key):
    return ''.join(chr(ord(c) ^ key) for c in text)

key = int(input("Enter encryption key (1-255): "))
message = input("Enter message to encrypt: ")
encrypted = xor_encrypt(message, key)
print(f"Encrypted (as chars): {encrypted}")
print(f"Encrypted (as codes): {[ord(c) for c in encrypted]}")
decrypted = xor_encrypt(encrypted, key)
print(f"Decrypted back: {decrypted}")"""

def generate_list_operations_code():
    return """def show_menu():
    print("\n1. Add  2. Remove  3. Sort  4. Reverse  5. Search  6. Stats  7. Show  8. Quit")

my_list = []
while True:
    show_menu()
    choice = input("Choose: ")
    if choice == '1':
        item = input("Enter item: ")
        my_list.append(item)
        print(f"Added. List has {len(my_list)} item(s).")
    elif choice == '2':
        item = input("Enter item to remove: ")
        if item in my_list:
            my_list.remove(item)
            print("Removed.")
        else:
            print("Not found.")
    elif choice == '3':
        my_list.sort()
        print("Sorted.")
    elif choice == '4':
        my_list.reverse()
        print("Reversed.")
    elif choice == '5':
        item = input("Search for: ")
        if item in my_list:
            print(f"Found at index {my_list.index(item)}.")
        else:
            print("Not found.")
    elif choice == '6':
        print(f"Count: {len(my_list)}")
        if my_list:
            try:
                nums = list(map(float, my_list))
                print(f"Sum: {sum(nums)}, Min: {min(nums)}, Max: {max(nums)}, Avg: {sum(nums)/len(nums):.2f}")
            except ValueError:
                print("(numeric stats only available for number lists)")
    elif choice == '7':
        print(f"List: {my_list}")
    elif choice == '8':
        break"""

def generate_stopwatch_code():
    return """import time
print("Simple Stopwatch")
print("Press Enter to start/stop, type 'q' and Enter to quit.")
running = False
start_time = 0
elapsed = 0
while True:
    cmd = input()
    if cmd.lower() == 'q':
        break
    if not running:
        start_time = time.time() - elapsed
        running = True
        print("  ▶ Running...")
    else:
        elapsed = time.time() - start_time
        running = False
        mins = int(elapsed // 60)
        secs = elapsed % 60
        print(f"  ■ Stopped: {mins:02d}:{secs:05.2f}")"""

def generate_mini_quiz_code():
    return """import random
questions = [
    ("What is the capital of France?", ["London","Paris","Berlin","Madrid"], 1),
    ("Which planet is closest to the Sun?", ["Venus","Earth","Mercury","Mars"], 2),
    ("What is 12 x 12?", ["132","144","154","124"], 1),
    ("Who wrote Romeo and Juliet?", ["Dickens","Shakespeare","Hemingway","Twain"], 1),
    ("What is H2O?", ["Oxygen","Hydrogen","Water","Salt"], 2),
]
random.shuffle(questions)
score = 0
print("=== Mini Quiz ===\n")
for i, (q, opts, ans) in enumerate(questions, 1):
    print(f"Q{i}: {q}")
    for j, opt in enumerate(opts):
        print(f"  {j}. {opt}")
    try:
        choice = int(input("Your answer (0-3): "))
        if choice == ans:
            print("Correct!\n")
            score += 1
        else:
            print(f"Wrong! Answer was: {opts[ans]}\n")
    except ValueError:
        print("Invalid input, skipping.\n")
print(f"Final Score: {score}/{len(questions)}")"""

def generate_number_properties_code():
    return """num = int(input("Enter a number: "))
print(f"\nProperties of {num}:")
print(f"  Even/Odd:     {'Even' if num % 2 == 0 else 'Odd'}")
print(f"  Positive:     {num > 0}")
print(f"  Perfect sq:   {int(num**0.5)**2 == num}")

def is_prime(n):
    if n < 2: return False
    return all(n % i != 0 for i in range(2, int(n**0.5)+1))
print(f"  Prime:        {is_prime(num)}")

digits = [int(d) for d in str(abs(num))]
print(f"  Digit sum:    {sum(digits)}")
print(f"  Digit count:  {len(digits)}")
print(f"  Reversed:     {int(str(abs(num))[::-1])}")
print(f"  Binary:       {bin(num)}")
print(f"  Octal:        {oct(num)}")
print(f"  Hex:          {hex(num)}")"""

# Enhanced keyword-based generation with extensive patterns
def generate_code(prompt):
    p = normalize_text(prompt)
    
    # New basic examples
    if any(word in p for word in ["hello world", "print hello"]):
        return generate_hello_world_code()
    elif any(word in p for word in ["add numbers", "sum two numbers"]):
        return generate_add_numbers_code()
    elif any(word in p for word in ["square root", "sqrt"]):
        return generate_square_root_code()
    elif "fizzbuzz" in p:
        return generate_fizzbuzz_code()
    elif any(word in p for word in ["remove duplicates", "unique list"]):
        return generate_remove_duplicates_code()
    elif "magic 8 ball" in p:
        return generate_magic_8_ball_code()
    elif "pig latin" in p:
        return generate_pig_latin_code()
    elif "mad libs" in p:
        return generate_mad_libs_code()
    elif any(k in prompt for k in ['hari', 'print hari']):
        return generate_print_hari_code()
    elif "hangman" in p:
        return generate_hangman_code()
    elif "tic tac toe" in p:
        return generate_tic_tac_toe_code()
    elif any(word in p for word in ["dice roller", "roll dice"]):
        return generate_dice_roller_code()
    elif "acronym generator" in p:
        return generate_acronym_generator_code()
    elif "alarm clock" in p:
        return generate_alarm_clock_code()
    elif "email slicer" in p:
        return generate_email_slicer_code()
    elif "story generator" in p:
        return generate_story_generator_code()
    elif "qr code" in p:
        return generate_qr_code_code()
    elif any(word in p for word in ["guess number", "number guessing"]):
        return generate_guess_number_code()
    elif "bubble sort" in p:
        return generate_bubble_sort_code()
    elif "linked list" in p:
        return generate_linked_list_code()
    elif any(word in p for word in ["stack implementation", "stack data", "lifo", "implement stack", "stack program"]):
        return generate_stack_code()
    elif any(word in p for word in ["queue implementation", "queue data", "fifo", "implement queue", "queue program"]):
        return generate_queue_code()
    elif any(word in p for word in ["bfs", "breadth first search"]):
        return generate_bfs_graph_code()
    elif any(word in p for word in ["prime", "check prime", "prime number"]):
        return generate_prime_code()
    elif any(word in p for word in ["palindrome", "check palindrome"]):
        return generate_palindrome_code()
    elif any(word in p for word in ["factorial", "compute factorial"]):
        return generate_factorial_code()
    elif any(word in p for word in ["fibonacci", "fib sequence"]):
        return generate_fibonacci_code()
    elif any(word in p for word in ["sort list", "sorted list", "sort numbers"]):
        return generate_sort_list_code()
    elif any(word in p for word in ["calculator", "simple calc", "arithmetic"]):
        return generate_calculator_code()
    elif any(word in p for word in ["gcd", "greatest common divisor"]):
        return generate_gcd_code()
    elif any(word in p for word in ["binary search", "search array"]):
        return generate_binary_search_code()
    elif any(word in p for word in ["todo", "to-do list", "task manager"]):
        return generate_todo_list_code()
    elif any(word in p for word in ["file reader", "read file"]):
        return generate_file_reader_code()
    elif any(word in p for word in ["scraper", "web scrape", "parse website"]):
        return generate_web_scraper_code()
    elif any(word in p for word in ["linear search", "sequential search"]):
        return generate_linear_search_code()
    elif any(word in p for word in ["matrix multiply", "matrix multiplication"]):
        return generate_matrix_mult_code()
    elif any(word in p for word in ["json parser", "parse json", "json validator"]):
        return generate_json_parser_code()
    elif any(word in p for word in ["password generator", "gen password"]):
        return generate_password_gen_code()
    elif any(word in p for word in ["rock paper scissors", "rps game"]):
        return generate_rock_paper_scissors_code()
    elif any(word in p for word in ["bmi calculator", "body mass index"]):
        return generate_bmi_calc_code()
    elif any(word in p for word in ["unit converter", "convert units", "celsius fahrenheit"]):
        return generate_unit_converter_code()
    elif any(word in p for word in ["simple gui", "tkinter window"]):
        return generate_simple_gui_code()
    elif any(word in p for word in ["sqlite", "database", "sql table"]):
        return generate_sqlite_db_code()
    elif any(word in p for word in ["email sender", "send email"]):
        return generate_email_sender_code()
    elif "selection sort" in p:
        return generate_selection_sort_code()
    elif "insertion sort" in p:
        return generate_insertion_sort_code()
    elif "merge sort" in p:
        return generate_merge_sort_code()
    elif "quick sort" in p:
        return generate_quick_sort_code()
    elif "heap sort" in p:
        return generate_heap_sort_code()
    elif any(word in p for word in ["hash table", "hash map"]):
        return generate_hash_table_code()
    elif any(word in p for word in ["binary search tree", "bst"]):
        return generate_binary_search_tree_code()
    elif "dijkstra" in p:
        return generate_dijkstra_code()
    elif any(word in p for word in ["dynamic programming fib", "dp fib"]):
        return generate_dynamic_programming_fib_code()
    elif "n queens" in p or "backtracking nqueens" in p:
        return generate_backtracking_nqueens_code()
    elif any(word in p for word in ["caesar cipher", "caesar", "shift cipher"]):
        return generate_caesar_cipher_code()
    elif any(word in p for word in ["number to words", "num to words", "numbers to words"]):
        return generate_number_to_words_code()
    elif any(word in p for word in ["word frequency", "word count", "count words"]):
        return generate_word_frequency_code()
    elif any(word in p for word in ["temperature converter", "temp converter", "convert temperature"]):
        return generate_temperature_converter_code()
    elif any(word in p for word in ["bank account", "simple bank", "banking system"]):
        return generate_simple_bank_code()
    elif any(word in p for word in ["contact book", "phonebook", "address book", "contact manager"]):
        return generate_contact_book_code()
    elif any(word in p for word in ["dfs", "depth first search"]):
        return generate_dfs_code()
    elif any(word in p for word in ["coin change", "minimum coins", "dp coin"]):
        return generate_coin_change_code()

    # ── Batch 2 keywords ──
    elif any(word in p for word in ["countdown timer", "countdown"]):
        return generate_countdown_timer_code()
    elif any(word in p for word in ["reverse number", "number reverse"]):
        return generate_number_reverse_code()
    elif any(word in p for word in ["armstrong", "narcissistic number"]):
        return generate_armstrong_code()
    elif any(word in p for word in ["lcm", "least common multiple"]):
        return generate_lcm_code()
    elif any(word in p for word in ["number pattern", "star pattern", "pyramid pattern"]):
        return generate_number_patterns_code()
    elif any(word in p for word in ["anagram", "check anagram"]):
        return generate_anagram_code()
    elif any(word in p for word in ["vowel counter", "count vowels"]):
        return generate_vowel_counter_code()
    elif any(word in p for word in ["reverse string", "string reverse"]):
        return generate_string_reverse_code()
    elif any(word in p for word in ["multiplication table", "times table"]):
        return generate_multiplication_table_code()
    elif any(word in p for word in ["even odd", "check even", "check odd"]):
        return generate_even_odd_code()
    elif any(word in p for word in ["leap year", "check leap"]):
        return generate_leap_year_code()
    elif any(word in p for word in ["sum of digits", "digit sum"]):
        return generate_sum_digits_code()
    elif any(word in p for word in ["simple interest", "si calculator"]):
        return generate_simple_interest_code()
    elif any(word in p for word in ["compound interest", "ci calculator"]):
        return generate_compound_interest_code()
    elif any(word in p for word in ["area calculator", "shape area", "calculate area"]):
        return generate_area_calculator_code()
    elif any(word in p for word in ["currency converter", "convert currency", "exchange rate"]):
        return generate_currency_converter_code()
    elif any(word in p for word in ["prime range", "sieve", "primes up to", "sieve of eratosthenes"]):
        return generate_prime_range_code()
    elif any(word in p for word in ["hard guess", "number guessing hard", "guess 1000"]):
        return generate_number_guessing_hard_code()
    elif any(word in p for word in ["roman numeral", "roman number", "to roman"]):
        return generate_roman_numeral_code()
    elif any(word in p for word in ["typing speed", "typing test", "wpm test"]):
        return generate_typing_speed_code()
    elif any(word in p for word in ["morse code", "encode morse", "decode morse"]):
        return generate_morse_code_code()
    elif any(word in p for word in ["snake game", "snake curses"]):
        return generate_snake_game_code()
    elif any(word in p for word in ["calendar", "show calendar", "monthly calendar"]):
        return generate_calendar_code()
    elif any(word in p for word in ["text statistics", "text stats", "word stats"]):
        return generate_text_statistics_code()
    elif any(word in p for word in ["base converter", "number base", "binary to decimal", "decimal to binary"]):
        return generate_number_base_converter_code()
    elif any(word in p for word in ["random quote", "quote generator", "inspirational quote"]):
        return generate_random_quote_code()
    elif any(word in p for word in ["simple encryption", "xor encrypt", "xor cipher"]):
        return generate_simple_encryption_code()
    elif any(word in p for word in ["list operations", "list manager", "list menu"]):
        return generate_list_operations_code()
    elif any(word in p for word in ["stopwatch", "simple stopwatch"]):
        return generate_stopwatch_code()
    elif any(word in p for word in ["quiz", "mini quiz", "trivia"]):
        return generate_mini_quiz_code()
    elif any(word in p for word in ["number properties", "properties of number"]):
        return generate_number_properties_code()

    else:
        # Enhanced fallback with full list of supported types (updated with new DSA)
        supported = [
            "hello world", "add numbers", "square root", "fizzbuzz", "remove duplicates", "magic 8 ball",
            "pig latin", "mad libs", "hangman", "tic tac toe", "dice roller", "acronym generator",
            "alarm clock", "email slicer", "story generator", "qr code", "guess number", "bubble sort",
            "linked list", "stack", "queue", "bfs graph", "prime check", "palindrome", "factorial",
            "fibonacci", "sort list", "calculator", "gcd", "binary search", "todo list", "file reader",
            "web scraper", "linear search", "matrix mult", "json parser", "password gen", "rock paper scissors",
            "bmi calc", "unit converter", "simple gui", "sqlite db", "email sender", "selection sort",
            "insertion sort", "merge sort", "quick sort", "heap sort", "hash table", "binary search tree",
            "dijkstra", "dynamic programming fib", "n queens",
            "caesar cipher", "number to words", "word frequency",
            "temperature converter", "bank account", "contact book",
            "dfs", "coin change", "countdown timer", "armstrong", "lcm",
            "number pattern", "anagram", "vowel counter", "reverse string",
            "multiplication table", "even odd", "leap year", "sum of digits",
            "simple interest", "compound interest", "area calculator",
            "currency converter", "prime range", "roman numeral",
            "typing speed", "morse code", "snake game", "calendar",
            "text statistics", "base converter", "random quote",
            "simple encryption", "list operations", "stopwatch",
            "mini quiz", "number properties"
        ]
        return f"""# Generated based on prompt: "{prompt}"
# This is a basic Python template. For custom programs, use keywords from supported types: {', '.join(supported[:10])}... (see full list in code).

def main():
    # Your logic here
    print("Hello from generated code!")
    # Example: user_input = input("Enter something: ")
    # Process user_input...

if __name__ == "__main__":
    main()
"""

class VariableVisitor(ast.NodeVisitor):
    def __init__(self):
        self.assigned = set()
        self.used = set()
        self.functions = 0
        self.loops = 0
        self.conditionals = 0
        self.imports = set()
        self.potential_missing_imports = set()

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.assigned.add(target.id)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used.add(node.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.functions += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.loops += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.loops += 1
        self.generic_visit(node)

    def visit_If(self, node):
        self.conditionals += 1
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.imports.add(node.module.split('.')[0])
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name):
            module_name = node.value.id
            if module_name not in self.imports and module_name not in self.assigned:
                self.potential_missing_imports.add(module_name)
        self.generic_visit(node)

def review_code(code):
    issues = []
    summary = []
    try:
        tree = ast.parse(code)
        visitor = VariableVisitor()
        visitor.visit(tree)

        unused = visitor.assigned - visitor.used
        if unused:
            issues.append(f"Unused variables: {', '.join(unused)}. These are assigned but never used, which might indicate dead code or a bug.")

        import builtins
        undefined = (visitor.used - visitor.assigned - set(dir(builtins))) - visitor.imports
        if visitor.potential_missing_imports:
            issues.append(f"Potential missing imports: {', '.join(visitor.potential_missing_imports)}. These look like module names used without import statements.")

        summary.append(f"Code structure summary:")
        summary.append(f"- Total lines: {len(code.splitlines())}")
        summary.append(f"- Functions defined: {visitor.functions}")
        summary.append(f"- Loops (for/while): {visitor.loops}")
        summary.append(f"- Conditionals (if/elif/else): {visitor.conditionals}")
        summary.append(f"- Imports: {', '.join(visitor.imports) if visitor.imports else 'None'}")

        # AST-based: check if any FunctionDef has a Return node
        has_return = any(
            isinstance(node, ast.Return)
            for node in ast.walk(tree)
        )
        if visitor.functions > 0 and not has_return:
            issues.append("Functions defined but no explicit 'return' statements found. This is fine if functions only print/mutate, but add returns where values are needed.")

        if 'while True' in code and 'break' not in code:
            issues.append("Potential infinite loop: 'while True' without a 'break' statement.")

        # Check for bare 'except:' (catches everything including KeyboardInterrupt)
        for i, line in enumerate(code.splitlines(), 1):
            stripped = line.strip()
            if stripped == 'except:':
                issues.append(f"Line {i}: Bare 'except:' catches all exceptions including system exits. Use 'except Exception:' or specify the exception type.")
            # Check for very long lines
            if len(line) > 120:
                issues.append(f"Line {i}: Very long line ({len(line)} chars). Consider breaking it up for readability.")

        # Check for missing if __name__ == '__main__': guard when functions exist
        if visitor.functions > 0 and '__name__' not in code:
            issues.append("Tip: Consider wrapping top-level code in a main() function and adding a __name__ guard so it is safe to import.")

        # Check for mutable default arguments (common Python gotcha)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        issues.append(f"Line {node.lineno}: Function '{node.name}' uses a mutable default argument (list/dict/set). This is a common Python gotcha — use None as default and initialise inside the function instead.")

    except SyntaxError as e:
        issues.append(f"Syntax Error: {str(e)}. Check the line mentioned for issues like missing parentheses, colons, or incorrect indentation.")

    result = "Code Review Result:\n"
    if issues:
        result += "\n".join(issues) + "\n\n"
    else:
        result += "No major issues detected. Code is syntactically valid.\n\n"
    
    if summary:
        result += "\n".join(summary)
    
    return result

def fix_missing_colon(code):
    lines = code.splitlines()
    fixed = []
    control_kw = r'^\s*(if|elif|else|for|while|def|class|try|except|finally|with|async\s+def|async\s+with|async\s+for)\b'

    for line in lines:
        stripped = line.rstrip()   # keep leading indent
        content = stripped.lstrip()
        
        if re.match(control_kw, content) and not content.endswith(':'):
            # only add : if it doesn't already have one (ignore comments)
            if '#' not in content or content.index('#') > content.rfind(':'):
                fixed.append(stripped + ':')
                continue
        
        fixed.append(line)
    
    return '\n'.join(fixed)

def fix_indentation(code):
    lines = code.splitlines()
    fixed = []
    expected_indent = 0
    prev_had_colon = False

    for line in lines:
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)

        if not stripped or stripped.startswith('#'):
            fixed.append(line)
            continue

        # Line after colon → should be more indented
        if prev_had_colon:
            if current_indent <= expected_indent:
                # missing indent → fix to expected
                fixed.append('    ' * (expected_indent // 4 + 1) + stripped)
                expected_indent += 4
            else:
                fixed.append(line)
                # keep user's deeper indent (maybe intentional)
                expected_indent = current_indent
        else:
            # Should be at current block level or less
            if current_indent < expected_indent:
                # dedent
                levels = current_indent // 4
                fixed.append('    ' * levels + stripped)
                expected_indent = current_indent
            elif current_indent > expected_indent:
                # unexpected extra indent → reduce to expected
                fixed.append('    ' * (expected_indent // 4) + stripped)
            else:
                fixed.append(line)

        prev_had_colon = stripped.endswith(':') and not stripped.startswith(('else:', 'elif ', 'except', 'finally'))

        # Reset on dedent keywords
        if stripped.startswith(('else:', 'elif ', 'except', 'finally')):
            expected_indent = max(0, expected_indent - 4)

    return '\n'.join(fixed)

def detect_and_add_imports(code, undefined):
    added = []
    lines = code.split("\n")
    insert_pos = 0  # Insert after existing imports
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('import') or stripped.startswith('from'):
            insert_pos = i + 1  # keep moving past each import line
    
    for undef in undefined:
        if undef.lower() in common_modules:
            import_stmt = common_modules[undef.lower()]
            if import_stmt not in added:
                added.append(import_stmt)
    
    if added:
        lines = lines[:insert_pos] + added + lines[insert_pos:]
    
    return "\n".join(lines), added

def auto_fix_code(code, issue=""):
    changes = []

    # Step 1: Fix missing colons
    fixed = fix_missing_colon(code)
    if fixed != code:
        changes.append("added missing colons after control statements")

    # Step 2: Conservative indent fix
    fixed = fix_indentation(fixed)
    if fixed != code:  # rough check
        changes.append("corrected inconsistent / missing indentation")

    # Step 3: Try to add obvious missing imports
    try:
        tree = ast.parse(fixed)
    except SyntaxError:
        pass
    else:
        visitor = VariableVisitor()
        visitor.visit(tree)
        undefined = visitor.used - visitor.assigned - set(dir(__builtins__)) - visitor.imports
        
        if undefined:
            fixed, added = detect_and_add_imports(fixed, undefined)
            if added:
                changes.append(f"added missing imports: {', '.join(added)}")

    changes_str = ", ".join(changes) if changes else "no automatic fixes applied"
    
    try:
        ast.parse(fixed)
        result = f"Fixed Code:\n{fixed}\n\nChanges: {changes_str}\nNo remaining syntax errors."
    except SyntaxError as e:
        result = f"Partial fix applied:\n{fixed}\n\nChanges: {changes_str}\nStill has error: {str(e)}"

    return result

import traceback

def explain_error(code):
    """
    Checks for syntax errors in user-submitted code and returns
    a clean, user-friendly message without exposing internal tracebacks.
    """
    try:
        compile(code, "<user_input>", "exec")
        return "No syntax errors detected in your code.\nIt should be syntactically valid (runtime errors are still possible)."
    
    except SyntaxError as e:
        msg = "Syntax Error in the code you entered:\n\n"
        msg += f"→ {str(e)}\n"

        # Show the problematic line + arrow pointing to error
        if e.lineno is not None:
            lines = code.splitlines()
            if 1 <= e.lineno <= len(lines):
                bad_line = lines[e.lineno - 1].rstrip()
                msg += f"\nOn line {e.lineno}:\n"
                msg += f"  {bad_line}\n"
                
                if e.offset is not None and e.offset > 0:
                    msg += "  " + " " * (e.offset - 1) + "^ here\n"

        msg += "\nCommon causes and fixes:\n"
        msg += " • Missing colon   :     after def / if / for / while / class / with / else / elif\n"
        msg += "   Example:  def is_prime(n)    →    def is_prime(n):\n"
        msg += " • Indentation error (use 4 spaces consistently, don't mix tabs & spaces)\n"
        msg += " • Unclosed (, [, {, \" or '\n"
        msg += " • Typo in keyword (printt → print, etc.)\n"

        return msg

    except Exception as unexpected:
        # Very rare – something else went wrong during checking
        return f"Unexpected problem while checking syntax:\n{type(unexpected).__name__}: {str(unexpected)}"

class ExplanationVisitor(ast.NodeVisitor):
    def __init__(self, level):
        self.explanations = []
        self.level = level
        self.line_map = {}  # To map nodes to lines

    def visit(self, node):
        if hasattr(node, 'lineno'):
            line = node.lineno
            if self.level == "beginner":
                self.explain_beginner(node)
            elif self.level == "intermediate":
                self.explain_intermediate(node)
            elif self.level == "advanced":
                self.explain_advanced(node)
        self.generic_visit(node)

    def explain_beginner(self, node):
        if isinstance(node, ast.Assign):
            self.explanations.append(f"Line {node.lineno}: Assigning a value to a variable. Like storing something in a box.")
        elif isinstance(node, ast.If):
            self.explanations.append(f"Line {node.lineno}: Checking if something is true, and doing actions based on that.")
        elif isinstance(node, ast.For) or isinstance(node, ast.While):
            self.explanations.append(f"Line {node.lineno}: Repeating some code multiple times.")
        elif isinstance(node, ast.FunctionDef):
            self.explanations.append(f"Line {node.lineno}: Defining a reusable piece of code called a function.")
        elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            self.explanations.append(f"Line {node.lineno}: Bringing in external code or tools (modules).")

    def explain_intermediate(self, node):
        if isinstance(node, ast.Assign):
            target = ast.unparse(node.targets[0])
            value = ast.unparse(node.value)
            self.explanations.append(f"Line {node.lineno}: Assigning '{value}' to '{target}'.")
        elif isinstance(node, ast.If):
            test = ast.unparse(node.test)
            self.explanations.append(f"Line {node.lineno}: If condition '{test}' is True, execute the block.")
        elif isinstance(node, ast.For):
            target = ast.unparse(node.target)
            iter_ = ast.unparse(node.iter)
            self.explanations.append(f"Line {node.lineno}: Looping over '{iter_}', assigning each to '{target}'.")
        elif isinstance(node, ast.While):
            test = ast.unparse(node.test)
            self.explanations.append(f"Line {node.lineno}: While '{test}' is True, repeat the block.")
        elif isinstance(node, ast.FunctionDef):
            args = ', '.join(arg.arg for arg in node.args.args)
            self.explanations.append(f"Line {node.lineno}: Defining function '{node.name}' with parameters '{args}'.")
        elif isinstance(node, ast.Call):
            func = ast.unparse(node.func)
            self.explanations.append(f"Line {node.lineno}: Calling function '{func}'.")

    def explain_advanced(self, node):
        # More technical
        if isinstance(node, ast.Assign):
            self.explanations.append(f"Line {node.lineno}: Assignment statement. May involve unpacking if multiple targets.")
        elif isinstance(node, ast.If):
            self.explanations.append(f"Line {node.lineno}: Conditional branch. Supports elif/else chains.")
        elif isinstance(node, ast.For):
            self.explanations.append(f"Line {node.lineno}: Iterable loop. Handles else clause for no-break cases.")
        elif isinstance(node, ast.While):
            self.explanations.append(f"Line {node.lineno}: Condition-based loop. Also supports else clause.")
        elif isinstance(node, ast.FunctionDef):
            self.explanations.append(f"Line {node.lineno}: Function definition. May include decorators, type hints, etc.")
        elif isinstance(node, ast.Try):
            self.explanations.append(f"Line {node.lineno}: Exception handling block with try/except/else/finally.")

def explain_program(code, level="beginner"):
    levels = {"beginner", "intermediate", "advanced"}
    if level not in levels:
        level = "beginner"
    
    explanation = f"Detailed Program Explanation (Level: {level.title()}):\n\n"
    
    try:
        tree = ast.parse(code)
        visitor = ExplanationVisitor(level)
        visitor.visit(tree)
        
        if visitor.explanations:
            explanation += "Line-by-line/key structure explanations:\n" + "\n".join(visitor.explanations) + "\n\n"
        else:
            explanation += "No specific structures detected for detailed breakdown.\n\n"
        
        explanation += "Overall Flow:\n"
        explanation += "- The code starts executing from the top.\n"
        if level == "beginner":
            explanation += "- Imports (if any) load tools. Functions are defined but run when called. Main code runs directly.\n"
            explanation += "- Variables hold data, loops repeat actions, conditions make decisions.\n"
        elif level == "intermediate":
            explanation += "- Global code executes first, then any if __name__ == '__main__' block.\n"
            explanation += "- Watch for side effects like prints, inputs, or file operations.\n"
        elif level == "advanced":
            explanation += "- Execution model: Module-level code runs on import. Scopes: global, local, nonlocal.\n"
            explanation += "- Potential optimizations: Complexity analysis, e.g., loops may be O(n).\n"
        
        explanation += "\nTips:\n"
        if level == "beginner":
            explanation += "- Run it step-by-step in your mind or with print statements to debug.\n"
        elif level == "intermediate":
            explanation += "- Use a debugger like pdb to step through.\n"
        elif level == "advanced":
            explanation += "- Consider edge cases, exceptions, and performance.\n"
    
    except SyntaxError as e:
        explanation += f"Cannot fully explain due to syntax error: {str(e)}\n"
        explanation += "Fix syntax first for detailed breakdown.\n"
    
    return explanation

def process_action(action, user_input, extra=""):
    if action == "generate":
        return generate_code(user_input)
    elif action == "review":
        return review_code(user_input)
    elif action == "fix":
        issues = review_code(user_input)  # Get issues first
        return auto_fix_code(user_input, issues)  # Pass issues for targeted fixes
    elif action == "error_explain":
        return explain_error(user_input)
    elif action == "program_explain":
        level = extra or "beginner"
        return explain_program(user_input, level)
    return "Invalid action selected."

@app.route("/", methods=["GET", "POST"])
def index():
    output = ""
    user_input = ""
    extra_input = ""
    if request.method == "POST":
        user_input = request.form.get("user_input", "")
        action = request.form.get("action", "")
        extra_input = request.form.get("extra_input", "")
        output = process_action(action, user_input, extra_input)
    return render_template("index.html", output=output, user_input=user_input, extra_input=extra_input)

if __name__ == "__main__":
    app.run(debug=True)
