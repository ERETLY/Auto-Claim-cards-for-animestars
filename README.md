# Auto-Claim-cards-for-animestars
Auto Claim cards for animestars
Скрипт делался для Ubuntu без gui.
1. Вам нужно в main.py изменить расположение хром драйвера на ваше расположение (я качал старую версию драйвера 114 а так же версию хрома тоже 114 - можете на просторах интернета найти или вообще переделать под винду, там Edge драйвер к примеру, но за работоспобность не отвечаю).
2. Добавить куки в cookies.py и запустить файл. (Формат куки должен быть True False вместо true false и sameSite должен везде равняться "None".
3. После чего, если у вас несколько аккаунтов в файле cookies.py меняем название файла куки и вставляем новые куки и так же запускаем.
3. Поменять файлы куки в main.py - добавить или убрать / поменять названия. (по дефолту стоит cookies.py, cookies1.py, cookies2.py.
4. В массив ниже (под куками) написать колво карт которые вы хотите находить за день (допустим группа звезда - 21 карта).
5. Запустить сам файл main.py, если в консоли видите что клик был сделан и идет ожидание карточки - все сделали правильно. 
