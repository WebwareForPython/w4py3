.. _deployment:

Deployment
==========

Webware for Python 3 uses the Web Server Gateway Interface (WSGI_) which allows deploying Webware apps with any available `WSGI server`_.

If your performance requirements are not that high, you can use `waitress`_ as WSGI server, which is used as the development server for Webware, to serve your application on a production system as well. If your performance requirements are higher, we recommend serving Webware applications using Apache_ and mod_wsgi_. But there are also many other options, and you can add  caching_, `load balancing`_ and other techniques or use a CDN_ to improve performance.

.. _WSGI: https://wsgi.readthedocs.io/en/latest/learn.html
.. _WSGI server: https://www.fullstackpython.com/wsgi-servers.html
.. _waitress: https://docs.pylonsproject.org/projects/waitress/
.. _Apache: https://httpd.apache.org/
.. _mod_wsgi: https://modwsgi.readthedocs.io
.. _caching: https://www.mnot.net/cache_docs/
.. _load balancing: https://en.wikipedia.org/wiki/Load_balancing_(computing)
.. _CDN: https://en.wikipedia.org/wiki/Content_delivery_network


Installation on the Production System
-------------------------------------
In order to install your Webware for Python 3 application on the production system, first make sure the minimum required Python 3.6 version is already installed. One popular and recommended option is running a Linux distribution on your production system - see `Installing Python 3 on Linux`_.

.. _Installing Python 3 on Linux: https://docs.python-guide.org/starting/install3/linux/

Next, we recommend creating a virtual environment for your Webware for Python 3 application. We also recommend creating a dedicated user as owner of your application, and placing the virtual environment into the home directory of that user. When you are logged in as that user under Linux, you can create the virtual environment with the following command. If you get an error, you may need to install ``python3-venv`` as an additional Linux package before you can run this command::

    python3 -m venv .venv

This will create the virtual environment in the subdirectory ``.venv``. Of course, you can also use a different name for that directory. Now, install Webware for Python 3 into that virtual environment. Under Linux, you can do this as follows::

    . .venv/bin/activate
    pip install "Webware-for-Python>=3"

You will also need to install other Python packages required by your application into the virtual environment with pip, unless these are provided as part of the application, e.g. in a ``Lib`` subdirectory of the application working directory. If you want to use a Python-based WSGI server such as waitress, you need to install it into this virtual environment as well::

   pip install waitress

As the next step, you need to copy the application working directory containing your Webware for Python 3 application to your production system. We recommend putting it into the directory where you created the virtual environment, so that both are siblings. It is important that the application working directory is readable for the user that will run the WSGI server, but not writable. For security reasons, we recommend running the WSGI server with as a dedicated user with low privileges who is not the owner of the application working directory. The directory should also not be readable to other users. The subdirectories of the application working directory should be readable only as well, except for the ``Cache``, ``ErrorMsgs``, ``Logs`` and ``Sessions`` subdirectories, which must be writable. You can use the ``webware make`` command to change the ownership of the application working directory to a certain user or group. You can also run this command on an existing working directory that you copied to the production server. For instance, assuming you activated the virtual environment with Webware for Python, and you have superuser privileges, you could make the application accessible to the group ``www-data`` like this::

    webware make -g www-data path-to-app-work-dir

We recommend using an automatic deployment solution such as Fabric_ for copying your application working directory from your development or staging server to your production server. It is also possible to use Git_ hooks to `deploy your application with Git`_.

.. _Fabric: https://www.fabfile.org/
.. _Git: https://git-scm.com/
.. _Deploy your application with Git: https://buddy.works/blog/how-deploy-projects-with-git

Also, make sure the virtual environment you created above is readable by the user running the WSGI server, e.g. by using the same group ownership as above::

    chgrp -R www-data .venv


Starting the WSGI Server on Boot
--------------------------------

On a production system, you want to set up your system so that the WSGI server starts automatically when the system boots. If you are using Apache and mod_wsgi, as explained further below, then you only need to make sure Apache starts automatically, and you can skip this step.

There are a lot of options to start applications at boot time. First, you can use the startup system of your operating system directly. We will show how this works using systemd_ as an example. Second, you can use one of the many available process managers to start and control the WSGI server. We will show how this works using Supervisor_.

.. _systemd: https://github.com/systemd/systemd
.. _Supervisor: http://supervisord.org/

Using systemd
~~~~~~~~~~~~~

