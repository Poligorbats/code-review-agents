# Example 1: Basic issues — mutable defaults, bare except, style violations
# This file is intentionally written with common Python anti-patterns for demo purposes.

def calculate_stats(numbers=[]):
    total = 0
    for i in range(len(numbers)):
        total = total + numbers[i]
    avg = total / len(numbers)
    
    result = {}
    result['total'] = total
    result['average'] = avg
    result['count'] = len(numbers)
    result['max'] = numbers[0]
    result['min'] = numbers[0]
    
    for i in range(len(numbers)):
        if numbers[i] > result['max']:
            result['max'] = numbers[i]
        if numbers[i] < result['min']:
            result['min'] = numbers[i]
    
    return result


def find_duplicates(l):
    duplicates = []
    for i in range(len(l)):
        for j in range(len(l)):
            if i != j:
                if l[i] == l[j]:
                    if l[i] not in duplicates:
                        duplicates.append(l[i])
    return duplicates


def read_file(filename):
    try:
        f = open(filename)
        data = f.read()
        f.close()
        return data
    except:
        return None


def flatten(nested, result=[]):
    for item in nested:
        if type(item) == list:
            flatten(item, result)
        else:
            result.append(item)
    return result
