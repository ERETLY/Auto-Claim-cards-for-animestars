import pickle

# Обновленные данные куков с корректными значениями
cookies =
сюда куки вставляем

# Сохранение куков в файл с помощью pickle. Если куков несколько, сами меняем имя файла на cookies1.pkl (можно любое так то)
with open('cookies.pkl', 'wb') as filehandler:
    pickle.dump(cookies, filehandler)

print("Cookies saved to cookies.pkl")
