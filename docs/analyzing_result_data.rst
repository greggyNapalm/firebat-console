======================
Анализ выходных данных
======================

answ.txt
========
Содержит полную информацию о всех запросах и ответах

Рассмотрим лог ответов smoke теста

``<CR><LF>`` они же ``\r\n``  - `разделители полей HTTP протокола <http://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol>`_, являются частью HTTP запроса и ответа, их Phantom не модифицирует.

``<LF>`` он же ``\n`` - разделитель запросов и ответов, его вставляет Phantom.
::

                         размер запроса в байтах
                         |
                         |   размер ответа в байтах
                         |   |
                         |   |   длительность временного интервала между отправкой запроса и получением ответа(rtt) в микросекундах
                         |   |   |
                         |   |   |   время ожидания ответа в микросекундах
                         |   |   |   |
                         |   |   |   |  код ошибки C runtime library, он же errno
                         |   |   |   |  |
                         /\ / \ / \ / \ |
                      _  84 666 809 589 0<LF>
                     /   GET / HTTP/1.0<CR><LF>
                    /    User-Agent: phantom_14/1.2.3<CR><LF>
    запрос --------|     Host: 127.0.0.1<CR><LF>
                    \    Connection: Close<CR><LF>
                     \_  <CR><LF>
    разделитель ------>_ <LF>
                      /  HTTP/1.0 200 OK<CR><LF>
                     /   Server: SimpleHTTP/0.6 Python/2.5.2<CR><LF>
                    /    Date: Fri, 27 Apr 2012 11:07:13 GMT<CR><LF>
                   /     Content-type: text/html<CR><LF>
                  /      Content-Length: 527<CR><LF>
                 /       <CR><LF>
                /        <title>Directory listing for /</title>
               /         <h2>Directory listing for /</h2>
              /          <hr>
             /           <ul>
    ответ --|            <li><a href="1.conf">1.conf</a>
            \            <li><a href="ammo.stpd">ammo.stpd</a>
             \           <li><a href="answ.txt">answ.txt</a>
              \          <li><a href="bootstrap.sh">bootstrap.sh</a>
               \         <li><a href="phantom.conf">phantom.conf</a>
                \        <li><a href="phantom_current.conf">phantom_current.conf</a>
                 \       <li><a href="phantom_no_ssl.conf">phantom_no_ssl.conf</a>
                  \      <li><a href="phantom_stat.log">phantom_stat.log</a>
                   \     <li><a href="phout.txt">phout.txt</a>
                    \    <li><a href="trash/">trash/</a>
                     \   </ul>
                      \_ <hr>
    разделитель ------>  <LF>


phout.txt
=========
Содержит агрегированные данные по всем ответам

::

                         длительность временного интервала между отправкой запроса и получением ответа(rtt) в микросекундах 
                         |
                         |   время, потраченное на установление соединения в миллисекундах(FIXME: tcp handshake?)
                         |   |
                         |   |  время отправки запроса в микросекундах 
                         |   |  |
                         |   |  |    время генерации ответа на стороне сервера в микросекундах
                         |   |  |    |
                         |   |  |    |  время ожидания ответа в микросекундах
                         |   |  |    |  |
                         |   |  |    |  |    время потраченное на исполнение запроса в микросекундах, позволяет оценить погрешность Phantom'а
                         |   |  |    |  |    |
                         |   |  |    |  |    |  размер запроса в байтах
                         |   |  |    |  |    |  |
                         |   |  |    |  |    |  |    размер ответа в байтах
                         |   |  |    |  |    |  |    |
                         |   |  |    |  |    |  |    |  код ошибки C runtime library, он же errno
                         |   |  |    |  |    |  |    |  |
         epoch           |   |  |    |  |    |  |    |  |    статус код HTTP протокола
     ______|_____        |   |  |    |  |    |  |    |  |    |
    /            \      / \ / \ /\  / \ /\  / \ /\  / \ |   / \
    1335524833.562      809 140 25  575 69  589 84  666 0   200
    1335524834.559      907 75  20  768 44  770 84  666 0   200

phantom_stat.log
================
FIXME: format?
