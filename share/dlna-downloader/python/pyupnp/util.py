

def path_from_url(url):
   return '/'+url.split('/', 3)[3]


def host_from_url(url):
   try:
      host = url.split('/')[2].split(':')[0]
      return host
   except:
      return 'Unkown ip'


def port_from_url(url):
   try:
      port = int(url.split('/')[2].split(':')[1])
      return port
   except:
      return 80


def http_header_to_dict(header):
    dict = {}
    line_no = 1
    try:
        for line in header.split(b'\r\n'):
            if not line:
                break

            try:
                key, value = line.decode().split(':', maxsplit=1)
                dict[key.strip().upper()] = value.strip()
            except:
                dict[line.decode().strip()] = str(line_no)
                pass

        line_no += 1
    except:
        pass

    return dict


def XPath(elementtree, path):
   namespaces = {}
   namespaces['s'] = 'http://schemas.xmlsoap.org/soap/envelope/'
   namespaces['u'] = 'urn:schemas-upnp-org:service:ContentDirectory:1'
   namespaces['d'] = 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/'
   namespaces['dlna'] = 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/'
   namespaces['dc'] = 'http://purl.org/dc/elements/1.1/'
   namespaces['upnp'] = 'urn:schemas-upnp-org:metadata-1-0/upnp/'
   
   return elementtree.find(path, namespaces)
