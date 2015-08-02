Name:		ngx_openresty
Version:	1.9.3.1rc1
Release:	1%{?dist}
Summary:	a fast web app server by extending nginx

Group:		Productivity/Networking/Web/Servers
License:	BSD
URL:		openresty.org
Source0:	http://openresty.org/download/%{name}-%{version}.tar.gz
Source1:	https://github.com/roberthawdon/openresty-rpm-spec/raw/master/nginx.init
Source2:	https://github.com/roberthawdon/openresty-rpm-spec/raw/master/nginx.service
Source3:	https://github.com/roberthawdon/openresty-rpm-spec/raw/master/mod_security.conf
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires:	sed openssl-devel pcre-devel readline-devel GeoIP-devel gd-devel libxslt-devel perl-devel zlib-devel httpd-devel libxml2-devel curl-devel lua-devel
Requires:	openssl pcre readline GeoIP gd
Requires(pre):	shadow-utils

Provides:	webserver mod_security

%if 0%{?rhel} >= 7
BuildRequires:	systemd
%endif

%define user nginx
%define group %{user}
%define homedir %{_usr}/local/openresty
%define nginx_confdir %{_sysconfdir}/nginx
%define nginx_home_tmp      %{homedir}/tmp
%define nginx_confdir       %{_sysconfdir}/nginx
%define nginx_datadir       %{_datadir}/nginx
%define nginx_logdir        %{_localstatedir}/log/nginx
%define nginx_webroot       %{nginx_datadir}/html

%description
OpenResty (aka. ngx_openresty) is a full-fledged web application server by bundling the standard Nginx core, lots of 3rd-party Nginx modules, as well as most of their external dependencies.


%prep
%setup -q


%build

# Build mod_security standalone module
cd ../ModSecurity
./autogen.sh
CFLAGS="%{optflags} $(pcre-config --cflags)" ./configure \
        --enable-standalone-module \
        --enable-shared 
make %{?_smp_mflags}

# Build OpenResty
cd ../%{name}-%{version}
./configure \
    --prefix=%{nginx_datadir} \
    --sbin-path=%{_sbindir}/nginx \
    --conf-path=%{nginx_confdir}/nginx.conf \
    --error-log-path=%{nginx_logdir}/error.log \
    --http-log-path=%{nginx_logdir}/access.log \
    --http-client-body-temp-path=%{nginx_home_tmp}/client_body \
    --http-proxy-temp-path=%{nginx_home_tmp}/proxy \
    --http-fastcgi-temp-path=%{nginx_home_tmp}/fastcgi \
    --http-uwsgi-temp-path=%{nginx_home_tmp}/uwsgi \
    --http-scgi-temp-path=%{nginx_home_tmp}/scgi \
    --with-ipv6 \
    --with-pcre-jit \
    --with-luajit \
    --with-http_geoip_module \
    --add-module="../ModSecurity/nginx/modsecurity"
make %{?_smp_mflags}


%pre
getent group %{user} || groupadd -f -r %{user}
getent passwd %{user} || useradd -M -d %{homedir} -g %{user} -s /bin/nologin %{user}


%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot}
%if 0%{?rhel} <= 6
mkdir -p %{buildroot}/etc/init.d
sed -e 's/%NGINX_CONF_DIR%/%{lua: esc,qty=string.gsub(rpm.expand("%{homedir}"), "/", "\\/"); print(esc)}\/nginx\/conf/g' \
	-e 's/%NGINX_BIN_DIR%/%{lua: esc,qty=string.gsub(rpm.expand("%{homedir}"), "/", "\\/"); print(esc)}\/nginx\/sbin/g' \
	%{SOURCE1} > %{buildroot}/etc/init.d/nginx
%endif
%if 0%{?rhel} >= 7
mkdir -p %{buildroot}/usr/lib/systemd/system
sed -e 's/%NGINX_BIN_DIR%/%{lua: esc,qty=string.gsub(rpm.expand("%{homedir}"), "/", "\\/"); print(esc)}\/nginx\/sbin/g' \
	%{SOURCE2} > %{buildroot}/usr/lib/systemd/system/nginx.service
%endif
cp %{SOURCE3} %{buildroot}/etc/nginx/mod_security.conf

%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
#%{homedir}/*

%if 0%{?rhel} <= 6
%attr(755,root,root) /etc/init.d/nginx
%endif
%if 0%{?rhel} >= 7
%attr(755,root,root) /usr/lib/systemd/system/nginx.service
%endif

%doc LICENSE CHANGES README
%{nginx_datadir}/
%{_bindir}/nginx-upgrade
%{_sbindir}/nginx
%{_mandir}/man3/nginx.3pm*
%{_mandir}/man8/nginx.8*
%{_mandir}/man8/nginx-upgrade.8*
%dir %{nginx_confdir}
%dir %{nginx_confdir}/conf.d
%config(noreplace) %{nginx_confdir}/fastcgi.conf
%config(noreplace) %{nginx_confdir}/fastcgi.conf.default
%config(noreplace) %{nginx_confdir}/fastcgi_params
%config(noreplace) %{nginx_confdir}/fastcgi_params.default
%config(noreplace) %{nginx_confdir}/koi-utf
%config(noreplace) %{nginx_confdir}/koi-win
%config(noreplace) %{nginx_confdir}/mime.types
%config(noreplace) %{nginx_confdir}/mime.types.default
%config(noreplace) %{nginx_confdir}/nginx.conf
%config(noreplace) %{nginx_confdir}/mod_security.conf
%config(noreplace) %{nginx_confdir}/nginx.conf.default
%config(noreplace) %{nginx_confdir}/scgi_params
%config(noreplace) %{nginx_confdir}/scgi_params.default
%config(noreplace) %{nginx_confdir}/uwsgi_params
%config(noreplace) %{nginx_confdir}/uwsgi_params.default
%config(noreplace) %{nginx_confdir}/win-utf
%config(noreplace) %{_sysconfdir}/logrotate.d/nginx
%dir %{perl_vendorarch}/auto/nginx
%{perl_vendorarch}/nginx.pm
%{perl_vendorarch}/auto/nginx/nginx.so
%attr(700,%{nginx_user},%{nginx_group}) %dir %{nginx_home}
%attr(700,%{nginx_user},%{nginx_group}) %dir %{nginx_home_tmp}
%attr(700,%{nginx_user},%{nginx_group}) %dir %{nginx_logdir}


%postun


%changelog

