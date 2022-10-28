
j = input()
s = input()

count = 0
for item in s:
    if item in j:
        count += 1

print(count)