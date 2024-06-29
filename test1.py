a = [(1, 2, 7, 3), (4, 5, 9, 6)]

result_dict = {}

for domain, *detail in a:
    if domain not in result_dict: result_dict[domain] = []
    result_dict[domain].append(detail)

print(result_dict)