We assume that you have already copied your application working directory to the production system as explained above, and we assume you're using waitress as your WSGI server. In order to make your application available as a systemd_ service, you only need to add the following service file into the directory ``/etc/systemd/system``. The service file should be named something like ``webware.service`` or ``name-of-your-app.service`` if you're running multiple Webware applications::

    [Unit]
    Description=My Webware application
    After=network.target
    StartLimitIntervalSec=0

    [Service]
    Type=simple
    Restart=on-failure
    RestartSec=1
    User=www-data
    Group=www-data
    ExecStart=path-to-virtual-env/bin/webware serve --prod
    WorkingDirectory=path-to-app-work-dir

    [Install]
    WantedBy=multi-user.target

Adapt the options as needed. ``Description`` should be a meaningful description of your Webware application. With ``User`` and ``Group`` you specify under which user and group your Webware application shall run, see the remarks above. Adapt the ``EexecStart`` option so that it uses the path to your virtual environment, and specify the path to your application working directory as the ``WorkingDirectory`` option. You can change the host address, port and add other options to ``webware serve`` in the ``ExecStart`` option. By default, the server runs on port 8080, but you can specify a different port using the ``-p`` option. If you want to run waitress behind a reverse proxy, for instance because you want to run on port 80 which needs superuser privileges or you need TLS support which is not provided by waitress, then you you need to serve only on the local interface, using options such as ``-l 127.0.0.1 -p 8080``. The ``--prod`` option tells Webware to run in production mode.

Note that if you use the ``--reload`` option with ``webware serve`` in ``ExecStart``, then you should also set ``KillMode=process`` and ``ExecStopPost=/bin/sleep 1`` in the service file to make sure that Webware can be shut down properly.

After adding or changing the service file, you need to run the following command so that systemd refreshes its configuration::

    sudo systemctl daemon-reload

You tell systemd to automatically run your service file on system boot by enabling the service with the following command::

    sudo systemctl enable webware

If you named your service file differently, you need to specify that name instead of ``webware`` in this command. Likewise, you can disable the service with::

    sudo systemctl disable webware

To start the service manually, run this command::

    sudo systemctl start webware

You can list errors that appeared while running the service using this command::

    sudo journalctl -ru webware

The output of your application will be logged to the file ``Logs/Application.log`` inside the application working directory if you did not specify anything else in the Webware application configuration.

To restart the service, you need to do this::

    sudo systemctl restart webware

If you want to automatically restart the service whenever there are changes in the application working directory, you can install a systemd `path unit`_ to watch the directory and run the above command whenever something changes. Alternatively, you can run ``webware serve`` with the ``--reload`` option. In that case, you also need to install hupper_ into the virtual environment where you installed Webware, because it is used to implement the ``reload`` functionality. If you are using a deployment tool such as Fabric_, you can  simply run the above command after deploying the application instead of watching the directory for changes.

.. _path unit: https://www.redhat.com/sysadmin/introduction-path-units
.. _hupper: https://github.com/Pylons/hupper

Using Supervisor
~~~~~~~~~~~~~~~~

You can also use Supervisor_ to control your WSGI server. On many Linux distributions, Supervisor can be installed with the package manager, but you can also install it manually using::

    pip install supervisor

The disadvantage of such a manual installation is that you will also need to integrate it into the service management infrastructure of your system manually, e.g. using a service file as explained above. Therefore we recommend that you install the Linux package if it is available. For instance, on Ubuntu you would do this with::

    sudo apt-get install supervisor

In the following, we assume that you installed Supervisor like this. You will then usually have a directory ``/etc/supervisor`` with a subdirectory ``conf.d``. Inside this subdirectory, create the following configuration file.  The configuration file should be name something like ``webware.conf`` or ``name-of-your-app.conf`` if you're running multiple Webware applications::

    [program:webware]
    user=www-data
    command=path-to-virtual-env/bin/webware serve --prod
    directory=path-to-app-work-dir

You can add many more options to the configuration. Adapt the options above and add other options as needed. You may want to change the section header ``[program:webware]`` to a more specific name if you are running multiple Webware applications. The ``user`` options specifies which user shall run your Webware application. Adapt the ``command`` option so that it uses the path to your virtual environment, and specify the path to your application working directory as the ``directory`` option. You can change the host address, port and add other options to ``webware serve`` in the ``command`` option. By default, the server runs on port 8080, but you can specify a different port using the ``-p`` option. If you want to run waitress behind a reverse proxy, for instance because you want to run on port 80 which needs superuser privileges or you need TLS support which is not provided by waitress, then you you need to serve only on the local interface, using options such as ``-l 127.0.0.1 -p 8080``. The ``--prod`` option tells Webware to run in production mode.

