![Header](header.png)

<div align="center">

# vpnwall

**Kill-switch VPN для macOS с изоляцией по системным пользователям**

[![License](https://img.shields.io/badge/license-MIT-2C2C2C?style=for-the-badge&labelColor=1E1E1E)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-2C2C2C?style=for-the-badge&logo=python&labelColor=1E1E1E)]()
[![macOS](https://img.shields.io/badge/macos-10.15+-2C2C2C?style=for-the-badge&logo=apple&labelColor=1E1E1E)]()

</div>

Принудительно направляет трафик выбранных приложений исключительно через VPN-интерфейс. При отключении VPN заблокированные приложения теряют весь доступ в интернет. Работает за счёт создания изолированных системных пользователей macOS для каждого приложения и использования правил брандмауэра `pf` (packet filter), ограничивающих их трафик только VPN-интерфейсом.

## ■ Возможности

- ❖ **Принудительный VPN для каждого приложения** — каждое приложение запускается под отдельным системным пользователем
- ❖ **Kill-switch** — нет VPN = нет интернета для настроенных приложений
- ❖ **Правила брандмауэра pf** — блокирует TCP/UDP по пользователю, разрешает только через VPN-интерфейс
- ❖ **Гибкий выбор VPN-интерфейса** — поддерживает конкретный utun или маску `utun+`
- ❖ **LaunchDaemon** — автозапуск при загрузке через включённый plist
- ❖ **Конфигурация JSON** — постоянный реестр приложений в `config.json`
- ❖ **Скрытые пользователи** — системные пользователи с префиксом `_vpnwall_`, скрытые с экрана входа

## ■ Стек

<div align="center">

| Компонент | Технология |
|-----------|------------|
| CLI | Python 3.10+ |
| Брандмауэр | macOS pf (packet filter) |
| Конфигурация | JSON |
| Автозапуск | launchd (plist) |

</div>

## ■ Запуск

```bash
# Add an app to VPN-only mode
sudo vpnwall add Arc

# Enable firewall rules
sudo vpnwall enable

# Run app through VPN
sudo vpnwall run Arc

# Check status
sudo vpnwall status

# Set VPN interface
sudo vpnwall set-interface utun3

# Disable / remove
sudo vpnwall disable
sudo vpnwall remove Arc
```

## ■ Скриншоты

<div align="center">

![Screenshot](screenshots/main.png)

*Главный интерфейс с отображением статуса kill-switch VPN и настроенных приложений*

</div>

## ■ License

MIT © [pluttan](https://github.com/pluttan)
