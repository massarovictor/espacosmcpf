import bcrypt

senha_plana = 'prof@mcpf.edu'
hashed_password = bcrypt.hashpw(senha_plana.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(hashed_password)