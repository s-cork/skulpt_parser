print((True or False))
print((True or True))
print((False or False) == False)

print((True and False) == False)
print((True and True))
print((False and False) == False)

print((not True) == False)
print((not False))

print((not True or False) == ((not True) or False))
print((not False or False) == ((not False) or False))

print((not True and True) == ((not True) and True))
print((not False and True) == ((not False) and True))

print((not True and not False or False) == (((not True) and (not False)) or False))