Reload the Supervisor configuration file and restart affected programs like this::

    supervisorctl reread
    supervisorctl update

This should automatically start the Webware application.

By default, the output of your application will be redirected to the file ``Logs/Application.log`` inside the application working directory by Webware. You can change the location of this file using the Webware application configuration, or you can also use Supervisor options to redirect the output to a log file and control that log file.

To show the process status of your application, run this command::

    supervisorctl status webware

If you named the configuration section differently, you need to specify that name instead of ``webware`` in this command. In order to restart the application, run this command::

    supervisorctl restart webware

If you want to automatically restart whenever there are changes in the application working directory, you can for example use Supervisor to run a separate program that watches the directory using inotify_, and runs the above command whenever something changes, or you can run ``webware serve`` with the ``--reload`` option. In that case, as explained above, you also need to install hupper_ into the virtual environment where you installed Webware. If you are using a deployment tool such as Fabric_, you can  simply run the above command after deploying the application instead of watching the directory for changes.

.. _inotify: https://www.linuxjournal.com/content/linux-filesystem-events-inotify


Logfile Rotation
----------------

The application log file (which you will find in ``Logs/Application.log`` inside the application working directory by default) will increase in size over time. We recommend configuring logrotate_ to rotate this log file, since this does not happen automatically. On most Linux distributions, logrotate is already pre-installed and you just need to put a configuration file like this into the folder ``/etc/logrotate.d``::

    path-to-app-work-dir/Logs/Application.log {
      weekly
      rotate 9
      copytruncate
      compress
      dateext
      missingok
      notifempty
      su www-data www-data
    }

.. _logrotate: https://github.com/logrotate/logrotate

Modify the configuration as you see fit. The ``su`` directive should specify the user and the group under which the WSGI server is running. Note that you can specify more than one log path and/or use wildcards, so that you can apply the same configuration to several Webware applications and avoid repeating the same options.

Assuming you created the configuration file as ``/etc/logrotate.d/webware``, you can test it with this command::

    logrotate -f /etc/logrotate.d/webware


Running behind a Reverse Proxy
------------------------------

There are several reasons why you may want to run the WSGI server that is serving your Webware application behind a reverse proxy. First, it can serve as a kind of load balancer, redirecting traffic to other applications or static files away from your Webware application and request the WSGI server only for the dynamic content where it is really needed. Second, it can provide TLS encryption in order to support HTTPS connections, compress data going in and out the server, and cache frequently used content, and is optimized to do all of this very quickly. If you're using the waitress WSGI server, this is an important issue, since waitress itself does not provide TLS support. Third, a reverse proxy also adds another security layer to your production system. In the following we show how you can use Apache_ and NGINX_ as reverse proxy for your Webware application.

Again, if you are using Apache and mod_wsgi, as explained further below, then you normally don't need a separate proxy server, and you can skip this step.

Using Apache as Reverse Proxy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The first thing you need to do after installing Apache_ is to enable the Apache mod_proxy_ and mod_proxy_http_ modules. You can usually do this as follows::

    sudo a2enmod proxy proxy_http

.. _mod_proxy: https://httpd.apache.org/docs/current/mod/mod_proxy.html
.. _mod_proxy_http: https://httpd.apache.org/docs/current/mod/mod_proxy_http.html

At this point, you may want to enable other Apache modules as well. For instance, if you want to use encryption with TLS (HTTPS connections), you need to also enable the mod_ssl_ module::

    sudo a2enmod ssl

.. _mod_ssl: https://httpd.apache.org/docs/current/mod/mod_ssl.html

Maybe you want to enable some more modules providing load balancing capabilities, such as mod_proxy_balancer_ and mod_lbmethod_byrequests_. We won't cover these modules in this deployment guide, but keep in mind that they are available if you need to scale up.

.. _mod_proxy_balancer: https://httpd.apache.org/docs/current/mod/mod_proxy_balancer.html
.. _mod_lbmethod_byrequests: https://httpd.apache.org/docs/current/mod/mod_lbmethod_byrequests.html

Assuming you configured the WSGI server to run on port 8080 using the localhost interface 127.0.0.1, you now need to add the following directives to your Apache configuration::

    ProxyPass / http://127.0.0.1:8080/
    ProxyPassReverse / http://127.0.0.1:8080/

Note: Do *not* set ``SSLProxyEngine On``, even if you want to communicate via HTTPS with your clients. You would only need this when the communication between Apache and the WSGI server is encrypted as well, which is usually not necessary, particularly if you run the reverse proxy and the WSGI server on the same machine, and would only work with WSGI servers that support encryption.

