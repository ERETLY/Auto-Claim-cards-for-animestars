# Auto-Claim-cards-for-animestars
Auto Claim cards for animestars
Скрипт делался для Ubuntu без gui. Но щас все для винды вставлено.
1. Оставил хромдрайвер для винды в папке и для убунту не в папке.
2. Добавить куки в cookies.py и запустить файл. (Формат куки должен быть True False None вместо true false null и sameSite должен везде равняться "None"). - через chatgpt можете сделать, дать ему то что в скобках и сам куки, он сразу выдаст нужный формат.
3. После чего, если у вас несколько аккаунтов в файле cookies.py меняем название файла куки и вставляем новые куки и так же запускаем.
4. Поменять файлы куки в main.py - добавить или убрать / поменять названия. (по дефолту стоит cookies.py, cookies1.py, cookies2.py.
5. В массив ниже (под куками) написать колво карт которые вы хотите находить за день (допустим группа звезда - 21 карта).
6. Запустить сам файл main.py или mainWin.py, "python main.py", если в консоли видите что идет ожидание карточки - все сделали правильно. 
