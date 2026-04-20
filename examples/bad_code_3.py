# Example 3: Algorithm bugs + performance issues + no edge case handling
# Intentionally bad code for demo purposes.


def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n):          # bug: should be range(n - i - 1)
            if arr[j] > arr[j+1]:  # bug: index out of bounds on last iteration
                temp = arr[j]
                arr[j] = arr[j+1]
                arr[j+1] = temp
    return arr


def binary_search(arr, target):
    left = 0
    right = len(arr)                # bug: should be len(arr) - 1

    while left < right:
        mid = (left + right) / 2   # bug: float index, should use //
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1        # bug: can cause infinite loop, should be mid
    return -1


def fibonacci(n):
    if n == 0:
        return 0
    if n == 1:
        return 1
    # No memoization — exponential time O(2^n)
    return fibonacci(n-1) + fibonacci(n-2)


def count_words(text):
    words = {}
    text = text.lower()
    word = ""
    for char in text:
        # Long chain of conditions instead of using str methods
        if (char != " " and char != "\n" and char != "\t"
                and char != "," and char != "." and char != "!"
                and char != "?" and char != ";" and char != ":"):
            word = word + char   # string concatenation in loop: O(n^2)
        else:
            if word != "":
                if word in words:
                    words[word] = words[word] + 1
                else:
                    words[word] = 1
                word = ""
    return words


def is_palindrome(s):
    reversed_s = ""
    for i in range(len(s)-1, -1, -1):
        reversed_s = reversed_s + s[i]   # string concat in loop
    if s == reversed_s:
        return True
    else:
        return False
