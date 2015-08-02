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
Source3:	mod_secuirty.conf
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires:	sed openssl-devel pcre-devel readline-devel GeoIP-devel gd-devel libxslt-devel perl-devel zlib-devel httpd-devel libxml2-devel curl-devel lua-devel
Requires:	openssl pcre readline GeoIP gd
Requires(pre):	shadow-utils

Provides:	webserver mod_security

%if 0%{?rhel} >= 7
BuildRequires:	systemd
%endif

%define user nginx
%define homedir %{_usr}/local/openresty

%description
OpenResty (aka. ngx_openresty) is a full-fledged web application server by bundling the standard Nginx core, lots of 3rd-party Nginx modules, as well as most of their external dependencies.


%prep
%setup -q


%build

# Build mod_security standalone module
cd ../ModSecurity
CFLAGS="%{optflags} $(pcre-config --cflags)" ./configure \
        --enable-standalone-module \
        --enable-shared 
make %{?_smp_mflags}

# Build OpenResty
cd ../%{name}-%{version}
./configure --with-ipv6 --with-pcre-jit --with-luajit --with-http_geoip_module --add-module="../ModSecurity/nginx/modsecurity"
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
%{homedir}/luajit/*
%{homedir}/lualib/*
%{homedir}/nginx
%{homedir}/nginx/html/*
%{homedir}/nginx/logs
%{homedir}/nginx/sbin
%{homedir}/nginx/sbin/nginx
%{homedir}/bin/resty

%{homedir}/nginx/conf
%{homedir}/nginx/conf/fastcgi.conf.default
%{homedir}/nginx/conf/fastcgi_params.default
%{homedir}/nginx/conf/mime.types.default
%{homedir}/nginx/conf/mod_security.conf
%{homedir}/nginx/conf/nginx.conf.default
%{homedir}/nginx/conf/scgi_params.default
%{homedir}/nginx/conf/uwsgi_params.default

%config %{homedir}/nginx/conf/fastcgi.conf
%config %{homedir}/nginx/conf/fastcgi_params
%config %{homedir}/nginx/conf/koi-utf
%config %{homedir}/nginx/conf/koi-win
%config %{homedir}/nginx/conf/mime.types
%config %{homedir}/nginx/conf/nginx.conf
%config %{homedir}/nginx/conf/scgi_params
%config %{homedir}/nginx/conf/uwsgi_params
%config %{homedir}/nginx/conf/win-utf


%postun


%changelog