If you want to support encryption, you also need to create a server certificate and specify it in your Apache configuration. For testing only, a self-signed certificate will do, which may be already installed and configured. In the Internet you will find many instructions for creating a real server certificate and configuring Apache to use it.

Reload Apache after any changes you make to the configuration, e.g. with ``systemctl reload apache2`` or ``apachectl -k graceful``.

The two lines of configuration above make Apache work as a reverse proxy for any URL, i.e. all traffic is passed on to the WSGI server. This means that the WSGI server will also deliver any static assets that are part of your application, like images, CSS scripts, JavaScript files or static HTML pages. This is inefficient and creates an unnecessary load on the WSGI server. It is much more efficient if you let Apache serve the static assets. To achieve this, use the following Apache configuration::

    Alias /static path-to-app-work-dir/Static
    <Directory path-to-app-work-dir/Static>
        Require all granted
    </Directory>
    ProxyPass /static !
    ProxyPass / http://127.0.0.1:8080/
    ProxyPassReverse / http://127.0.0.1:8080/

With this configuration, you can access the static assets in the ``Static`` subdirectory of the application working directory with the URL prefix ``/static``, while everything else will be passed on to the WSGI server and handled by Webware for Python.

You can also do it the other way around, e.g. let everything behind the prefix ``/app`` be handled by Webware for Python, and everything else looked up as a static asset in the ``Static`` subdirectory of the application working directory, using a configuration like this::

    DocumentRoot path-to-app-work-dir/Static
    <Directory path-to-app-work-dir/Static>
        Require all granted
    </Directory>
    ProxyPass /app http://127.0.0.1:8080/
    ProxyPassReverse /app http://127.0.0.1:8080/

In this case, you should also tell the Webware application that you are using the ``/app`` prefix. If you are running the waitress server with ``webware serve`` you can do so using the ``--url-prefix`` command line option::

    webware serve -l 127.0.0.1 -p 8080 --url-prefix /app --prod

This prefix will then be passed to Webware in the ``SCRIPT_NAME`` environment variable, which is used when determining the ``servletPath()`` of a Webware ``HTTPRequest``.

Similarly, to tell Webware that you are using HTTPS connections, you can use the ``--url-scheme`` command line option::

    webware serve -l 127.0.0.1 -p 8080 --url-schema https --prod

You should then also add the following line to the Apache configuration::

    RequestHeader set X-Forwarded-Proto https

If you want to override WSGI environment variables using proxy headers, you need to add the options ``--trusted-proxy`` and ``trusted-proxy-headers`` to the ``webware serve`` command.

See also the remarks on `running behind a reverse proxy`_ in the `waitress documentation`_.

.. _running behind a reverse proxy: https://docs.pylonsproject.org/projects/waitress/en/stable/reverse-proxy.html
.. _waitress documentation: https://docs.pylonsproject.org/projects/waitress/

Using NGINX as a Reverse Proxy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Frequently, NGINX_ is used instead of Apache as a reverse proxy, because it is more lightweight and performs a bit better when serving static content. Contrary to Apache, you don't need to enable any additional modules to make NGINX work as a reverse proxy.

After `installing NGINX`_ and configuring the WSGI server to run on port 8080 using the localhost interface 127.0.0.1, you now need to add the following lines to your NGINX configuration::

    location /static {
       alias path-to-app-work-dir/Static;
    }

    location / {
       proxy_pass http://127.0.0.1:8080/;

       proxy_set_header Host $host;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Host $host;
       proxy_set_header X-Forwarded-Port $server_port;
       proxy_set_header X-Real-IP $remote_addr;
    }

.. _NGINX: https://www.nginx.com/
.. _installing NGINX: https://docs.nginx.com/nginx/admin-guide/installing-nginx/installing-nginx-open-source/

If you want to support encryption, you also need to create a server certificate and specify it in your NGINX configuration. For testing only, a self-signed certificate will do, which may be already installed. In the Internet you will find many instructions for creating a real server certificate and configuring NGINX to use it.

After reloading the NGINX configuration, e.g. with ``nginx -s reload``, NGINX should now act as a reverse proxy and deliver your Webware application at the root URL, and static content in the ``Static`` subdirectory of the application working directory with the URL prefix ``/static``.

If you want to do it the other way around, i.e. serve any static assets at the root URL, and your Webware application with the URL prefix ``/app``, use this configuration instead::

    root path-to-app-work-dir/Static

    location / {
    }

    location /app {
       proxy_pass http://127.0.0.1:8080/;

       proxy_set_header Host $host;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Host $host;
       proxy_set_header X-Forwarded-Port $server_port;
       proxy_set_header X-Real-IP $remote_addr;
    }

