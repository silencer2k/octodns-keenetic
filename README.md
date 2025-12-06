## Keenetic DNS proxy provider for octoDNS

An [octoDNS](https://github.com/octodns/octodns/) provider that targets [Keenetic](https://keenetic.com/) routers.

### Installation

#### Command line

```
pip install octodns-keenetic
```

### Configuration

```yaml
providers:
  keenetic:
    class: octodns_keenetic.KeeneticProvider
    host: 192.168.0.1
    login: env/KEENETIC_LOGIN
    password: env/KEENETIC_PASSWORD
    # Ignore unsupported records
    strict_supports: false
```
