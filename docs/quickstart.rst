=============
Быстрый старт
=============

Smoke test
==========
Копируем код из репозитория
::

    git clone git://github.com/greggyNapalm/phantom_doc.git

открываем два терминала и в обоих переходим в каталог с тестом
::

    cd phantom_doc/examples/smoke

В первом терминале
    запускаем простой HTTP сервер, он будет возвращать листинг текущей директории в ответ на запрос
    ::
    
        $ python -m SimpleHTTPServer

Во втором терминале
    проверяем, что процесс успешно забиндил сокет и слушает его:
    ::
    
        $ netstat ntpl | grep 8000
    
    сделаем пробный запрос любой удобной утилитой:
    ::
    
        $ curl -v "http://localhost:8000/"
    
    ответ не должен быть пустым, статус код HTTP ответа должен быть ``200``.
    
    Проверяем на синтаксическую корректность конфиг стрельбы
    ::
    
        $ phantom check phantom.conf
    
    Если в STDOUT выводится переформатированное содержимое файла phantom.conf - файл прошёл синтаксическую проверку, в ином случае будут указаны ошибки, которые нужно исправить.
    
    Запускаем тест
    ::
    
        $ phantom run phantom.conf

Вывод терминала с запущеной стрельбой должен быть примерно следующим:
::

    2012-04-27 13:48:31.052 +0400 [info] phantom Start
    time    2012-04-27 13:48:33 +0400       (total)
    
    ** benchmark_io
    HTTP    200:2
    network 0:2
    times   45:2
    overall 2008    0        17.91% 168     83      1332    663     2       0
    tasks   1
    source_log      0
    
    2012-04-27 13:48:33.061 +0400 [error] brief_logger bq_sleep: Operation canceled
    2012-04-27 13:48:33.072 +0400 [error] bencmark_logger bq_sleep: Operation canceled
    2012-04-27 13:48:33.074 +0400 [info] phantom Exit

Терминала с запущеным Web сервером:
::

    $ python -m SimpleHTTPServer
    Serving HTTP on 0.0.0.0 port 8000 ...
    localhost - - [27/Apr/2012 13:27:03] "GET / HTTP/1.1" 200 -
    localhost - - [27/Apr/2012 13:27:10] "GET / HTTP/1.1" 200 -

Таким образом оба наших HTTP запроса описаных в файле ``ammo.stpd`` обработаны успешно, результат теста сохранён в файлах: ``answ.txt``, ``phout.txt``, ``phantom_stat.log``.

Для детального разбора результатов можно обратиться к разделу `Анализ выходных данных`_.

.. _Анализ выходных данных: http://phantom-doc-ru.readthedocs.org/en/latest/analyzing_result_data.html