In this case, you should also tell the Webware application that you are using the ``/app`` prefix. If you are running the waitress server with ``webware serve`` you can do so using the ``--url-prefix`` command line option::

    webware serve -l 127.0.0.1 -p 8080 --url-prefix /app --prod

This prefix will then be passed to Webware in the ``SCRIPT_NAME`` environment variable, which is used when determining the ``servletPath()`` of a Webware ``HTTPRequest``.

If you want to override WSGI environment variables using proxy headers, you need to add the options ``--trusted-proxy`` and ``trusted-proxy-headers`` to the ``webware serve`` command.

See also the remarks on `running behind a reverse proxy`_ in the `waitress documentation`_.


Using Apache and mod_wsgi
-------------------------

While you can deploy Webware applications using the waitress WSGI server, as explained above, or run the application with other possibly better performing WSGI servers, as explained further below, our recommended way of deploying Webware application is using Apache_ and mod_wsgi_, since it combines excellent performance with low installation and maintenance effort. In particular, you will not need to care about running a separate WSGI server and starting it automatically, because this is handled by mod_wsgi already, and you will not need to install a reverse proxy, because you can use Apache to server the static content and dispatch to Webware via mod_wsgi for the dynamic content. The Apache web server can also care about everything that is needed to serve your content securely via HTTPS.

The first thing you need is to make sure that Apache is installed on your production system with the `"worker" MPM module`_. On some systems, the "prefork" MPM module is still the default, but "worker" is much better suited for our purposes. See also the section on `processes and threading`_ in the `mod_wsgi documentation`_.

.. _"worker" MPM module: https://httpd.apache.org/docs/current/mod/worker.html
.. _mod_wsgi documentation: https://modwsgi.readthedocs.io/
.. _processes and threading: https://modwsgi.readthedocs.io/en/develop/user-guides/processes-and-threading.html

Next you will need to install mod_wsgi. If possible, install a version that is available as a binary package for your system. There may be different versions of mod_wsgi available. Make sure you install the one for the Apache version running on your system and the Python version you are using in your Webware application. The package may be called something like "apache2-mod_wsgi-python3" or "libapache2-mod-wsgi-py3". If no suitable, current version of mod_wsgi is available, you will need to `install mood_wsgi from source`_.

.. _install mood_wsgi from source: https://modwsgi.readthedocs.io/en/develop/user-guides/quick-installation-guide.html

After installation, the module should be already enabled, but to be sure, enable the mod_wsgi Apache module with the following command::

    sudo a2enmod wsgi

At this point, you may want to enable other Apache modules as well. For instance, if you want to use encryption with TLS (HTTPS connections), you need to also enable the mod_ssl_ module::

    sudo a2enmod ssl

In that case, you also need to create a server certificate and specify it in your Apache configuration. For testing only, a self-signed certificate will do, which may be already installed and configured. In the Internet you will find many instructions for creating a real server certificate and configuring Apache to use it.

Add the following lines to your Apache configuration in order to serve your Webware application under the root URL, and static assets under the URL prefix ``/static``::

    Alias /static path-to-app-work-dir/Static

    <Directory path-to-app-work-dir/Static>
        Require all granted
    </Directory>

    WSGIDaemonProcess webware threads=20 python-home=path-to-virtual-env
    WSGIProcessGroup webware

    WSGIScriptAlias / path-to-app-work-dir/Scripts/WSGIScript.py

    <Directory path-to-app-work-dir/Scripts>
        Require all granted
    </Directory>

Note that ``path-to-virtual-env`` should really be the path of the directory containing the virtual environment where you installed Webware for Python 3 and other requirements for your Webware application, not the path to the Python interpreter.

Reload Apache after any changes you make to the configuration, e.g. with ``systemctl reload apache2`` or ``apachectl -k graceful``.

If you want to do it the other way around, i.e. serve any static assets at the root URL, and your Webware application with the URL prefix ``/app``, use this configuration instead::

    DocumentRoot path-to-app-work-dir/Static

    <Directory path-to-app-work-dir/Static>
        Require all granted
    </Directory>

    WSGIDaemonProcess webware threads=20 python-home=path-to-virtual-env
    WSGIProcessGroup webware

    WSGIScriptAlias /app path-to-app-work-dir/Scripts/WSGIScript.py

    <Directory path-to-app-work-dir/Scripts>
        Require all granted
    </Directory>

