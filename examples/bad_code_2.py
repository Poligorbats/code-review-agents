# Example 2: High complexity, global state, security issues
# Intentionally bad code for demo purposes.

import json

cache = {}
errors = []
USERS = []


def process_user_data(data):
    global cache, errors, USERS
    
    if data == None:
        errors.append("data is None")
        return False
    
    try:
        if type(data) == str:
            data = json.loads(data)
        
        if 'name' in data:
            name = data['name']
        else:
            name = 'unknown'
        
        if 'age' in data:
            age = data['age']
            if type(age) == str:
                age = int(age)
            if age < 0:
                errors.append("negative age")
                return False
            elif age > 150:
                errors.append("unrealistic age")
                return False
            elif age >= 0 and age < 18:
                category = 'minor'
            elif age >= 18 and age < 65:
                category = 'adult'
            elif age >= 65:
                category = 'senior'
        else:
            age = 0
            category = 'unknown'
        
        if 'email' in data:
            email = data['email']
            if '@' in email:
                if '.' in email.split('@')[1]:
                    valid_email = True
                else:
                    valid_email = False
            else:
                valid_email = False
        else:
            email = ''
            valid_email = False

        user = {'name': name, 'age': age, 'category': category, 
                'email': email, 'valid_email': valid_email}
        
        key = name + str(age)
        if key in cache:
            return cache[key]
        
        USERS.append(user)
        cache[key] = user
        return user
    
    except Exception as e:
        errors.append(str(e))
        return False


def get_user_report():
    report = ""
    report = report + "Total users: " + str(len(USERS)) + "\n"
    report = report + "Errors: " + str(len(errors)) + "\n"
    
    minors = []
    adults = []
    seniors = []
    unknowns = []
    
    for u in USERS:
        if u['category'] == 'minor':
            minors.append(u)
        if u['category'] == 'adult':
            adults.append(u)
        if u['category'] == 'senior':
            seniors.append(u)
        if u['category'] == 'unknown':
            unknowns.append(u)
    
    report = report + "Minors: " + str(len(minors)) + "\n"
    report = report + "Adults: " + str(len(adults)) + "\n"
    report = report + "Seniors: " + str(len(seniors)) + "\n"
    
    return report


def search_users(query):
    results = []
    for u in USERS:
        if query in u['name']:
            results.append(u)
        elif query in u['email']:
            results.append(u)
    return results
