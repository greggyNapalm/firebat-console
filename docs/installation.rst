===========
Инсталляция
===========

Сборка **deb** пакета на основе исходного кода
==============================================

На данный момент сборка приложения реализована и протестирована под серверный дистрибутив Ubuntu LTS(GNU Linux), именно о нём и пойдёт речь в дальнейшем.

Устанавливаем необходимые пакеты:
::

    $ apt-get install devscripts debhelper libssl-dev binutils-dev

Копируем последнюю ревизию кода из репозитория:
FIXME: add link to repo
::

    $ git clone git://path_to_repo

Если версия дистрибутива Ubuntu Linux старше чем 12 LTS, необходимо наложить небольшой патч:
::

    $ cd src
    $ cat > phantom_deb_control_ssl_ver.patch <<EOF
    5c5
    < Build-Depends: debhelper (>= 7), libc6-dev, g++, libssl-dev (>= 0.9.8m-1), perl
    ---
    > Build-Depends: debhelper (>= 7), libc6-dev, g++, libssl-dev (>= 0.9.8), perl
    EOF
    $ patch debian/control < phantom_deb_control_ssl_ver.patch

Собираем и устанавливаем пакет:
::

    $ debuild -us -uc
    $ cd ..; dpkg -i phantom-ssl_* phantom_*

Проверяем, результат установки пакета:
::

    # В списке установленых пакетов должны быть только что собранные нами
    $ dpkg -l | grep -i phantom

    # Слинкованые файлы должны быть найдены
    $ ldd `which phantom`

    # В STDOUT должны бать выведена справка по разделу конфига
    $ phantom syntax /usr/lib/phantom/mod_io_benchmark{,_method_stream{,_ipv4,_ipv6,_source_random,_source_log,_proto_http}}.so

Предыдущие команды должны быть выполнены без ошибок. `Ожидаемый вывод <https://gist.github.com/2507603>`_

На данном этапе мы имеем проинсталированный и готовый к работе Phantom, переходим к ваполнению первого пробного теста в разделе `Быстрый страт`_.

.. _Быстрый страт: http://phantom-doc-ru.readthedocs.org/en/latest/quickstart.html