In this case, the prefix ``/app`` will be also passed to Webware by mod_wsgi in the ``SCRIPT_NAME`` environment variable, and is considered when determining the ``servletPath()`` of a Webware ``HTTPRequest``.

You can test the Apache configuration for errors with the command ``apache2ctl configtest``.  To debug problems with mod_wsgi, you can also use these settings in the Apache configuration::

    LogLevel info
    WSGIVerboseDebugging On

A frequent problem is that the virtual environment into which you installed Webware uses a different Python version than the one that the currently enabled mod_wsgi module was built for. In this case, re-create the virtual environment with the proper Python version, or install a mod_wsgi module that was built for the Python version you are using in your Webware application.

The output of your application will be logged to the file ``Logs/Application.log`` inside the application working directory if you did not specify anything else in the Webware application configuration (see also `Logfile Rotation`_).

Note that mod_wsgi can be operated in two modes, "embedded mode" and "daemon mode". The above configuration uses "daemon mode" which is the recommended mode for running Webware applications, even if "embedded mode" is the default mode for historical reasons. The configuration creates one "process group" called "webware". You can adapt and optimize the configuration by setting various options, like this::

    WSGIDaemonProcess webware \
    user=www-data group=www-data \
    threads=15 \
    python-home=path-to-virtual-env \
    display-name='%{GROUP}' \
    lang='de_DE.UTF-8' locale='de_DE.UTF-8' \
    queue-timeout=45 socket-timeout=60 connect-timeout=15 \
    request-timeout=60 inactivity-timeout=0 startup-timeout=15 \
    deadlock-timeout=60 graceful-timeout=15 eviction-timeout=0 \
    restart-interval=0 shutdown-timeout=5 maximum-requests=0

You can also define more than one process group, and use different process groups for different applications. In this case, mod_macro_ can be useful to avoid specifying the same options multiple times. It can be used like this to define different groups with a different number of threads that are created in each daemon process::

    <Macro WSGIProcess $name $threads>
        WSGIDaemonProcess $name \
        user=www-data group=www-data \
        threads=$threads \
        display-name='%{GROUP}' \
        python-home=path-to-common-virtual-env \
        lang='de_DE.UTF-8' locale='de_DE.UTF-8' \
        queue-timeout=45 socket-timeout=60 connect-timeout=15 \
        request-timeout=60 inactivity-timeout=0 startup-timeout=15 \
        deadlock-timeout=60 graceful-timeout=15 eviction-timeout=0 \
        restart-interval=0 shutdown-timeout=5 maximum-requests=0
    </Macro>

    Use WSGIProcess app1 25

    WSGIScriptAlias /app1 \
        path-to-app1-work-dir/Scripts/WSGIScript.py process-group=app1

    <Directory path-to-app1-work-dir/Scripts>
        Require all granted
    </Directory>

    Use WSGIProcess app2 10

    WSGIScriptAlias /app2 \
        path-to-app2-work-dir/Scripts/WSGIScript.py process-group=app2

    <Directory path-to-app2-work-dir/Scripts>
        Require all granted
    </Directory>

.. _mod_macro: https://httpd.apache.org/docs/current/mod/mod_macro.html

In the above configurations, we are running only one process per process group, but multiple threads. The first app will use 25 threads, while the second app will use only 10. The WSGI environment variable ``wsgi.multithread`` will be set to ``True``, while ``wsgi.multiprocess`` will be set to ``False``. You can check these settings in your Webware application. The ThreadedAppServer of the legacy Webware for Python 2 used the same single process, multiple threads model, and is the recommended, tried and tested way to run Webware applications. But with Webware for Python 3, you can also configure mod_wsgi and other WSGI servers to run Webware applications using multiple processes, each using one or more threads. This may achieve better performance if you have many requests and your application is CPU-bound, because the GIL_ in Python prevents CPU-bound threads from executing in parallel. For typical I/O-bound web application, which spend most of their time waiting for the database, this is usually not a big problem. For certain applications you may want to try out the multi process model, but you need to be aware of special precautions and limitations that must be considered in this case. See the section `Caveats of Multiprocessing Mode`_ below and the section on `processes and threading`_ in the `mod_wsgi documentation`_.

.. _GIL: https://realpython.com/python-gil/

If you want to restart the daemon process after deploying a new version of the Webware application to the application working directory, you can do so by changing (touching) the WSGI file::

    touch Scripts/WSGIScript.py

The mod_wsgi documentation also explains how to `restart daemon processes`_ by sending a `SIGINT` signal, which can be also done by the Webware application itself, and it also explains how you can `monitor your application for code changes`_ and automatically restart in that case.

.. _restart daemon processes: https://modwsgi.readthedocs.io/en/develop/user-guides/reloading-source-code.html#restarting-daemon-processes
.. _monitor your application for code changes: https://modwsgi.readthedocs.io/en/develop/user-guides/reloading-source-code.html#monitoring-for-code-changes


Other WSGI servers
------------------

Depending on your production environment and the type of your application, it may make sense to deploy Webware applications with `other WSGI servers`_. In the following we will give some advice for configuring some of the more popular WSGI servers to run Webware applications.

.. _other WSGI servers: https://wsgi.readthedocs.io/en/latest/servers.html

Using Bjoern as WSGI server
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Bjoern_ is a fast, lightweight WSGI server for Python, written in C using Marc Lehmann's high performance libev_ event loop and Ryan Dahl's http-parser_.

.. _Bjoern: https://github.com/jonashaag/bjoern
.. _libev: http://software.schmorp.de/pkg/libev.html
.. _http-parser: https://github.com/nodejs/http-parser

You first need to install ``libev4`` and ``libev-devel``, then you can ``pip install bjoern`` into the virtual environment where you already installed Webware.

In order to make use of Bjoern, you need to add the following at the end of the ``Scripts\WSGIScript.py`` file in the application working directory::

    from bjoern import run

    run(application, 'localhost', 8088)

Since Bjoern does not support the WSGI ``write()`` callable, you must configure Webware to not use this mechanism, by using the following settings at the top of the ``Scripts\WSGIScript.py``::

    settings = dict(WSGIWrite=False)

A systemd unit file at ``/etc/systemd/system/bjoern.service`` could look like this::

    [Unit]
    Description=Bjoern WSGI server running Webware application
    After=network.target
    StartLimitIntervalSec=0

    [Install]
    WantedBy=multi-user.target

    [Service]
    User=www-data
    Group=www-data
    PermissionsStartOnly=true
    WorkingDirectory=path-to-app-work-dir
    ExecStart=path-to-virtual-env/bin/python Scripts/WSGIScript.py
    TimeoutSec=600
    Restart=on-failure
    RuntimeDirectoryMode=775

You can then enable and run the service as follows::

    systemctl enable bjoern
    systemctl start bjoern

Using MeinHeld as WSGI server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MeinHeld_ is another lightweight, high performance WSGI server.

.. _MeinHeld: https://github.com/mopemope/meinheld

You first need to ``pip install meinheld`` into the virtual environment where you already installed Webware.

Add the following at the end of the ``Scripts\WSGIScript.py`` file in the application working directory in order to use MeinHeld::

    from meinheld import server

    server.listen(("127.0.0.1", 8080))
    server.run(application)

Similarly to Bjoern, you need to also adapt the settings at the top of the ``Scripts\WSGIScript.py`` file::

    settings = dict(WSGIWrite=False)

Using CherryPy as WSGI server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cherrypy_ is a minimalist Python web framework that also contains a reliable, HTTP/1.1-compliant, WSGI thread-pooled webserver.

.. _Cherrypy: https://cherrypy.org/

TO make use of CherryPy’s WSGI server, add the following at the end of the ``Scripts\WSGIScript.py`` file in the application working directory::

    import cherrypy

    cherrypy.tree.graft(application, '/')
    cherrypy.server.unsubscribe()
    server = cherrypy._cpserver.Server()
    server.socket_host = '127.0.0.1'
    server.socket_port = 8080
    server.thread_pool = 30
    server.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()

Using uWSGI as WSGI server
~~~~~~~~~~~~~~~~~~~~~~~~~~

The uWSGI_ project aims at developing a full stack for building hosting services, and it also contains a WSGI server component.

.. _uWSGI: https://uwsgi-docs.readthedocs.io/en/latest/WSGIquickstart.html

You first need to ``pip install uwsgi`` into the virtual environment where you already installed Webware.

You can start the uWSGI server component as follows::

    cd path-to-app-work-dir
    . ../.venv/bin/activate
    uwsgi --http-socket 127.0.0.1:8080 --threads 30 \\
        --virtualenv path-to-virtual-env --wsgi-file Scripts/WSGIScript.py

You can also create a systemd file to run this automatically when the system boots, as explained above.

Many more `uWSGI configuration options`_ are explained in the uWSGI documentation, we will not go into more details here.

.. _uWSGI configuration options: https://uwsgi-docs.readthedocs.io/en/latest/Options.html

Using Gunicorn as WSGI server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Gunicorn_ is a fast WSGI server for Unix using a pre-fork worker model.

.. _Gunicorn: https://gunicorn.org/

You first need to ``pip install gunicorn`` into the virtual environment where you already installed Webware.

You can start the Gunicorn WSGI server as follows::

    cd path-to-app-work-dir
    . ../.venv/bin/activate
    PYTHONPATH=Scripts gunicorn -b 127.0.0.1:8080 WSGIScript:application

You can also create a systemd file to run this automatically when the system boots, as explained above.

Many more `Gunicorn configuration options`_ are explained in the Gunicorn documentation, we will not go into more details here.

.. _Gunicorn configuration options: https://docs.gunicorn.org/en/latest/configure.html


Sourceless Installs
-------------------

When deploying a Webware application, you do not really need to copy the source code to the production system, it suffices to deploy the compiled compiled Python files. Though this is actually not considered a good practice, and it also does not really help to keep the source code secret (as it can be decompiled pretty easily), there may be reasons why you still want to do this, for instance to impede casual users to tinker with your code on the server.

To do this, you first need to compile all your Python files in the application working directory::

    cd path-to-app-work-dir
    . ../.venv/bin/activate
    python -OO -m compileall -b .

By activating the virtual environment, you make sure that you compile the source files with the proper Python version. The ``-b`` option puts the compiled files as siblings to the source files using the ``.pyc`` extension, which is essential here. The ``-OO`` option removes all assert statements and docstrings from the code.

If you want to serve contexts outside the application working directory, like the default Examples or Admin context, you need to compile these as well, in a similar way.

You can now remove all the source files except the WSGI script and the ``__pycache__`` directories, they are not needed on the production system anymore::

    cd path-to-app-work-dir
    find . -type f -name '*.py' -delete -o \
           -type d -name 'Scripts' -prune -o \
           -type d -name __pycache__ -exec rm -rf {} \+

In order to make this work, you will also need to modify some settings in ``Configs/Application.config``, like this::

    ExtensionsToIgnore = {
        '.py', '.pyo', '.tmpl', '.bak', '.py_bak',
        '.py~', '.psp~', '.html~', '.tmpl~'
    }
    ExtensionCascadeOrder = ['.pyc', '.psp', '.html']
    FilesToHide = {
        '.*', '*~', '*.bak', '*.py_bak', '*.tmpl',
         '*.py', '*.pyo', '__init__.*', '*.config'
    }




Caveats of Multiprocessing Mode
-------------------------------

As explained above, it is possible to operate mod_wsgi and some other WSGI servers in multiprocessing mode, where several processes serve the same Webware application in parallel, or you can run several multithreaded WSGI servers in parallel, maybe even on different machines, and use a load balancer as a reverse proxy to distribute the load between the different servers.

This is totally doable, and may make sense in order to better utilize existing hardware. Because of the the GIL_, a multithreaded Python application will not be able to get the full performance from a multi-core machine when running a CPU-bound application. However, there are some caveats that you need to be aware of:

- The Webware TaskManager will be started with every Application process. If this is not what you want, you can change the ``RunTasks`` configuration setting to False, and run the TaskManager in a dedicated process.
- Some load balancers support "sticky sessions", identifying clients by their session cookies and dispatching them to the same server processes. But usually, in multiprocessing mode, you cannot guarantee that requests from the same client are served by the same process, and it would also partially defeat the whole purpose of running multiple processes. Therefore, the SessionMemoryStore, SessionFileStore and SessionDynamicStore are not suitable in that mode, since the session data that is created in the local memory of one process will not be available in a different process. Also, accessing session files from different processes simultaneously can be problematic. Instead, we recommend changing the ``SessionStore`` configuration setting to use the SessionRedisStore or the SessionMemcachedStore. Storing the session data in the database is also possible, but may degrade performance.
- When caching frequently used data in local memory, this will become less effective and waste memory when running multiple processes. Consider using a distributed caching system such as Redis_ or Memcached_ instead. If you are using the SessionRedisStore or the SessionMemcachedStore, you will need to install one of these systems anyway.
- Webware applications often store global, application wide state in class attributes of servlet classes or elsewhere in local memory. Again, be aware that this does not work anymore if you are running the same application in multiple processes.
- Redirecting standard error and output to the same log file is not supported when running multiple processes, so the ``LogFilename`` setting should be set to None, and a different logging mechanism should be used. When using mod_wsgi you may need to use the ``WSGIRestrictStdout`` directive and log on that level. Future versions of Webware for Python 3 will address this problem and provide proper logging mechanisms instead of just printing to stdout.

.. _Redis: https://redis.io/
.. _Memcached: https://memcached.org/
